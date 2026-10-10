"""
backend/api/inspect.py — Standalone archive inspection endpoint.
"""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from application.compression_service import inspect_archive
from exceptions import FileCompressorError

router = APIRouter(prefix="/api/inspect", tags=["inspect"])


@router.post("")
async def inspect(archive: UploadFile = File(...)):
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
        "filename": archive.filename or "archive.zip",
        "version": inspection.version,
        "entry_count": inspection.entry_count,
        "total_original": inspection.total_original,
        "overall_reduction_percent": round(inspection.overall_reduction_percent, 2),
        "entries": entries,
    }
