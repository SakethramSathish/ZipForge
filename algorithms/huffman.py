"""
algorithms/huffman.py — Canonical Huffman Coding compression.

## Algorithm Overview

Huffman coding assigns shorter bit codes to more-frequent bytes and longer
codes to rarer bytes. This implementation uses **canonical Huffman coding**
for a deterministic, compact metadata representation.

## Compression Pipeline

    1. Build a frequency table (256-entry histogram)
    2. Build the Huffman tree using a min-heap (heapq)
    3. Assign code lengths via depth-first traversal of the tree
    4. Derive canonical codes from the sorted code lengths
    5. Encode the input as a bitstream using the canonical codes
    6. Flush the bitstream (with zero-padding) and record padding count

## Metadata Format (serialized into archive)

    [2 bytes] Number of unique symbols (uint16 LE)
    Per symbol (repeated for each unique symbol):
        [1 byte]  Symbol (byte value 0-255)
        [1 byte]  Code length (bits, 1-32)
    [1 byte]  Padding bits in the last byte of the payload (0-7)

From this metadata the decompressor reconstructs the canonical Huffman
table and decodes the bitstream.

## Special Cases

- **Empty input**: payload = b"", metadata encodes 0 symbols.
- **Single unique byte**: assigned code "0" (1 bit). All input bytes
  encode to one bit each.
- **Two unique bytes**: one gets "0", the other "1".
- **Equal frequencies**: ties broken by (length, symbol_value) for
  determinism.

## Canonical Huffman Code Generation

Given code lengths for each symbol:
1. Sort symbols first by code length, then by symbol value.
2. Assign the smallest code of the required length to the first symbol.
3. Increment the code; shift left when moving to a longer length.
"""

from __future__ import annotations

import heapq
import struct
import time
from collections import Counter
from typing import NamedTuple

from config import ALGO_ID_HUFFMAN, HUFFMAN_MAX_CODE_LENGTH
from algorithms.base import CompressionAlgorithm
from binary.bit_reader import BitReader
from binary.bit_writer import BitWriter
from exceptions import CompressionError, DecompressionError
from models.compression import AlgorithmName, CompressionResult


# ---------------------------------------------------------------------------
# Internal tree node
# ---------------------------------------------------------------------------

class _HuffNode(NamedTuple):
    """Min-heap node: (frequency, counter, symbol_or_None, left, right)."""
    freq: int
    counter: int        # tie-break to avoid comparing children
    symbol: int | None  # None for internal nodes
    left: "_HuffNode | None" = None
    right: "_HuffNode | None" = None

    def __lt__(self, other: "_HuffNode") -> bool:  # type: ignore[override]
        if self.freq != other.freq:
            return self.freq < other.freq
        return self.counter < other.counter


# ---------------------------------------------------------------------------
# Main algorithm class
# ---------------------------------------------------------------------------

class HuffmanAlgorithm(CompressionAlgorithm):
    """
    Canonical Huffman coding implementation.

    Compress:  build canonical table → encode bitstream
    Decompress: rebuild canonical table from metadata → decode bitstream
    """

    @property
    def name(self) -> str:
        return AlgorithmName.HUFFMAN.value

    @property
    def algorithm_id(self) -> int:
        return ALGO_ID_HUFFMAN

    # ------------------------------------------------------------------
    # Compression
    # ------------------------------------------------------------------

    def compress(self, data: bytes) -> CompressionResult:
        start = time.perf_counter()

        try:
            payload, metadata = self._encode(data)
        except Exception as exc:
            raise CompressionError(f"Huffman compression failed: {exc}") from exc

        duration = time.perf_counter() - start
        return CompressionResult(
            original_size=len(data),
            compressed_size=len(payload),
            algorithm=AlgorithmName.HUFFMAN,
            payload=payload,
            metadata=metadata,
            duration=duration,
        )

    def _encode(self, data: bytes) -> tuple[bytes, bytes]:
        if not data:
            metadata = self._pack_metadata({}, 0)
            return b"", metadata

        # Step 1: Frequency table
        freq: dict[int, int] = dict(Counter(data))

        # Step 2 & 3: Build tree and get code lengths
        code_lengths = self._build_code_lengths(freq)

        # Step 4: Canonical codes from lengths
        codes = self._canonical_codes(code_lengths)

        # Step 5: Encode bitstream
        bw = BitWriter()
        for byte_val in data:
            code, length = codes[byte_val]
            bw.write_bits(code, length)
        payload_bytes, padding = bw.flush()

        # Pack metadata
        metadata = self._pack_metadata(code_lengths, padding)
        return payload_bytes, metadata

    def _build_code_lengths(self, freq: dict[int, int]) -> dict[int, int]:
        """Return {symbol: code_length} using a Huffman tree."""
        if len(freq) == 1:
            # Single unique symbol — assign length 1
            sym = next(iter(freq))
            return {sym: 1}

        # Build min-heap
        counter = 0
        heap: list[_HuffNode] = []
        for sym, f in freq.items():
            heapq.heappush(heap, _HuffNode(f, counter, sym))
            counter += 1

        # Merge until one root remains
        while len(heap) > 1:
            left = heapq.heappop(heap)
            right = heapq.heappop(heap)
            merged = _HuffNode(
                freq=left.freq + right.freq,
                counter=counter,
                symbol=None,
                left=left,
                right=right,
            )
            counter += 1
            heapq.heappush(heap, merged)

        root = heap[0]
        code_lengths: dict[int, int] = {}
        self._traverse(root, 0, code_lengths)

        # Clamp to max code length (extremely rare for 256-symbol alphabet)
        for sym in code_lengths:
            if code_lengths[sym] > HUFFMAN_MAX_CODE_LENGTH:
                raise CompressionError(
                    f"Huffman code length {code_lengths[sym]} exceeds maximum "
                    f"{HUFFMAN_MAX_CODE_LENGTH}"
                )
        return code_lengths

    def _traverse(
        self,
        node: _HuffNode,
        depth: int,
        result: dict[int, int],
    ) -> None:
        if node.symbol is not None:
            # Leaf node
            result[node.symbol] = max(depth, 1)  # min 1 bit for single-symbol case
        else:
            if node.left is not None:
                self._traverse(node.left, depth + 1, result)
            if node.right is not None:
                self._traverse(node.right, depth + 1, result)

    @staticmethod
    def _canonical_codes(code_lengths: dict[int, int]) -> dict[int, tuple[int, int]]:
        """
        Derive canonical Huffman codes from code lengths.

        Returns {symbol: (code_int, code_length)}.
        """
        # Sort by (length, symbol)
        sorted_syms = sorted(code_lengths.items(), key=lambda x: (x[1], x[0]))

        codes: dict[int, tuple[int, int]] = {}
        current_code = 0
        previous_length = 0

        for sym, length in sorted_syms:
            if previous_length > 0:
                current_code += 1
                shift = length - previous_length
                current_code <<= shift
            # else: first symbol gets code 0 (no shift needed)
            codes[sym] = (current_code, length)
            previous_length = length

        return codes

    # ------------------------------------------------------------------
    # Metadata serialization
    # ------------------------------------------------------------------

    @staticmethod
    def _pack_metadata(code_lengths: dict[int, int], padding: int) -> bytes:
        """
        Serialize the canonical Huffman table and padding count.

        Format:
            [2 bytes] symbol_count (uint16 LE)
            Per symbol:
                [1 byte] symbol
                [1 byte] code_length
            [1 byte] padding_bits
        """
        buf = bytearray()
        sorted_syms = sorted(code_lengths.items(), key=lambda x: (x[1], x[0]))
        buf += struct.pack("<H", len(sorted_syms))
        for sym, length in sorted_syms:
            buf.append(sym)
            buf.append(length)
        buf.append(padding)
        return bytes(buf)

    @staticmethod
    def _unpack_metadata(metadata: bytes) -> tuple[dict[int, tuple[int, int]], int]:
        """
        Parse metadata back into (canonical_codes dict, padding_bits).
        """
        if len(metadata) < 3:
            raise DecompressionError(
                f"Huffman metadata too short: {len(metadata)} bytes"
            )
        symbol_count = struct.unpack("<H", metadata[:2])[0]
        pos = 2
        needed = symbol_count * 2 + 1  # sym + len per entry, plus padding byte
        if len(metadata) < 2 + needed:
            raise DecompressionError(
                f"Huffman metadata truncated: expected {2 + needed} bytes, got {len(metadata)}"
            )

        code_lengths: dict[int, int] = {}
        for _ in range(symbol_count):
            sym = metadata[pos]
            length = metadata[pos + 1]
            pos += 2
            if length == 0 or length > HUFFMAN_MAX_CODE_LENGTH:
                raise DecompressionError(
                    f"Huffman metadata: invalid code length {length} for symbol {sym}"
                )
            code_lengths[sym] = length

        padding = metadata[pos]
        if padding > 7:
            raise DecompressionError(
                f"Huffman metadata: invalid padding value {padding}"
            )

        codes = HuffmanAlgorithm._canonical_codes(code_lengths)
        return codes, padding

    # ------------------------------------------------------------------
    # Decompression
    # ------------------------------------------------------------------

    def decompress(self, payload: bytes, metadata: bytes) -> bytes:
        """
        Decode a Huffman bitstream using the canonical table in *metadata*.

        Raises:
            DecompressionError: on malformed payload or metadata.
        """
        try:
            codes, padding = self._unpack_metadata(metadata)
        except DecompressionError:
            raise
        except Exception as exc:
            raise DecompressionError(f"Huffman metadata parse error: {exc}") from exc

        # Empty-data case
        if not payload and not codes:
            return b""

        if not payload:
            # Metadata says there are symbols but payload is empty — invalid
            raise DecompressionError("Huffman: non-empty code table but empty payload")

        # Build reverse lookup: (code_int, length) → symbol
        reverse: dict[tuple[int, int], int] = {
            (code, length): sym for sym, (code, length) in codes.items()
        }

        # If only one unique symbol, all bits decode to that symbol
        if len(codes) == 1:
            sym = next(iter(codes))
            total_bits = len(payload) * 8 - padding
            return bytes([sym] * total_bits)

        # General case: walk the bit stream
        br = BitReader(payload, padding_bits=padding)
        out = bytearray()
        current_code = 0
        current_length = 0
        max_length = max(length for _, length in codes.values())

        while not br.is_exhausted:
            bit = br.read_bit()
            current_code = (current_code << 1) | bit
            current_length += 1

            sym_candidate = reverse.get((current_code, current_length))
            if sym_candidate is not None:
                out.append(sym_candidate)
                current_code = 0
                current_length = 0
            elif current_length > max_length:
                raise DecompressionError(
                    f"Huffman: invalid code at bit position {br.position}, "
                    f"length {current_length} exceeds max {max_length}"
                )

        if current_length > 0:
            # Trailing bits after last symbol — could be the padding itself
            # This is expected when padding > 0 and happens to align
            # Check if remaining bits are just padding zeros
            # We already passed padding_bits to BitReader so this shouldn't happen
            raise DecompressionError(
                f"Huffman: {current_length} bits remain after decoding all symbols"
            )

        return bytes(out)
