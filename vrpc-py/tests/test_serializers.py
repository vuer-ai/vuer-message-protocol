"""
Tests for MessagePack and JSON serializers.
"""

import pytest
import numpy as np
from vuer_rpc import (
    MessagePackSerializer,
    JSONSerializer,
    set_event,
    ZData,
)


def test_msgpack_basic_encoding():
    """Test basic MessagePack encoding/decoding."""
    serializer = MessagePackSerializer(greedy=False)

    data = {
        "string": "hello",
        "number": 42,
        "float": 3.14,
        "bool": True,
        "null": None,
        "list": [1, 2, 3],
        "nested": {"key": "value"}
    }

    encoded = serializer.encode(data)
    assert isinstance(encoded, bytes)

    decoded = serializer.decode(encoded)
    assert decoded == data


def test_msgpack_with_numpy():
    """Test MessagePack with numpy arrays (greedy mode)."""
    serializer = MessagePackSerializer(greedy=True)

    arr = np.array([1, 2, 3, 4, 5])
    data = {
        "array": arr,
        "value": 42
    }

    encoded = serializer.encode(data)
    decoded = serializer.decode(encoded)

    assert decoded["value"] == 42
    assert isinstance(decoded["array"], np.ndarray)
    np.testing.assert_array_equal(decoded["array"], arr)


def test_msgpack_with_nested_numpy():
    """Test MessagePack with nested structures containing numpy."""
    serializer = MessagePackSerializer(greedy=True)

    data = {
        "layer1": {
            "layer2": {
                "array": np.array([[1.0, 2.0], [3.0, 4.0]]),
                "text": "nested"
            }
        },
        "list": [
            np.array([1, 2, 3]),
            np.array([4, 5, 6]),
        ]
    }

    encoded = serializer.encode(data)
    decoded = serializer.decode(encoded)

    # Check nested array
    np.testing.assert_array_equal(
        decoded["layer1"]["layer2"]["array"],
        data["layer1"]["layer2"]["array"]
    )

    # Check list of arrays
    np.testing.assert_array_equal(decoded["list"][0], data["list"][0])
    np.testing.assert_array_equal(decoded["list"][1], data["list"][1])


def test_msgpack_with_torch():
    """Test MessagePack with PyTorch tensors."""
    pytest.importorskip("torch")
    import torch
    from vuer_rpc.extensions import torch_support  # noqa: F401

    serializer = MessagePackSerializer(greedy=True)

    tensor = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
    data = {"tensor": tensor, "value": "test"}

    encoded = serializer.encode(data)
    decoded = serializer.decode(encoded)

    assert decoded["value"] == "test"
    assert isinstance(decoded["tensor"], torch.Tensor)
    torch.testing.assert_close(decoded["tensor"], tensor)


def test_msgpack_event_serialization():
    """Test serializing Vuer events with MessagePack."""
    serializer = MessagePackSerializer(greedy=True)

    # Create event with numpy array
    arr = np.array([1, 2, 3])
    event = set_event({
        "tag": "scene",
        "data": arr
    })

    encoded = serializer.encode(event)
    decoded = serializer.decode(encoded)

    assert decoded["etype"] == "SET"
    assert decoded["data"]["tag"] == "scene"
    np.testing.assert_array_equal(decoded["data"]["data"], arr)


def test_json_basic_encoding():
    """Test basic JSON encoding/decoding."""
    serializer = JSONSerializer(greedy=False)

    data = {
        "string": "hello",
        "number": 42,
        "float": 3.14,
        "bool": True,
        "null": None,
        "list": [1, 2, 3],
        "nested": {"key": "value"}
    }

    encoded = serializer.encode(data)
    assert isinstance(encoded, bytes)

    decoded = serializer.decode(encoded)
    assert decoded == data


def test_json_with_numpy():
    """Test JSON with numpy arrays (greedy mode)."""
    serializer = JSONSerializer(greedy=True)

    arr = np.array([1, 2, 3, 4, 5])
    data = {
        "array": arr,
        "value": 42
    }

    encoded = serializer.encode(data)
    decoded = serializer.decode(encoded)

    assert decoded["value"] == 42
    assert isinstance(decoded["array"], np.ndarray)
    np.testing.assert_array_equal(decoded["array"], arr)


def test_json_bytes_encoding():
    """Test that JSON properly handles bytes via base64."""
    serializer = JSONSerializer(greedy=False)

    # ZData contains bytes
    arr = np.array([1, 2, 3])
    zdata = ZData.encode(arr)

    encoded = serializer.encode(zdata)
    decoded = serializer.decode(encoded)

    # Should preserve the ZData structure
    assert decoded["ztype"] == "numpy.ndarray"
    assert isinstance(decoded["b"], bytes)


def test_serializer_greedy_vs_non_greedy():
    """Test difference between greedy and non-greedy modes."""
    arr = np.array([1, 2, 3])
    data = {"array": arr}

    # Greedy mode - automatically encodes numpy
    greedy_serializer = MessagePackSerializer(greedy=True)
    greedy_encoded = greedy_serializer.encode(data)
    greedy_decoded = greedy_serializer.decode(greedy_encoded)
    assert isinstance(greedy_decoded["array"], np.ndarray)

    # Non-greedy mode - user must manually encode
    non_greedy_serializer = MessagePackSerializer(greedy=False)
    manual_data = {"array": ZData.encode(arr)}
    non_greedy_encoded = non_greedy_serializer.encode(manual_data)
    non_greedy_decoded = non_greedy_serializer.decode(non_greedy_encoded)

    # Manual decoding required in non-greedy mode
    decoded_array = ZData.decode(non_greedy_decoded["array"])
    assert isinstance(decoded_array, np.ndarray)


def test_cross_serializer_compatibility():
    """Test that data serialized with one format can be conceptually equivalent."""
    data = {
        "text": "hello",
        "number": 42,
        "nested": {"key": "value"}
    }

    msgpack_ser = MessagePackSerializer(greedy=False)
    json_ser = JSONSerializer(greedy=False)

    # Both should preserve the data
    msgpack_roundtrip = msgpack_ser.decode(msgpack_ser.encode(data))
    json_roundtrip = json_ser.decode(json_ser.encode(data))

    assert msgpack_roundtrip == data
    assert json_roundtrip == data
    assert msgpack_roundtrip == json_roundtrip


def test_large_numpy_array():
    """Test serialization of large numpy arrays."""
    serializer = MessagePackSerializer(greedy=True)

    # Create a large array
    large_arr = np.random.randn(1000, 1000)
    data = {"large_array": large_arr}

    encoded = serializer.encode(data)
    decoded = serializer.decode(encoded)

    np.testing.assert_array_equal(decoded["large_array"], large_arr)


def test_empty_structures():
    """Test serialization of empty structures."""
    serializer = MessagePackSerializer(greedy=True)

    data = {
        "empty_dict": {},
        "empty_list": [],
        "empty_array": np.array([]),
    }

    encoded = serializer.encode(data)
    decoded = serializer.decode(encoded)

    assert decoded["empty_dict"] == {}
    assert decoded["empty_list"] == []
    assert len(decoded["empty_array"]) == 0
