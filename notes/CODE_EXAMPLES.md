# Code Examples: vuer-ts and zaku-service Protocol Implementations

This document provides specific, runnable code examples from vuer-ts and zaku-service implementations.

---

## 1. WebSocket Message Serialization

### vuer-ts: MessagePack Serialization with Ordering Guarantee

**Source**: `/Users/ge/fortyfive/vuer-ts/src/vuer/websocket.tsx` (lines 72-241)

```typescript
import { pack, unpack } from 'msgpackr';
import { useWebSocket } from 'react-use-websocket';

// === SENDING (Client → Server) ===
const sendMsg = useCallback<msgFn>(
  (event: ClientEvent) => {
    if (!readyState) return;
    
    // Serialize using MessagePack
    const message = pack(event);
    if (event) sendMessage(message);
  },
  [readyState, sendMessage],
);

// === RECEIVING (Server → Client) with Ordering ===
const messageQueue = useRef<MessageEvent[]>([]);
const isProcessing = useRef<boolean>(false);

// Sequential processing to guarantee order
const processMessageQueue = useCallback(async () => {
  if (isProcessing.current || messageQueue.current.length === 0) {
    return;
  }

  isProcessing.current = true;

  // Process all queued messages sequentially
  while (messageQueue.current.length > 0) {
    const message = messageQueue.current.shift();

    try {
      // Deserialize with guaranteed ordering
      const buf = await message.data.arrayBuffer();
      const event = unpack(buf);

      // Call external handler if provided
      if (typeof paramsOnMessage === 'function') {
        paramsOnMessage(event);
      }

      // Publish in strict order to downlink
      downlink.publish(event);
    } catch (error) {
      console.error('Error processing WebSocket message:', error);
    }
  }

  isProcessing.current = false;
}, [paramsOnMessage, downlink]);

// Incoming message handler - queues for sequential processing
const onMessage = useCallback(
  (message: MessageEvent) => {
    if (!message?.data?.arrayBuffer) return;

    // Add message to queue to preserve order
    messageQueue.current.push(message);

    // Start processing if not already running
    if (!isProcessing.current) {
      processMessageQueue();
    }
  },
  [processMessageQueue],
);
```

### Key Points

1. **Dual-mode Serialization**: `msgpackr` handles both JSON and binary
2. **Message Ordering**: Queue-based processing prevents race conditions
3. **Non-blocking Deserialization**: arrayBuffer() is async but processed sequentially

---

## 2. Event Types and Contracts

### vuer-ts: Complete Event Type System

**Source**: `/Users/ge/fortyfive/vuer-ts/src/vuer/interfaces.tsx`

```typescript
// Base event interface
export interface EventType {
  /** Timestamp of the event */
  ts: number;
  /** Event type identifier */
  etype: string;
}

// Client-originated events
export interface ClientEvent<T = unknown | Record<string, unknown>>
  extends EventType {
  key?: string;        // Optional identifier for the entity
  value?: T;           // Payload data
}

// Server-sent events
export interface ServerEvent<T = unknown | Record<string, unknown>>
  extends EventType {
  data: T;             // Response data
}

// Server RPC - includes correlation ID
export interface ServerRPC extends ServerEvent {
  uuid: string;        // Unique request ID for response routing
  rtype: string;       // RPC method type
}
```

### vuer-ts: Scene Graph Events

**Source**: `/Users/ge/fortyfive/vuer-ts/src/vuer/sceneGraph/events.ts`

```typescript
export interface SetEvent extends ServerEvent {
  data: { key?: string; tag: string } & SceneType;
}

export interface AddEvent extends ServerEvent {
  data: { nodes: Node[]; to: string | SceneChildrenKeyT };
}

export interface UpdateEvent extends ServerEvent {
  data: { nodes: UpdateNodeType[] };
}

export interface UpsertEvent extends ServerEvent {
  data: { nodes: Node[]; to: string | SceneChildrenKeyT };
}

export interface RemoveEvent extends ServerEvent {
  data: { keys: string[] };
}

export interface TimeoutEvent extends ServerEvent {
  data: { timeout: number; fn: string | (() => void) };
}
```

### Event Factory Functions

**Source**: `/Users/ge/fortyfive/vuer-ts/src/vuer/sceneGraph/eventHelpers.ts`

```typescript
export const SetOp = (
  scene: { tag: string } & SceneType,
  ts?: number,
): SetEvent => {
  return {
    ts: ts || Date.now(),
    etype: 'SET',
    data: scene,
  };
};

export const AddOp = (
  nodes: Node[],
  to: string = 'children',
  ts?: number,
): AddEvent => {
  return {
    ts: ts || Date.now(),
    etype: 'ADD',
    data: {
      nodes,
      to,
    },
  };
};

export const UpdateOp = (nodes: UpdateNodeType[], ts?: number): UpdateEvent => {
  return {
    ts: ts || Date.now(),
    etype: 'UPDATE',
    data: {
      nodes,
    },
  };
};

export const RemoveOp = (keys: string[], ts?: number): RemoveEvent => {
  return {
    ts: ts || Date.now(),
    etype: 'REMOVE',
    data: {
      keys,
    },
  };
};
```

---

## 3. Event Store Pattern

### vuer-ts: Store with Reducers and Subscribers

**Source**: `/Users/ge/fortyfive/vuer-ts/src/vuer/store.tsx` (lines 1-169)

```typescript
import uuid4 from 'uuid4';
import { EventType } from './interfaces';

// Type definitions
export type ReducerType<E extends EventType> = (event: E) => E;
export type HandlerType<E extends EventType> = (event: E) => void;

export type reducersType<E extends EventType> = Record<
  string,
  Record<string, ReducerType<E>>
>;

export type handlersType<E extends EventType> = Record<
  string,
  Record<
    string,
    | HandlerType<E>
    | {
        type: 'regex';
        regex: RegExp;
        handler: HandlerType<E>;
      }
  >
>;

/**
 * Event store with reducer and subscriber pattern
 */
export class Store<E extends EventType> {
  reducers: reducersType<E>;
  subscribers: handlersType<E>;

  constructor() {
    this.reducers = {};
    this.subscribers = {};
  }

  /**
   * Add a reducer function for specific event type
   * Reducers transform events before publication
   */
  addReducer(eventType: string, reducer: ReducerType<E>, id?: string) {
    const uuid = id || uuid4();
    if (!this.reducers[eventType]) {
      this.reducers[eventType] = {};
    }
    this.reducers[eventType][uuid] = reducer;
    return () => {
      delete this.reducers[eventType][uuid];
    };
  }

  /**
   * Subscribe to events by type, regex, or wildcard
   */
  subscribe(eventType: string | RegExp, handler: HandlerType<E>, id?: string) {
    const uuid = id || uuid4();

    if (typeof eventType === 'string') {
      if (!this.subscribers[eventType]) {
        this.subscribers[eventType] = {};
      }
      this.subscribers[eventType][uuid] = handler;
    } else {
      // Regex subscription
      const regexKey = `regex@${uuid}`;
      if (!this.subscribers[regexKey]) {
        this.subscribers[regexKey] = {};
      }
      this.subscribers[regexKey][uuid] = {
        type: 'regex',
        regex: eventType,
        handler,
      };
    }

    return () => {
      if (typeof eventType === 'string') {
        delete this.subscribers[eventType][uuid];
      } else {
        const regexKey = `regex@${uuid}`;
        delete this.subscribers[regexKey][uuid];
      }
    };
  }

  /**
   * Publish event through reducers and to all subscribers
   */
  publish(event: E): E | void {
    if (!event) return;
    const eventType = event.etype;

    // Phase 1: Apply all reducers (transforms event)
    const reducers = this.reducers[eventType] || {};
    for (const id in reducers) {
      const reducer = this.reducers[eventType][id];
      event = reducer(event);
    }

    // Phase 2: Call specific event subscribers (async)
    const subs = this.subscribers[eventType] || {};
    for (const id in subs) {
      const handler = subs[id] as HandlerType<E>;
      setTimeout(() => {
        handler(event);
      }, 0);
    }

    // Phase 3: Check regex-based subscribers
    for (const key in this.subscribers) {
      if (key.startsWith('regex@')) {
        for (const id in this.subscribers[key]) {
          const subscriber = this.subscribers[key][id];
          if (
            typeof subscriber === 'object' &&
            'type' in subscriber &&
            subscriber.type === 'regex' &&
            subscriber.regex.test(eventType)
          ) {
            setTimeout(() => {
              subscriber.handler(event);
            }, 0);
          }
        }
      }
    }

    // Phase 4: Call wildcard subscribers
    const multicast = this.subscribers['*'] || {};
    for (const id in multicast) {
      const handler = multicast[id] as HandlerType<E>;
      setTimeout(() => {
        handler(event);
      }, 0);
    }

    return event;
  }
}
```

### Usage Example

```typescript
// Create a store
const downlink = new Store<ServerEvent>();

// Add a reducer (transforms incoming events)
downlink.addReducer('ADD', (event) => {
  console.log('Normalizing ADD event...');
  return {
    ...event,
    data: {
      ...event.data,
      timestamp: Date.now(),
    },
  };
});

// Subscribe to specific event type
downlink.subscribe('ADD', (event) => {
  console.log('ADD handler:', event);
});

// Subscribe with regex pattern
downlink.subscribe(/UPDATE|UPSERT/, (event) => {
  console.log('Pattern handler:', event.etype);
});

// Subscribe to all events
downlink.subscribe('*', (event) => {
  console.log('Wildcard handler:', event.etype);
});

// Publish an event
downlink.publish({
  ts: Date.now(),
  etype: 'ADD',
  data: {
    nodes: [{ key: 'node1', tag: 'mesh' }],
    to: 'children',
  },
});
```

---

## 4. RPC Patterns

### zaku-service: Request-Response with Topic Injection

**Source**: `/Users/ge/fortyfive/zaku-service/zaku/client.py` (lines 371-439)

#### Simple RPC

```python
def rpc(self, *args, _timeout=1.0, **kwargs):
    """
    Synchronous RPC call with single response
    """
    from uuid import uuid4

    # Generate unique response topic
    request_id = uuid4()
    topic_name = f"rpc-{request_id}"

    # Add job with injected response topic
    self.add(
        {
            "_request_id": topic_name,  # Client will listen on this
            "_args": args,
            **kwargs,
        }
    )

    # Wait for response on injected topic
    return self.subscribe_one(topic_name, timeout=_timeout)
```

#### Streaming RPC

```python
def rpc_stream(
    self,
    *args,
    _timeout=1.0,
    **kwargs,
):
    """
    Streaming RPC with multiple responses
    """
    from uuid import uuid4

    request_id = uuid4()
    topic_name = f"rpc-{request_id}"

    # Add job with injected response topic
    self.add(
        {
            "_request_id": topic_name,
            "_args": args,
            **kwargs,
        }
    )

    # Stream responses from injected topic
    return self.subscribe_stream(topic_name, timeout=_timeout)
```

#### Client Usage

```python
from zaku import TaskQ

# Initialize client
queue = TaskQ(name="my-rpc-queue", uri="http://localhost:9000")

# Simple RPC call
result = queue.rpc(seed=100, _timeout=5)
print(result)  # {"seed": 100, "result": "good"}

# Streaming RPC
stream = queue.rpc_stream(start=5, end=10, _timeout=5)
for result in stream:
    print(result)  # Receives multiple messages
```

#### Worker Implementation

```python
from zaku import TaskQ
from time import sleep

def worker_process(queue_name):
    """Worker that processes RPC requests"""
    queue = TaskQ(name=queue_name, uri="http://localhost:9000")

    while True:
        with queue.pop() as job:
            if job is None:
                sleep(0.1)
                continue

            # Extract response topic
            response_topic = job.pop("_request_id")
            args = job.pop("_args", ())

            # Process the request
            sleep(1.0)  # Simulate work

            # Send response back to client via injected topic
            queue.publish(
                {"result": "good", **job},
                topic=response_topic,
            )

def streaming_worker(queue_name):
    """Worker that streams multiple responses"""
    queue = TaskQ(name=queue_name, uri="http://localhost:9000")

    while True:
        with queue.pop() as job:
            if job is None:
                sleep(0.1)
                continue

            response_topic = job.pop("_request_id")

            # Stream multiple results
            for i in range(job["start"], job["end"]):
                sleep(0.1)
                queue.publish(
                    {"value": i, "step": i - job["start"]},
                    topic=response_topic,
                )
```

---

## 5. Data Serialization with Type Encoding

### zaku-service: ZData Encoding System

**Source**: `/Users/ge/fortyfive/zaku-service/zaku/interfaces.py` (lines 26-99)

```python
import msgpack
import numpy as np
from io import BytesIO
from typing import Union, Dict

class ZData:
    """
    Handles encoding and decoding of various data types
    for efficient binary transmission
    """

    @staticmethod
    def encode(data: Union["torch.Tensor", np.ndarray]):
        """Convert arrays and tensors to z-format"""
        import torch
        from PIL.Image import Image

        T = type(data)

        # Handle PIL Images
        if isinstance(data, Image):
            with BytesIO() as buffer:
                data.save(buffer, format=data.format or "PNG")
                binary = buffer.getvalue()
            return dict(ztype="image", b=binary)

        # Handle NumPy arrays
        elif T is np.ndarray:
            binary = data.tobytes()
            return dict(
                ztype="numpy.ndarray",
                b=binary,
                dtype=str(data.dtype),
                shape=data.shape,
            )

        # Handle PyTorch tensors
        elif T is torch.Tensor:
            # Convert to CPU numpy, then to binary
            np_v = data.cpu().numpy()
            binary = np_v.tobytes()
            return dict(
                ztype="torch.Tensor",
                b=binary,
                dtype=str(np_v.dtype),
                shape=np_v.shape,
            )

        else:
            # Passthrough for basic types
            return data

    @staticmethod
    def get_ztype(data: Dict) -> Union[str, None]:
        """Check if data is z-encoded"""
        if type(data) is dict and "ztype" in data:
            return data["ztype"]
        return None

    @staticmethod
    def decode(zdata):
        """Decode z-format back to original types"""
        import torch

        T = ZData.get_ztype(zdata)

        if not T:
            return zdata

        # Decode PIL Images
        elif T == "image":
            from PIL import Image
            buff = BytesIO(zdata["b"])
            image = Image.open(buff)
            return image

        # Decode NumPy arrays
        elif T == "numpy.ndarray":
            array = np.frombuffer(zdata["b"], dtype=zdata["dtype"])
            array = array.reshape(zdata["shape"])
            return array

        # Decode PyTorch tensors
        elif T == "torch.Tensor":
            array = np.frombuffer(zdata["b"], dtype=zdata["dtype"])
            array = array.reshape(zdata["shape"]).copy()
            torch_array = torch.Tensor(array)
            return torch_array

        else:
            raise TypeError(f"ZData type {T} is not supported")


class Payload(SimpleNamespace):
    """
    Wrapper for serializing complex payloads with automatic
    type encoding
    """

    greedy = True  # Enable aggressive encoding

    def __init__(self, _greedy=None, **payload):
        if _greedy:
            self.greedy = _greedy
        super().__init__(**payload)

    def serialize(self):
        """Convert to MessagePack binary"""
        payload = self.__dict__
        if self.greedy:
            # Encode all values using ZData
            data = {k: ZData.encode(v) for k, v in payload.items()}
            data["_greedy"] = self.greedy
            msg = msgpack.packb(data, use_bin_type=True)
        else:
            msg = msgpack.packb(payload, use_bin_type=True)
        return msg

    @staticmethod
    def deserialize(payload) -> Dict:
        """Decode from MessagePack binary"""
        unpacked = msgpack.unpackb(payload, raw=False)
        is_greedy = unpacked.pop("_greedy", None)
        if not is_greedy:
            return unpacked
        else:
            data = {}
            for k, v in unpacked.items():
                data[k] = ZData.decode(v)
            return data
```

### Usage Example

```python
import numpy as np
import torch
from zaku.interfaces import Payload

# Create payload with mixed types
payload = Payload(
    image=np.array([[1, 2], [3, 4]], dtype=np.float32),
    tensor=torch.ones((3, 224, 224)),
    text="hello",
    number=42,
)

# Serialize to binary
binary = payload.serialize()
print(f"Binary size: {len(binary)} bytes")

# Send binary over network (e.g., HTTP, Redis)
# ...

# Deserialize on receiving end
received = Payload.deserialize(binary)
print(type(received["image"]))    # numpy.ndarray
print(type(received["tensor"]))   # torch.Tensor
print(received["text"])            # "hello"
print(received["number"])          # 42
```

---

## 6. PubSub Pattern

### zaku-service: Publisher-Subscriber Implementation

**Source**: `/Users/ge/fortyfive/zaku-service/docs/examples/02_pubsub.md`

```python
from zaku import TaskQ
from multiprocessing import Process
from time import sleep

# === PUBLISHER ===
def publisher(topic_id="example-topic"):
    """Publishes messages to a topic"""
    queue = TaskQ(name="publisher-queue", uri="http://localhost:9000")

    for i in range(5):
        # Publish message to topic
        n = queue.publish(
            {"step": i, "param_2": f"key-{i}"},
            topic=topic_id
        )
        print(f"Published to {n} subscribers")
        sleep(0.1)

# === SUBSCRIBER (Single Message) ===
def subscriber_one():
    """Receives a single message from topic"""
    queue = TaskQ(name="subscriber-queue", uri="http://localhost:9000")

    # Wait for one message with timeout
    result = queue.subscribe_one("example-topic", timeout=5)
    print(f"Received: {result}")
    assert result["step"] == 0

# === SUBSCRIBER (Stream) ===
def subscriber_stream():
    """Streams all messages from topic"""
    queue = TaskQ(name="subscriber-queue", uri="http://localhost:9000")

    # Stream messages
    stream = queue.subscribe_stream("example-topic", timeout=5)
    for i, result in enumerate(stream):
        print(f"Received: {result}")
        assert result["step"] == i

    assert i == 4  # Should receive 5 messages

# === EXECUTION ===
if __name__ == "__main__":
    # Start publisher in separate process
    p = Process(target=publisher)
    p.start()

    # Subscribe to stream
    subscriber_stream()

    p.join()
```

---

## 7. Task Queue with Job Lifecycle

### zaku-service: Job Management

**Source**: `/Users/ge/fortyfive/zaku-service/zaku/client.py` (lines 225-345)

```python
from zaku import TaskQ

queue = TaskQ(name="my-queue", uri="http://localhost:9000")

# === ADD JOBS ===
for i in range(10):
    job_id = queue.add({"seed": i * 100, "data": f"job-{i}"})
    print(f"Added job: {job_id}")

# === TAKE/PROCESS JOBS ===
while True:
    job_id, job = queue.take()
    if job is None:
        print("No jobs available")
        break

    print(f"Processing job {job_id}: {job}")
    # Process job...

    # Mark as complete
    queue.mark_done(job_id)

# === USING CONTEXT MANAGER (Recommended) ===
while True:
    with queue.pop() as job:
        if job is None:
            print("No jobs available")
            break

        # Auto-marks done on successful completion
        # Auto-marks reset on exception
        print(f"Processing: {job}")
        # Process job...
        # If exception, job is reset for retry

# === COUNT JOBS ===
num_jobs = queue.count()
print(f"Jobs in queue: {num_jobs}")

# === CLEAR ALL JOBS ===
queue.clear_queue()

# === MARK FOR RETRY ===
queue.mark_reset(job_id)

# === UNSTALE TASKS ===
# Reset jobs that have been in progress too long
queue.unstale_tasks(ttl=300)
```

---

## 8. Server-side HTTP Endpoints

### zaku-service: TaskServer Routes

**Source**: `/Users/ge/fortyfive/zaku-service/zaku/server.py` (lines 301-433)

```python
from aiohttp import web
import msgpack

class TaskServer:
    async def create_queue(self, request: web.Request):
        """PUT /queues - Create queue with Redis index"""
        data = await request.json()
        try:
            await Job.create_queue(self.redis, **data, prefix=self.prefix)
        except Exception as e:
            return web.Response(text="ERROR: " + str(e), status=200)
        return web.Response(text="OK")

    async def add_job(self, request: web.Request):
        """PUT /tasks - Add job to queue"""
        msg = await request.read()
        data = msgpack.unpackb(msg)  # Binary payload
        await Job.add(self.redis, prefix=self.prefix, **data)
        return web.Response(text="OK")

    async def take_handler(self, request: web.Request):
        """POST /tasks - Take (grab) next job atomically"""
        data = await request.json()
        try:
            job_id, payload = await Job.take(
                self.redis, **data, prefix=self.prefix
            )
        except Exception as e:
            return web.Response(status=200)

        if payload:
            msg = msgpack.packb(
                {"job_id": job_id, "payload": payload},
                use_bin_type=True
            )
            return web.Response(body=msg, status=200)
        return web.Response(status=200)

    async def count_files_handler(self, request: web.Request):
        """GET /tasks/counts - Count available jobs"""
        data = await request.json()
        counts = await Job.count_files(
            self.redis, **data, prefix=self.prefix
        )
        msg = msgpack.packb({"counts": counts}, use_bin_type=True)
        return web.Response(body=msg, status=200)

    async def mark_done_handler(self, request: web.Request):
        """DELETE /tasks - Mark job as done"""
        data = await request.json()
        await Job.remove(self.redis, **data, prefix=self.prefix)
        return web.Response(text="OK")

    async def mark_reset_handler(self, request: web.Request):
        """POST /tasks/reset - Mark job for retry"""
        data = await request.json()
        await Job.reset(self.redis, **data, prefix=self.prefix)
        return web.Response(text="OK")

    async def publish_job(self, request: web.Request):
        """PUT /publish - Publish message to topic"""
        msg = await request.read()
        data = msgpack.unpackb(msg)
        num_subscribers = await Job.publish(
            self.redis, prefix=self.prefix, **data
        )
        return web.Response(text=str(num_subscribers), status=200)

    async def subscribe_one_handler(self, request: web.Request):
        """POST /subscribe_one - Wait for one message"""
        data = await request.json()
        payload = await Job.subscribe(self.redis, **data, prefix=self.prefix)
        if payload:
            return web.Response(body=payload, status=200)
        return web.Response(status=200)

    async def subscribe_streaming_handler(self, request) -> web.StreamResponse:
        """POST /subscribe_stream - Stream messages"""
        data = await request.json()

        async def stream_response(response):
            try:
                async for payload in Job.subscribe_stream(
                    self.redis, **data, prefix=self.prefix
                ):
                    await response.write(payload)
                await response.write_eof()
            except ConnectionResetError:
                print("Client disconnected")
                return response
            return response

        response = web.StreamResponse(
            status=200,
            reason="OK",
            headers={"Content-Type": "text/plain"},
        )
        await response.prepare(request)
        await stream_response(response)
        return response

    def setup_server(self):
        """Configure all HTTP routes"""
        self._route("/queues", self.create_queue, method="PUT")
        self._route("/tasks", self.add_job, method="PUT")
        self._route("/tasks", self.take_handler, method="POST")
        self._route("/tasks/counts", self.count_files_handler, method="GET")
        self._route("/tasks/reset", self.mark_reset_handler, method="POST")
        self._route("/tasks", self.mark_done_handler, method="DELETE")
        self._route("/publish", self.publish_job, method="PUT")
        self._route("/subscribe_one", self.subscribe_one_handler, method="POST")
        self._route(
            "/subscribe_stream",
            self.subscribe_streaming_handler,
            method="POST"
        )
        return self.app
```

---

## 9. Complete End-to-End Example

### Full RPC Flow

```python
"""
Complete example: Client calls RPC, worker processes, returns result
"""

from zaku import TaskQ
from multiprocessing import Process
from time import sleep

def main():
    # Start worker in background
    worker = Process(target=worker_process, args=("rpc-queue",))
    worker.start()

    # Give worker time to start
    sleep(0.5)

    # === CLIENT ===
    client_queue = TaskQ(name="client-queue", uri="http://localhost:9000")

    # Make RPC call (blocking)
    result = client_queue.rpc(x=10, y=20, _timeout=5)
    print(f"RPC Result: {result}")
    assert result["sum"] == 30

    worker.terminate()
    worker.join()


def worker_process(queue_name):
    """Worker that adds two numbers"""
    queue = TaskQ(name=queue_name, uri="http://localhost:9000")

    while True:
        with queue.pop() as job:
            if job is None:
                sleep(0.1)
                continue

            # Extract response topic
            response_topic = job.pop("_request_id")

            # Extract parameters
            x = job.get("x", 0)
            y = job.get("y", 0)

            # Simulate processing
            sleep(0.5)

            # Calculate result
            result = {"sum": x + y, "x": x, "y": y}

            # Send response back to client
            queue.publish(result, topic=response_topic)


if __name__ == "__main__":
    main()
```

---

## Summary

These code examples demonstrate:

1. **MessagePack Serialization**: Efficient binary encoding with ordering guarantees
2. **Event Types**: Type-safe event definitions with inheritance hierarchy
3. **Event Store**: Reducer + Subscriber pattern for event processing
4. **RPC Patterns**: Request-response with topic injection for routing
5. **Data Encoding**: Complex type serialization (numpy, torch, images)
6. **PubSub**: Publisher-subscriber with streaming and single-message variants
7. **Job Management**: Task queue with lifecycle management and atomic operations
8. **HTTP Endpoints**: RESTful API for task/message operations
9. **End-to-End Flow**: Complete working example from client to worker and back

