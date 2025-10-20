"""
ZData - Extensible type encoding system for binary serialization.

Provides encoding/decoding for numpy arrays and allows registration of custom types.
Optional extensions for PyTorch tensors, PIL images, and safetensors are available.

Basic usage:
    >>> import numpy as np
    >>> from vmp_py import ZData
    >>> arr = np.array([1, 2, 3])
    >>> encoded = ZData.encode(arr)
    >>> decoded = ZData.decode(encoded)

With optional extensions:
    >>> from vmp_py.extensions import torch_support
    >>> import torch
    >>> tensor = torch.randn(3, 3)
    >>> encoded = ZData.encode(tensor)

Custom types:
    >>> class Point:
    ...     def __init__(self, x, y): self.x, self.y = x, y
    >>> def encode_point(p):
    ...     return {"ztype": "custom.Point", "b": f"{p.x},{p.y}".encode()}
    >>> def decode_point(z):
    ...     x, y = map(float, z["b"].decode().split(","))
    ...     return Point(x, y)
    >>> ZData.register_type("custom.Point", encode_point, decode_point, Point)
"""

from typing import Any, Callable, Optional
from .type_registry import TYPE_REGISTRY, ZDataDict, TypeEncoder, TypeDecoder

# Import built-in types (numpy is always available)
from . import builtin_types  # noqa: F401


class ZData:
    """
    Main interface for ZData encoding/decoding.

    Uses the global TYPE_REGISTRY which can be extended by:
    1. Importing optional extensions (torch_support, image_support, etc.)
    2. Registering custom types with ZData.register_type()
    3. Directly accessing TYPE_REGISTRY in external libraries

    Examples:
        >>> import numpy as np
        >>> arr = np.array([1, 2, 3])
        >>> encoded = ZData.encode(arr)
        >>> decoded = ZData.decode(encoded)

        >>> # Register custom type
        >>> class Point:
        ...     def __init__(self, x, y): self.x, self.y = x, y
        >>> ZData.register_type(
        ...     "custom.Point",
        ...     lambda p: {"ztype": "custom.Point", "b": f"{p.x},{p.y}".encode()},
        ...     lambda z: Point(*map(float, z["b"].decode().split(","))),
        ...     type_class=Point
        ... )
    """

    @staticmethod
    def encode(data: Any) -> Any:
        """
        Encode data to ZData format if a matching encoder is registered.

        Args:
            data: Data to encode (numpy array, torch tensor, PIL image, etc.)

        Returns:
            ZDataDict if data type is registered, otherwise returns data unchanged

        Example:
            >>> import numpy as np
            >>> arr = np.array([1, 2, 3])
            >>> encoded = ZData.encode(arr)
            >>> encoded['ztype']
            'numpy.ndarray'
        """
        return TYPE_REGISTRY.encode(data)

    @staticmethod
    def decode(zdata: Any) -> Any:
        """
        Decode ZData back to original type.

        Args:
            zdata: ZData dictionary or plain data

        Returns:
            Decoded object if zdata is valid ZData, otherwise returns zdata unchanged

        Raises:
            TypeError: If zdata has an unknown ztype

        Example:
            >>> encoded = ZData.encode(np.array([1, 2, 3]))
            >>> decoded = ZData.decode(encoded)
            >>> type(decoded)
            <class 'numpy.ndarray'>
        """
        return TYPE_REGISTRY.decode(zdata)

    @staticmethod
    def is_zdata(data: Any) -> bool:
        """
        Check if data is a ZData encoded object.

        Args:
            data: Data to check

        Returns:
            True if data is a ZData dictionary

        Example:
            >>> arr = np.array([1, 2, 3])
            >>> encoded = ZData.encode(arr)
            >>> ZData.is_zdata(encoded)
            True
            >>> ZData.is_zdata(arr)
            False
        """
        return TYPE_REGISTRY.is_zdata(data)

    @staticmethod
    def get_ztype(data: Any) -> Optional[str]:
        """
        Get the ztype of a ZData object.

        Args:
            data: Data to check

        Returns:
            The ztype string if data is ZData, None otherwise

        Example:
            >>> encoded = ZData.encode(np.array([1, 2, 3]))
            >>> ZData.get_ztype(encoded)
            'numpy.ndarray'
        """
        return TYPE_REGISTRY.get_ztype(data)

    @staticmethod
    def register_type(
        type_name: str,
        encoder: TypeEncoder,
        decoder: TypeDecoder,
        type_class: Optional[type] = None,
        type_checker: Optional[Callable[[Any], bool]] = None
    ):
        """
        Register a custom type for encoding/decoding.

        Args:
            type_name: Unique identifier for this type (e.g., "custom.MyType")
            encoder: Function that encodes data to ZDataDict
            decoder: Function that decodes ZDataDict back to original type
            type_class: Optional type class for direct type checking
            type_checker: Optional function for custom type checking

        Example:
            >>> class Point:
            ...     def __init__(self, x, y): self.x, self.y = x, y
            ...
            >>> def encode_point(p):
            ...     return {"ztype": "custom.Point", "b": f"{p.x},{p.y}".encode()}
            ...
            >>> def decode_point(z):
            ...     x, y = map(float, z["b"].decode().split(","))
            ...     return Point(x, y)
            ...
            >>> ZData.register_type("custom.Point", encode_point, decode_point, Point)
            >>> point = Point(1.0, 2.0)
            >>> encoded = ZData.encode(point)
            >>> decoded = ZData.decode(encoded)
        """
        TYPE_REGISTRY.register(type_name, encoder, decoder, type_class, type_checker)

    @staticmethod
    def list_types() -> list[str]:
        """
        List all registered type names.

        Returns:
            List of registered ztype names

        Example:
            >>> ZData.list_types()
            ['numpy.ndarray', 'torch.Tensor', ...]
        """
        return TYPE_REGISTRY.list_registered_types()
