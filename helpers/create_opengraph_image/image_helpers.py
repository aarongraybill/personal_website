"""Image I/O helpers for the batik crack simulation.

Arrays use image coordinates throughout: ``array[y, x]``. Color images have
shape ``(height, width, channels)``; masks have shape ``(height, width)``.
The eventual Wyvill implementation can use boolean masks for the wax domain
and float32 RGB arrays for dye and per-pixel control maps.
"""

from pathlib import Path
from typing import Literal

import numpy as np
from numpy.typing import NDArray
from PIL import Image


ImageMode = Literal["L", "RGB", "RGBA"]
MaskChannel = Literal["luminance", "alpha", "red", "green", "blue"]
UInt8Image = NDArray[np.uint8]
FloatImage = NDArray[np.float32]
BoolMask = NDArray[np.bool_]


def load_image(
    path: str | Path,
    *,
    mode: ImageMode = "RGBA",
    size: tuple[int, int] | None = None,
) -> UInt8Image:
    """Load an image as a uint8 NumPy array.

    Args:
        path: PNG, JPEG, or another Pillow-supported image.
        mode: Number and meaning of output channels.
        size: Optional ``(width, height)``. Images are resized with Lanczos.
    """
    image_path = Path(path).expanduser()
    if not image_path.is_file():
        raise FileNotFoundError(f"Image does not exist: {image_path}")

    with Image.open(image_path) as source:
        image = source.convert(mode)
        if size is not None:
            _validate_size(size)
            image = image.resize(size, Image.Resampling.LANCZOS)
        return np.asarray(image, dtype=np.uint8).copy()


def as_float_image(image: NDArray[np.generic]) -> FloatImage:
    """Convert an image to float32 in [0, 1].

    Integer arrays are scaled by their dtype's maximum. Floating-point input
    is assumed to already use [0, 1] and is clipped to that range.
    """
    array = np.asarray(image)
    if np.issubdtype(array.dtype, np.integer):
        maximum = np.iinfo(array.dtype).max
        result = array.astype(np.float32) / maximum
    elif np.issubdtype(array.dtype, np.floating):
        result = array.astype(np.float32)
    else:
        raise TypeError(f"Unsupported image dtype: {array.dtype}")
    return np.clip(result, 0.0, 1.0)


def extract_mask(
    image: NDArray[np.generic],
    *,
    channel: MaskChannel = "luminance",
    threshold: float = 0.5,
    invert: bool = False,
) -> BoolMask:
    """Create a boolean wax mask from a grayscale, RGB, or RGBA array.

    Pixels at or above ``threshold`` are treated as wax (``True``). Use the
    alpha channel for transparent silhouettes, or luminance for ordinary mask
    images. The result is directly suitable for a distance transform.
    """
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0 and 1")

    array = as_float_image(image)
    if array.ndim == 2:
        values = array
    elif array.ndim == 3 and array.shape[2] in (3, 4):
        channel_index = {"red": 0, "green": 1, "blue": 2}
        if channel == "luminance":
            values = (
                0.2126 * array[..., 0]
                + 0.7152 * array[..., 1]
                + 0.0722 * array[..., 2]
            )
        elif channel == "alpha":
            if array.shape[2] != 4:
                raise ValueError("alpha masks require an RGBA image")
            values = array[..., 3]
        else:
            values = array[..., channel_index[channel]]
    else:
        raise ValueError("image must have shape (H, W), (H, W, 3), or (H, W, 4)")

    mask = values >= threshold
    return np.logical_not(mask) if invert else mask


def load_mask(
    path: str | Path,
    *,
    size: tuple[int, int] | None = None,
    channel: MaskChannel = "luminance",
    threshold: float = 0.5,
    invert: bool = False,
) -> BoolMask:
    """Load an image and convert it to a boolean wax-domain mask."""
    mode: ImageMode = "RGBA" if channel == "alpha" else "RGB"
    image = load_image(path, mode=mode, size=size)
    return extract_mask(
        image, channel=channel, threshold=threshold, invert=invert
    )


def save_image(path: str | Path, image: NDArray[np.generic]) -> None:
    """Save a boolean, floating-point, or uint8 array as PNG/JPEG.

    Boolean arrays are written as black and white masks. Floating-point arrays
    are interpreted in [0, 1]. Parent directories are created automatically.
    """
    output_path = Path(path).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    array = np.asarray(image)
    if array.dtype == np.bool_:
        encoded = array.astype(np.uint8) * 255
    elif np.issubdtype(array.dtype, np.floating):
        encoded = np.rint(np.clip(array, 0.0, 1.0) * 255).astype(np.uint8)
    elif array.dtype == np.uint8:
        encoded = array
    else:
        raise TypeError("image must be boolean, floating point, or uint8")

    if encoded.ndim not in (2, 3):
        raise ValueError("image must have shape (H, W) or (H, W, channels)")
    if encoded.ndim == 3 and encoded.shape[2] not in (3, 4):
        raise ValueError("color images must have 3 (RGB) or 4 (RGBA) channels")

    Image.fromarray(encoded).save(output_path)


def _validate_size(size: tuple[int, int]) -> None:
    if len(size) != 2 or any(not isinstance(value, int) for value in size):
        raise TypeError("size must be a (width, height) pair of integers")
    if any(value <= 0 for value in size):
        raise ValueError("width and height must be positive")
