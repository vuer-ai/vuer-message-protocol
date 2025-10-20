"""
Type registry for ZData encoding/decoding.

Provides a global registry that can be extended by users to add custom types.
This module can be imported and extended in user code or third-party libraries.
"""

from typing import Any, Callable, Dict, Optional, Protocol
from typing_extensions import TypedDict


class ZDataDict(TypedDict, total=False):
    """Type definition for ZData encoded objects."""
    ztype: str
    b: bytes
    dtype: Optional[str]
    shape: Optional[tuple]


class TypeEncoder(Protocol):
    """Protocol for type encoders."""
    def __call__(self, data: Any) -> ZDataDict:
        """Encode data to ZData format."""
        ...


class TypeDecoder(Protocol):
    """Protocol for type decoders."""
    def __call__(self, zdata: ZDataDict) -> Any:
        """Decode ZData back to original type."""
        ...


class TypeRegistry:
    """
    Registry for custom type encoders and decoders.

    This registry can be extended by users to add support for custom types.
    The registry supports three ways of registering types:
    1. By exact type class
    2. By custom type checker function
    3. By import path (for lazy registration)
    """

    def __init__(self):
        self._encoders: Dict[type, tuple[str, TypeEncoder]] = {}
        self._decoders: Dict[str, TypeDecoder] = {}
        self._type_checkers: list[tuple[Callable[[Any], bool], str, TypeEncoder]] = []

    def register(
        self,
        type_name: str,
        encoder: TypeEncoder,
        decoder: TypeDecoder,
        type_class: Optional[type] = None,
        type_checker: Optional[Callable[[Any], bool]] = None
    ):
        """
        Register a type for encoding/decoding.

        Args:
            type_name: Unique identifier for this type (e.g., "numpy.ndarray")
            encoder: Function that encodes data to ZDataDict
            decoder: Function that decodes ZDataDict back to original type
            type_class: Optional type class for direct type checking
            type_checker: Optional function for custom type checking

        Example:
            >>> def encode_point(p):
            ...     return {"ztype": "custom.Point", "b": f"{p.x},{p.y}".encode()}
            >>> def decode_point(z):
            ...     x, y = map(float, z["b"].decode().split(","))
            ...     return Point(x, y)
            >>> TYPE_REGISTRY.register(
            ...     "custom.Point",
            ...     encode_point,
            ...     decode_point,
            ...     type_class=Point
            ... )
        """
        # Register decoder
        self._decoders[type_name] = decoder

        # Register encoder by type class
        if type_class is not None:
            self._encoders[type_class] = (type_name, encoder)

        # Register encoder by type checker
        if type_checker is not None:
            self._type_checkers.append((type_checker, type_name, encoder))

    def encode(self, data: Any) -> Any:
        """
        Encode data using registered encoders.

        Returns the encoded ZDataDict if a matching encoder is found,
        otherwise returns the data unchanged.
        """
        # Check by exact type
        data_type = type(data)
        if data_type in self._encoders:
            type_name, encoder = self._encoders[data_type]
            return encoder(data)

        # Check using custom type checkers
        for checker, type_name, encoder in self._type_checkers:
            if checker(data):
                return encoder(data)

        # No encoder found, return as-is
        return data

    def decode(self, zdata: Any) -> Any:
        """
        Decode ZData using registered decoders.

        Returns the decoded object if zdata is a valid ZData dict,
        otherwise returns the data unchanged.
        """
        if not isinstance(zdata, dict) or "ztype" not in zdata:
            return zdata

        ztype = zdata["ztype"]
        if ztype not in self._decoders:
            raise TypeError(f"Unknown ZData type: {ztype}")

        decoder = self._decoders[ztype]
        return decoder(zdata)

    def is_zdata(self, data: Any) -> bool:
        """Check if data is a ZData encoded object."""
        return isinstance(data, dict) and "ztype" in data

    def get_ztype(self, data: Any) -> Optional[str]:
        """Get the ztype of a ZData object."""
        if self.is_zdata(data):
            return data["ztype"]
        return None

    def list_registered_types(self) -> list[str]:
        """List all registered type names."""
        return list(self._decoders.keys())


# Global type registry - users can extend this
TYPE_REGISTRY = TypeRegistry()
