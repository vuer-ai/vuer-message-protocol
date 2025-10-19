# Implementation Guide: Building vuer-message-protocol

Based on analysis of vuer-ts and zaku-service, this guide explains how to implement the Vuer Message Protocol across multiple languages.

---

## Architecture Overview

### Protocol Layers

```
Application Layer (Events, RPC, PubSub)
         ↓
Protocol Layer (Message Format, Envelopes)
         ↓
Serialization Layer (MessagePack, JSON, Protobuf)
         ↓
Transport Layer (WebSocket, HTTP, TCP)
         ↓
Network
```

### Key Components

1. **Event Types**: Type-safe event definitions
2. **Message Serialization**: Binary (MessagePack) and text (JSON) formats
3. **RPC Pattern**: Request-response with topic injection
4. **PubSub Pattern**: Publisher-subscriber with ephemeral messages
5. **Task Queue Pattern**: Persistent message queue with job lifecycle
6. **Transport**: WebSocket (bidirectional), HTTP (REST), TCP (raw)

---

## Core Message Structure

### Base Event Format

```typescript
// Minimal event structure (both directions)
{
  ts: number;              // Timestamp (milliseconds)
  etype: string;           // Event type: "SET", "ADD", "UPDATE", "REMOVE", "RPC", etc.
  data?: any;              // Event-specific payload
  key?: string;            // Optional entity identifier
  value?: any;             // Optional client-originated data
  uuid?: string;           // Optional request correlation ID
}
```

### Message Envelope (for complex transports)

```json
{
  "version": "1.0",
  "id": "msg-uuid",
  "type": "event|rpc|pubsub",
  "payload": { ... },
  "metadata": {
    "source": "client|server|worker",
    "encoding": "msgpack|json",
    "priority": 0-10
  }
}
```

---

## Implementation Patterns

### Pattern 1: Event Factory

Create type-safe event builders for each language.

**TypeScript**:
```typescript
export const event = {
  set: (key, data) => ({ ts: Date.now(), etype: 'SET', key, data }),
  add: (nodes, to) => ({ ts: Date.now(), etype: 'ADD', data: { nodes, to } }),
  update: (nodes) => ({ ts: Date.now(), etype: 'UPDATE', data: { nodes } }),
  remove: (keys) => ({ ts: Date.now(), etype: 'REMOVE', data: { keys } }),
};
```

**Python**:
```python
def event_set(key, data):
    return {"ts": int(time() * 1000), "etype": "SET", "key": key, "data": data}

def event_add(nodes, to="children"):
    return {"ts": int(time() * 1000), "etype": "ADD", "data": {"nodes": nodes, "to": to}}
```

**Swift**:
```swift
struct Event: Codable {
    let ts: Int
    let etype: String
    let data: AnyCodable?
    let key: String?
    
    static func set(key: String, data: Any) -> Event {
        return Event(ts: Int(Date().timeIntervalSince1970 * 1000), 
                    etype: "SET", 
                    data: AnyCodable(data), 
                    key: key)
    }
}
```

### Pattern 2: Serialization Abstraction

Support multiple encodings transparently.

```typescript
interface Serializer {
  encode(event: Event): Buffer;
  decode(buffer: Buffer): Event;
}

class MessagePackSerializer implements Serializer {
  encode(event: Event): Buffer {
    return msgpack.encode(event);
  }
  
  decode(buffer: Buffer): Event {
    return msgpack.decode(buffer);
  }
}

class JSONSerializer implements Serializer {
  encode(event: Event): Buffer {
    return Buffer.from(JSON.stringify(event));
  }
  
  decode(buffer: Buffer): Event {
    return JSON.parse(buffer.toString());
  }
}
```

### Pattern 3: Transport Abstraction

Support multiple transports interchangeably.

```typescript
interface Transport {
  connect(uri: string): Promise<void>;
  send(event: Event): Promise<void>;
  receive(): AsyncIterator<Event>;
  disconnect(): Promise<void>;
}

class WebSocketTransport implements Transport {
  // WebSocket implementation
}

class HTTPTransport implements Transport {
  // HTTP polling or long-poll implementation
}

class TCPTransport implements Transport {
  // Raw TCP implementation
}
```

### Pattern 4: Event Store (Middleware)

All languages should provide event subscription/publishing.

```typescript
interface EventStore {
  subscribe(eventType: string | RegExp, handler: (event: Event) => void): () => void;
  publish(event: Event): void;
  addReducer(eventType: string, reducer: (event: Event) => Event): () => void;
}
```

### Pattern 5: RPC Pattern

Implement response topic injection for all languages.

```typescript
// High-level API
async rpc(method: string, params: any, timeout: number = 5000): Promise<any> {
  const request_id = uuidv4();
  const response_topic = `rpc-${request_id}`;
  
  // Send request with injected response topic
  this.publish({
    ts: Date.now(),
    etype: 'RPC',
    uuid: request_id,
    rtype: method,
    data: { ...params, _request_id: response_topic }
  });
  
  // Wait for response on injected topic
  return this.waitForEvent(response_topic, timeout);
}
```

---

## Language-Specific Implementations

### TypeScript/JavaScript (vuer-ts Reference)

**Key Files**:
- `src/vuer/interfaces.tsx` - Type definitions
- `src/vuer/store.tsx` - Event store
- `src/vuer/websocket.tsx` - WebSocket transport
- `src/vuer/sceneGraph/eventHelpers.ts` - Event factories

**Dependencies**:
- `msgpackr` - MessagePack encoding
- `react-use-websocket` - WebSocket client
- `uuid4` - UUID generation

**Suggested Package Structure**:
```
vmp-ts/
├── src/
│   ├── index.ts
│   ├── types/
│   │   ├── event.ts
│   │   ├── rpc.ts
│   │   └── payload.ts
│   ├── serializers/
│   │   ├── msgpack.ts
│   │   └── json.ts
│   ├── transports/
│   │   ├── websocket.ts
│   │   ├── http.ts
│   │   └── tcp.ts
│   ├── store.ts
│   └── client.ts
├── package.json
└── tsconfig.json
```

### Python (zaku-service Reference)

**Key Files**:
- `zaku/interfaces.py` - Type definitions
- `zaku/client.py` - Client API
- `zaku/server.py` - Server
- `docs/examples/` - Usage patterns

**Dependencies**:
- `msgpack` - MessagePack encoding
- `aiohttp` - Async HTTP client/server
- `redis` - Redis for pub/sub and queue
- `pydantic` - Data validation

**Suggested Package Structure**:
```
vmp-py/
├── vmp/
│   ├── __init__.py
│   ├── types/
│   │   ├── event.py
│   │   ├── rpc.py
│   │   └── payload.py
│   ├── serializers/
│   │   ├── msgpack.py
│   │   └── json.py
│   ├── transports/
│   │   ├── websocket.py
│   │   ├── http.py
│   │   └── tcp.py
│   ├── store.py
│   └── client.py
├── pyproject.toml
└── README.md
```

### Swift (for iOS/macOS)

**Suggested Structure**:
```
VMP-Swift/
├── Sources/VMP/
│   ├── Types/
│   │   ├── Event.swift
│   │   ├── RPC.swift
│   │   └── Payload.swift
│   ├── Serializers/
│   │   ├── MessagePackSerializer.swift
│   │   └── JSONSerializer.swift
│   ├── Transports/
│   │   ├── WebSocketTransport.swift
│   │   └── HTTPTransport.swift
│   ├── EventStore.swift
│   └── Client.swift
├── Package.swift
└── README.md
```

**Dependencies**:
- `MessagePacker` or `MessagePack.swift` - MessagePack
- `Starscream` - WebSocket client
- `URLSession` - HTTP
- `Codable` - JSON serialization

### C++ (for robotics/agents)

**Suggested Structure**:
```
vmp-cpp/
├── include/vmp/
│   ├── types/
│   │   ├── event.hpp
│   │   ├── rpc.hpp
│   │   └── payload.hpp
│   ├── serializers/
│   │   ├── msgpack.hpp
│   │   └── json.hpp
│   ├── transports/
│   │   ├── websocket.hpp
│   │   ├── http.hpp
│   │   └── tcp.hpp
│   ├── event_store.hpp
│   └── client.hpp
├── src/
│   └── (implementation files)
├── CMakeLists.txt
└── README.md
```

**Dependencies**:
- `msgpack-c` - MessagePack
- `nlohmann/json` - JSON
- `websocketpp` - WebSocket
- `curl` - HTTP

---

## Event Types Reference

### Core Events (Scene Graph)

```typescript
// Scene initialization/reset
SET = {
  ts: number,
  etype: "SET",
  data: { key?: string, tag: string, ...sceneProps }
}

// Add nodes to scene
ADD = {
  ts: number,
  etype: "ADD",
  data: { nodes: Node[], to: string }
}

// Update existing nodes
UPDATE = {
  ts: number,
  etype: "UPDATE",
  data: { nodes: UpdateNode[] }
}

// Insert or update (idempotent)
UPSERT = {
  ts: number,
  etype: "UPSERT",
  data: { nodes: Node[], to: string }
}

// Remove nodes
REMOVE = {
  ts: number,
  etype: "REMOVE",
  data: { keys: string[] }
}

// Scheduled execution
TIMEOUT = {
  ts: number,
  etype: "TIMEOUT",
  data: { timeout: number, fn: string }
}
```

### RPC Events

```typescript
// RPC request
{
  ts: number,
  etype: "RPC",
  uuid: string,         // Unique request ID
  rtype: string,        // Method name
  data: { _request_id: string, ...params }
}

// RPC response
{
  ts: number,
  etype: "RPC_RESPONSE",
  uuid: string,         // Correlates to request
  data: { result: any }
}

// RPC error
{
  ts: number,
  etype: "RPC_ERROR",
  uuid: string,
  data: { error_code: string, error_message: string }
}
```

### PubSub Events

```typescript
// Publish to topic
PUBLISH = {
  ts: number,
  etype: "PUBLISH",
  data: { topic_id: string, message: any }
}

// Subscribe to topic
SUBSCRIBE = {
  ts: number,
  etype: "SUBSCRIBE",
  data: { topic_id: string }
}

// Unsubscribe from topic
UNSUBSCRIBE = {
  ts: number,
  etype: "UNSUBSCRIBE",
  data: { topic_id: string }
}
```

---

## Testing Strategy

### Unit Tests (Per Language)

1. **Serialization**: Encode/decode round-trips
2. **Event Types**: Type validation
3. **Store**: Subscribe/publish mechanics
4. **RPC**: Request-response flow

### Integration Tests

1. **Cross-language**: TS ↔ Python, Python ↔ C++, etc.
2. **Transport**: WebSocket, HTTP, TCP
3. **Scenarios**: Complex event sequences

### Performance Tests

1. **Throughput**: Messages/second
2. **Latency**: End-to-end latency
3. **Memory**: Memory usage under load
4. **Serialization**: Encode/decode speed

---

## Deployment Considerations

### Production Checklist

- [ ] Versioning scheme defined
- [ ] Backward compatibility strategy
- [ ] Error handling and recovery
- [ ] Monitoring and metrics
- [ ] Authentication/authorization
- [ ] Rate limiting
- [ ] Message compression (for large payloads)
- [ ] Timeout handling
- [ ] Connection pooling
- [ ] Graceful shutdown

### Scaling Strategy

1. **Message broker** (Redis/RabbitMQ) for pub/sub
2. **Load balancer** for server instances
3. **Connection pooling** on clients
4. **Batch processing** for high-throughput scenarios
5. **Message compression** for large payloads

---

## Migration Path from Existing Systems

### From vuer-ts

1. Export vuer-ts interfaces to vmp-ts
2. Update websocket.tsx to use new transport layer
3. Gradual migration of event types
4. Maintain backward compatibility with adapter layer

### From zaku-service

1. Extract Payload class to vmp-py/vmp-ts
2. Create compatibility layer for HTTP endpoints
3. Support both old and new event types
4. Gradual client migration

---

## Recommended Reading

1. **MessagePack Spec**: https://msgpack.org/
2. **JSON-RPC 2.0**: https://www.jsonrpc.org/specification
3. **gRPC**: https://grpc.io/docs/
4. **AsyncAPI**: https://www.asyncapi.com/
5. **Event Sourcing**: https://martinfowler.com/eaaDev/EventSourcing.html

---

## Next Steps

1. Finalize event type definitions across all languages
2. Implement serialization layer with tests
3. Implement transport abstraction with tests
4. Create code generation tools (TypeScript interfaces → Python dataclasses)
5. Build comprehensive examples for each language
6. Create performance benchmarks
7. Establish versioning and release strategy
8. Document breaking changes policy

