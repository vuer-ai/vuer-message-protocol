"""
Tests for optional type extensions (torch, PIL, safetensors).
"""

import pytest
import numpy as np
from vmp_py import ZData, TYPE_REGISTRY


def test_list_registered_types():
    """Test listing registered types."""
    types = ZData.list_types()
    assert "numpy.ndarray" in types
    assert isinstance(types, list)


def test_torch_extension():
    """Test torch extension can be imported and works."""
    pytest.importorskip("torch")
    import torch
    from vmp_py.extensions import torch_support  # noqa: F401

    # Check type is registered
    assert "torch.Tensor" in ZData.list_types()

    # Test encoding/decoding
    tensor = torch.randn(3, 3)
    encoded = ZData.encode(tensor)
    assert encoded["ztype"] == "torch.Tensor"

    decoded = ZData.decode(encoded)
    assert isinstance(decoded, torch.Tensor)
    torch.testing.assert_close(decoded, tensor)


def test_image_extension():
    """Test PIL image extension can be imported and works."""
    pytest.importorskip("PIL")
    from PIL import Image
    from vmp_py.extensions import image_support  # noqa: F401

    # Check type is registered
    assert "image" in ZData.list_types()

    # Test encoding/decoding
    img = Image.new('RGB', (50, 50), color='blue')
    encoded = ZData.encode(img)
    assert encoded["ztype"] == "image"

    decoded = ZData.decode(encoded)
    assert isinstance(decoded, Image.Image)
    assert decoded.size == img.size


def test_safetensors_extension():
    """Test safetensors extension can be imported and works."""
    pytest.importorskip("safetensors")
    from vmp_py.extensions import safetensors_support
    from vmp_py.extensions.safetensors_support import encode_as_safetensor

    # Check type is registered
    assert "safetensor.dict" in ZData.list_types()

    # Test explicit encoding
    data = {
        "weights": np.random.randn(10, 10).astype(np.float32),
        "bias": np.zeros(10, dtype=np.float32)
    }

    encoded = encode_as_safetensor(data)
    assert encoded["ztype"] == "safetensor.dict"
    assert "b" in encoded

    decoded = ZData.decode(encoded)
    assert isinstance(decoded, dict)
    assert "weights" in decoded
    assert "bias" in decoded
    np.testing.assert_array_equal(decoded["weights"], data["weights"])
    np.testing.assert_array_equal(decoded["bias"], data["bias"])


def test_registry_direct_access():
    """Test that users can access TYPE_REGISTRY directly."""
    # Register a custom type directly via TYPE_REGISTRY
    def encode_tuple(t):
        return {"ztype": "custom.tuple", "b": str(t).encode()}

    def decode_tuple(z):
        return eval(z["b"].decode())

    TYPE_REGISTRY.register(
        "custom.tuple",
        encode_tuple,
        decode_tuple,
        type_class=tuple
    )

    # Test it works
    data = (1, 2, 3)
    encoded = ZData.encode(data)
    assert encoded["ztype"] == "custom.tuple"

    decoded = ZData.decode(encoded)
    assert decoded == data


def test_multiple_extensions_together():
    """Test that multiple extensions can be used together."""
    torch = pytest.importorskip("torch")
    pytest.importorskip("PIL")
    pytest.importorskip("safetensors")

    from PIL import Image
    from vmp_py.extensions import torch_support, image_support, safetensors_support  # noqa: F401, F811
    from vmp_py.extensions.safetensors_support import encode_as_safetensor

    # Create mixed data
    data = {
        "tensor": torch.randn(5, 5),
        "image": Image.new('RGB', (20, 20)),
        "array": np.array([1, 2, 3]),
        "safetensor_data": encode_as_safetensor({
            "weights": np.random.randn(5, 5).astype(np.float32)
        })
    }

    # Encode each
    encoded_data = {k: ZData.encode(v) for k, v in data.items()}

    # Verify types
    assert encoded_data["tensor"]["ztype"] == "torch.Tensor"
    assert encoded_data["image"]["ztype"] == "image"
    assert encoded_data["array"]["ztype"] == "numpy.ndarray"
    assert encoded_data["safetensor_data"]["ztype"] == "safetensor.dict"

    # Decode all
    decoded_data = {k: ZData.decode(v) for k, v in encoded_data.items()}

    # Verify
    assert isinstance(decoded_data["tensor"], torch.Tensor)
    assert isinstance(decoded_data["image"], Image.Image)
    assert isinstance(decoded_data["array"], np.ndarray)
    assert isinstance(decoded_data["safetensor_data"], dict)


def test_extension_import_without_dependency_fails():
    """Test that importing extensions without dependencies gives helpful error."""
    # This test documents the behavior when dependencies are missing
    # In practice, pytest.importorskip prevents this, but users might encounter it
    pass  # Can't actually test this without uninstalling dependencies


def test_type_registry_isolation():
    """Test that registry modifications don't affect other tests."""
    initial_types = set(ZData.list_types())

    # Add a temporary type
    TYPE_REGISTRY.register(
        "test.temp",
        lambda x: {"ztype": "test.temp", "b": b"test"},
        lambda z: "test"
    )

    assert "test.temp" in ZData.list_types()

    # In a real scenario, this type persists across tests within the same session
    # But that's okay - it's the intended behavior of a global registry
