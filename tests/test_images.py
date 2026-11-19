import io

import pytest
from PIL import Image

from tests.conftest import make_image_bytes
from visionai.errors import InvalidInputError
from visionai.vision.images import load_image, to_jpeg_bytes

MB = 1024 * 1024


def test_loads_jpeg_as_rgb(jpeg_bytes):
    img = load_image(jpeg_bytes, 5 * MB)
    assert img.mode == "RGB"
    assert img.size == (64, 48)


def test_png_with_alpha_is_converted_to_rgb():
    img = load_image(make_image_bytes("PNG", mode="RGBA"), 5 * MB)
    assert img.mode == "RGB"


@pytest.mark.parametrize("data", [b"", b"not an image at all"])
def test_rejects_empty_or_garbage(data):
    with pytest.raises(InvalidInputError):
        load_image(data, 5 * MB)


def test_rejects_oversize_file(jpeg_bytes):
    with pytest.raises(InvalidInputError, match="too large"):
        load_image(jpeg_bytes, max_bytes=10)


def test_rejects_unsupported_format():
    with pytest.raises(InvalidInputError, match="Unsupported"):
        load_image(make_image_bytes("GIF", mode="P"), 5 * MB)


def test_to_jpeg_downscales_large_images():
    big = Image.new("RGB", (4000, 2000))
    out = Image.open(io.BytesIO(to_jpeg_bytes(big, max_side=1000)))
    assert out.format == "JPEG"
    assert max(out.size) == 1000
