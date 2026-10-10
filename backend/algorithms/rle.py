"""
algorithms/rle.py — Run-Length Encoding (RLE) compression.

## Encoding Format

RLE encodes data as a sequence of tokens. Each token is either:

    RUN token:     [ESCAPE_BYTE] [count] [byte]
        - ESCAPE_BYTE = 0xFE (marks a run)
        - count = 2..255 (run of 2 or more identical bytes)
        - byte = the repeated byte value

    LITERAL token: [byte]
        - Any byte whose value is NOT ESCAPE_BYTE passes through unchanged.
        - The byte 0xFE itself is encoded as [ESCAPE_BYTE] [1] [0xFE].

## Metadata

The metadata block is a single big-endian uint64 storing the original data length.
This allows the decompressor to preallocate and detect truncated streams.

## Why this design?

Using an escape byte avoids the need for a separate control bit per byte,
which would expand non-compressible data significantly. The escape byte
(0xFE) is chosen as a value that is relatively rare in typical data.
Long runs (3+ identical bytes) are always encoded efficiently.

Worst case expansion: data containing many 0xFE bytes expands by 3x
(each 0xFE → 3 bytes). For typical mixed binary data this is acceptable.
"""

from __future__ import annotations

import struct
import time

from config import (
    ALGO_ID_RLE,
    RLE_ESCAPE_BYTE,
    RLE_MAX_RUN,
)
from algorithms.base import CompressionAlgorithm
from exceptions import CompressionError, DecompressionError
from models.compression import AlgorithmName, CompressionResult


class RLEAlgorithm(CompressionAlgorithm):
    """
    Byte-oriented Run-Length Encoding.

    Handles:
    - Empty input
    - Single-byte files
    - Long runs (length up to 255 per token)
    - Alternating bytes (no compression; escape-escaped if needed)
    - All 256 byte values including the escape byte itself
    - Malformed streams (raises DecompressionError)
    """

    ESCAPE = RLE_ESCAPE_BYTE  # 0xFE

    @property
    def name(self) -> str:
        return AlgorithmName.RLE.value

    @property
    def algorithm_id(self) -> int:
        return ALGO_ID_RLE

    # ------------------------------------------------------------------
    # Compression
    # ------------------------------------------------------------------

    def compress(self, data: bytes) -> CompressionResult:
        """Compress *data* using RLE. Always succeeds (STORE is handled upstream)."""
        start = time.perf_counter()

        try:
            payload = self._encode(data)
        except Exception as exc:
            raise CompressionError(f"RLE compression failed: {exc}") from exc

        # Metadata: original size as big-endian uint64
        metadata = struct.pack(">Q", len(data))
        duration = time.perf_counter() - start

        return CompressionResult(
            original_size=len(data),
            compressed_size=len(payload),
            algorithm=AlgorithmName.RLE,
            payload=payload,
            metadata=metadata,
            duration=duration,
        )

    def _encode(self, data: bytes) -> bytes:
        if not data:
            return b""

        out = bytearray()
        i = 0
        n = len(data)

        while i < n:
            current = data[i]
            # Count run length (max RLE_MAX_RUN = 255 per token)
            j = i + 1
            while j < n and data[j] == current and (j - i) < RLE_MAX_RUN:
                j += 1
            run_length = j - i  # guaranteed >= 1

            if run_length >= 3 or current == self.ESCAPE:
                # Encode as a run token even if length == 1 (for escape byte)
                out.append(self.ESCAPE)
                out.append(run_length)
                out.append(current)
            else:
                # 1 or 2 identical non-escape bytes: emit literally
                for _ in range(run_length):
                    out.append(current)
            i = j

        return bytes(out)

    # ------------------------------------------------------------------
    # Decompression
    # ------------------------------------------------------------------

    def decompress(self, payload: bytes, metadata: bytes) -> bytes:
        """
        Decompress RLE-encoded *payload*.

        Args:
            payload:  RLE-encoded bytes.
            metadata: 8-byte big-endian uint64 = original data length.

        Returns:
            The original bytes.

        Raises:
            DecompressionError: on malformed input or truncated stream.
        """
        if len(metadata) < 8:
            raise DecompressionError(
                f"RLE metadata too short: expected 8 bytes, got {len(metadata)}"
            )
        original_size = struct.unpack(">Q", metadata[:8])[0]

        # Handle empty-data edge case
        if original_size == 0:
            if payload:
                raise DecompressionError("RLE: metadata claims empty data but payload is non-empty")
            return b""

        out = bytearray()
        i = 0
        n = len(payload)

        while i < n:
            byte = payload[i]
            i += 1

            if byte == self.ESCAPE:
                # Expect count and value next
                if i + 1 >= n + 1:  # need 2 more bytes
                    if i >= n:
                        raise DecompressionError(
                            f"RLE: escape byte at position {i-1} not followed by count and value"
                        )
                if i >= n:
                    raise DecompressionError(
                        "RLE: truncated run token (missing count byte)"
                    )
                count = payload[i]
                i += 1
                if i >= n:
                    raise DecompressionError(
                        "RLE: truncated run token (missing value byte)"
                    )
                value = payload[i]
                i += 1
                if count == 0:
                    raise DecompressionError("RLE: run count of 0 is invalid")
                out.extend(bytes([value]) * count)
            else:
                out.append(byte)

        result = bytes(out)
        if len(result) != original_size:
            raise DecompressionError(
                f"RLE: decompressed size {len(result)} does not match "
                f"expected {original_size}"
            )
        return result
