"""
models/image.py — Image compression result models and settings.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ImageProfile(str, Enum):
    EXTREME = "EXTREME"
    RECOMMENDED = "RECOMMENDED"
    LESS_COMPRESSION = "LESS_COMPRESSION"
    TARGET_SIZE = "TARGET_SIZE"


class TargetStatus(str, Enum):
    ACHIEVED = "ACHIEVED"
    UNACHIEVABLE = "UNACHIEVABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class ImageCompressionResult:
    """
    Result of an image compression or target-size optimization.

    Attributes:
        original_size:    Original image file size in bytes.
        final_size:       Output image file size in bytes.
        output_format:    Output format string (e.g. "JPEG", "PNG", "WEBP").
        quality:          Encoder quality parameter used (1-100 scale, or -1 for lossless).
        profile:          The compression profile applied.
        target_size:      Requested target in bytes (0 if not a target-size operation).
        target_status:    Whether the target was achieved.
        iterations:       Number of optimizer iterations used.
        duration:         Wall-clock seconds for the operation.
        output_bytes:     The compressed image bytes.
        metadata_preserved: Whether image metadata was preserved.
    """
    original_size: int
    final_size: int
    output_format: str
    quality: int
    profile: ImageProfile
    target_size: int = 0
    target_status: TargetStatus = TargetStatus.NOT_APPLICABLE
    iterations: int = 1
    duration: float = 0.0
    output_bytes: bytes = b""
    metadata_preserved: bool = False

    @property
    def bytes_saved(self) -> int:
        return max(0, self.original_size - self.final_size)

    @property
    def reduction_percent(self) -> float:
        if self.original_size == 0:
            return 0.0
        return (self.bytes_saved / self.original_size) * 100.0

    @property
    def target_achieved(self) -> bool:
        return self.target_status == TargetStatus.ACHIEVED


@dataclass(frozen=True)
class TargetSizeSettings:
    """
    Configuration for the target-size binary search optimizer.

    Attributes:
        target_bytes:        Maximum allowed output size in bytes.
        min_quality:         Lowest acceptable encoder quality.
        max_quality:         Highest encoder quality to try.
        max_iterations:      Maximum binary-search iterations.
        output_format:       Preferred output format ('JPEG', 'WEBP', etc.).
        preserve_metadata:   Whether to preserve EXIF/ICC metadata.
    """
    target_bytes: int
    min_quality: int = 5
    max_quality: int = 95
    max_iterations: int = 12
    output_format: str = "JPEG"
    preserve_metadata: bool = False
