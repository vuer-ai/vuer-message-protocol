"""
Serializers for encoding and decoding messages.

Provides MessagePack and JSON serialization with support for
ZData encoding of special types (numpy, torch, PIL).
"""

import json
import msgpack
from typing import Any, Protocol
from .zdata import ZData


class Serializer(Protocol):
    """Protocol for serializer implementations."""

    def encode(self, data: Any) -> bytes:
        """Encode data to bytes."""
        ...

    def decode(self, data: bytes) -> Any:
        """Decode bytes to data."""
        ...


def _recursive_encode(data: Any, greedy: bool = True) -> Any:
    """
    Recursively encode data using ZData for special types.

    Args:
        data: Data to encode (can be nested)
        greedy: If True, encode all ZData-supported types

    Returns:
        Encoded data with ZData wrappers where applicable
    """
    if not greedy:
        return data

    # Handle dictionaries recursively
    if isinstance(data, dict):
        return {k: _recursive_encode(v, greedy) for k, v in data.items()}

    # Handle lists and tuples recursively
    if isinstance(data, (list, tuple)):
        encoded = [_recursive_encode(item, greedy) for item in data]
        return encoded if isinstance(data, list) else tuple(encoded)

    # Try to encode with ZData
    return ZData.encode(data)


def _recursive_decode(data: Any, greedy: bool = True) -> Any:
    """
    Recursively decode data using ZData for encoded types.

    Args:
        data: Data to decode (can be nested)
        greedy: If True, decode all ZData-encoded types

    Returns:
        Decoded data with ZData wrappers removed where applicable
    """
    if not greedy:
        return data

    # Handle ZData encoded objects
    if ZData.is_zdata(data):
        return ZData.decode(data)

    # Handle dictionaries recursively
    if isinstance(data, dict):
        return {k: _recursive_decode(v, greedy) for k, v in data.items()}

    # Handle lists and tuples recursively
    if isinstance(data, (list, tuple)):
        decoded = [_recursive_decode(item, greedy) for item in data]
        return decoded if isinstance(data, list) else tuple(decoded)

    return data


class MessagePackSerializer:
    """
    MessagePack serializer with ZData support.

    Provides efficient binary encoding with optional recursive ZData encoding
    for numpy arrays, torch tensors, and PIL images.
    """

    def __init__(self, greedy: bool = True):
        """
        Initialize MessagePack serializer.

        Args:
            greedy: If True, recursively encode/decode ZData types
        """
        self.greedy = greedy

    def encode(self, data: Any) -> bytes:
        """
        Encode data to MessagePack binary format.

        Args:
            data: Data to encode (dicts, lists, primitives, ZData types)

        Returns:
            MessagePack encoded bytes

        Example:
            >>> import numpy as np
            >>> serializer = MessagePackSerializer()
            >>> data = {"array": np.array([1, 2, 3])}
            >>> encoded = serializer.encode(data)
            >>> isinstance(encoded, bytes)
            True
        """
        # Recursively encode ZData types if greedy
        if self.greedy:
            data = _recursive_encode(data, greedy=True)

        # Pack to MessagePack
        return msgpack.packb(data, use_bin_type=True)

    def decode(self, data: bytes) -> Any:
        """
        Decode MessagePack binary to Python objects.

        Args:
            data: MessagePack encoded bytes

        Returns:
            Decoded Python object with ZData types restored

        Example:
            >>> encoded = serializer.encode({"array": np.array([1, 2, 3])})
            >>> decoded = serializer.decode(encoded)
            >>> isinstance(decoded["array"], np.ndarray)
            True
        """
        # Unpack from MessagePack
        unpacked = msgpack.unpackb(data, raw=False)

        # Recursively decode ZData types if greedy
        if self.greedy:
            unpacked = _recursive_decode(unpacked, greedy=True)

        return unpacked


class JSONSerializer:
    """
    JSON serializer with ZData support.

    Provides text-based encoding with optional ZData support.
    Note: Binary data in ZData will be base64 encoded.
    """

    def __init__(self, greedy: bool = True):
        """
        Initialize JSON serializer.

        Args:
            greedy: If True, recursively encode/decode ZData types
        """
        self.greedy = greedy

    def encode(self, data: Any) -> bytes:
        """
        Encode data to JSON format.

        Args:
            data: Data to encode

        Returns:
            JSON encoded bytes (UTF-8)

        Note:
            Binary data in ZData objects will be base64 encoded for JSON compatibility.
        """
        # Recursively encode ZData types if greedy
        if self.greedy:
            data = _recursive_encode(data, greedy=True)

        # Convert bytes to base64 for JSON compatibility
        data = self._bytes_to_base64(data)

        return json.dumps(data, separators=(',', ':')).encode('utf-8')

    def decode(self, data: bytes) -> Any:
        """
        Decode JSON to Python objects.

        Args:
            data: JSON encoded bytes

        Returns:
            Decoded Python object with ZData types restored
        """
        # Decode JSON
        unpacked = json.loads(data.decode('utf-8'))

        # Convert base64 back to bytes
        unpacked = self._base64_to_bytes(unpacked)

        # Recursively decode ZData types if greedy
        if self.greedy:
            unpacked = _recursive_decode(unpacked, greedy=True)

        return unpacked

    def _bytes_to_base64(self, data: Any) -> Any:
        """Convert bytes to base64 strings recursively for JSON compatibility."""
        import base64

        if isinstance(data, bytes):
            return {"__bytes__": base64.b64encode(data).decode('ascii')}

        if isinstance(data, dict):
            return {k: self._bytes_to_base64(v) for k, v in data.items()}

        if isinstance(data, (list, tuple)):
            converted = [self._bytes_to_base64(item) for item in data]
            return converted if isinstance(data, list) else tuple(converted)

        return data

    def _base64_to_bytes(self, data: Any) -> Any:
        """Convert base64 strings back to bytes recursively."""
        import base64

        if isinstance(data, dict):
            # Check for our bytes marker
            if "__bytes__" in data and len(data) == 1:
                return base64.b64decode(data["__bytes__"])
            return {k: self._base64_to_bytes(v) for k, v in data.items()}

        if isinstance(data, (list, tuple)):
            converted = [self._base64_to_bytes(item) for item in data]
            return converted if isinstance(data, list) else tuple(converted)

        return data


# Default serializer instances
msgpack_serializer = MessagePackSerializer(greedy=True)
json_serializer = JSONSerializer(greedy=True)
