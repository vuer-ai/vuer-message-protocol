"""
PyTorch tensor support for ZData.

Import this module to register PyTorch tensor encoding/decoding:
    >>> from vmp_py.extensions import torch_support
    >>> # Now torch.Tensor is supported
"""

import numpy as np
from ..type_registry import TYPE_REGISTRY, ZDataDict

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    raise ImportError(
        "PyTorch is not installed. Install it with: "
        "uv pip install 'vmp-py[torch]' or pip install torch"
    )


def _encode_torch(data: torch.Tensor) -> ZDataDict:
    """Encode PyTorch tensor to ZData format."""
    # Convert to CPU numpy, then to binary
    np_array = data.cpu().numpy()
    binary = np_array.tobytes()
    return {
        "ztype": "torch.Tensor",
        "b": binary,
        "dtype": str(np_array.dtype),
        "shape": np_array.shape,
    }


def _decode_torch(zdata: ZDataDict) -> torch.Tensor:
    """Decode ZData back to PyTorch tensor."""
    array = np.frombuffer(zdata["b"], dtype=zdata["dtype"])
    array = array.reshape(zdata["shape"]).copy()
    return torch.from_numpy(array)


# Register torch.Tensor type
if TORCH_AVAILABLE:
    TYPE_REGISTRY.register(
        "torch.Tensor",
        _encode_torch,
        _decode_torch,
        type_class=torch.Tensor
    )
