"""
models/compression.py — Core lossless compression result models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AlgorithmName(str, Enum):
    STORE = "STORE"
    RLE = "RLE"
    HUFFMAN = "HUFFMAN"
    LZW = "LZW"
    AUTO = "AUTO"


@dataclass(frozen=True)
class CompressionResult:
    """
    Returned by a compression algorithm's compress() method.

    Attributes:
        original_size:    Byte count of the input data.
        compressed_size:  Byte count of the compressed payload.
        algorithm:        Name of the algorithm that produced this result.
        payload:          The compressed bytes.
        metadata:         Algorithm-specific metadata needed for decompression.
        duration:         Wall-clock time in seconds for this compression.
    """
    original_size: int
    compressed_size: int
    algorithm: AlgorithmName
    payload: bytes
    metadata: bytes
    duration: float = 0.0

    @property
    def bytes_saved(self) -> int:
        return max(0, self.original_size - self.compressed_size)

    @property
    def reduction_percent(self) -> float:
        if self.original_size == 0:
            return 0.0
        return (self.bytes_saved / self.original_size) * 100.0

    @property
    def compression_ratio(self) -> float:
        if self.compressed_size == 0:
            return float("inf")
        return self.original_size / self.compressed_size


@dataclass(frozen=True)
class ExtractionResult:
    """
    Result of decompressing a .fcmp archive.

    Attributes:
        extracted_paths: Paths of successfully extracted files.
        failed_entries:  Mapping of entry path → error message for failures.
        total_entries:   Total number of entries in the archive.
        duration:        Total extraction wall-clock time in seconds.
    """
    extracted_paths: list[str]
    failed_entries: dict[str, str]
    total_entries: int
    duration: float = 0.0

    @property
    def success_count(self) -> int:
        return len(self.extracted_paths)

    @property
    def failure_count(self) -> int:
        return len(self.failed_entries)

    @property
    def all_succeeded(self) -> bool:
        return self.failure_count == 0
