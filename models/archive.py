"""
models/archive.py — Archive entry and inspection models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class IntegrityStatus(str, Enum):
    VALID = "VALID"
    CORRUPTED = "CORRUPTED"
    UNVERIFIED = "UNVERIFIED"


@dataclass(frozen=True)
class ArchiveEntry:
    """
    Metadata for a single entry within an FCMP archive.

    Attributes:
        path:             The stored relative file path (forward-slash separated).
        algorithm:        Algorithm name string ("STORE", "RLE", "HUFFMAN", "LZW").
        original_size:    Size of the original file data in bytes.
        compressed_size:  Size of the compressed payload in bytes.
        sha256_hex:       Hex-encoded SHA-256 of the original bytes.
        integrity_status: Verification status (set after extraction/check).
        metadata:         Algorithm-specific metadata bytes (opaque).
        payload:          The compressed payload bytes (may be empty in listings).
    """
    path: str
    algorithm: str
    original_size: int
    compressed_size: int
    sha256_hex: str
    integrity_status: IntegrityStatus = IntegrityStatus.UNVERIFIED
    metadata: bytes = field(default=b"", compare=False, hash=False)
    payload: bytes = field(default=b"", compare=False, hash=False)

    @property
    def reduction_percent(self) -> float:
        if self.original_size == 0:
            return 0.0
        saved = self.original_size - self.compressed_size
        return (saved / self.original_size) * 100.0

    @property
    def compression_ratio(self) -> float:
        if self.compressed_size == 0:
            return float("inf")
        return self.original_size / self.compressed_size


@dataclass(frozen=True)
class ArchiveInspection:
    """
    Result of inspecting a .fcmp archive (without full extraction).

    Attributes:
        version:        Archive format version.
        entry_count:    Number of entries in the archive.
        entries:        Metadata for each entry.
        total_original: Sum of original sizes across all entries.
        total_compressed: Sum of compressed sizes across all entries.
    """
    version: int
    entry_count: int
    entries: list[ArchiveEntry]
    total_original: int
    total_compressed: int

    @property
    def overall_reduction_percent(self) -> float:
        if self.total_original == 0:
            return 0.0
        return ((self.total_original - self.total_compressed) / self.total_original) * 100.0
