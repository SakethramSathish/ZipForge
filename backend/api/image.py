"""
backend/api/image.py — Image optimizer endpoints.
"""

from __future__ import annotations

import base64
import io
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from PIL import Image

from application.image_service import compress_image, optimize_image_to_target
from exceptions import FileCompressorError
from models.image import TargetStatus
from api.cache import cache

router = APIRouter(prefix="/api/image", tags=["image"])


def _to_data_url(data: bytes, format_hint: str) -> str:
    fmt = format_hint.lower().replace("jpg", "jpeg")
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/{fmt};base64,{b64}"


@router.post("/optimize")
async def optimize(
    file: UploadFile = File(...),
    mode: str = Form("profile"),  # "profile" or "target"
    profile_name: str = Form("RECOMMENDED"),
    output_format: str = Form("Auto"),
    preserve_metadata: bool = Form(False),
    target_size_bytes: Optional[int] = Form(None),
):
    original_bytes = await file.read()
    if not original_bytes:
        raise HTTPException(status_code=400, detail="Empty image provided.")

    original_size = len(original_bytes)

    # Get image dimensions
    try:
        with Image.open(io.BytesIO(original_bytes)) as pil_img:
            width, height = pil_img.size
            orig_format = pil_img.format or "JPEG"
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid image format: {str(exc)}")

    try:
        if mode == "target" and target_size_bytes is not None and target_size_bytes > 0:
            target_fmt = output_format if output_format in ("JPEG", "WEBP") else "JPEG"
            res = optimize_image_to_target(
                original_bytes,
                target_size_bytes=target_size_bytes,
                output_format=target_fmt,
            )
            target_status_val = (
                "ACHIEVED" if res.target_status == TargetStatus.ACHIEVED else "BEST_EFFORT"
            )
            iterations = res.iterations
        else:
            fmt_arg = None if output_format == "Auto" else output_format
            res = compress_image(
                original_bytes,
                profile_name=profile_name,
                output_format=fmt_arg,
                preserve_metadata=preserve_metadata,
            )
            target_status_val = None
            iterations = 1
    except FileCompressorError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Image optimization error: {str(exc)}")

    # Dimensions of optimized image
    opt_width, opt_height = width, height
    try:
        with Image.open(io.BytesIO(res.output_bytes)) as opt_img:
            opt_width, opt_height = opt_img.size
    except Exception:
        pass

    job_id = cache.create_id()
    ext = res.output_format.lower()
    download_filename = f"optimized.{ext}"
    cache.set(
        job_id,
        {
            "image_bytes": res.output_bytes,
            "filename": download_filename,
            "mime": f"image/{ext.replace('jpg', 'jpeg')}",
        },
    )

    return {
        "success": True,
        "job_id": job_id,
        "original_size": original_size,
        "final_size": res.final_size,
        "reduction_percent": round(res.reduction_percent, 2),
        "quality": res.quality,
        "output_format": res.output_format,
        "target_status": target_status_val,
        "iterations": iterations,
        "dimensions": {
            "original": {"width": width, "height": height},
            "optimized": {"width": opt_width, "height": opt_height},
        },
        "original_preview": _to_data_url(original_bytes, orig_format),
        "optimized_preview": _to_data_url(res.output_bytes, res.output_format),
        "download_filename": download_filename,
    }
