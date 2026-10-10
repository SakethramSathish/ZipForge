"""
backend/api/decompress.py — Archive preview and extraction endpoints.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile

from application.compression_service import decompress_to_memory, inspect_archive
from exceptions import FileCompressorError
from api.cache import cache

router = APIRouter(prefix="/api/decompress", tags=["decompress"])

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


@router.post("/preview")
async def preview_archive(archive: UploadFile = File(...)):
    content = await archive.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty archive file provided.")

    try:
        inspection = inspect_archive(content)
    except FileCompressorError as exc:
        raise HTTPException(status_code=422, detail=f"Archive inspection failed: {str(exc)}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to inspect archive: {str(exc)}")

    entries = []
    for entry in inspection.entries:
        entries.append(
            {
                "path": entry.path,
                "algorithm": entry.algorithm,
                "original_size": entry.original_size,
                "compressed_size": entry.compressed_size,
                "reduction_percent": round(entry.reduction_percent, 2),
                "integrity_status": entry.integrity_status,
                "sha256": getattr(entry, "sha256", ""),
            }
        )

    return {
        "success": True,
        "version": inspection.version,
        "entry_count": inspection.entry_count,
        "total_original": inspection.total_original,
        "overall_reduction_percent": round(inspection.overall_reduction_percent, 2),
        "entries": entries,
    }


@router.post("/extract")
async def extract_archive(archive: UploadFile = File(...)):
    content = await archive.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty archive file provided.")

    try:
        extracted_entries = decompress_to_memory(content)
    except FileCompressorError as exc:
        raise HTTPException(status_code=422, detail=f"Decompression error: {str(exc)}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to decompress archive: {str(exc)}")

    job_id = cache.create_id()
    cache.set(
        job_id,
        {
            "extracted_files": extracted_entries,
        },
    )

    files_list = []
    for idx, (path, data) in enumerate(extracted_entries):
        ext = Path(path).suffix.lower()
        mime = _MIME_TYPES.get(ext, "application/octet-stream")
        files_list.append(
            {
                "index": idx,
                "path": path,
                "name": Path(path).name,
                "size": len(data),
                "mime": mime,
            }
        )

    return {
        "success": True,
        "job_id": job_id,
        "count": len(extracted_entries),
        "files": files_list,
    }
