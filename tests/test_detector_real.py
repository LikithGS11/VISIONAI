import pytest
from PIL import Image

from visionai.config import PROJECT_ROOT

DEMO = PROJECT_ROOT / "images" / "ATSFHIGLVLE.jpg"


@pytest.mark.slow
def test_real_model_on_demo_image():
    from visionai.vision.detector import get_detector

    if not DEMO.exists():
        pytest.skip("demo image missing")
    result = get_detector().detect(Image.open(DEMO))
    assert result.annotated is not None
    assert result.annotated.size == (result.width, result.height)
    for d in result.objects:
        assert d.position in {"left", "ahead", "right"}
        assert 0 <= d.confidence <= 100
    assert isinstance(result.summary(), str)
