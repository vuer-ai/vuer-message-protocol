"""
PIL Image support for ZData.

Import this module to register PIL Image encoding/decoding:
    >>> from vmp_py.extensions import image_support
    >>> # Now PIL.Image is supported
"""

from io import BytesIO
from ..type_registry import TYPE_REGISTRY, ZDataDict

try:
    from PIL.Image import Image as PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    raise ImportError(
        "Pillow is not installed. Install it with: "
        "uv pip install 'vuer-rpc[image]' or pip install Pillow"
    )


def _encode_pil_image(data: PILImage) -> ZDataDict:
    """Encode PIL Image to ZData format."""
    with BytesIO() as buffer:
        # Preserve format if available, otherwise use PNG
        fmt = getattr(data, 'format', None) or 'PNG'
        data.save(buffer, format=fmt)
        binary = buffer.getvalue()
    return {
        "ztype": "image",
        "b": binary,
    }


def _decode_pil_image(zdata: ZDataDict) -> PILImage:
    """Decode ZData back to PIL Image."""
    from PIL import Image
    buffer = BytesIO(zdata["b"])
    return Image.open(buffer)


# Register PIL.Image type
if PIL_AVAILABLE:
    TYPE_REGISTRY.register(
        "image",
        _encode_pil_image,
        _decode_pil_image,
        type_class=PILImage
    )
