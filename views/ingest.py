"""
Async ingestion endpoint: accepts images + metadata, uploads to blob, and enqueues Service Bus work.
"""

import json
from datetime import datetime
from typing import Dict, Tuple

from flask import Blueprint, current_app, jsonify, request

from config import Config
from ingest import (
    build_blob_path,
    compute_image_id,
    enqueue_service_bus,
    upload_to_blob,
)

ingest_bp = Blueprint("ingest_bp", __name__)

REQUIRED_FIELDS = ("sku", "station", "line", "shift", "lot", "camera_id", "captured_at")


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def parse_captured_at(value: str) -> datetime:
    """Parse ISO8601 timestamps, allowing a trailing Z."""
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def validate_metadata(form) -> Tuple[Dict, datetime]:
    missing = [field for field in REQUIRED_FIELDS if not form.get(field)]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    captured_raw = form.get("captured_at")
    try:
        captured_at = parse_captured_at(captured_raw)
    except Exception as exc:
        raise ValueError(f"Invalid captured_at (must be ISO8601): {exc}") from exc

    metadata = {
        "sku": form.get("sku"),
        "station": form.get("station"),
        "line": form.get("line"),
        "shift": form.get("shift"),
        "lot": form.get("lot"),
        "camera_id": form.get("camera_id"),
        "captured_at": captured_at,
    }
    return metadata, captured_at


@ingest_bp.route("/ingest", methods=["POST"])
def ingest_image():
    if "image" not in request.files:
        return jsonify({"error": "image file is required"}), 400

    file = request.files["image"]
    if not file or file.filename == "" or not allowed_file(file.filename):
        return jsonify({"error": "invalid or missing image file"}), 400

    try:
        metadata, captured_at = validate_metadata(request.form)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    image_bytes = file.read()
    if not image_bytes:
        return jsonify({"error": "empty image payload"}), 400

    max_len = current_app.config.get("MAX_CONTENT_LENGTH", Config.MAX_CONTENT_LENGTH)
    if len(image_bytes) > max_len:
        return jsonify({"error": "File too large"}), 413

    image_id = compute_image_id(image_bytes)
    content_type = file.mimetype or "application/octet-stream"
    blob_path = build_blob_path(metadata, image_id)
    byte_len = len(image_bytes)

    storage_account_url = Config.AZURE_STORAGE_ACCOUNT_URL
    storage_container = Config.AZURE_STORAGE_CONTAINER_RAW
    storage_conn_str = Config.AZURE_STORAGE_CONNECTION_STRING
    if not storage_account_url and not storage_conn_str:
        return jsonify({"error": "Storage configuration missing"}), 503

    service_bus_namespace = Config.SERVICE_BUS_NAMESPACE_FQDN
    service_bus_queue = Config.SERVICE_BUS_QUEUE
    service_bus_conn_str = Config.SERVICE_BUS_CONNECTION_STRING
    if not service_bus_namespace and not service_bus_conn_str:
        return jsonify({"error": "Service Bus configuration missing"}), 503

    credential = None
    if not storage_conn_str or not service_bus_conn_str:
        try:
            from azure.identity import DefaultAzureCredential

            credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
        except Exception as exc:
            # If connection strings are provided, credential may stay None
            if not storage_conn_str or not service_bus_conn_str:
                return jsonify({"error": f"Credential initialization failed: {exc}"}), 503

    try:
        upload_to_blob(
            image_bytes=image_bytes,
            blob_path=blob_path,
            container_name=storage_container,
            content_type=content_type,
            account_url=storage_account_url,
            credential=credential,
            connection_string=storage_conn_str,
        )
    except Exception as exc:
        return jsonify({"error": f"Blob upload failed: {exc}"}), 503

    message_body = {
        "image_id": image_id,
        "blob_path": blob_path,
        "metadata": {
            **{k: v for k, v in metadata.items() if k != "captured_at"},
            "captured_at": captured_at.isoformat(),
        },
        "content_type": content_type,
        "byte_len": byte_len,
    }

    try:
        enqueue_service_bus(
            message_body=message_body,
            message_id=image_id,
            queue_name=service_bus_queue,
            namespace=service_bus_namespace,
            credential=credential,
            connection_string=service_bus_conn_str,
        )
    except Exception as exc:
        # Do not delete blob; allow reconciliation later
        return jsonify({"error": f"Queue enqueue failed: {exc}"}), 503

    return jsonify({"image_id": image_id, "status": "ACCEPTED"}), 202
