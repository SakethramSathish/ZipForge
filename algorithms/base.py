"""
algorithms/base.py — Abstract base class for all compression algorithms.

Defines the interface that RLE, Huffman, LZW, and STORE must implement.
All algorithms are independently usable without Streamlit.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from models.compression import CompressionResult


class CompressionAlgorithm(ABC):
    """
    Abstract base class for lossless compression algorithms.

    Each algorithm must implement:
        compress(data)     → CompressionResult
        decompress(...)    → bytes

    The *metadata* field in CompressionResult carries any information
    needed by the decompressor (e.g. Huffman code lengths, original
    data length). The exact serialization format is algorithm-specific
    and must be documented in each implementation.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the canonical name string (e.g. 'RLE', 'HUFFMAN')."""
        ...

    @property
    @abstractmethod
    def algorithm_id(self) -> int:
        """Return the integer ID used in the FCMP archive format."""
        ...

    @abstractmethod
    def compress(self, data: bytes) -> CompressionResult:
        """
        Compress *data* and return a CompressionResult.

        The result's *payload* combined with *metadata* must be sufficient
        for decompress() to exactly reconstruct *data*.

        Args:
            data: Raw bytes to compress.

        Returns:
            CompressionResult with populated payload, metadata, and metrics.

        Raises:
            CompressionError: if compression fails.
        """
        ...

    @abstractmethod
    def decompress(self, payload: bytes, metadata: bytes) -> bytes:
        """
        Decompress *payload* using *metadata* and return original bytes.

        Args:
            payload:  The compressed bytes from CompressionResult.payload.
            metadata: The algorithm metadata from CompressionResult.metadata.

        Returns:
            The reconstructed original bytes.

        Raises:
            DecompressionError: if the payload or metadata is invalid.
        """
        ...
