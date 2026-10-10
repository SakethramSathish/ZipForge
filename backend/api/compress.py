"""
backend/api/compress.py — Compression endpoints.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from application.compression_service import compress_files, compress_files_to_target
from exceptions import FileCompressorError
from api.cache import cache

router = APIRouter(prefix="/api/compress", tags=["compress"])

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


@router.post("")
async def compress(
    files: List[UploadFile] = File(...),
    level: str = Form("RECOMMENDED"),
    algorithm: Optional[str] = Form(None),
    archive_name: str = Form("archive"),
    use_target_size: bool = Form(False),
    target_size_bytes: Optional[int] = Form(None),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided for compression.")

    file_pairs: List[tuple[str, bytes]] = []
    for f in files:
        content = await f.read()
        file_pairs.append((f.filename or "file", content))

    total_input = sum(len(d) for _, d in file_pairs)
    t0 = time.perf_counter()

    # Determine algorithm based on level or override
    _LEVEL_TO_ALGO = {
        "EXTREME": "AUTO",
        "RECOMMENDED": "AUTO",
        "LESS": "STORE",
    }
    selected_algo = algorithm if algorithm else _LEVEL_TO_ALGO.get(level.upper(), "AUTO")

    target_status: Optional[str] = None
    try:
        if use_target_size and target_size_bytes is not None and target_size_bytes > 0:
            archive_bytes, results, target_status, processed_files = compress_files_to_target(
                file_pairs,
                target_size_bytes=target_size_bytes,
            )
        else:
            archive_bytes, results, processed_files = compress_files(
                file_pairs,
                algorithm=selected_algo,
            )
    except FileCompressorError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Compression error: {str(exc)}")

    elapsed = time.perf_counter() - t0
    total_compressed = len(archive_bytes)
    reduction = max(0.0, (total_input - total_compressed) / max(total_input, 1) * 100)
    ratio = total_input / max(total_compressed, 1)

    clean_name = archive_name.rstrip(".").strip() if archive_name else "archive"
    safe_name = "".join(c for c in clean_name if c.isalnum() or c in "-_. ").strip() or "archive"

    job_id = cache.create_id()
    cache.set(
        job_id,
        {
            "archive_bytes": archive_bytes,
            "archive_filename": f"{safe_name}.zip",
            "processed_files": processed_files,
            "safe_name": safe_name,
        },
    )

    per_file_details = []
    for r, (fname, _) in zip(results, file_pairs):
        algo_name = r.algorithm.value if hasattr(r.algorithm, "value") else str(r.algorithm)
        per_file_details.append(
            {
                "name": fname,
                "original_size": r.original_size,
                "compressed_size": r.compressed_size,
                "reduction_percent": round(r.reduction_percent, 2),
                "compression_ratio": round(r.compression_ratio, 2) if r.compression_ratio != float("inf") else 9999.0,
                "algorithm": algo_name,
                "duration_ms": round(r.duration * 1000, 2),
                "sha256": getattr(r, "sha256", ""),
            }
        )

    is_single_file = len(processed_files) == 1
    single_dl_name = None
    single_dl_mime = None
    if is_single_file:
        orig_fname, _ = processed_files[0]
        ext = Path(orig_fname).suffix.lower()
        single_dl_mime = _MIME_TYPES.get(ext, "application/octet-stream")
        if clean_name and clean_name.lower() != "archive":
            single_dl_name = f"{safe_name}{ext}"
        else:
            single_dl_name = orig_fname

    return {
        "success": True,
        "job_id": job_id,
        "archive_name": f"{safe_name}.zip",
        "total_input": total_input,
        "total_compressed": total_compressed,
        "reduction_percent": round(reduction, 2),
        "compression_ratio": round(ratio, 2),
        "elapsed_seconds": round(elapsed, 3),
        "target_status": target_status,
        "is_single_file": is_single_file,
        "single_file_name": single_dl_name,
        "single_file_mime": single_dl_mime,
        "files": per_file_details,
    }
