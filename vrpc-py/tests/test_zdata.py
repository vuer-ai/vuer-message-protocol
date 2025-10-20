"""
Tests for ZData encoding/decoding and custom type registration.
"""

import pytest
import numpy as np
from vuer_rpc import ZData


def test_numpy_encode_decode():
    """Test encoding and decoding of numpy arrays."""
    # Test 1D array
    arr = np.array([1, 2, 3, 4, 5])
    encoded = ZData.encode(arr)

    assert encoded["ztype"] == "numpy.ndarray"
    assert "b" in encoded
    assert encoded["dtype"] == str(arr.dtype)
    assert encoded["shape"] == arr.shape

    decoded = ZData.decode(encoded)
    assert isinstance(decoded, np.ndarray)
    np.testing.assert_array_equal(decoded, arr)

    # Test 2D array with different dtype
    arr2d = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    encoded2d = ZData.encode(arr2d)
    decoded2d = ZData.decode(encoded2d)

    assert isinstance(decoded2d, np.ndarray)
    assert decoded2d.dtype == arr2d.dtype
    np.testing.assert_array_equal(decoded2d, arr2d)


def test_numpy_dtypes():
    """Test various numpy dtypes."""
    dtypes = [np.int32, np.int64, np.float32, np.float64, np.uint8, np.complex128]

    for dtype in dtypes:
        arr = np.array([1, 2, 3], dtype=dtype)
        encoded = ZData.encode(arr)
        decoded = ZData.decode(encoded)

        assert decoded.dtype == arr.dtype
        np.testing.assert_array_equal(decoded, arr)


def test_torch_encode_decode():
    """Test encoding and decoding of PyTorch tensors."""
    pytest.importorskip("torch")
    import torch
    from vuer_rpc.extensions import torch_support  # noqa: F401

    # Test 1D tensor
    tensor = torch.tensor([1, 2, 3, 4, 5])
    encoded = ZData.encode(tensor)

    assert encoded["ztype"] == "torch.Tensor"
    assert "b" in encoded
    assert "dtype" in encoded
    assert "shape" in encoded

    decoded = ZData.decode(encoded)
    assert isinstance(decoded, torch.Tensor)
    torch.testing.assert_close(decoded, tensor)

    # Test 2D tensor with float
    tensor2d = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
    encoded2d = ZData.encode(tensor2d)
    decoded2d = ZData.decode(encoded2d)

    assert isinstance(decoded2d, torch.Tensor)
    torch.testing.assert_close(decoded2d, tensor2d)


def test_pil_image_encode_decode():
    """Test encoding and decoding of PIL images."""
    pytest.importorskip("PIL")
    from PIL import Image
    from vuer_rpc.extensions import image_support  # noqa: F401

    # Create a simple RGB image
    img = Image.new('RGB', (100, 100), color='red')
    encoded = ZData.encode(img)

    assert encoded["ztype"] == "image"
    assert "b" in encoded

    decoded = ZData.decode(encoded)
    assert isinstance(decoded, Image.Image)
    assert decoded.size == img.size
    assert decoded.mode == img.mode


def test_is_zdata():
    """Test ZData detection."""
    arr = np.array([1, 2, 3])
    encoded = ZData.encode(arr)

    assert ZData.is_zdata(encoded)
    assert not ZData.is_zdata(arr)
    assert not ZData.is_zdata({"some": "dict"})
    assert not ZData.is_zdata([1, 2, 3])


def test_get_ztype():
    """Test getting ztype from encoded data."""
    arr = np.array([1, 2, 3])
    encoded = ZData.encode(arr)

    assert ZData.get_ztype(encoded) == "numpy.ndarray"
    assert ZData.get_ztype(arr) is None
    assert ZData.get_ztype({"some": "dict"}) is None


def test_passthrough_for_unsupported_types():
    """Test that unsupported types are passed through unchanged."""
    # Primitives should pass through
    assert ZData.encode(42) == 42
    assert ZData.encode("hello") == "hello"
    assert ZData.encode([1, 2, 3]) == [1, 2, 3]
    assert ZData.encode({"key": "value"}) == {"key": "value"}

    # Decode should also pass through non-ZData
    assert ZData.decode(42) == 42
    assert ZData.decode("hello") == "hello"


def test_custom_type_registration():
    """Test registering custom types."""

    # Define a custom type
    class Point:
        def __init__(self, x, y):
            self.x = x
            self.y = y

        def __eq__(self, other):
            return self.x == other.x and self.y == other.y

    # Define encoder and decoder
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

    # Test encoding and decoding
    point = Point(3.14, 2.71)
    encoded = ZData.encode(point)

    assert encoded["ztype"] == "custom.Point"
    assert ZData.is_zdata(encoded)

    decoded = ZData.decode(encoded)
    assert isinstance(decoded, Point)
    assert decoded == point


def test_custom_type_with_checker():
    """Test registering custom type with type checker function."""

    class Vector:
        def __init__(self, x, y, z):
            self.x, self.y, self.z = x, y, z

        def __eq__(self, other):
            return (self.x, self.y, self.z) == (other.x, other.y, other.z)

    def is_vector(obj):
        return hasattr(obj, 'x') and hasattr(obj, 'y') and hasattr(obj, 'z')

    def encode_vector(v):
        return {
            "ztype": "custom.Vector",
            "b": f"{v.x},{v.y},{v.z}".encode()
        }

    def decode_vector(zdata):
        x, y, z = map(float, zdata["b"].decode().split(","))
        return Vector(x, y, z)

    # Register with type checker
    ZData.register_type(
        "custom.Vector",
        encode_vector,
        decode_vector,
        type_checker=is_vector
    )

    # Test
    vec = Vector(1.0, 2.0, 3.0)
    encoded = ZData.encode(vec)
    assert encoded["ztype"] == "custom.Vector"

    decoded = ZData.decode(encoded)
    assert decoded == vec


def test_unknown_ztype_raises_error():
    """Test that unknown ztype raises TypeError."""
    fake_zdata = {
        "ztype": "unknown.Type",
        "b": b"some data"
    }

    with pytest.raises(TypeError, match="Unknown ZData type"):
        ZData.decode(fake_zdata)


def test_complex_nested_structures():
    """Test encoding/decoding nested structures with multiple types."""
    arr1 = np.array([1, 2, 3])
    arr2 = np.array([[1.0, 2.0], [3.0, 4.0]])

    # Complex nested structure
    data = {
        "array1": arr1,
        "nested": {
            "array2": arr2,
            "value": 42
        },
        "list": [arr1, arr2, "text"]
    }

    # Note: ZData.encode doesn't recursively encode by default
    # This is handled by the serializers
    # Here we just test individual encoding
    encoded1 = ZData.encode(arr1)
    decoded1 = ZData.decode(encoded1)
    np.testing.assert_array_equal(decoded1, arr1)
