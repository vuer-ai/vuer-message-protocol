# Vuer Message Protocol (vRPC)

A lightweight, cross-language messaging and RPC protocol designed used by vuer and zaku.

## Project Structure

```
vuer-message-protocol/
├── README.md
├── vrpc-ts/          # TypeScript implementation
├── vrpc-py/          # Python implementation, uses uv
├── vrpc-rs/          # Rust implementation, uses cargo
├── vrpc-swift/       # Swift implementation, uses SPM
├── vrpc-cpp/         # C++ implementation (planned)
└── protocol/         # Shared protocol definitions
```

VMP uses MessagePack for efficient binary serialization and transport with `Content-Type: application/msgpack`.
MessagePack provides compact binary encoding while maintaining cross-language compatibility.

## Serializing Tensor Data in Python with ZData

ZData (Zaku Data) is a wrapper format for encoding custom data types including NumPy arrays, PyTorch tensors, and PIL
images. The schema uses `ztype` as the discriminator field to avoid naming collisions with the existing `dtype` property
from NumPy and PyTorch.

```typescript
// ZData wrapper format for special data types in Zaku
type ZData =
  | { ztype: "image"; b: Uint8Array }
  | { ztype: "numpy.ndarray"; b: Uint8Array; dtype: string; shape: number[] }
  | { ztype: "torch.Tensor"; b: Uint8Array; dtype: string; shape: number[] }
```

**Design Rationale**: The `ztype` field indicates what kind of object was encoded, while `dtype` retains its original
meaning from NumPy/PyTorch to specify the element data type. NumPy dtype objects aren't serializable, so they are
converted to string representations (e.g., `"float32"`, `"int64"`, `"uint8"`, `"complex128"`) for transport. NumPy's
`frombuffer()` accepts these string dtype specifications and reconstructs the proper type.

**Examples**:

- NumPy array: `{ztype: "numpy.ndarray", b: <binary>, dtype: "float32", shape: [224, 224, 3]}`
- PyTorch tensor: `{ztype: "torch.Tensor", b: <binary>, dtype: "int64", shape: [1, 512]}`

## Serializing Vuer Components

The vuer component schema is a (mostly) nested dictionary of key-value pairs. The keys are strings and the values are
arbitrary data types. The component looks like this:

<table>
<tr>
<th>Component Schema</th>
<th>Allowed Value Types</th>
</tr>
<tr>
<td>

```typescript
interface VuerComponent {
  tag: string;
  children: VuerComponent[];
  
  [key: string]: unknown
}
```

</td>
<td>

<code>string</code> | <code>number</code> | <code>boolean</code><br/>
<code>null</code> | <code>object</code> | <code>array</code><br/>
<code>ZData</code>

</td>
</tr>
</table>

## Vuer Message Envelopes

```typescript
interface Message {
  ts: number;                       // timestamp
  etype: string;                    // event type or queue name
  rtype?: string;                   // response type (RPC)
  args?: any[];                     // positional arguments for RPC
  kwargs?: { [key: string]: any };  // keyword arguments
  data?: any;                       // server payload
  value?: any;                      // client payload
}

interface ClientEvent {
  ts: number;       // timestamp
  etype: string;    // event type
  rtype?: string;   // response type (RPC)
  value: any;       // client payload
}

interface ServerEvent {
  ts: number;       // timestamp
  etype: string;    // event type
  data: any;        // server payload
}
```

### Vuer Events

The vuer message contains a timestamp (ts), event type (etype), server payload (data), and client payload (value).

<table>
<tr>
<th>Message (Base)</th>
<th>ClientEvent</th>
<th>ServerEvent</th>
</tr>
<tr>
<td>

Generic message envelope with all possible fields

</td>
<td>

Client-to-server events with `value` payload

</td>
<td>

Server-to-client events with `data` payload

</td>
</tr>
</table>

### Remote Procedural Call

<table>
<tr>
<th>RPC_Request</th>
<th>RPC_Response</th>
</tr>
<tr>
<td>

RPC request with `rtype` specifying response event type. Includes optional `args` and `kwargs` fields.

</td>
<td>

RPC response where `etype` matches the request's `rtype`. Returns payload in `data` (server) or `value` (client).

</td>
</tr>
</table>

**Vuer** uses a client-server architecture where RPC requests contain both `etype` (event type) and `rtype` (response
type). The response rotates `rtype` to become its `etype` on the return trip. Both client and server can initiate RPC
requests, with clients using the `value` field for payloads and servers using `data`. RPC requests have the additional
`args: any[]` field for positional arguments, and `kwargs: { [key: string]: any }` for keyword arguments.

```typescript
// Component-scoped Client Event
{ etype: "MOVABLE:{component-key}", value: {...} }

// Server Event
{ etype: "UPDATE", data: {...} }

// Server-to-client RPC event
{ etype: "CAMERA:{component-key}", rtype: "RESPONSE:{request_id}", kwargs: {...} }

// RPC Response
{ etype: "RESPONSE:{component-key}", value: {...}, ok: true, error: null }

// Hierarchical queue name in Zaku -- includes the args array.
{ etype: "WORKER_POOL:render:task-123", rtype: "{uuid}", args: [...], kwargs: {...} }
```

VMP uses hierarchical naming with `:` separating components (e.g., `MOVABLE:{component-key}:UPDATE`). All event types follow screaming snake case with uppercase and underscores (e.g., `SERVER_RPC`, `GRAB_RENDER`). The colon separator enables natural prefix matching in Redis queries and component-scoped event handlers. Event types are namespaced by component type and instance ID (the component key).

**Zaku** relies on long-lived Redis queues for most of its async operations. In this case, routing is determined by the
name of the queue, which is usually set up prior to the request. Therefore, zaku RPC does not currently rely on `etype`,
but this will change when we introduce more complex object actions. For instance, a stateful worker that has multiple
life-cycle methods. In this case the `etype` will look like `QUEUE_NAME:{method-name}` where the `$QUEUE_NAME` is
postfixed with the worker ID or class name. Request payload will again be placed in the `value` field, while response
payloads use the `data` field (renamed from `_results`). We currently use `_request_id` for the response queue name. But
request types can be globally namespaced.

###

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
  # Process job... then return the results as value
  queue.publish({"value": "good", "ok": True, "error": None}, topic=topic)
```

## Vuer vs Zaku: Protocol Comparison

The two implementations use fundamentally different message envelope designs, making unified serialization and RPC
helpers challenging.

| Aspect                        | Vuer (Event-Based)                                                                                                                                                                     | Zaku (Queue-Based)                                                                                                                                                                              | Implications                                                                                                    |
|-------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------|
| **Routing Mechanism**         | Event types (flat namespace)<br/>e.g., `"CLICK"`, `"RPC"`                                                                                                                              | Queue names (hierarchical)<br/>e.g., `"ZAKU_TEST:debug-queue-1"`                                                                                                                                | Zaku supports namespace hierarchy, Vuer relies on flat event names                                              |
| **Message Envelope**          | **Nested structure:**<br/>Client: `{ts, etype, key?, value?}`<br/>Server: `{ts, etype, data}`                                                                                          | **Flat structure:**<br/>`{_request_id, _args?, ...kwargs}`                                                                                                                                      | Vuer separates server/client payloads with dedicated fields; Zaku mixes metadata and payload at same level      |
| **Payload Structure**         | • `data`: Server → Client payload<br/>• `value`: Client → Server payload<br/>• Deep nesting supported                                                                                  | • All fields flattened at top level<br/>• No envelope/payload distinction<br/>• Metadata (`_request_id`, `_args`) mixed with data                                                               | Vuer provides clean separation; Zaku optimized for Redis field-based search                                     |
| **Serialization (Python)**    | **Recursive multi-level:**<br/>• `serializer()` walks nested structures<br/>• Calls `._serialize()` on objects<br/>• Recursively processes lists/tuples<br/>• No special type handling | **Flat single-level:**<br/>• `Payload.serialize()` iterates top-level keys<br/>• `ZData.encode()` per value<br/>• Handles numpy, torch, PIL images<br/>• **Does NOT recurse into nested dicts** | Vuer can serialize arbitrary component trees; Zaku trades depth for numpy/torch support and Redis searchability |
| **Serialization (Transport)** | **msgpackr** (TypeScript)<br/>**msgpack** (Python)<br/>Direct object packing                                                                                                           | **msgpack** (Python only)<br/>Pre-processes with ZData encoding                                                                                                                                 | Both use MessagePack, but Vuer relies on native msgpack features while Zaku wraps with custom type handling     |
| **RPC Correlation**           | • Request: `uuid` + `rtype` fields<br/>• Response: Event type matches `rtype`<br/>• Example: `rtype="RPC_RESPONSE@{uuid}"`                                                             | • Request: `_request_id` field<br/>• Response: Publish to topic `_request_id`<br/>• Example: `"rpc-{uuid}"`                                                                                     | Vuer uses typed events for correlation; Zaku uses pub/sub topics                                                |
| **Type Safety**               | Event types define message schema<br/>TypeScript interfaces enforce structure                                                                                                          | Queue names + payload keys define schema<br/>TypedDict for documentation only                                                                                                                   | Vuer has stronger client-side type checking; Zaku relies on runtime validation                                  |

**Key Tensions**:

1. **Envelope Design**: Vuer's nested `{etype, data/value}` vs Zaku's flat `{_request_id, **payload}` prevents shared
   message handling
2. **Serialization Depth**: Vuer's recursive serializer handles component trees; Zaku's single-level approach enables
   Redis field queries but cannot serialize deeply nested structures
3. **Special Type Handling**: Zaku supports numpy/torch/PIL at top level; Vuer has no special handling (relies on
   user-side encoding)

**Next Steps**: Standardize serialization infrastructure before unifying message envelope formats. Current differences
block generalized RPC helpers that work across both systems. Consider:

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
