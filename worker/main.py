"""
Service Bus worker: downloads images, runs analysis, uploads results.
"""
from __future__ import annotations
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, Optional, TYPE_CHECKING

from pydantic import BaseModel, ValidationError, field_validator
from azure.storage.blob import BlobServiceClient

# Allow imports from repo root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from analyzer_core import analyze_image_bytes  # noqa: E402
from ingest import build_blob_path  # noqa: E402
from config import Config  # noqa: E402

if TYPE_CHECKING:  # pragma: no cover
    from azure.storage.blob import BlobServiceClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("worker")


class MessageBody(BaseModel):
    image_id: str
    blob_path: str
    metadata: Dict[str, Any]
    content_type: str
    byte_len: int


class AnalysisSchema(BaseModel):
    defect_id: str
    timestamp: datetime
    facility: str
    product_sku: str
    defect_detected: bool
    defect_type: str
    severity: str
    confidence: float
    description: str
    affected_area: str | None = None
    bounding_box: Dict[str, Any] | None = None
    probable_stage: str | None = None
    root_cause: str | None = None
    five_why_chain: list | None = None
    contributing_factors: list | None = None
    ishikawa_analysis: Dict[str, Any] | None = None
    corrective_actions: list | None = None
    preventive_actions: list | None = None
    reasoning_tokens_used: int | None = None
    model_version: str | None = None

    @field_validator("confidence")
    @classmethod
    def non_negative_confidence(cls, v):
        if v < 0:
            raise ValueError("confidence must be non-negative")
        return v


def get_blob_service():
    from azure.identity import DefaultAzureCredential
    from azure.storage.blob import BlobServiceClient

    if Config.AZURE_STORAGE_CONNECTION_STRING:
        return BlobServiceClient.from_connection_string(conn_str=Config.AZURE_STORAGE_CONNECTION_STRING)
    credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
    return BlobServiceClient(account_url=Config.AZURE_STORAGE_ACCOUNT_URL, credential=credential)


def get_servicebus_client():
    from azure.identity import DefaultAzureCredential
    from azure.servicebus import ServiceBusClient

    if Config.SERVICE_BUS_CONNECTION_STRING:
        return ServiceBusClient.from_connection_string(conn_str=Config.SERVICE_BUS_CONNECTION_STRING)
    credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
    return ServiceBusClient(fully_qualified_namespace=Config.SERVICE_BUS_NAMESPACE_FQDN, credential=credential)


def build_results_path(metadata: Dict[str, Any], image_id: str) -> str:
    path = build_blob_path(metadata, image_id)
    if path.startswith("raw/"):
        return "results/" + path[len("raw/") :]
    return f"results/{path}"


def blob_exists(blob_service: BlobServiceClient, container: str, blob: str) -> bool:
    client = blob_service.get_blob_client(container=container, blob=blob)
    return client.exists()


def download_blob(blob_service: BlobServiceClient, container: str, blob: str) -> bytes:
    client = blob_service.get_blob_client(container=container, blob=blob)
    return client.download_blob().readall()


def upload_json(blob_service: BlobServiceClient, container: str, blob: str, data: Dict[str, Any]):
    from azure.storage.blob import ContentSettings

    client = blob_service.get_blob_client(container=container, blob=blob)
    client.upload_blob(
        json.dumps(data, ensure_ascii=False, indent=2),
        overwrite=True,
        content_settings=ContentSettings(content_type="application/json"),
    )


async def process_message(message, blob_service, results_container: str):
    start = time.time()
    image_id = None
    try:
        chunks = []
        for section in message.body:
            if isinstance(section, str):
                chunks.append(section.encode("utf-8"))
            elif isinstance(section, (bytes, bytearray)):
                chunks.append(bytes(section))
            else:
                chunks.append(bytes(section))
        body = b"".join(chunks)
        payload = MessageBody.model_validate(json.loads(body))
        image_id = payload.image_id
    except Exception as exc:
        logger.error("Failed to parse message: %s", exc)
        raise DeadLetterError("invalid_message", str(exc))

    metadata = payload.metadata
    results_blob = build_results_path(metadata, payload.image_id)

    try:
        if blob_exists(blob_service, results_container, results_blob):
            logger.info("Idempotent: result already exists for image_id=%s", payload.image_id)
            return "complete"
    except Exception as exc:
        logger.warning("Idempotency check failed (transient): %s", exc)
        return "abandon"

    try:
        image_bytes = download_blob(blob_service, Config.AZURE_STORAGE_CONTAINER_RAW, payload.blob_path)
    except Exception as exc:
        logger.warning("Download failed for image_id=%s: %s", payload.image_id, exc)
        return "abandon"

    try:
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: analyze_image_bytes(
                    image_bytes,
                    product_sku=metadata.get("sku", ""),
                    facility=metadata.get("facility", "yangjiang"),
                    production_data=metadata,
                    timeout_sec=60,
                ),
            ),
            timeout=65,
        )
    except asyncio.TimeoutError:
        logger.warning("Analysis timeout for image_id=%s", payload.image_id)
        return "abandon"
    except Exception as exc:
        logger.error("Analysis failed for image_id=%s: %s", payload.image_id, exc)
        if "image" in str(exc).lower():
            raise DeadLetterError("bad_image", str(exc))
        return "abandon"

    try:
        AnalysisSchema.model_validate(result)
    except ValidationError as exc:
        logger.error("Schema validation failed for image_id=%s: %s", payload.image_id, exc)
        raise DeadLetterError("schema_invalid", str(exc))

    try:
        upload_json(blob_service, results_container, results_blob, result)
    except Exception as exc:
        logger.warning("Result upload failed for image_id=%s: %s", payload.image_id, exc)
        return "abandon"

    latency_ms = int((time.time() - start) * 1000)
    logger.info(
        "Processed image_id=%s sku=%s station=%s line=%s shift=%s latency_ms=%s",
        payload.image_id,
        metadata.get("sku"),
        metadata.get("station"),
        metadata.get("line"),
        metadata.get("shift"),
        latency_ms,
    )
    return "complete"


class DeadLetterError(Exception):
    def __init__(self, reason: str, description: str):
        super().__init__(description)
        self.reason = reason
        self.description = description


def main():
    if not Config.AZURE_STORAGE_ACCOUNT_URL and not Config.AZURE_STORAGE_CONNECTION_STRING:
        raise SystemExit("Storage configuration missing")
    if not Config.SERVICE_BUS_NAMESPACE_FQDN and not Config.SERVICE_BUS_CONNECTION_STRING:
        raise SystemExit("Service Bus configuration missing")

    results_container = Config.AZURE_STORAGE_CONTAINER_PROCESSED
    blob_service = get_blob_service()
    sb_client = get_servicebus_client()

    with sb_client:
        receiver = sb_client.get_queue_receiver(queue_name=Config.SERVICE_BUS_QUEUE, max_wait_time=5)
        with receiver:
            for message in receiver:
                try:
                    outcome = asyncio.run(process_message(message, blob_service, results_container))
                    if outcome == "complete":
                        receiver.complete_message(message)
                    elif outcome == "abandon":
                        receiver.abandon_message(message)
                except DeadLetterError as dle:
                    logger.error("Dead-lettering image_id=%s reason=%s desc=%s", getattr(message, "message_id", None), dle.reason, dle.description)
                    receiver.dead_letter_message(message, reason=dle.reason, error_description=dle.description)
                except Exception as exc:
                    logger.error("Unexpected error: %s", exc)
                    receiver.abandon_message(message)


if __name__ == "__main__":
    main()
