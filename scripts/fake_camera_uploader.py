#!/usr/bin/env python3
"""
Simple folder-watching uploader that simulates a camera posting images to the API.
"""

import argparse
import json
import shutil
import time
import uuid
from pathlib import Path

import requests

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def is_image(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in IMG_EXTS


def is_stable_file(path: Path, delay: float = 0.1) -> bool:
    """Return True if file size is stable across a short interval."""
    first_size = path.stat().st_size
    time.sleep(delay)
    second_size = path.stat().st_size
    return first_size == second_size


def post_image(
    api_url: str,
    image_path: Path,
    payload: dict,
    timeout: int,
    max_retries: int = 2,
    backoffs: tuple = (1, 3),
):
    """POST image with basic retry/backoff on 429/5xx."""
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            with image_path.open("rb") as handle:
                files = {"image": (image_path.name, handle, "application/octet-stream")}
                response = requests.post(api_url, files=files, data=payload, timeout=timeout)
        except Exception as exc:  # network or timeout
            last_error = exc
        else:
            if response.status_code in (429,) or response.status_code >= 500:
                last_error = requests.HTTPError(
                    f"HTTP {response.status_code}: {response.text}", response=response
                )
            else:
                response.raise_for_status()
                return response.json()

        if attempt < max_retries:
            sleep_for = backoffs[min(attempt, len(backoffs) - 1)]
            print(f"Retrying in {sleep_for}s... (attempt {attempt + 1}/{max_retries})")
            time.sleep(sleep_for)

    raise last_error or RuntimeError("Upload failed")


def main():
    parser = argparse.ArgumentParser(description="Watch a folder and POST images to the analyzer API.")
    parser.add_argument("--watch_dir", default="./incoming_images", help="Folder to watch for new images")
    parser.add_argument("--archive_dir", default="./archive", help="Move processed images here")
    parser.add_argument("--results_dir", default="./results", help="Write JSON results here")
    parser.add_argument("--api_url", required=True, help="e.g. https://<FQDN>/api/v1/analyze")
    parser.add_argument("--product_sku", default="WK-KN-200")
    parser.add_argument("--facility", default="yangjiang")
    parser.add_argument("--station", default="final_qc")
    parser.add_argument("--line_id", default="L1")
    parser.add_argument("--shift", default="A")
    parser.add_argument("--lot", default="")
    parser.add_argument("--operator", default="")
    parser.add_argument("--poll_sec", type=float, default=1.0)
    parser.add_argument("--timeout_sec", type=int, default=60)
    parser.add_argument("--no_archive", action="store_true", help="Do not move processed images")
    parser.add_argument("--dry_run", action="store_true", help="List actions without calling the API")
    args = parser.parse_args()

    watch_dir = Path(args.watch_dir)
    archive_dir = Path(args.archive_dir)
    results_dir = Path(args.results_dir)

    watch_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    if not args.no_archive:
        archive_dir.mkdir(parents=True, exist_ok=True)

    seen = set()

    print(f"[fake-camera] Watching: {watch_dir.resolve()}")
    print(f"[fake-camera] Posting to: {args.api_url}")
    print(f"[fake-camera] SKU={args.product_sku} facility={args.facility} station={args.station} line={args.line_id} shift={args.shift}")

    while True:
        try:
            images = sorted([path for path in watch_dir.iterdir() if is_image(path)])
            for path in images:
                if path.name in seen:
                    continue

                # Skip files that are still being written (size changing)
                if not is_stable_file(path, delay=0.1):
                    continue

                event_id = f"{path.stem}-{uuid.uuid4().hex[:8]}"
                payload = {
                    "product_sku": args.product_sku,
                    "facility": args.facility,
                    "station": args.station,
                    "line_id": args.line_id,
                    "shift": args.shift,
                    "lot": args.lot,
                    "operator": args.operator,
                    "event_id": event_id,
                }

                print(f"\nUploading: {path.name} (event_id={event_id})")
                if args.dry_run:
                    print(f"[dry-run] Would POST to {args.api_url} with payload: {payload}")
                    seen.add(path.name)
                    continue

                try:
                    result = post_image(
                        api_url=args.api_url,
                        image_path=path,
                        payload=payload,
                        timeout=args.timeout_sec,
                    )
                except Exception as exc:  # broad but we only log and continue
                    print(f"Failed: {path.name} ({exc})")
                    error_path = results_dir / f"{path.stem}.error.json"
                    error_payload = {
                        "file": path.name,
                        "event_id": event_id,
                        "error": str(exc),
                    }
                    error_path.write_text(json.dumps(error_payload, ensure_ascii=False, indent=2), encoding="utf-8")
                    print(f"Wrote error: {error_path.name}")
                    seen.add(path.name)
                    continue

                out_json = results_dir / f"{path.stem}.json"
                out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"Wrote: {out_json.name}")

                if not args.no_archive:
                    destination = archive_dir / path.name
                    shutil.move(str(path), str(destination))
                    print(f"Archived: {destination.name}")

                seen.add(path.name)

            time.sleep(args.poll_sec)

        except KeyboardInterrupt:
            print("\nStopped.")
            return


if __name__ == "__main__":
    main()
