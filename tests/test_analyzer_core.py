import io

import pytest

try:
    import azure  # noqa: F401
except ImportError:
    pytest.skip("azure SDK not installed", allow_module_level=True)

from PIL import Image

from analyzer_core import analyze_image_bytes, compute_quality_metrics, quality_gate


def make_image_bytes(color: int = 0):
    img = Image.new("RGB", (10, 10), color=(color, color, color))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_quality_gate_dark_image():
    dark_bytes = make_image_bytes(color=1)
    metrics = compute_quality_metrics(dark_bytes)
    gate = quality_gate(metrics)
    assert gate["pass"] is False
    assert gate["reason"] == "too_dark"


def test_fast_pass_short_circuits_to_pass(monkeypatch):
    class FakeAnalyzer:
        def _run_vision_classification_agent(self, image_path, product_sku, reasoning_effort="minimal"):
            return {"defect_detected": False, "confidence": 0.9, "defect_type": "none"}

        def analyze_defect(self, **kwargs):
            raise AssertionError("Full pass should not be called when fast PASS with high confidence")

        vision_deployment = "fast"
        reasoning_deployment = "full"
        reports_deployment = "full"

    result = analyze_image_bytes(
        make_image_bytes(color=200),
        product_sku="SKU",
        analyzer=FakeAnalyzer(),
        quality_gate_enabled=False,
    )
    assert result["decision"] == "PASS"
    assert result["route"] == "FAST_ONLY"


def test_falls_back_to_full_when_uncertain(monkeypatch):
    class FakeResult:
        def to_dict(self):
            return {"defect_detected": True, "defect_type": "scratch", "confidence": 0.5}

    class FakeAnalyzer:
        def __init__(self):
            self.full_called = False

        def _run_vision_classification_agent(self, image_path, product_sku, reasoning_effort="minimal"):
            return {"defect_detected": False, "confidence": 0.5, "defect_type": "unknown"}

        async def analyze_defect(self, **kwargs):
            self.full_called = True
            return FakeResult()

        vision_deployment = "fast"
        reasoning_deployment = "full"
        reports_deployment = "full"

    result = analyze_image_bytes(
        make_image_bytes(color=120),
        product_sku="SKU",
        analyzer=FakeAnalyzer(),
        quality_gate_enabled=False,
    )
    assert result["route"] == "FULL"
    assert result["decision"] == "FAIL"
