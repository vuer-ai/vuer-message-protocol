"""
Safetensors support for ZData.

Safetensors is a safe and fast format for storing tensors.
Import this module to register safetensors encoding/decoding:
    >>> from vmp_py.extensions import safetensors_support
    >>> # Now safetensors format is supported
"""

import numpy as np
from ..type_registry import TYPE_REGISTRY, ZDataDict

try:
    from safetensors.numpy import save, load
    SAFETENSORS_AVAILABLE = True
except ImportError:
    SAFETENSORS_AVAILABLE = False
    raise ImportError(
        "Safetensors is not installed. Install it with: "
        "uv pip install 'vuer-rpc[safetensors]' or pip install safetensors"
    )


def _encode_safetensor_dict(data: dict) -> ZDataDict:
    """
    Encode a dictionary of numpy arrays to safetensors format.

    Args:
        data: Dictionary with string keys and numpy array values

    Returns:
        ZDataDict with safetensors binary encoding
    """
    # Validate that all values are numpy arrays
    if not isinstance(data, dict):
        raise TypeError("safetensor_dict requires a dictionary")

    for key, value in data.items():
        if not isinstance(value, np.ndarray):
            raise TypeError(f"All values must be numpy arrays, got {type(value)} for key '{key}'")

    # Serialize to safetensors format
    binary = save(data)

    return {
        "ztype": "safetensor.dict",
        "b": binary,
    }


def _decode_safetensor_dict(zdata: ZDataDict) -> dict:
    """Decode safetensors binary back to dictionary of numpy arrays."""
    return load(zdata["b"])


def _is_safetensor_dict(data) -> bool:
    """
    Check if data is a dictionary suitable for safetensors encoding.

    Returns True if data is a dict with all numpy array values.
    """
    if not isinstance(data, dict):
        return False

    # Check if all values are numpy arrays
    return all(isinstance(v, np.ndarray) for v in data.values())


# Register safetensor.dict type with custom checker
# This allows automatic encoding of dicts with numpy arrays
if SAFETENSORS_AVAILABLE:
    # Note: We use type_checker instead of type_class because dict is too generic
    # Users need to explicitly use this or have a dict of numpy arrays
    TYPE_REGISTRY.register(
        "safetensor.dict",
        _encode_safetensor_dict,
        _decode_safetensor_dict,
        type_checker=None  # Users must explicitly encode or use helper function
    )


def encode_as_safetensor(data: dict) -> ZDataDict:
    """
    Explicitly encode a dictionary of numpy arrays as safetensors.

    This is a helper function for when you want to force safetensors encoding.

    Args:
        data: Dictionary with string keys and numpy array values

    Returns:
        ZDataDict with safetensors encoding

    Example:
        >>> from vmp_py.extensions.safetensors_support import encode_as_safetensor
        >>> data = {"weights": np.random.randn(100, 100)}
        >>> encoded = encode_as_safetensor(data)
    """
    return _encode_safetensor_dict(data)
