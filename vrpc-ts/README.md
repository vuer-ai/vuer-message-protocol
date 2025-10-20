# @vuer-ai/vuer-rpc

TypeScript implementation of Vuer RPC (vRPC) - a lightweight, cross-language messaging and RPC protocol.

## Features

- **MessagePack serialization** - Efficient binary encoding using msgpackr
- **Extensible type system** - Register custom ZData encoders/decoders
- **RPC support** - Request-response correlation with timeout handling
- **React hooks** - Ready-to-use hooks for React 19+ applications
- **Type-safe** - Full TypeScript support with strict typing

## Installation

```bash
pnpm add @vuer-ai/vuer-rpc
```

## Quick Start

### Basic Message Serialization

```typescript
import { serialize, deserialize } from '@vuer-ai/vuer-rpc';

// Create and serialize a message
const message = {
  ts: Date.now(),
  etype: 'UPDATE',
  data: { position: [1, 2, 3] }
};

const binary = serialize(message);
const decoded = deserialize(binary);
```

### RPC Communication

```typescript
import { RPCManager, serialize, deserialize } from '@vuer-ai/vuer-rpc';

const rpcManager = new RPCManager();

// Send RPC request
const response = await rpcManager.request(
  (request) => {
    const binary = serialize(request);
    websocket.send(binary);
  },
  {
    etype: 'GET_POSITION',
    kwargs: { componentKey: 'main-camera' }
  },
  5000 // timeout in ms
);

console.log('Response:', response.data);

// Handle incoming messages
websocket.on('message', (data) => {
  const message = deserialize(data);
  rpcManager.handleResponse(message);
});
```

### Custom ZData Types

```typescript
import { registerZDataType, serialize, deserialize } from '@vuer-ai/vuer-rpc';

// Register a custom type for Date objects
registerZDataType({
  ztype: 'datetime',
  encode: (value: Date) => {
    if (value instanceof Date) {
      return {
        ztype: 'datetime',
        iso: value.toISOString(),
      };
    }
    return null;
  },
  decode: (zdata) => {
    if (zdata.ztype === 'datetime' && 'iso' in zdata) {
      return new Date(zdata.iso as string);
    }
    return null;
  },
});

// Now dates are automatically encoded/decoded
const message = {
  ts: Date.now(),
  etype: 'EVENT',
  data: { timestamp: new Date() }
};

const binary = serialize(message);
const decoded = deserialize(binary);
// decoded.data.timestamp is a Date object
```

### React Integration

```typescript
import { useMessageHandler, useRPC } from '@vuer-ai/vuer-rpc';
import { useState, useEffect } from 'react';

function VuerClient() {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [position, setPosition] = useState([0, 0, 0]);

  // Connect to WebSocket
  useEffect(() => {
    const socket = new WebSocket('ws://localhost:8000');
    setWs(socket);
    return () => socket.close();
  }, []);

  // Handle messages with RPC support
  const { send, rpc } = useMessageHandler(ws, (message) => {
    if (message.etype === 'UPDATE') {
      setPosition(message.data.position);
    }
  });

  const handleGetPosition = async () => {
    const response = await rpc({
      etype: 'GET_POSITION',
      kwargs: { componentKey: 'main-camera' }
    });
    console.log('Position:', response.data);
  };

  const handleClick = () => {
    send({
      ts: Date.now(),
      etype: 'CLICK',
      value: { x: 100, y: 200 }
    });
  };

  return (
    <div>
      <div>Position: {position.join(', ')}</div>
      <button onClick={handleGetPosition}>Get Position</button>
      <button onClick={handleClick}>Send Click</button>
    </div>
  );
}
```

## API Reference

### Core Functions

- `serialize(value, options?)` - Serialize data to MessagePack binary
- `deserialize(binary, options?)` - Deserialize MessagePack binary to data
- `registerZDataType(handler)` - Register custom ZData type encoder/decoder
- `createRPCRequest(params)` - Create an RPC request message
- `createRPCResponse(params)` - Create an RPC response message

### React Hooks

- `useRPC(transport)` - Manage RPC requests with automatic correlation
- `useMessageHandler(transport, onMessage)` - Bidirectional messaging with RPC
- `useMessageQueue(transport)` - Queue messages with auto-flush
- `useMessageSubscription(etype, handler)` - Subscribe to specific event types

### Types

See the [type definitions](./src/types.ts) for complete TypeScript interfaces.

## ZData Format

ZData is a wrapper format for encoding special data types:

```typescript
// Image
{ ztype: 'image', b: Uint8Array }

// NumPy array
{ ztype: 'numpy.ndarray', b: Uint8Array, dtype: 'float32', shape: [224, 224, 3] }

// PyTorch tensor
{ ztype: 'torch.Tensor', b: Uint8Array, dtype: 'int64', shape: [1, 512] }

// Custom types
{ ztype: 'your-custom-type', ...customFields }
```

## Message Envelopes

### Generic Message

```typescript
{
  ts: number;        // timestamp
  etype: string;     // event type
  rtype?: string;    // response type (for RPC)
  args?: any[];      // positional arguments
  kwargs?: object;   // keyword arguments
  data?: any;        // server payload
  value?: any;       // client payload
}
```

### RPC Request

```typescript
{
  ts: number;
  etype: 'CAMERA:main',
  rtype: 'rpc-uuid',
  kwargs: { duration: 1.5 }
}
```

### RPC Response

```typescript
{
  ts: number;
  etype: 'rpc-uuid',
  data: { position: [1, 2, 3] },
  ok: true,
  error: null
}
```

## License

MIT
