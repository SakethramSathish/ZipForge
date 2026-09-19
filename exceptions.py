"""
exceptions.py — Application-specific exception hierarchy.

All custom exceptions are defined here for consistent error handling
across the entire application.
"""


class FileCompressorError(Exception):
    """Base exception for all file compressor errors."""


# ---------------------------------------------------------------------------
# Archive errors
# ---------------------------------------------------------------------------

class ArchiveFormatError(FileCompressorError):
    """Raised when an archive has an invalid or unsupported format."""


class ArchiveVersionError(ArchiveFormatError):
    """Raised when an archive uses an unsupported version."""


class ArchiveTruncatedError(ArchiveFormatError):
    """Raised when an archive is unexpectedly truncated."""


class CorruptPayloadError(FileCompressorError):
    """Raised when a compressed payload cannot be decoded."""


# ---------------------------------------------------------------------------
# Algorithm errors
# ---------------------------------------------------------------------------

class UnsupportedAlgorithmError(FileCompressorError):
    """Raised when an algorithm ID or name is not recognised."""


class CompressionError(FileCompressorError):
    """Raised when compression fails for any reason."""


class DecompressionError(FileCompressorError):
    """Raised when decompression fails for any reason."""


# ---------------------------------------------------------------------------
# Integrity errors
# ---------------------------------------------------------------------------

class IntegrityError(FileCompressorError):
    """Raised when SHA-256 verification fails, indicating data corruption."""


# ---------------------------------------------------------------------------
# Security errors
# ---------------------------------------------------------------------------

class UnsafePathError(FileCompressorError):
    """Raised when a path would escape the target extraction directory."""


class MalformedArchiveError(FileCompressorError):
    """Raised when archive metadata contains invalid/malicious values."""


# ---------------------------------------------------------------------------
# Image errors
# ---------------------------------------------------------------------------

class ImageOptimizationError(FileCompressorError):
    """Raised when image optimization fails."""


class UnsupportedImageFormatError(FileCompressorError):
    """Raised when an image format is not supported."""


class TransparencyConversionError(FileCompressorError):
    """Raised when converting a transparent image to a non-alpha format without policy."""


# ---------------------------------------------------------------------------
# Configuration errors
# ---------------------------------------------------------------------------

class ConfigurationError(FileCompressorError):
    """Raised for invalid configuration values."""
