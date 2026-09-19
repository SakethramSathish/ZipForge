"""
image/compressor.py — Profile-based image compression.

Applies a named profile (EXTREME, RECOMMENDED, LESS_COMPRESSION) to
compress an image using Pillow encoding.
"""

from __future__ import annotations

import io
import time

from image.formats import detect_format, encode_image, load_image, prepare_image_for_encoding
from image.profiles import get_profile
from models.image import ImageCompressionResult, ImageProfile, TargetStatus


def compress_image(
    image_bytes: bytes,
    profile: ImageProfile = ImageProfile.RECOMMENDED,
    output_format: str | None = None,
    preserve_metadata: bool = False,
) -> ImageCompressionResult:
    """
    Compress an image using the specified profile.

    Args:
        image_bytes:       Raw bytes of the input image.
        profile:           Compression level profile.
        output_format:     Override output format (e.g. "JPEG", "WEBP").
                           If None, format is inferred from input.
        preserve_metadata: Whether to preserve EXIF/ICC metadata.

    Returns:
        ImageCompressionResult with compressed bytes and metrics.

    Raises:
        UnsupportedImageFormatError: if the image cannot be loaded.
        TransparencyConversionError: if a conflicting format conversion is attempted.
        ImageOptimizationError:      on encoding failure.
    """
    from exceptions import ImageOptimizationError

    start = time.perf_counter()
    original_size = len(image_bytes)

    img, original_fmt = load_image(image_bytes)
    prof = get_profile(profile)

    # Determine output format
    fmt = output_format or detect_format(img, original_fmt)

    # Handle metadata
    meta_preserved = preserve_metadata or prof.preserve_metadata

    # Prepare image for the target format
    prepared = prepare_image_for_encoding(img, fmt)

    try:
        output_bytes = encode_image(
            prepared,
            output_format=fmt,
            quality=prof.quality,
            optimize=prof.optimize,
            progressive=prof.progressive,
            preserve_exif=meta_preserved,
        )
    except Exception as exc:
        raise ImageOptimizationError(
            f"Failed to encode image with profile {profile.value}: {exc}"
        ) from exc

    duration = time.perf_counter() - start
    final_size = len(output_bytes)

    return ImageCompressionResult(
        original_size=original_size,
        final_size=final_size,
        output_format=fmt,
        quality=prof.quality,
        profile=profile,
        target_size=0,
        target_status=TargetStatus.NOT_APPLICABLE,
        iterations=1,
        duration=duration,
        output_bytes=output_bytes,
        metadata_preserved=meta_preserved,
    )
