"""
Helpers for asynchronous ingestion: hashing, blob upload, and Service Bus enqueue.
"""

import hashlib
import json
import re
from datetime import datetime
from typing import Any, Dict, Optional


def compute_image_id(image_bytes: bytes) -> str:
    """Return a deterministic SHA-256 hex digest for the image bytes."""
    return hashlib.sha256(image_bytes).hexdigest()


def safe_segment(value: str) -> str:
    """Sanitize a path segment to avoid surprising blob paths."""
    return re.sub(r"[^A-Za-z0-9_.-]", "_", value.strip())


def build_blob_path(metadata: Dict[str, Any], image_id: str) -> str:
    """Build blob path using captured_at date and metadata fields."""
    captured = metadata.get("captured_at")
    captured_dt = captured if isinstance(captured, datetime) else None
    if captured_dt is None and isinstance(captured, str):
        try:
            captured_dt = datetime.fromisoformat(captured)
        except Exception:
            captured_dt = datetime.utcnow()
    elif captured_dt is None:
        captured_dt = datetime.utcnow()

    yyyy = f"{captured_dt.year:04d}"
    mm = f"{captured_dt.month:02d}"
    dd = f"{captured_dt.day:02d}"

    sku = safe_segment(str(metadata.get("sku", "")))
    station = safe_segment(str(metadata.get("station", "")))
    line = safe_segment(str(metadata.get("line", "")))
    shift = safe_segment(str(metadata.get("shift", "")))
    lot = safe_segment(str(metadata.get("lot", "")))
    camera_id = safe_segment(str(metadata.get("camera_id", "")))

    return (
        f"raw/{yyyy}/{mm}/{dd}"
        f"/sku={sku}/station={station}/line={line}/shift={shift}/lot={lot}/cam={camera_id}/{image_id}.jpg"
    )


def upload_to_blob(
    image_bytes: bytes,
    *,
    blob_path: str,
    container_name: str,
    content_type: str,
    account_url: Optional[str] = None,
    credential: Any = None,
    connection_string: Optional[str] = None,
) -> str:
    """Upload bytes to Azure Blob Storage and return the blob path."""
    from azure.storage.blob import BlobServiceClient, ContentSettings

    if connection_string:
        service_client = BlobServiceClient.from_connection_string(connection_string)
    elif account_url:
        service_client = BlobServiceClient(account_url=account_url, credential=credential)
    else:
        raise ValueError("Storage configuration is missing: set account URL or connection string.")

    blob_client = service_client.get_blob_client(container=container_name, blob=blob_path)
    blob_client.upload_blob(
        image_bytes,
        overwrite=True,
        content_settings=ContentSettings(content_type=content_type),
    )
    return blob_path


def enqueue_service_bus(
    *,
    message_body: Dict[str, Any],
    message_id: str,
    queue_name: str,
    namespace: Optional[str] = None,
    credential: Any = None,
    connection_string: Optional[str] = None,
) -> None:
    """Send a single message to Service Bus queue."""
    from azure.servicebus import ServiceBusClient, ServiceBusMessage

    body_json = json.dumps(message_body)

    if connection_string:
        client = ServiceBusClient.from_connection_string(conn_str=connection_string)
    elif namespace and credential:
        client = ServiceBusClient(fully_qualified_namespace=namespace, credential=credential)
    else:
        raise ValueError("Service Bus configuration is missing: set namespace or connection string.")

    with client:
        sender = client.get_queue_sender(queue_name=queue_name)
        with sender:
            sender.send_messages(
                ServiceBusMessage(
                    body_json,
                    message_id=message_id,
                    content_type="application/json",
                )
            )
