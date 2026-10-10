"""
backend/api/benchmark.py — Multi-algorithm benchmark comparison endpoint.
"""

from __future__ import annotations

import time
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile

from algorithms.registry import get_registry

router = APIRouter(prefix="/api/benchmark", tags=["benchmark"])


@router.post("")
async def run_benchmark(file: UploadFile = File(...)):
    bench_data = await file.read()
    if not bench_data:
        raise HTTPException(status_code=400, detail="Empty file provided for benchmark.")

    bench_size = len(bench_data)
    registry = get_registry()

    algorithms_to_bench = [
        ("RLE", registry.get_by_name("RLE")),
        ("HUFFMAN", registry.get_by_name("HUFFMAN")),
        ("LZW", registry.get_by_name("LZW")),
        ("STORE", registry.get_by_name("STORE")),
    ]

    results = []
    for algo_name, algo in algorithms_to_bench:
        try:
            # Measure compression
            compress_result = algo.compress(bench_data)

            # Measure decompression
            t_decomp_start = time.perf_counter()
            decompressed = algo.decompress(compress_result.payload, compress_result.metadata)
            decomp_time = time.perf_counter() - t_decomp_start
            verified = decompressed == bench_data

            speed_kbps = (
                (bench_size / 1024) / max(compress_result.duration, 0.000001)
                if compress_result.duration > 0
                else 0.0
            )

            results.append(
                {
                    "algorithm": algo_name,
                    "original_size": bench_size,
                    "compressed_size": compress_result.compressed_size,
                    "reduction_percent": round(compress_result.reduction_percent, 2),
                    "compression_ratio": round(compress_result.compression_ratio, 2)
                    if compress_result.compression_ratio != float("inf")
                    else 9999.0,
                    "compress_duration_ms": round(compress_result.duration * 1000, 2),
                    "decompress_duration_ms": round(decomp_time * 1000, 2),
                    "speed_kbps": round(speed_kbps, 1),
                    "verified": verified,
                    "error": None,
                }
            )
        except Exception as exc:
            results.append(
                {
                    "algorithm": algo_name,
                    "original_size": bench_size,
                    "compressed_size": bench_size,
                    "reduction_percent": 0.0,
                    "compression_ratio": 1.0,
                    "compress_duration_ms": 0.0,
                    "decompress_duration_ms": 0.0,
                    "speed_kbps": 0.0,
                    "verified": False,
                    "error": str(exc),
                }
            )

    # Determine best algorithm
    valid = [r for r in results if r["reduction_percent"] > 0 and r["verified"]]
    best_algo = max(valid, key=lambda r: r["reduction_percent"])["algorithm"] if valid else "STORE"

    for r in results:
        r["is_best"] = r["algorithm"] == best_algo and r["reduction_percent"] > 0

    return {
        "success": True,
        "filename": file.filename or "sample",
        "original_size": bench_size,
        "best_algorithm": best_algo,
        "results": results,
    }
