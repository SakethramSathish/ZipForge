"""
models/metrics.py — Benchmark and performance metric models.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CompressionMetrics:
    """Single algorithm benchmark result for a file."""
    filename: str
    algorithm: str
    original_size: int
    compressed_size: int
    reduction_percent: float
    compression_ratio: float
    compression_time: float   # seconds
    decompression_time: float # seconds
    throughput_mbps: float    # MB/s during compression

    @classmethod
    def compute(
        cls,
        filename: str,
        algorithm: str,
        original_size: int,
        compressed_size: int,
        compression_time: float,
        decompression_time: float,
    ) -> "CompressionMetrics":
        bytes_saved = max(0, original_size - compressed_size)
        reduction = (bytes_saved / original_size * 100.0) if original_size else 0.0
        ratio = (original_size / compressed_size) if compressed_size else float("inf")
        throughput = (original_size / 1024 / 1024 / compression_time) if compression_time > 0 else 0.0
        return cls(
            filename=filename,
            algorithm=algorithm,
            original_size=original_size,
            compressed_size=compressed_size,
            reduction_percent=reduction,
            compression_ratio=ratio,
            compression_time=compression_time,
            decompression_time=decompression_time,
            throughput_mbps=throughput,
        )


@dataclass(frozen=True)
class ImageBenchmarkResult:
    """Benchmark result for image optimization."""
    filename: str
    input_format: str
    output_format: str
    original_size: int
    final_size: int
    target_size: int
    quality: int
    iterations: int
    optimization_time: float
    reduction_percent: float
    target_achieved: bool
