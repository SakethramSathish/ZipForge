"""
backend/api/download.py — Streaming artifact download endpoints.
"""

from __future__ import annotations

import io
from pathlib import Path
import urllib.parse
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, StreamingResponse

from api.cache import cache

router = APIRouter(prefix="/api/download", tags=["download"])

_MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
    ".gif": "image/gif",
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".csv": "text/csv",
    ".json": "application/json",
    ".xml": "application/xml",
    ".html": "text/html",
    ".md": "text/markdown",
    ".zip": "application/zip",
}


@router.get("/archive/{job_id}")
async def download_archive(job_id: str):
    entry = cache.get(job_id)
    if not entry or "archive_bytes" not in entry:
        raise HTTPException(status_code=404, detail="Archive not found or expired.")

    filename = entry.get("archive_filename", "archive.zip")
    encoded_filename = urllib.parse.quote(filename)
    return Response(
        content=entry["archive_bytes"],
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\"; filename*=UTF-8''{encoded_filename}",
            "Content-Length": str(len(entry["archive_bytes"])),
        },
    )


@router.get("/file/{job_id}/{file_index}")
async def download_processed_file(job_id: str, file_index: int):
    entry = cache.get(job_id)
    if not entry or "processed_files" not in entry:
        raise HTTPException(status_code=404, detail="Files not found or expired.")

    processed = entry["processed_files"]
    if file_index < 0 or file_index >= len(processed):
        raise HTTPException(status_code=404, detail="File index out of range.")

    orig_name, file_bytes = processed[file_index]
    safe_name = entry.get("safe_name")
    ext = Path(orig_name).suffix.lower()
    mime = _MIME_TYPES.get(ext, "application/octet-stream")

    if len(processed) == 1 and safe_name and safe_name.lower() != "archive":
        dl_name = f"{safe_name}{ext}"
    else:
        dl_name = orig_name

    encoded_name = urllib.parse.quote(dl_name)
    return Response(
        content=file_bytes,
        media_type=mime,
        headers={
            "Content-Disposition": f"attachment; filename=\"{dl_name}\"; filename*=UTF-8''{encoded_name}",
            "Content-Length": str(len(file_bytes)),
        },
    )


@router.get("/extracted/{job_id}/{file_index}")
async def download_extracted_file(job_id: str, file_index: int):
    entry = cache.get(job_id)
    if not entry or "extracted_files" not in entry:
        raise HTTPException(status_code=404, detail="Extracted entries not found or expired.")

    extracted = entry["extracted_files"]
    if file_index < 0 or file_index >= len(extracted):
        raise HTTPException(status_code=404, detail="File index out of range.")

    path, data = extracted[file_index]
    filename = Path(path).name
    ext = Path(filename).suffix.lower()
    mime = _MIME_TYPES.get(ext, "application/octet-stream")

    encoded_name = urllib.parse.quote(filename)
    return Response(
        content=data,
        media_type=mime,
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\"; filename*=UTF-8''{encoded_name}",
            "Content-Length": str(len(data)),
        },
    )


@router.get("/image/{job_id}")
async def download_optimized_image(job_id: str):
    entry = cache.get(job_id)
    if not entry or "image_bytes" not in entry:
        raise HTTPException(status_code=404, detail="Optimized image not found or expired.")

    filename = entry.get("filename", "optimized.png")
    mime = entry.get("mime", "application/octet-stream")
    encoded_name = urllib.parse.quote(filename)

    return Response(
        content=entry["image_bytes"],
        media_type=mime,
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\"; filename*=UTF-8''{encoded_name}",
            "Content-Length": str(len(entry["image_bytes"])),
        },
    )
