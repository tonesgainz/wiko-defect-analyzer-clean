import datetime

import pytest

pytest.importorskip("azure")

from worker.main import AnalysisSchema, blob_exists, build_results_path


def test_blob_exists_idempotent_true():
    class FakeClient:
        def __init__(self, exists):
            self._exists = exists

        def exists(self):
            return self._exists

    class FakeService:
        def __init__(self, exists):
            self._exists = exists

        def get_blob_client(self, container, blob):
            return FakeClient(self._exists)

    assert blob_exists(FakeService(True), "c", "b") is True
    assert blob_exists(FakeService(False), "c", "b") is False


def test_analysis_schema_validation():
    data = {
        "defect_id": "DEF-1",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "facility": "yangjiang",
        "product_sku": "SKU",
        "defect_detected": True,
        "defect_type": "edge_irregularity",
        "severity": "major",
        "confidence": 0.9,
        "description": "desc",
    }
    AnalysisSchema.model_validate(data)

    bad = {**data, "confidence": -0.1}
    with pytest.raises(Exception):
        AnalysisSchema.model_validate(bad)


def test_build_results_path():
    metadata = {
        "sku": "SKU",
        "station": "final_qc",
        "line": "L1",
        "shift": "A",
        "lot": "LOT1",
        "camera_id": "CAM",
        "captured_at": "2024-12-25T10:00:00Z",
    }
    path = build_results_path(metadata, "abc")
    assert path.startswith("results/")
    assert "sku=SKU" in path
