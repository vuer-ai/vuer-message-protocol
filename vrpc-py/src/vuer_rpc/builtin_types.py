"""
Built-in type encoders/decoders for ZData.

This module registers numpy support by default, which is a core dependency.
"""

import numpy as np
from .type_registry import TYPE_REGISTRY, ZDataDict


def _encode_numpy(data: np.ndarray) -> ZDataDict:
    """Encode NumPy array to ZData format."""
    binary = data.tobytes()
    return {
        "ztype": "numpy.ndarray",
        "b": binary,
        "dtype": str(data.dtype),
        "shape": data.shape,
    }


def _decode_numpy(zdata: ZDataDict) -> np.ndarray:
    """Decode ZData back to NumPy array."""
    array = np.frombuffer(zdata["b"], dtype=zdata["dtype"])
    array = array.reshape(zdata["shape"])
    return array


# Register numpy (always available since it's a core dependency)
TYPE_REGISTRY.register(
    "numpy.ndarray",
    _encode_numpy,
    _decode_numpy,
    type_class=np.ndarray
)
