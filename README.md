# Vuer Message Protocol (vRPC)

A lightweight, cross-language messaging and RPC protocol designed used by vuer and zaku.

## Project Structure

```
vuer-message-protocol/
├── README.md
├── vmp-ts/           # TypeScript implementation
├── vmp-py/           # Python implementation, uses uv
├── vmp-swift/        # Swift implementation
├── vmp-cpp/          # C++ implementation
└── protocol/         # Shared protocol definitions
```

## Data Serialization Format

VMP uses message pack for efficient binary serialization.

- **MessagePack** encoding for efficient binary serialization
- **Data wrapper** for complex data types:
    - NumPy arrays (with shape and dtype metadata)
    - PyTorch tensors
    - PIL images
    - Base64-encoded binary data
- Transport with `Content-Type: application/msgpack`

### Vuer Event Messages

The vuer message contains a timestamp (ts), event type (etype), server payload (data), client payload (value), and
response ID.

```typescript
interface Message {
    ts: number;
    etype: string;  // event type or the message queue name
    rtype?: string; // used for RPC
    data?: any;
    value?: any;
}
```

```typescript
interface ClientEvent {
    ts: number;
    etype: string;
    rtype?: string;
    value: any;
}
```

```typescript
interface ServerEvent {
    ts: number;
    etype: string;
    data: any;
}
```

## Remote Procedural Call

There are two RPC patterns. In vuer, requests are typed by event types. Whereas in Zaku the minimum unit of
communication is a messaging containing a payload. There is no well-defined event type similar to the vuer messages. In
vuer, the RPC is a special type of event that contains the response event type, so that the client or the server can
specify the response it is looking for.

- In vuer:
    - `etype` is `EVENT_KEY` and `data` is the server request payload.
    - `rtype` is `EVENT_KEY_RESPONSE` and `value` is the client response payload.
- In Zaku: `etype` is `QUEUE_NAME:{key}` and `value` is the request payload.
  - <span class="text: red">Ge:</span> return results in `data` field. And use the standard
    `etype` and `rtype` for the routing in zaku.
  - if you want protected fields, use "$[A-z]+" for the event types.
- If I want nested structure, for instance `[ component type, id, method name ]`, I should use `:` to separate them. This will make the notation consistent between the redis-backed zaku while also offering better readability on the front end where we use screaming snake case. 

Now looking at this example, I should be able to change it to component-scoped handling instead. The colons offer a natural way to do prefix matching. In general, how we choose the event type string is in the user space.
```typescript
{ etype: "MOVABLE:{component-key}", value: {...} }
# or--
{ etype: "MOVABLE:{component-key}", data: {...} }
```

**migration strategy** Let's start moving component events to the new format. And while we are doing this, we can build a new component-scoped event handling setup for a better developer experience. `etype` is equivalent to queue names in zaku.

### Request ID

Each RPC request creates a new, unique queue for its response. Therefore response type; queue, or response ID is not different from each other.

I will use the general framework of response queue for this as well (as it should). I think the etype nomenclature is abusive because type shall not contain component instance id. However, in a generalized framework where each object has its own route, this is okay. `eventKey` is too redusive. `eventType` is too rigid. The messaging envelop is not specific to RPC, therefore it should not be called `request***`. 

If we consider this to be an event, and that is the event markup, then eventType with slightly abused postfix of the component id is a good choice.

the `useEvent("MOVABLE", "()=> {})` handler will be scoped by the component tag. 

### 1. Vuer's Event-Based RPC

Not all components contain events, and each component may have multiple events. 
We use screaming snake case for event types. The rtypes are single-use event
types for the response.

```typescript
interface ServerRPC {
    etype: "SERVER_RPC@{key}";
    rtype: "SERVER_RPC_RESPONSE@{uuid}";         // Request correlation ID
}

// response from the front end
interface ServerRPCResponse {
    etype: "SERVER_RPC_RESPONSE@{uuid}";         // Response correlation ID
    value?: any;         // Success result
    error?: string;       // Error message
}
```

### 2. Zaku's Queue-Based RPC

The transport in Zaku is a flat (no more than two levels) nested dictionary.
This is because, to parse objects in-depth, we need to have a serialization
strategy for each data type that we encounter. This is not a problem for the vuer-ts
implementation because it only needs to serialize component definitions (we have full 
control). This is, however, a problem for the python client in zaku.

So the zaku RPC works as follows: it is a queue-based RPC. The queue name is
the same as the key in the request payload. The response is the same as the
request, except that the queue name is replaced with the response key.

The packaging schema is different from the schema of the request in the queue.

```python
from typing import Any, NotRequired, TypedDict

class ZakuRPCRequest(TypedDict):
    # this should be renamed to "rtype". The queue name should be the "etype".
    _request_id: str           # Single-use topic ID for the response (e.g., "rpc-{uuid}")
    _args: NotRequired[list[Any]]  # Positional arguments (optional)
    # Additional keyword arguments allowed via TypedDict total=False inheritance

class ZakuRPCResponse(TypedDict, total=False):
    # Worker can return any key-value pairs
    # Published to the topic specified in _request_id
    pass  # Flexible response structure
```

**Example Usage:**

Client side:
```python
# Client makes RPC call
result = queue.rpc(seed=100, _timeout=5)
# Internally creates: {"_request_id": "rpc-{uuid}", "_args":[], "seed": 100}
```


Worker side:
```python
# Worker processes the job
with queue.pop() as job:
    topic = job.pop("_request_id")  # Extract response topic
    # Process job...
    queue.publish({"result": "good", **job}, topic=topic)
```

## Vuer vs Zaku: Protocol Comparison

The two implementations use fundamentally different message envelope designs, making unified serialization and RPC helpers challenging.

| Aspect | Vuer (Event-Based) | Zaku (Queue-Based) | Implications |
|--------|-------------------|-------------------|--------------|
| **Routing Mechanism** | Event types (flat namespace)<br/>e.g., `"CLICK"`, `"RPC"` | Queue names (hierarchical)<br/>e.g., `"ZAKU_TEST:debug-queue-1"` | Zaku supports namespace hierarchy, Vuer relies on flat event names |
| **Message Envelope** | **Nested structure:**<br/>Client: `{ts, etype, key?, value?}`<br/>Server: `{ts, etype, data}` | **Flat structure:**<br/>`{_request_id, _args?, ...kwargs}` | Vuer separates server/client payloads with dedicated fields; Zaku mixes metadata and payload at same level |
| **Payload Structure** | • `data`: Server → Client payload<br/>• `value`: Client → Server payload<br/>• Deep nesting supported | • All fields flattened at top level<br/>• No envelope/payload distinction<br/>• Metadata (`_request_id`, `_args`) mixed with data | Vuer provides clean separation; Zaku optimized for Redis field-based search |
| **Serialization (Python)** | **Recursive multi-level:**<br/>• `serializer()` walks nested structures<br/>• Calls `._serialize()` on objects<br/>• Recursively processes lists/tuples<br/>• No special type handling | **Flat single-level:**<br/>• `Payload.serialize()` iterates top-level keys<br/>• `ZData.encode()` per value<br/>• Handles numpy, torch, PIL images<br/>• **Does NOT recurse into nested dicts** | Vuer can serialize arbitrary component trees; Zaku trades depth for numpy/torch support and Redis searchability |
| **Serialization (Transport)** | **msgpackr** (TypeScript)<br/>**msgpack** (Python)<br/>Direct object packing | **msgpack** (Python only)<br/>Pre-processes with ZData encoding | Both use MessagePack, but Vuer relies on native msgpack features while Zaku wraps with custom type handling |
| **RPC Correlation** | • Request: `uuid` + `rtype` fields<br/>• Response: Event type matches `rtype`<br/>• Example: `rtype="RPC_RESPONSE@{uuid}"` | • Request: `_request_id` field<br/>• Response: Publish to topic `_request_id`<br/>• Example: `"rpc-{uuid}"` | Vuer uses typed events for correlation; Zaku uses pub/sub topics |
| **Type Safety** | Event types define message schema<br/>TypeScript interfaces enforce structure | Queue names + payload keys define schema<br/>TypedDict for documentation only | Vuer has stronger client-side type checking; Zaku relies on runtime validation |

**Key Tensions**:

1. **Envelope Design**: Vuer's nested `{etype, data/value}` vs Zaku's flat `{_request_id, **payload}` prevents shared message handling
2. **Serialization Depth**: Vuer's recursive serializer handles component trees; Zaku's single-level approach enables Redis field queries but cannot serialize deeply nested structures
3. **Special Type Handling**: Zaku supports numpy/torch/PIL at top level; Vuer has no special handling (relies on user-side encoding)

**Next Steps**: Standardize serialization infrastructure before unifying message envelope formats. Current differences block generalized RPC helpers that work across both systems. Consider:
- Adopting Zaku's `ZData` encoding in Vuer for numpy/torch support
- Defining a common envelope format that supports both flat (Redis-searchable) and nested (component-tree) use cases

## Documentation

For detailed implementation guides and examples, see:

- `PROTOCOL_ANALYSIS.md` - Technical deep dive
- `CODE_EXAMPLES.md` - Runnable code samples
- `IMPLEMENTATION_GUIDE.md` - Step-by-step implementation
- `INDEX.md` - Navigation and quick reference

## License

MIT
