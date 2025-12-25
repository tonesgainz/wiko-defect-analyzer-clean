import io

import pytest

pytest.importorskip("flask")

from ingest import compute_image_id
from views.ingest import validate_metadata


def test_compute_image_id_deterministic():
    assert compute_image_id(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_validate_metadata_missing_fields():
    class DummyForm(dict):
        def get(self, key, default=None):
            return super().get(key, default)

    with pytest.raises(ValueError) as excinfo:
        validate_metadata(DummyForm({"sku": "123"}))

    message = str(excinfo.value)
    assert "Missing required fields" in message
    assert "station" in message


def test_ingest_endpoint_success(monkeypatch):
    import app as app_module
    from views import ingest as ingest_view

    # Force connection-string mode to avoid credential creation during tests
    ingest_view.Config.AZURE_STORAGE_ACCOUNT_URL = None
    ingest_view.Config.AZURE_STORAGE_CONNECTION_STRING = "UseDevelopmentStorage=true"
    ingest_view.Config.SERVICE_BUS_NAMESPACE_FQDN = None
    ingest_view.Config.SERVICE_BUS_CONNECTION_STRING = "Endpoint=sb://dummy/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=dummy"

    upload_calls = {}
    enqueue_calls = {}

    def fake_upload(**kwargs):
        upload_calls.update(kwargs)
        return kwargs["blob_path"]

    def fake_enqueue(**kwargs):
        enqueue_calls.update(kwargs)
        return None

    monkeypatch.setattr(ingest_view, "upload_to_blob", fake_upload)
    monkeypatch.setattr(ingest_view, "enqueue_service_bus", fake_enqueue)

    client = app_module.app.test_client()
    image_bytes = b"hello world"
    data = {
        "sku": "WK-KN-200",
        "station": "final_qc",
        "line": "L1",
        "shift": "A",
        "lot": "LOT-123",
        "camera_id": "CAM-01",
        "captured_at": "2024-12-25T10:00:00Z",
        "image": (io.BytesIO(image_bytes), "sample.jpg"),
    }

    resp = client.post("/api/v1/ingest", data=data, content_type="multipart/form-data")

    assert resp.status_code == 202
    body = resp.get_json()
    assert body["status"] == "ACCEPTED"
    assert "image_id" in body

    assert upload_calls["container_name"] == ingest_view.Config.AZURE_STORAGE_CONTAINER_RAW
    assert upload_calls["blob_path"] == enqueue_calls["message_body"]["blob_path"]
    assert enqueue_calls["message_id"] == body["image_id"]
    assert enqueue_calls["message_body"]["byte_len"] == len(image_bytes)
    assert enqueue_calls["message_body"]["metadata"]["sku"] == "WK-KN-200"
    assert enqueue_calls["message_body"]["metadata"]["captured_at"] == "2024-12-25T10:00:00+00:00"
