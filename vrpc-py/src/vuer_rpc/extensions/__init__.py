"""
Optional type extensions for VMP.

This module provides optional type support that requires additional dependencies.
Import these modules to register their types with the global TYPE_REGISTRY.

Example:
    >>> from vmp_py.extensions import torch_support
    >>> # Now torch tensors can be encoded/decoded
    >>> from vmp_py import ZData
    >>> import torch
    >>> tensor = torch.randn(3, 3)
    >>> encoded = ZData.encode(tensor)
"""

__all__ = []

# Optional imports - these will register types when imported
try:
    from . import torch_support
    __all__.append('torch_support')
except ImportError:
    pass

try:
    from . import image_support
    __all__.append('image_support')
except ImportError:
    pass

try:
    from . import safetensors_support
    __all__.append('safetensors_support')
except ImportError:
    pass
