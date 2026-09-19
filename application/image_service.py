"""
application/image_service.py — Image compression application service.

Orchestrates image compression and target-size optimization.
No dependency on Streamlit.
"""

from __future__ import annotations

import logging

from config import (
    DEFAULT_IMAGE_PROFILE,
    LOGGER_NAME,
    TARGET_SIZE_MAX_ITERATIONS,
    TARGET_SIZE_MAX_QUALITY,
    TARGET_SIZE_MIN_QUALITY,
)
from image.compressor import compress_image as _compress_image
from image.optimizer import ProgressCallback, optimize_to_target
from models.image import (
    ImageCompressionResult,
    ImageProfile,
    TargetSizeSettings,
)

logger = logging.getLogger(LOGGER_NAME)


def compress_image(
    image_bytes: bytes,
    profile_name: str = DEFAULT_IMAGE_PROFILE,
    output_format: str | None = None,
    preserve_metadata: bool = False,
) -> ImageCompressionResult:
    """
    Compress an image using a named profile.

    Args:
        image_bytes:       Raw image file bytes.
        profile_name:      "EXTREME", "RECOMMENDED", or "LESS_COMPRESSION".
        output_format:     Optional override ("JPEG", "PNG", "WEBP").
        preserve_metadata: Whether to preserve EXIF metadata.

    Returns:
        ImageCompressionResult.
    """
    try:
        profile = ImageProfile(profile_name.upper())
    except ValueError:
        logger.warning("Unknown profile %r; falling back to RECOMMENDED", profile_name)
        profile = ImageProfile.RECOMMENDED

    logger.info(
        "Compressing image: %d bytes, profile=%s, format=%s",
        len(image_bytes), profile_name, output_format or "auto",
    )
    return _compress_image(
        image_bytes,
        profile=profile,
        output_format=output_format,
        preserve_metadata=preserve_metadata,
    )


def optimize_image_to_target(
    image_bytes: bytes,
    target_size_bytes: int,
    output_format: str = "JPEG",
    min_quality: int = TARGET_SIZE_MIN_QUALITY,
    max_quality: int = TARGET_SIZE_MAX_QUALITY,
    max_iterations: int = TARGET_SIZE_MAX_ITERATIONS,
    preserve_metadata: bool = False,
    progress_callback: ProgressCallback | None = None,
) -> ImageCompressionResult:
    """
    Optimize an image to fit within *target_size_bytes*.

    Args:
        image_bytes:       Raw image file bytes.
        target_size_bytes: Maximum output size in bytes.
        output_format:     Preferred output format.
        min_quality:       Minimum acceptable encoder quality.
        max_quality:       Maximum encoder quality to try.
        max_iterations:    Binary search iteration limit.
        preserve_metadata: Whether to preserve EXIF metadata.
        progress_callback: Called on each iteration with (iter, max, quality, size).

    Returns:
        ImageCompressionResult.  Check target_status for ACHIEVED/UNACHIEVABLE.
    """
    logger.info(
        "Target-size optimization: target=%d bytes, format=%s, quality=[%d, %d]",
        target_size_bytes, output_format, min_quality, max_quality,
    )
    settings = TargetSizeSettings(
        target_bytes=target_size_bytes,
        min_quality=min_quality,
        max_quality=max_quality,
        max_iterations=max_iterations,
        output_format=output_format,
        preserve_metadata=preserve_metadata,
    )
    return optimize_to_target(image_bytes, settings, progress_callback=progress_callback)
