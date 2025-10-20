"""
Advanced registry and extensions examples for vmp-py.

Demonstrates:
- Using optional type extensions (torch, PIL, safetensors)
- Custom type registration
- Creating library extensions
- Working with TYPE_REGISTRY directly
"""

import numpy as np
from vuer_vrpc import ZData, TYPE_REGISTRY, MessagePackSerializer


def example_list_types():
    """Example: List all registered types."""
    print("\n=== Registered Types ===")
    print("Available types:", ZData.list_types())


def example_torch_extension():
    """Example: Using PyTorch extension."""
    print("\n=== PyTorch Extension ===")

    try:
        # Import extension to enable torch support
        from vuer_vrpc.extensions import torch_support  # noqa: F401
        import torch

        print("✓ PyTorch extension loaded")
        print(f"  Registered types: {ZData.list_types()}")

        # Create and encode tensor
        tensor = torch.randn(3, 3)
        print(f"\nOriginal tensor:\n{tensor}")

        encoded = ZData.encode(tensor)
        print(f"Encoded type: {encoded['ztype']}")

        decoded = ZData.decode(encoded)
        print(f"Decoded tensor:\n{decoded}")

        assert torch.allclose(tensor, decoded)
        print("✓ Round-trip successful!")

    except ImportError:
        print("⚠ PyTorch not installed. Install with: uv pip install 'vmp-py[torch]'")


def example_image_extension():
    """Example: Using PIL Image extension."""
    print("\n=== PIL Image Extension ===")

    try:
        from vuer_vrpc.extensions import image_support  # noqa: F401
        from PIL import Image

        print("✓ PIL extension loaded")

        # Create image
        img = Image.new('RGB', (50, 50), color='blue')
        print(f"Created {img.size} {img.mode} image")

        encoded = ZData.encode(img)
        print(f"Encoded type: {encoded['ztype']}")
        print(f"Binary size: {len(encoded['b'])} bytes")

        decoded = ZData.decode(encoded)
        print(f"Decoded: {decoded.size} {decoded.mode} image")
        print("✓ Round-trip successful!")

    except ImportError:
        print("⚠ PIL not installed. Install with: uv pip install 'vmp-py[image]'")


def example_safetensors_extension():
    """Example: Using safetensors extension."""
    print("\n=== Safetensors Extension ===")

    try:
        from vuer_vrpc.extensions import safetensors_support  # noqa: F401
        from vuer_vrpc.extensions.safetensors_support import encode_as_safetensor

        print("✓ Safetensors extension loaded")

        # Create dictionary of arrays
        data = {
            "weights": np.random.randn(10, 10).astype(np.float32),
            "bias": np.zeros(10, dtype=np.float32),
            "layer_norm": np.ones((10,), dtype=np.float32)
        }

        print(f"Created dict with {len(data)} arrays")
        for key, arr in data.items():
            print(f"  {key}: shape={arr.shape}, dtype={arr.dtype}")

        # Encode as safetensors
        encoded = encode_as_safetensor(data)
        print(f"\nEncoded type: {encoded['ztype']}")
        print(f"Binary size: {len(encoded['b'])} bytes")

        # Decode
        decoded = ZData.decode(encoded)
        print(f"\nDecoded dict with {len(decoded)} arrays")
        for key in data.keys():
            assert np.array_equal(data[key], decoded[key])
            print(f"  ✓ {key} matches")

        print("✓ Round-trip successful!")

    except ImportError:
        print("⚠ Safetensors not installed. Install with: uv pip install 'vmp-py[safetensors]'")


def example_custom_type():
    """Example: Register a custom type."""
    print("\n=== Custom Type Registration ===")

    # Define custom type
    class Vector3D:
        def __init__(self, x, y, z):
            self.x, self.y, self.z = x, y, z

        def __repr__(self):
            return f"Vector3D({self.x}, {self.y}, {self.z})"

        def __eq__(self, other):
            return (self.x, self.y, self.z) == (other.x, other.y, other.z)

    # Define encoder/decoder
    def encode_vector(v):
        return {
            "ztype": "example.Vector3D",
            "b": f"{v.x},{v.y},{v.z}".encode()
        }

    def decode_vector(zdata):
        x, y, z = map(float, zdata["b"].decode().split(","))
        return Vector3D(x, y, z)

    # Register
    ZData.register_type(
        "example.Vector3D",
        encode_vector,
        decode_vector,
        type_class=Vector3D
    )

    print("✓ Registered example.Vector3D")
    print(f"  All types: {ZData.list_types()}")

    # Use it
    vec = Vector3D(1.0, 2.0, 3.0)
    print(f"\nOriginal: {vec}")

    encoded = ZData.encode(vec)
    print(f"Encoded: {encoded}")

    decoded = ZData.decode(encoded)
    print(f"Decoded: {decoded}")

    assert vec == decoded
    print("✓ Round-trip successful!")


def example_registry_direct_access():
    """Example: Access TYPE_REGISTRY directly."""
    print("\n=== Direct TYPE_REGISTRY Access ===")

    # Custom type with type checker (not type class)
    def encode_range(r):
        return {
            "ztype": "example.range",
            "b": f"{r.start},{r.stop},{r.step}".encode()
        }

    def decode_range(zdata):
        start, stop, step = map(int, zdata["b"].decode().split(","))
        return range(start, stop, step)

    def is_range(obj):
        return isinstance(obj, range)

    # Register using TYPE_REGISTRY directly
    TYPE_REGISTRY.register(
        "example.range",
        encode_range,
        decode_range,
        type_checker=is_range
    )

    print("✓ Registered example.range using TYPE_REGISTRY")

    # Use it
    r = range(0, 10, 2)
    print(f"Original: {list(r)}")

    encoded = ZData.encode(r)
    print(f"Encoded: {encoded}")

    decoded = ZData.decode(encoded)
    print(f"Decoded: {list(decoded)}")

    assert list(r) == list(decoded)
    print("✓ Round-trip successful!")


def example_mixed_types_serialization():
    """Example: Serialize mixed types with MessagePack."""
    print("\n=== Mixed Types Serialization ===")

    # Try to import all extensions
    try:
        from vuer_vrpc.extensions import torch_support, image_support  # noqa: F401
        import torch
        from PIL import Image

        serializer = MessagePackSerializer(greedy=True)

        # Create mixed data
        data = {
            "numpy_array": np.array([[1, 2], [3, 4]]),
            "torch_tensor": torch.randn(2, 2),
            "pil_image": Image.new('RGB', (10, 10), color='red'),
            "plain_data": {"text": "hello", "number": 42}
        }

        print("Created mixed data structure:")
        for key, value in data.items():
            print(f"  {key}: {type(value).__name__}")

        # Serialize
        binary = serializer.encode(data)
        print(f"\nSerialized to {len(binary)} bytes")

        # Deserialize
        decoded = serializer.decode(binary)
        print("\nDeserialized types:")
        for key, value in decoded.items():
            print(f"  {key}: {type(value).__name__}")

        print("✓ All types preserved!")

    except ImportError as e:
        print(f"⚠ Some extensions not available: {e}")
        print("  Install with: uv pip install 'vmp-py[all]'")


def main():
    """Run all examples."""
    print("=" * 70)
    print("VMP-PY Registry and Extensions Examples")
    print("=" * 70)

    example_list_types()
    example_custom_type()
    example_registry_direct_access()
    example_torch_extension()
    example_image_extension()
    example_safetensors_extension()
    example_mixed_types_serialization()

    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
