import inspect
"""
Shared analyzer entrypoint usable by both Flask API and worker, with quality gate + routing.
"""

import asyncio
import io
import os
import tempfile
from contextlib import contextmanager
from typing import Any, Dict, Optional

import numpy as np
from PIL import Image

from agents.defect_analyzer_gpt52 import WikoDefectAnalyzerGPT52
from config import Config

_analyzer = WikoDefectAnalyzerGPT52()

BRIGHTNESS_MIN = 40.0
BRIGHTNESS_MAX = 220.0
BLUR_MIN_VARIANCE = 150.0
FAST_PASS_CONF = float(os.getenv("FAST_PASS_CONFIDENCE", "0.85"))


def compute_quality_metrics(image_bytes: bytes) -> Dict[str, float]:
    """Compute simple quality metrics using numpy only."""
    with Image.open(io.BytesIO(image_bytes)) as img:
        gray = img.convert("L")
        arr = np.array(gray, dtype=np.float32)

    brightness_mean = float(arr.mean())

    # Simple Laplacian approximation using rolls (no OpenCV)
    lap = (
        -4 * arr
        + np.roll(arr, 1, axis=0)
        + np.roll(arr, -1, axis=0)
        + np.roll(arr, 1, axis=1)
        + np.roll(arr, -1, axis=1)
    )
    blur_variance = float(np.var(lap))

    return {
        "brightness_mean": brightness_mean,
        "blur_variance": blur_variance,
    }


def quality_gate(metrics: Dict[str, float]) -> Dict[str, Any]:
    """Evaluate quality metrics and return pass/fail with reason."""
    brightness_mean = metrics["brightness_mean"]
    blur_variance = metrics["blur_variance"]

    if brightness_mean < BRIGHTNESS_MIN:
        return {"pass": False, "reason": "too_dark"}
    if brightness_mean > BRIGHTNESS_MAX:
        return {"pass": False, "reason": "too_bright"}
    if blur_variance < BLUR_MIN_VARIANCE:
        return {"pass": False, "reason": "too_blurry"}
    return {"pass": True, "reason": "ok"}


@contextmanager
def _deployments(analyzer: WikoDefectAnalyzerGPT52, *, vision: Optional[str] = None, reasoning: Optional[str] = None, reports: Optional[str] = None):
    """Temporarily override deployments for fast/full routing."""
    orig = (
        analyzer.vision_deployment,
        analyzer.reasoning_deployment,
        analyzer.reports_deployment,
    )
    try:
        if vision:
            analyzer.vision_deployment = vision
        if reasoning:
            analyzer.reasoning_deployment = reasoning
        if reports:
            analyzer.reports_deployment = reports
        yield
    finally:
        analyzer.vision_deployment, analyzer.reasoning_deployment, analyzer.reports_deployment = orig



async def _maybe_await(x):
    return await x if inspect.isawaitable(x) else x

async def _run_fast_pass(
    analyzer: WikoDefectAnalyzerGPT52,
    image_path: str,
    *,
    product_sku: str,
) -> Dict[str, Any]:
    with _deployments(analyzer, vision=Config.FAST_MODEL_DEPLOYMENT or analyzer.vision_deployment):
        vision_result = await _maybe_await(analyzer._run_vision_classification_agent(
            image_path,
            product_sku,
            reasoning_effort="minimal",
        ))

    defect_detected = vision_result.get("defect_detected", False)
    confidence = float(vision_result.get("confidence", 0.0))
    decision = "UNCERTAIN"
    if not defect_detected and confidence >= FAST_PASS_CONF:
        decision = "PASS"
    elif defect_detected and confidence >= 0.6:
        decision = "FAIL"

    return {
        "decision": decision,
        "defect_detected": defect_detected,
        "defect_type": vision_result.get("defect_type", "unknown"),
        "confidence": confidence,
        "description": vision_result.get("description", ""),
        "bounding_box": vision_result.get("bounding_box"),
        "route": "FAST_ONLY" if decision == "PASS" else "FULL",
        "next_checks": vision_result.get("next_checks", []),
    }


async def _run_full_pass(
    analyzer: WikoDefectAnalyzerGPT52,
    image_path: str,
    *,
    product_sku: str,
    facility: str,
    production_data: Optional[Dict[str, Any]],
    timeout_sec: int,
) -> Dict[str, Any]:
    with _deployments(
        analyzer,
        vision=Config.FULL_MODEL_DEPLOYMENT or analyzer.vision_deployment,
        reasoning=Config.FULL_MODEL_DEPLOYMENT or analyzer.reasoning_deployment,
        reports=Config.FULL_MODEL_DEPLOYMENT or analyzer.reports_deployment,
    ):
        coro = analyzer.analyze_defect(
            image_path=image_path,
            product_sku=product_sku,
            facility=facility,
            production_data=production_data,
        )
        result = await asyncio.wait_for(coro, timeout=timeout_sec)

    result_dict = result.to_dict()
    decision = "FAIL" if result_dict.get("defect_detected") else "PASS"
    result_dict.update(
        {
            "decision": decision,
            "route": "FULL",
            "next_checks": result_dict.get("next_checks", []),
        }
    )
    return result_dict


def analyze_image_bytes(
    image_bytes: bytes,
    *,
    product_sku: str,
    facility: str = "yangjiang",
    production_data: Optional[Dict[str, Any]] = None,
    timeout_sec: int = 60,
    analyzer: Optional[WikoDefectAnalyzerGPT52] = None,
    quality_gate_enabled: bool = True,
) -> Dict[str, Any]:
    """
    Run defect analysis with quality gate and routing; returns dict.
    """
    analyzer = analyzer or _analyzer
    metrics = compute_quality_metrics(image_bytes)
    gate = quality_gate(metrics)

    effective_gate = quality_gate_enabled and Config.QUALITY_GATE_ENABLED
    quality_gate_info = {
        "metrics": metrics,
        "pass": gate["pass"] if effective_gate else True,
        "reason": gate["reason"] if effective_gate else "disabled",
    }

    if effective_gate and not gate["pass"]:
        return {
            "decision": "RECAPTURE",
            "defect_detected": False,
            "defect_type": "unknown",
            "confidence": 0.0,
            "next_checks": [],
            "route": "FAST_ONLY",
            "quality_gate": quality_gate_info,
        }

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        with tempfile.NamedTemporaryFile(suffix=".jpg") as tmp:
            tmp.write(image_bytes)
            tmp.flush()

            fast_result = loop.run_until_complete(
                _run_fast_pass(analyzer, tmp.name, product_sku=product_sku)
            )

            if fast_result["decision"] == "PASS":
                fast_result["quality_gate"] = quality_gate_info
                return fast_result

            full_result = loop.run_until_complete(
                _run_full_pass(
                    analyzer,
                    tmp.name,
                    product_sku=product_sku,
                    facility=facility,
                    production_data=production_data,
                    timeout_sec=timeout_sec,
                )
            )
            full_result["quality_gate"] = quality_gate_info
            return full_result
    finally:
        loop.close()
