"""
image/optimizer.py — Target-size image optimizer using binary search.

## Objective

Maximize encoder quality subject to:
    encoded_size <= target_size_bytes

## Algorithm

Binary search over the quality parameter space [min_quality, max_quality].

    low  = min_quality
    high = max_quality
    best = None

    while low <= high and iterations < max_iterations:
        quality = (low + high) // 2
        candidate = encode(image, quality)
        if len(candidate) <= target:
            best = candidate  # save — this is valid
            low = quality + 1  # try for higher quality
        else:
            high = quality - 1  # too large — reduce quality

After the loop, *best* is the highest-quality valid candidate.
If no candidate satisfies the constraint, status = TARGET_UNACHIEVABLE.

## Progress Reporting

The optimizer accepts an optional callback:
    progress_callback(iteration, total, quality, size) → None

This allows the UI to show real-time optimization progress.

## Edge Cases

- target > original_size: return original image (no quality loss needed)
- target == 0: impossible; report UNACHIEVABLE
- No candidate satisfies constraint: report UNACHIEVABLE with best attempt
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import NamedTuple

from config import LOGGER_NAME, TARGET_SIZE_MAX_ITERATIONS
from exceptions import ImageOptimizationError
from image.formats import detect_format, encode_image, load_image, prepare_image_for_encoding
from models.image import ImageCompressionResult, ImageProfile, TargetSizeSettings, TargetStatus

logger = logging.getLogger(LOGGER_NAME)


class _Candidate(NamedTuple):
    quality: int
    size: int
    data: bytes


ProgressCallback = Callable[[int, int, int, int], None]


def optimize_to_target(
    image_bytes: bytes,
    settings: TargetSizeSettings,
    progress_callback: ProgressCallback | None = None,
) -> ImageCompressionResult:
    """
    Find the highest-quality encoding of *image* whose size <= target.

    Args:
        image_bytes:       Input image bytes.
        settings:          TargetSizeSettings (target, quality bounds, etc.).
        progress_callback: Optional callback(iteration, max_iter, quality, size).

    Returns:
        ImageCompressionResult.  target_status reflects whether the constraint
        was satisfied.

    Raises:
        ImageOptimizationError: on internal encoding failure.
    """
    start = time.perf_counter()
    original_size = len(image_bytes)
    target = settings.target_bytes

    if target <= 0:
        raise ImageOptimizationError("Target size must be a positive number of bytes")

    img, original_fmt = load_image(image_bytes)

    # Determine output format
    fmt = settings.output_format.upper()
    if fmt not in ("JPEG", "WEBP", "PNG"):
        fmt = detect_format(img, original_fmt)

    prepared = prepare_image_for_encoding(img, fmt)

    # Edge case: target >= original file size — no quality reduction needed
    if target >= original_size:
        logger.info(
            "Target %d >= original %d; returning original at max quality",
            target, original_size,
        )
        try:
            max_q_bytes = encode_image(
                prepared, fmt, settings.max_quality, optimize=True
            )
        except Exception as exc:
            raise ImageOptimizationError(f"Encoding failed at max quality: {exc}") from exc

        if len(max_q_bytes) <= target:
            return _build_result(
                original_size=original_size,
                output_bytes=max_q_bytes,
                fmt=fmt,
                quality=settings.max_quality,
                target=target,
                target_status=TargetStatus.ACHIEVED,
                iterations=1,
                start=start,
                preserve_metadata=settings.preserve_metadata,
            )

    # Binary search
    low = settings.min_quality
    high = settings.max_quality
    best: _Candidate | None = None
    iteration = 0
    max_iter = settings.max_iterations

    while low <= high and iteration < max_iter:
        iteration += 1
        quality = (low + high) // 2

        try:
            candidate_bytes = encode_image(
                prepared, fmt, quality, optimize=True
            )
        except Exception as exc:
            raise ImageOptimizationError(
                f"Encoding failed at quality={quality}: {exc}"
            ) from exc

        candidate_size = len(candidate_bytes)
        logger.debug(
            "Iter %d/%d  quality=%d  size=%d  target=%d",
            iteration, max_iter, quality, candidate_size, target,
        )

        if progress_callback is not None:
            try:
                progress_callback(iteration, max_iter, quality, candidate_size)
            except Exception:
                pass  # Never let a UI callback break the optimizer

        if candidate_size <= target:
            # Valid candidate — keep it, try higher quality
            best = _Candidate(quality=quality, size=candidate_size, data=candidate_bytes)
            low = quality + 1
        else:
            # Too large — reduce quality
            high = quality - 1

    duration = time.perf_counter() - start

    if best is not None:
        logger.info(
            "Target-size optimization: target=%d  final=%d  quality=%d  iters=%d",
            target, best.size, best.quality, iteration,
        )
        return _build_result(
            original_size=original_size,
            output_bytes=best.data,
            fmt=fmt,
            quality=best.quality,
            target=target,
            target_status=TargetStatus.ACHIEVED,
            iterations=iteration,
            start=start,
            preserve_metadata=settings.preserve_metadata,
        )
    else:
        # No candidate satisfied the target — report the smallest we achieved
        logger.warning(
            "Target %d bytes UNACHIEVABLE within quality [%d, %d] in %d iterations",
            target, settings.min_quality, settings.max_quality, iteration,
        )
        # Encode at minimum quality as the best attempt
        try:
            min_q_bytes = encode_image(
                prepared, fmt, settings.min_quality, optimize=True
            )
        except Exception as exc:
            raise ImageOptimizationError(
                f"Could not encode at minimum quality: {exc}"
            ) from exc

        return _build_result(
            original_size=original_size,
            output_bytes=min_q_bytes,
            fmt=fmt,
            quality=settings.min_quality,
            target=target,
            target_status=TargetStatus.UNACHIEVABLE,
            iterations=iteration,
            start=start,
            preserve_metadata=settings.preserve_metadata,
        )


def _build_result(
    original_size: int,
    output_bytes: bytes,
    fmt: str,
    quality: int,
    target: int,
    target_status: TargetStatus,
    iterations: int,
    start: float,
    preserve_metadata: bool,
) -> ImageCompressionResult:
    duration = time.perf_counter() - start
    final_size = len(output_bytes)

    # Double-check the target constraint (must never falsely claim ACHIEVED)
    if target_status == TargetStatus.ACHIEVED and final_size > target:
        target_status = TargetStatus.UNACHIEVABLE

    return ImageCompressionResult(
        original_size=original_size,
        final_size=final_size,
        output_format=fmt,
        quality=quality,
        profile=ImageProfile.TARGET_SIZE,
        target_size=target,
        target_status=target_status,
        iterations=iterations,
        duration=duration,
        output_bytes=output_bytes,
        metadata_preserved=preserve_metadata,
    )
