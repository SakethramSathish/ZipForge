"""
image/profiles.py — Image compression quality profiles.

Three predefined profiles control encoder quality parameters.
Values are configured centrally (not scattered as magic numbers).

Profile    Quality    Description
---------  -------   -----------
EXTREME    30         Lower quality, maximum compression
RECOMMENDED 75        Good quality, good compression (default)
LESS       90         Higher quality, lower compression

Output format strategy:
- JPEG input:  output JPEG (or WEBP if beneficial, but JPEG by default)
- PNG + transparency: output PNG (preserve alpha channel)
- PNG + no transparency: output JPEG or WEBP
- WEBP input:  output WEBP

Metadata policy per profile:
- EXTREME:      strip metadata (size savings)
- RECOMMENDED:  strip metadata (default for size)
- LESS:         preserve metadata if possible
"""

from __future__ import annotations

from dataclasses import dataclass

from config import (
    IMAGE_EXTREME_QUALITY,
    IMAGE_LESS_QUALITY,
    IMAGE_RECOMMENDED_QUALITY,
)
from models.image import ImageProfile


@dataclass(frozen=True)
class ImageCompressionProfile:
    """
    Configuration for a single image compression preset.

    Attributes:
        name:               Profile enum value.
        quality:            Default JPEG/WebP encoder quality (1-100).
        min_quality:        Lowest quality for this profile.
        max_quality:        Highest quality for this profile.
        optimize:           Enable PIL optimize flag.
        progressive:        Enable progressive encoding (JPEG).
        preserve_metadata:  Whether to preserve EXIF by default.
        preferred_jpeg_format: Output format for JPEG-compatible images.
        description:        Human-readable description.
    """
    name: ImageProfile
    quality: int
    min_quality: int
    max_quality: int
    optimize: bool
    progressive: bool
    preserve_metadata: bool
    preferred_jpeg_format: str
    description: str


# ---------------------------------------------------------------------------
# Built-in profiles
# ---------------------------------------------------------------------------

PROFILE_EXTREME = ImageCompressionProfile(
    name=ImageProfile.EXTREME,
    quality=IMAGE_EXTREME_QUALITY,    # 30
    min_quality=15,
    max_quality=40,
    optimize=True,
    progressive=True,
    preserve_metadata=False,
    preferred_jpeg_format="JPEG",
    description="Lower quality, maximum compression",
)

PROFILE_RECOMMENDED = ImageCompressionProfile(
    name=ImageProfile.RECOMMENDED,
    quality=IMAGE_RECOMMENDED_QUALITY,  # 75
    min_quality=60,
    max_quality=85,
    optimize=True,
    progressive=True,
    preserve_metadata=False,
    preferred_jpeg_format="JPEG",
    description="Good quality, good compression",
)

PROFILE_LESS_COMPRESSION = ImageCompressionProfile(
    name=ImageProfile.LESS_COMPRESSION,
    quality=IMAGE_LESS_QUALITY,       # 90
    min_quality=82,
    max_quality=95,
    optimize=True,
    progressive=False,
    preserve_metadata=True,
    preferred_jpeg_format="JPEG",
    description="Higher quality, lower compression",
)

# Registry
_PROFILES: dict[ImageProfile, ImageCompressionProfile] = {
    ImageProfile.EXTREME: PROFILE_EXTREME,
    ImageProfile.RECOMMENDED: PROFILE_RECOMMENDED,
    ImageProfile.LESS_COMPRESSION: PROFILE_LESS_COMPRESSION,
}


def get_profile(profile: ImageProfile) -> ImageCompressionProfile:
    """Return the ImageCompressionProfile for the given enum value."""
    p = _PROFILES.get(profile)
    if p is None:
        raise ValueError(f"Unknown image profile: {profile!r}")
    return p


def get_default_profile() -> ImageCompressionProfile:
    """Return the RECOMMENDED profile (the default)."""
    return PROFILE_RECOMMENDED
