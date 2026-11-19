"""Safe image decoding and encoding. Uploads are never written to disk."""
from __future__ import annotations

import io

from PIL import Image, ImageOps, UnidentifiedImageError

from visionai.errors import InvalidInputError

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
# Hard cap well below PIL's decompression-bomb threshold (~178 MP).
MAX_PIXELS = 40_000_000


def load_image(data: bytes, max_bytes: int) -> Image.Image:
    """Decode uploaded bytes into an RGB image, validating size and format."""
    if not data:
        raise InvalidInputError("The uploaded file is empty.")
    if len(data) > max_bytes:
        raise InvalidInputError(f"Image is too large (max {max_bytes // (1024 * 1024)} MB).")

    try:
        with Image.open(io.BytesIO(data)) as img:
            if img.format not in ALLOWED_FORMATS:
                raise InvalidInputError("Unsupported image type. Use JPG, PNG or WEBP.")
            if img.width * img.height > MAX_PIXELS:
                raise InvalidInputError("Image resolution is too high.")
            # Respect phone camera orientation, then fully load into memory.
            return ImageOps.exif_transpose(img).convert("RGB")
    except InvalidInputError:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError) as exc:
        raise InvalidInputError("That file isn't a valid image.") from exc


def to_jpeg_bytes(image: Image.Image, max_side: int = 1600, quality: int = 85) -> bytes:
    """Encode as JPEG, downscaling large images to save bandwidth and AI cost."""
    img = image.convert("RGB")
    if max(img.size) > max_side:
        img = img.copy()
        img.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()
