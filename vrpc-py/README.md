# vmp-py - Vuer Message Protocol (Python)

A lightweight, cross-language messaging and RPC protocol designed for use with Vuer and Zaku.

## Features

- **ZData Encoding**: Extensible type system for encoding numpy arrays, PyTorch tensors, PIL images, and custom types
- **Message Envelopes**: Type-safe message structures for client-server communication
- **Event Factories**: Convenient functions for creating scene graph events
- **Serializers**: MessagePack and JSON serialization with automatic type handling
- **Fully Tested**: Comprehensive test suite with pytest

## Installation

Using uv (recommended):

```bash
uv pip install vmp-py
```

Using pip:

```bash
pip install vmp-py
```

### Optional Dependencies

Install with specific features:

```bash
# For PyTorch support
uv pip install "vmp-py[torch]"

# For PIL/Pillow support
uv pip install "vmp-py[image]"

# For safetensors support
uv pip install "vmp-py[safetensors]"

# For all extensions (torch, PIL, safetensors)
uv pip install "vmp-py[extensions]"

# For development (includes pytest + all extensions)
uv pip install "vmp-py[dev]"

# Install everything
uv pip install "vmp-py[all]"
```

## Quick Start

### Basic Usage

```python
import numpy as np
from vmp_py import ZData, MessagePackSerializer, set_event

# Encode numpy array
arr = np.array([1, 2, 3, 4, 5])
encoded = ZData.encode(arr)
print(encoded)  # {'ztype': 'numpy.ndarray', 'b': b'...', 'dtype': 'int64', 'shape': (5,)}

# Decode back to numpy
decoded = ZData.decode(encoded)
print(decoded)  # array([1, 2, 3, 4, 5])
```

### Creating Events

```python
from vmp_py import set_event, add_event, update_event

# Create a SET event to initialize the scene
scene = set_event({
    "tag": "scene",
    "key": "root",
    "bgColor": [0, 0, 0]
})

# Add nodes to the scene
nodes = add_event([
    {"tag": "mesh", "key": "box1", "position": [0, 0, 0]},
    {"tag": "mesh", "key": "box2", "position": [1, 1, 1]},
])

# Update existing nodes
updates = update_event([
    {"key": "box1", "position": [1, 0, 0]},
])
```

### Serialization

```python
import numpy as np
from vmp_py import MessagePackSerializer, set_event

serializer = MessagePackSerializer(greedy=True)

# Create event with numpy array
event = set_event({
    "tag": "scene",
    "data": np.array([[1, 2], [3, 4]])
})

# Serialize to binary
binary = serializer.encode(event)

# Deserialize
decoded_event = serializer.decode(binary)
print(decoded_event["data"]["data"])  # numpy array restored
```

## Optional Type Extensions

vmp-py uses an extensible type registry system. NumPy is supported by default, but you can enable support for additional types by importing their extensions.

### Using PyTorch

```python
# Import the extension to register torch.Tensor support
from vmp_py.extensions import torch_support
import torch

# Now torch tensors work automatically
tensor = torch.randn(3, 3)
encoded = ZData.encode(tensor)
decoded = ZData.decode(encoded)  # Returns torch.Tensor
```

### Using PIL Images

```python
# Import the extension to register PIL.Image support
from vmp_py.extensions import image_support
from PIL import Image

# Now PIL images work automatically
img = Image.new('RGB', (100, 100), color='red')
encoded = ZData.encode(img)
decoded = ZData.decode(encoded)  # Returns PIL.Image
```

### Using Safetensors

```python
# Import the extension for safetensors support
from vmp_py.extensions import safetensors_support
from vmp_py.extensions.safetensors_support import encode_as_safetensor
import numpy as np

# Encode a dictionary of numpy arrays as safetensors
data = {
    "weights": np.random.randn(100, 100).astype(np.float32),
    "bias": np.zeros(100, dtype=np.float32)
}

encoded = encode_as_safetensor(data)
decoded = ZData.decode(encoded)  # Returns dict of numpy arrays
```

### Import All Extensions at Once

```python
# Import all available extensions
from vmp_py import extensions

# Now torch, PIL, and safetensors all work
```

## Advanced Features

### Custom Type Registration

Register your own types for automatic encoding/decoding:

```python
from vmp_py import ZData

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

def encode_point(p):
    return {
        "ztype": "custom.Point",
        "b": f"{p.x},{p.y}".encode()
    }

def decode_point(zdata):
    x, y = map(float, zdata["b"].decode().split(","))
    return Point(x, y)

# Register the type
ZData.register_type(
    "custom.Point",
    encode_point,
    decode_point,
    type_class=Point
)

# Now it works automatically!
point = Point(3.14, 2.71)
encoded = ZData.encode(point)
decoded = ZData.decode(encoded)
```

### Extending the Registry in External Libraries

Library authors can register their types with vmp-py's global `TYPE_REGISTRY`. This allows seamless integration without requiring users to manually register types.

**Example: Creating a VMP extension library**

```python
# my_library/vmp_support.py
"""VMP support for my_library data types."""

from vmp_py import TYPE_REGISTRY
from .my_types import MyCustomType

def _encode_my_type(data: MyCustomType):
    return {
        "ztype": "my_library.MyCustomType",
        "b": data.to_bytes(),
        "metadata": data.get_metadata()
    }

def _decode_my_type(zdata):
    return MyCustomType.from_bytes(
        zdata["b"],
        metadata=zdata.get("metadata")
    )

# Register when this module is imported
TYPE_REGISTRY.register(
    "my_library.MyCustomType",
    _encode_my_type,
    _decode_my_type,
    type_class=MyCustomType
)

print(f"Registered my_library.MyCustomType with VMP")
```

**Users can then import your extension:**

```python
# User code
from my_library import vmp_support  # Registers the type
from vmp_py import ZData
from my_library import MyCustomType

# Works automatically!
obj = MyCustomType()
encoded = ZData.encode(obj)
decoded = ZData.decode(encoded)
```

**Best practices for library authors:**

1. **Use namespaced ztype names**: `"your_library.TypeName"` prevents collisions
2. **Make VMP support optional**: Don't require vmp-py as a hard dependency
3. **Document the import**: Tell users to import your `vmp_support` module
4. **Version your ztypes**: Use `"your_library.v1.TypeName"` if your format may change
5. **Access TYPE_REGISTRY directly**: Import from `vmp_py.type_registry` for type hints

**Example with optional dependency:**

```python
# my_library/vmp_support.py
try:
    from vmp_py import TYPE_REGISTRY
    VMP_AVAILABLE = True
except ImportError:
    VMP_AVAILABLE = False

if VMP_AVAILABLE:
    # Register types...
    TYPE_REGISTRY.register(...)
```

### Listing Registered Types

```python
from vmp_py import ZData

# See all registered types
types = ZData.list_types()
print(types)  # ['numpy.ndarray', 'torch.Tensor', 'image', ...]
```

### RPC Messages

```python
from vmp_py import create_rpc_request, create_rpc_response

# Client creates RPC request
request = create_rpc_request(
    "COMPUTE",
    "RESULT",
    args=[1, 2, 3],
    kwargs={"operation": "sum"},
    uuid="req-123"
)

# Server sends RPC response
response = create_rpc_response(
    "RESULT",
    data={"value": 6},
    ok=True
)
```

### Working with PyTorch

```python
from vmp_py.extensions import torch_support  # Enable torch support
import torch
from vmp_py import MessagePackSerializer

serializer = MessagePackSerializer(greedy=True)

# Serialize PyTorch tensors
data = {
    "weights": torch.randn(10, 10),
    "bias": torch.zeros(10)
}

binary = serializer.encode(data)
decoded = serializer.decode(binary)

# Tensors are automatically restored
assert isinstance(decoded["weights"], torch.Tensor)
```

## Message Types

### Message Envelopes

- **Message**: Base message with all possible fields
- **ClientEvent**: Client-to-server event with `value` payload
- **ServerEvent**: Server-to-client event with `data` payload
- **RPCRequest**: RPC request with `rtype` and optional `args`/`kwargs`
- **RPCResponse**: RPC response with `ok` and optional `error`

### Event Factories

- `set_event()`: Initialize or reset scene
- `add_event()`: Add nodes to scene
- `update_event()`: Update existing nodes
- `upsert_event()`: Insert or update (idempotent)
- `remove_event()`: Remove nodes by key
- `timeout_event()`: Schedule delayed execution

## API Reference

### ZData

```python
# Encode data
encoded = ZData.encode(data)

# Decode data
decoded = ZData.decode(encoded)

# Check if data is ZData
is_zdata = ZData.is_zdata(data)

# Get ztype
ztype = ZData.get_ztype(data)

# Register custom type
ZData.register_type(type_name, encoder, decoder, type_class=None, type_checker=None)
```

### Serializers

```python
# MessagePack (binary, efficient)
msgpack_ser = MessagePackSerializer(greedy=True)
binary = msgpack_ser.encode(data)
data = msgpack_ser.decode(binary)

# JSON (text, human-readable)
json_ser = JSONSerializer(greedy=True)
json_bytes = json_ser.encode(data)
data = json_ser.decode(json_bytes)
```

**Greedy Mode**: When `greedy=True`, the serializer automatically encodes/decodes ZData types recursively throughout the entire structure. When `greedy=False`, you must manually call `ZData.encode()` and `ZData.decode()`.

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/vuer-message-protocol.git
cd vuer-message-protocol/vmp-py

# Install with all dependencies
uv sync --all-extras
```

### Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=vmp_py --cov-report=html

# Run specific test file
uv run pytest tests/test_zdata.py -v
```

### Test Coverage

The library has comprehensive test coverage including:

- ZData encoding/decoding for numpy, torch, and PIL
- Custom type registration
- Message type creation
- Event factories
- MessagePack and JSON serialization
- Nested structure handling
- Edge cases and error conditions

## Protocol Specification

For detailed information about the Vuer Message Protocol, see the main repository documentation:

- [Protocol Analysis](../notes/PROTOCOL_ANALYSIS.md)
- [Implementation Guide](../notes/IMPLEMENTATION_GUIDE.md)
- [Code Examples](../notes/CODE_EXAMPLES.md)

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Related Projects

- [vuer-ts](../vmp-ts) - TypeScript implementation
- [vuer](https://github.com/vuer-ai/vuer) - 3D visualization framework
- [zaku](https://github.com/geyang/zaku-service) - Distributed task queue
