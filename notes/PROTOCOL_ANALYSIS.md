# Protocol Architecture Analysis: vuer-ts and zaku-service

Key Files in Existing Repositories:

**vuer-ts** (WebSocket-based real-time scene graph):
- `/Users/ge/fortyfive/vuer-ts/src/vuer/interfaces.tsx` - Event type definitions
- `/Users/ge/fortyfive/vuer-ts/src/vuer/store.tsx` - Store pattern with reducers
- `/Users/ge/fortyfive/vuer-ts/src/vuer/websocket.tsx` - WebSocket transport
- `/Users/ge/fortyfive/vuer-ts/src/vuer/sceneGraph/events.ts` - Scene graph events
- `/Users/ge/fortyfive/vuer-ts/src/vuer/sceneGraph/eventHelpers.ts` - Event factories

**zaku-service** (HTTP-based task queue and pub/sub):
- `/Users/ge/fortyfive/zaku-service/zaku/interfaces.py` - Type definitions (Payload, ZData)
- `/Users/ge/fortyfive/zaku-service/zaku/client.py` - Client API (RPC, PubSub, TaskQ)
- `/Users/ge/fortyfive/zaku-service/zaku/server.py` - Server implementation
- `/Users/ge/fortyfive/zaku-service/docs/examples/` - Usage patterns (queue, pubsub, RPC)


## 1. Data Serialization Format

### vuer-ts: MessagePack with TypeScript Types

**Location**: `/Users/ge/fortyfive/vuer-ts/src/vuer/websocket.tsx` (lines 13, 224)

```typescript
import { pack, unpack } from 'msgpackr';

// Serialization (client → server)
const message = pack(event);
if (event) sendMessage(message);

// Deserialization (server → client)
const buf = await message.data.arrayBuffer();
const event = unpack(buf);
```

**Format Strategy**:
- **Development**: JSON-compatible (human-readable)
- **Production**: MessagePack binary (efficient)
- **Dual-mode**: Seamless switching between formats
- **Message Ordering**: Queue-based processing ensures strict event ordering

### zaku-service: MessagePack with Payload Encoding

**Location**: `/Users/ge/fortyfive/zaku-service/zaku/interfaces.py` (lines 26-136)

```python
class Payload(SimpleNamespace):
    greedy = True  # Enable aggressive ZData conversion
    
    def serialize(self):
        payload = self.__dict__
        if self.greedy:
            # Convert numpy/torch arrays to efficient binary format
            data = {k: ZData.encode(v) for k, v in payload.items()}
            data["_greedy"] = self.greedy
            msg = msgpack.packb(data, use_bin_type=True)
        else:
            msg = msgpack.packb(payload, use_bin_type=True)
        return msg

    @staticmethod
    def deserialize(payload) -> Dict:
        unpacked = msgpack.unpackb(payload, raw=False)
        is_greedy = unpacked.pop("_greedy", None)
        if is_greedy:
            data = {}
            for k, v in unpacked.items():
                data[k] = ZData.decode(v)
            return data
        return unpacked
```

**Supported Data Types** (ZData):
- `numpy.ndarray` - Stored as binary + dtype + shape metadata
- `torch.Tensor` - Converted to CPU numpy, then binary encoded
- `PIL.Image` - PNG/Format preserved
- `generic` - Passthrough for standard types

**Schema**:
```python
{
    "ztype": "numpy.ndarray|torch.Tensor|image|generic",
    "b": bytes,           # Binary data
    "dtype": str,         # Data type string
    "shape": tuple        # Shape for reshaping
}
```

---

## 2. Remote Procedural Call (RPC) Patterns

### vuer-ts: Simple Request-Response via Events

**Architecture**: Event-based unification (no dedicated RPC types initially)

**Location**: `/Users/ge/fortyfive/vuer-ts/src/vuer/interfaces.tsx` (lines 96-100)

```typescript
// Server RPC requests include UUID for response correlation
export interface ServerRPC extends ServerEvent {
  uuid: string;      // Unique request identifier
  rtype: string;     // RPC type/method name
}

export interface ServerEvent<T = unknown | Record<string, unknown>>
  extends EventType {
  data: T;
}
```

### zaku-service: Request-Response with Topic Routing

**Pattern**: Implicit RPC via pub/sub with response topic injection

**Location**: `/Users/ge/fortyfive/zaku-service/docs/examples/03_remote_procedural_call.md`

#### Simple RPC (Single Response)

```python
# Client side - initiates RPC
from zaku import TaskQ

queue = TaskQ(name="ZAKU_TEST:debug-rpc-queue", uri="http://localhost:9000")
result = queue.rpc(seed=100, _timeout=5)
assert result["seed"] == 100
```

**Under the hood** (`/Users/ge/fortyfive/zaku-service/zaku/client.py`, lines 371-401):

```python
def rpc(self, *args, _timeout=1.0, **kwargs):
    request_id = uuid4()
    topic_name = f"rpc-{request_id}"
    
    # Inject response topic into request
    self.add({
        "_request_id": topic_name,    # Response topic
        "_args": args,
        **kwargs,
    })
    
    # Wait for response on injected topic
    return self.subscribe_one(topic_name, timeout=_timeout)
```

**Worker side**:

```python
def worker_process(queue_name):
    queue = TaskQ(name=queue_name, uri="http://localhost:9000")
    
    while True:
        with queue.pop() as job:
            if job is None:
                continue
            
            # Extract response topic
            topic = job.pop("_request_id")
            
            # Process job
            sleep(1.0)
            
            # Send response back
            queue.publish(
                {"result": "good", **job},
                topic=topic,  # Response routed to injected topic
            )
```

#### Streaming RPC (Multiple Responses)

```python
# Client
stream = queue.rpc_stream(start=5, end=10, _timeout=5)
for i, result in enumerate(stream):
    print(result)
    assert result["value"] == i + 5
```

**Worker**:

```python
def streamer_process(queue_name):
    queue = TaskQ(name=queue_name, uri="http://localhost:9000")
    
    while True:
        with queue.pop() as job:
            topic = job.pop("_request_id")
            
            # Stream multiple results
            for i in range(job["start"], job["end"]):
                sleep(0.1)
                queue.publish({"value": i}, topic=topic)
```

**RPC Flow Diagram**:
```
Client                          Server                    Worker
  |                              |                          |
  +------- rpc(seed=100) ------->|                          |
  |  (injects _request_id)       |                          |
  |                              +---- queue.pop() -------->|
  |                              |                          |
  |                              |  [Processing...]         |
  |                              |                          |
  |                              |<--- publish(result) -----+
  |                              |  (to response topic)     |
  |<-- subscribe_one(topic) -----+                          |
  |  (waits for response)        |                          |
```

---

## 3. Event Protocol Structure

### vuer-ts: Base Event Types

**Location**: `/Users/ge/fortyfive/vuer-ts/src/vuer/interfaces.tsx`

#### Core Event Interface (lines 79-101)

```typescript
export interface EventType {
  ts: number;                // Timestamp
  etype: string;             // Event type (SET, ADD, UPDATE, REMOVE, etc.)
}

export interface ClientEvent<T = unknown | Record<string, unknown>>
  extends EventType {
  key?: string;              // Optional node/scene key
  value?: T;                 // Event payload
}

export interface ServerEvent<T = unknown | Record<string, unknown>>
  extends EventType {
  data: T;                   // Server response data
}

export interface ServerRPC extends ServerEvent {
  uuid: string;              // Request correlation ID
  rtype: string;             // RPC method type
}
```

#### Scene Graph Event Types

**Location**: `/Users/ge/fortyfive/vuer-ts/src/vuer/sceneGraph/events.ts`

```typescript
// SET: Initialize/replace scene
export interface SetEvent extends ServerEvent {
  data: { key?: string; tag: string } & SceneType;
}

// ADD: Append nodes to scene
export interface AddEvent extends ServerEvent {
  data: { nodes: Node[]; to: string | SceneChildrenKeyT };
}

// UPDATE: Modify existing nodes (partial updates)
export interface UpdateEvent extends ServerEvent {
  data: { nodes: UpdateNodeType[] };
}

// UPSERT: Insert or update (idempotent)
export interface UpsertEvent extends ServerEvent {
  data: { nodes: Node[]; to: string | SceneChildrenKeyT };
}

// REMOVE: Delete nodes
export interface RemoveEvent extends ServerEvent {
  data: { keys: string[] };
}

// TIMEOUT: Scheduled execution
export interface TimeoutEvent extends ServerEvent {
  data: { timeout: number; fn: string | (() => void) };
}
```

### Event Operation Builders

**Location**: `/Users/ge/fortyfive/vuer-ts/src/vuer/sceneGraph/eventHelpers.ts`

```typescript
// Factory functions for creating events
const SetOp = (scene, ts?) => ({
  ts: ts || Date.now(),
  etype: 'SET',
  data: scene,
});

const AddOp = (nodes, to = 'children', ts?) => ({
  ts: ts || Date.now(),
  etype: 'ADD',
  data: { nodes, to },
});

const UpdateOp = (nodes, ts?) => ({
  ts: ts || Date.now(),
  etype: 'UPDATE',
  data: { nodes },
});

const RemoveOp = (keys, ts?) => ({
  ts: ts || Date.now(),
  etype: 'REMOVE',
  data: { keys },
});
```

### zaku-service: Task/PubSub Events

**Location**: `/Users/ge/fortyfive/zaku-service/docs/examples/02_pubsub.md`

#### PubSub Pattern (Ephemeral Messages)

```python
# Publisher
def publish(topic_id="example-topic"):
    for i in range(5):
        n = task_queue.publish(
            {"step": i, "param_2": f"key-{i}"}, 
            topic=topic_id
        )
        print("published to", n, "subscribers")

# Single Subscriber
result = task_queue.subscribe_one("example-topic", timeout=5)

# Streaming Subscriber
stream = task_queue.subscribe_stream("example-topic", timeout=5)
for i, result in enumerate(stream):
    print(result)
```

#### Task Queue Pattern (Persistent Jobs)

```python
# Add persistent job
queue.add({"job_id": i, "seed": i * 100})

# Take (grab) job with atomic status update
job_id, job = queue.take()  # Status: created → in_progress

# Mark complete
queue.mark_done(job_id)     # Removes job

# Mark for retry
queue.mark_reset(job_id)    # Status: in_progress → created

# Context manager (auto-handles success/failure)
with queue.pop() as job:
    if job is None:
        print("No job")
    process(job)            # Auto marks done on success
                            # Auto marks reset on exception
```

---

## 4. Event Handling & Publication

### vuer-ts: Store-based Event System

**Location**: `/Users/ge/fortyfive/vuer-ts/src/vuer/store.tsx`

#### Store Architecture (Reducer + Subscriber Pattern)

```typescript
export type ReducerType<E extends EventType> = (event: E) => E;
export type HandlerType<E extends EventType> = (event: E) => void;

export class Store<E extends EventType> {
  reducers: Record<string, Record<string, ReducerType<E>>>;
  subscribers: Record<string, Record<string, HandlerType<E>>>;

  // Add a reducer (transforms event before publication)
  addReducer(eventType: string, reducer: ReducerType<E>, id?: string) {
    // ... registration
  }

  // Subscribe to events
  subscribe(
    eventType: string | RegExp,
    handler: HandlerType<E>,
    id?: string
  ) {
    // Supports string, regex, or '*' (wildcard) matching
  }

  // Publish event (runs through reducers first, then subscribers)
  publish(event: E): E | void {
    const eventType = event.etype;
    
    // 1. Apply all reducers for this event type
    const reducers = this.reducers[eventType] || {};
    for (const id in reducers) {
      event = reducers[id](event);
    }

    // 2. Call all subscribers
    const subs = this.subscribers[eventType] || {};
    for (const id in subs) {
      setTimeout(() => {
        subs[id](event);
      }, 0);  // Async delivery
    }

    // 3. Check regex subscribers
    for (const key in this.subscribers) {
      if (key.startsWith('regex@')) {
        for (const id in this.subscribers[key]) {
          const sub = this.subscribers[key][id];
          if (sub.type === 'regex' && sub.regex.test(eventType)) {
            setTimeout(() => {
              sub.handler(event);
            }, 0);
          }
        }
      }
    }

    // 4. Call wildcard subscribers
    const multicast = this.subscribers['*'] || {};
    for (const id in multicast) {
      setTimeout(() => {
        multicast[id](event);
      }, 0);
    }

    return event;
  }
}
```

#### WebSocket Transport

**Location**: `/Users/ge/fortyfive/vuer-ts/src/vuer/websocket.tsx` (lines 72-168)

```typescript
// Sequential message processing with queue
const messageQueue = useRef<MessageEvent[]>([]);
const isProcessing = useRef<boolean>(false);

const processMessageQueue = useCallback(async () => {
  if (isProcessing.current || messageQueue.current.length === 0) return;
  
  isProcessing.current = true;
  
  while (messageQueue.current.length > 0) {
    const message = messageQueue.current.shift();
    try {
      const buf = await message.data.arrayBuffer();
      const event = unpack(buf);
      
      if (paramsOnMessage) {
        paramsOnMessage(event);
      }
      
      // Strict ordering: downlink.publish in exact arrival order
      downlink.publish(event);
    } catch (error) {
      console.error('Error processing WebSocket message:', error);
    }
  }
  
  isProcessing.current = false;
}, [paramsOnMessage, downlink]);

// Message handler queues and triggers processing
const onMessage = useCallback((message: MessageEvent) => {
  if (!message?.data?.arrayBuffer) return;
  
  messageQueue.current.push(message);
  
  if (!isProcessing.current) {
    processMessageQueue();
  }
}, [processMessageQueue]);
```

### zaku-service: Job State Management

**Location**: `/Users/ge/fortyfive/zaku-service/zaku/interfaces.py` (lines 155-300)

#### Job Lifecycle

```python
class Job(SimpleNamespace):
    created_ts: float
    status: Literal[None, "in_progress", "created"] = "created"
    grab_ts: float = None

# State transitions
created -----> in_progress -----> (done/removed)
                    |
                    +-----> created (on reset/retry)
```

#### Redis Storage with JSON Search

```python
# Redis index for efficient querying
schema = (
    NumericField("$.created_ts", as_name="created_ts"),
    TagField("$.status", as_name="status"),
    NumericField("$.grab_ts", as_name="grab_ts"),
)

# Queries
Query("@status:{created}")              # Find available jobs
Query("@status:{in_progress}")          # Find processing jobs
Query(f"@status:{{in_progress}} @grab_ts:[0 {time() - ttl}]")  # Stale jobs
```

#### Atomic Operations (Lua Scripts)

```python
lua_script = """
local index_name = KEYS[1]
local current_time = ARGV[1]

-- Atomic: find + update in single operation
local job_result = redis.call('FT.SEARCH', index_name, '@status:{created}', 'LIMIT', '0', '1')
if tonumber(job_result[1]) == 0 then
    return {nil, nil}
end

local job_id = job_result[2]
redis.call('JSON.SET', job_id, '$.status', '"in_progress"')
redis.call('JSON.SET', job_id, '$.grab_ts', current_time)
return {job_id}
"""
```

#### MongoDB Integration (Large Payloads)

```python
# Payloads > threshold → MongoDB, ID → Redis
await mongo_client.store_payload(collection_name, job_id, payload)
entry_key = f"{prefix}:{{{queue}}}:{job_id}"
await r.json().set(entry_key, ".", vars(job))  # Metadata only

# Retrieval: Fetch metadata from Redis, payload from MongoDB
payload = await mongo_client.retrieve_payload(collection_name, job_id)
```

---

## 5. Protocol Flow Comparison

### vuer-ts Event Flow

```
User/App
    |
    v
ClientEvent (pack with msgpackr)
    |
    v [WebSocket]
    |
Server Receives
    |
    v
unpack(arrayBuffer)
    |
    v
downlink.publish(ServerEvent)
    |
    +---> reducers (transform)
    |
    +---> subscribers (handler)
    |
    +---> regex subscribers (pattern matching)
    |
    +---> wildcard subscribers ('*')
```

### zaku-service Job Flow

```
Client
  |
  +-- queue.add(job_data)
  |      |
  |      v [HTTP PUT /tasks]
  |      |
  |   Server (TaskServer)
  |      |
  |      v Payload.serialize() + msgpack
  |      |
  |      v Redis: store metadata + MongoDB: store payload
  |
  +-- queue.rpc(params)
  |      |
  |      v Inject _request_id (response topic)
  |      |
  |      v queue.add() with _request_id
  |
Worker
  |
  +-- queue.pop() / with queue.pop()
  |      |
  |      v [HTTP POST /tasks]
  |      |
  |      v Server: Lua script (atomic take)
  |      |
  |      v Get job_id + payload
  |      |
  |      v Process
  |
  +-- queue.publish(result, topic=_request_id)
       |
       v [HTTP PUT /publish]
       |
       v Server: Job.publish() 
       |
       v Redis: publish to topic
       |
       v MongoDB: store payload (if large)
       |
       v PubSub subscribers notified

Client
  |
  +-- queue.subscribe_one(response_topic)
       |
       v [HTTP POST /subscribe_one]
       |
       v Server: Job.subscribe() with timeout
       |
       v Wait for message on topic
```

---

## 6. Protocol Documentation Artifacts

### vuer-ts Design (Current)
- **File**: `/Users/ge/fortyfive/vuer-ts/src/vuer/interfaces.tsx`
- **Structure**: TypeScript interfaces defining event contracts
- **Approach**: Type-driven (compile-time validation)

### zaku-service Documentation
- **Examples**: `/Users/ge/fortyfive/zaku-service/docs/examples/`
  - `01_simple_queue.md` - Basic queue operations
  - `02_pubsub.md` - Pub/Sub pattern
  - `03_remote_procedural_call.md` - RPC pattern
- **API Reference**: `/Users/ge/fortyfive/zaku-service/docs/api/`
  - `interfaces.md` - Type definitions
  - `server.md` - Server configuration
  - `taskq.md` - Client API

### vuer-message-protocol (Proposed)
- **Location**: `/Users/ge/fortyfive/vuer-message-protocol/`
- **Design Goals** (from `DESIGN_SCRATCH.md`):
  - Language-agnostic (TS, Python, Swift, C++)
  - Dual-mode: JSON (dev) + MessagePack (prod)
  - Combines JSON-RPC simplicity with gRPC efficiency
  - Support async, streaming, and event-driven patterns

**Proposed Structure**:
```
vuer-message-protocol/
├── protocol/           # Shared definitions
├── vmp-ts/             # TypeScript implementation
├── vmp-py/             # Python implementation
├── vmp-swift/          # Swift implementation
└── vmp-cpp/            # C++ implementation
```

---

## 7. Key Implementation Patterns

### Pattern 1: Message Ordering Guarantee (vuer-ts)

**Problem**: Async arrayBuffer() operations can race

**Solution**: Sequential processing queue

```typescript
// Preserve exact arrival order through message queue
messageQueue.current.push(message);  // Immediate append
processMessageQueue();               // Async processing in order
```

### Pattern 2: Implicit RPC via PubSub (zaku-service)

**Problem**: How to route responses?

**Solution**: Inject response topic into request

```python
_request_id = f"rpc-{uuid4()}"  # Unique response topic
# Client adds to queue with _request_id
# Worker extracts _request_id and publishes response to that topic
# Client subscribes to that specific topic
```

### Pattern 3: Dual Serialization (zaku-service)

**Problem**: Different data types need different encodings

**Solution**: ZData wrapper with type metadata

```python
{
    "ztype": "torch.Tensor",
    "b": binary_bytes,
    "dtype": "float32",
    "shape": [3, 224, 224]
}
```

### Pattern 4: Reducer + Subscriber Pipeline (vuer-ts)

**Problem**: Need to transform AND distribute events

**Solution**: Two-phase processing

```typescript
// Phase 1: Reducers transform event
event = reducer(event);

// Phase 2: Subscribers react to event
subscriber(event);
```

---

## 8. Recommendations for vuer-message-protocol

1. **Start with Event Contracts** (like vuer-ts interfaces)
   - Define canonical event types across languages
   - Use OpenAPI/AsyncAPI for documentation

2. **Support Streaming**
   - Server-sent events (HTTP)
   - WebSocket bidirectional
   - gRPC-like streaming with backpressure

3. **RPC Pattern**
   - Follow zaku's injection model for response routing
   - Include request_id/correlation_id in all RPCs
   - Support both single-response and streaming responses

4. **Serialization Options**
   - JSON (development/debugging)
   - MessagePack (production)
   - Protobuf (future, if needed)

5. **Error Handling**
   - Include error_code and error_message in responses
   - Distinguish client vs. server errors
   - Support structured error payloads

6. **Code Generation**
   - TypeScript: From interface definitions
   - Python: From pydantic models or dataclasses
   - Swift/C++: From protobuf or schema definitions

