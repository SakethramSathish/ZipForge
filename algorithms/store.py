"""
algorithms/store.py — STORE (no-compression) passthrough algorithm.

Used as a fallback when compression algorithms would produce output
larger than or equal to the original data.

The payload IS the original data. Metadata is an 8-byte big-endian
uint64 storing the original size for consistency with other algorithms.
"""

from __future__ import annotations

import struct
import time

from config import ALGO_ID_STORE
from algorithms.base import CompressionAlgorithm
from exceptions import DecompressionError
from models.compression import AlgorithmName, CompressionResult


class StoreAlgorithm(CompressionAlgorithm):
    """STORE: passthrough with no compression transformation."""

    @property
    def name(self) -> str:
        return AlgorithmName.STORE.value

    @property
    def algorithm_id(self) -> int:
        return ALGO_ID_STORE

    def compress(self, data: bytes) -> CompressionResult:
        start = time.perf_counter()
        metadata = struct.pack(">Q", len(data))
        duration = time.perf_counter() - start
        return CompressionResult(
            original_size=len(data),
            compressed_size=len(data),
            algorithm=AlgorithmName.STORE,
            payload=data,
            metadata=metadata,
            duration=duration,
        )

    def decompress(self, payload: bytes, metadata: bytes) -> bytes:
        if len(metadata) < 8:
            raise DecompressionError(
                f"STORE metadata too short: expected 8 bytes, got {len(metadata)}"
            )
        original_size = struct.unpack(">Q", metadata[:8])[0]
        if len(payload) != original_size:
            raise DecompressionError(
                f"STORE: payload length {len(payload)} != expected {original_size}"
            )
        return payload
