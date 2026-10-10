"""
algorithms/registry.py — Algorithm registry and automatic selection.

## Algorithm Registry

Algorithms are registered by name and ID. The registry is the single
source of truth for resolving algorithm names ↔ IDs ↔ instances.

## Automatic Selection

The AUTO mode:
1. Tries all candidate algorithms (RLE, Huffman, LZW).
2. Measures the actual compressed payload size for each.
3. Selects the one with the smallest payload.
4. Falls back to STORE if no algorithm beats the original size.

This is the only honest approach — we measure rather than assume.

For small inputs (<= 64 bytes) only STORE is tried (overhead dominates).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from config import (
    ALGO_ID_HUFFMAN,
    ALGO_ID_LZW,
    ALGO_ID_RLE,
    ALGO_ID_STORE,
    LOGGER_NAME,
)
from algorithms.base import CompressionAlgorithm
from algorithms.huffman import HuffmanAlgorithm
from algorithms.lzw import LZWAlgorithm
from algorithms.rle import RLEAlgorithm
from algorithms.store import StoreAlgorithm
from exceptions import UnsupportedAlgorithmError
from models.compression import AlgorithmName, CompressionResult

logger = logging.getLogger(LOGGER_NAME)

# Minimum input size to bother attempting compression
_MIN_COMPRESS_SIZE = 64


class AlgorithmRegistry:
    """
    Registry mapping algorithm names and IDs to algorithm instances.

    Usage:
        registry = AlgorithmRegistry.default()
        algo = registry.get_by_name("HUFFMAN")
        result = algo.compress(data)
    """

    def __init__(self) -> None:
        self._by_name: dict[str, CompressionAlgorithm] = {}
        self._by_id: dict[int, CompressionAlgorithm] = {}

    def register(self, algo: CompressionAlgorithm) -> None:
        self._by_name[algo.name] = algo
        self._by_id[algo.algorithm_id] = algo

    def get_by_name(self, name: str) -> CompressionAlgorithm:
        name_upper = name.strip().upper()
        algo = self._by_name.get(name_upper)
        if algo is None:
            raise UnsupportedAlgorithmError(
                f"Unknown algorithm name: {name!r}. "
                f"Available: {sorted(self._by_name.keys())}"
            )
        return algo

    def get_by_id(self, algo_id: int) -> CompressionAlgorithm:
        algo = self._by_id.get(algo_id)
        if algo is None:
            raise UnsupportedAlgorithmError(
                f"Unknown algorithm ID: {algo_id}. "
                f"Available IDs: {sorted(self._by_id.keys())}"
            )
        return algo

    def all_names(self) -> list[str]:
        return sorted(self._by_name.keys())

    def all_ids(self) -> list[int]:
        return sorted(self._by_id.keys())

    @classmethod
    def default(cls) -> "AlgorithmRegistry":
        """Return a registry populated with all built-in algorithms."""
        registry = cls()
        registry.register(StoreAlgorithm())
        registry.register(RLEAlgorithm())
        registry.register(HuffmanAlgorithm())
        registry.register(LZWAlgorithm())
        return registry


# Module-level default registry (singleton-like, but not enforced)
_DEFAULT_REGISTRY: AlgorithmRegistry | None = None


def get_registry() -> AlgorithmRegistry:
    """Return the default algorithm registry (created once)."""
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None:
        _DEFAULT_REGISTRY = AlgorithmRegistry.default()
    return _DEFAULT_REGISTRY


# ---------------------------------------------------------------------------
# Automatic selection
# ---------------------------------------------------------------------------

def select_best_compression(data: bytes) -> CompressionResult:
    """
    Try RLE, Huffman, and LZW; return the smallest valid result.

    Falls back to STORE if no algorithm reduces the size.

    Args:
        data: The raw bytes to compress.

    Returns:
        The best CompressionResult (lowest compressed_size <= original_size).
    """
    registry = get_registry()
    store = registry.get_by_name(AlgorithmName.STORE.value)

    if len(data) <= _MIN_COMPRESS_SIZE:
        logger.debug(
            "Input size %d bytes <= threshold %d; using STORE directly",
            len(data), _MIN_COMPRESS_SIZE,
        )
        return store.compress(data)

    candidates: list[CompressionResult] = []
    candidate_names = [AlgorithmName.RLE.value, AlgorithmName.HUFFMAN.value, AlgorithmName.LZW.value]

    for name in candidate_names:
        try:
            algo = registry.get_by_name(name)
            result = algo.compress(data)
            if result.compressed_size < result.original_size:
                candidates.append(result)
                logger.debug(
                    "Candidate %s: %d → %d bytes (%.1f%% reduction)",
                    name, result.original_size, result.compressed_size,
                    result.reduction_percent,
                )
        except Exception as exc:
            logger.warning("Algorithm %s failed during auto-selection: %s", name, exc)

    if not candidates:
        logger.info("No algorithm beat STORE; using STORE")
        return store.compress(data)

    best = min(candidates, key=lambda r: r.compressed_size)
    logger.info(
        "Auto-selected %s: %d → %d bytes (%.1f%% reduction)",
        best.algorithm, best.original_size, best.compressed_size,
        best.reduction_percent,
    )
    return best


def compress_with(data: bytes, algorithm: str) -> CompressionResult:
    """
    Compress *data* with the named algorithm, applying STORE fallback
    if the result is not smaller than the original.

    Args:
        data:      Input bytes.
        algorithm: Algorithm name or "AUTO".

    Returns:
        CompressionResult (may use STORE if compression not beneficial).
    """
    if algorithm.upper() == AlgorithmName.AUTO.value:
        return select_best_compression(data)

    registry = get_registry()
    algo = registry.get_by_name(algorithm)
    result = algo.compress(data)

    if result.compressed_size >= result.original_size:
        logger.info(
            "%s produced no benefit (%d >= %d); falling back to STORE",
            algorithm, result.compressed_size, result.original_size,
        )
        store = registry.get_by_name(AlgorithmName.STORE.value)
        return store.compress(data)

    return result
