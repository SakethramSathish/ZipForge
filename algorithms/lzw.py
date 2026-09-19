"""
algorithms/lzw.py — Lempel-Ziv-Welch (LZW) compression.

## LZW Dictionary Structure

    0-255:   Single-byte literals (always present)
    256:     CLEAR — resets dictionary to initial state
    257:     EOI   — end of encoded data
    258+:    Phrases built during encoding

## Code Width Schedule

Code width starts at 9 bits. It grows when the next code to be emitted
or consumed CANNOT fit in the current width, i.e., when:

    code >= (1 << current_width)

For code widths:
    9 bits  handles codes 0 – 511
    10 bits handles codes 0 – 1023
    ...

Width grows BEFORE using the new code. Specifically: the encoder tracks
the *last code assigned* (nc - 1). If nc > (1 << cw), the width grows
before emitting the next code.

## Encoder/Decoder Synchronization

Both maintain 'nc' (next code to assign) starting at 258.
Both grow code_width when nc > (1 << code_width).

Critical invariant: At each emission step, encoder.nc == decoder.nc.

This is achieved because:
- Encoder adds (prev_buf + new_byte) → nc++ BEFORE emitting the next code.
- Decoder adds (prev_entry + current_entry[0]) → nc++ BEFORE reading the next code.

Wait, that's not standard LZW. The CORRECT standard approach:

Encoder step for byte B:
    1. Check if buf+B is in dict.
    2. If not: emit code(buf), add (buf+B) → nc++, possibly grow cw. Set buf=B.
    3. If yes: extend buf.

Decoder step for code C:
    1. Look up entry = dict[C] (or handle KwKwK).
    2. Output entry.
    3. Add (prev_entry + entry[0]) → nc++, possibly grow cw.
    4. Set prev_entry = entry.

After step 1 of the encoder and step 3 of the decoder, nc is the same on both sides.
This assumes the decoder had a previous entry, which it does from step 2 onwards.
The first code has no previous entry so the decoder doesn't add (nc stays at 258).
The encoder, after emitting the first code, DID add an entry (nc became 259).

FIX: Make the encoder also NOT add an entry for the FIRST emit.
This is achieved by starting with a "virtual" previous code:
    - First, consume the first byte as 'buf' (no emit, no add).
    - From the second byte onwards, do the normal encoder loop.
    - This means the first code is emitted after two bytes have been consumed.

Wait — that changes the encoding. Instead, the simplest and most proven fix is
to change the growth point. Use the condition:

    nc > (1 << code_width) [for encoder after incrementing nc]
    nc >= (1 << code_width) [for decoder after incrementing nc]

This creates a one-step offset that exactly compensates for the one-step nc lag.
"""

from __future__ import annotations

import struct
import time

from config import (
    ALGO_ID_LZW,
    LZW_CLEAR_CODE,
    LZW_EOI_CODE,
    LZW_INITIAL_DICT_SIZE,
    LZW_MAX_CODE_WIDTH,
    LZW_MAX_DICT_SIZE,
    LZW_MIN_CODE_WIDTH,
)
from algorithms.base import CompressionAlgorithm
from binary.bit_reader import BitReader
from binary.bit_writer import BitWriter
from exceptions import CompressionError, DecompressionError
from models.compression import AlgorithmName, CompressionResult


class LZWAlgorithm(CompressionAlgorithm):
    """Variable-width LZW with MSB-first bits."""

    @property
    def name(self) -> str:
        return AlgorithmName.LZW.value

    @property
    def algorithm_id(self) -> int:
        return ALGO_ID_LZW

    # ------------------------------------------------------------------
    # Compression
    # ------------------------------------------------------------------

    def compress(self, data: bytes) -> CompressionResult:
        start = time.perf_counter()
        try:
            payload, metadata = self._encode(data)
        except Exception as exc:
            raise CompressionError(f"LZW compression failed: {exc}") from exc
        duration = time.perf_counter() - start
        return CompressionResult(
            original_size=len(data),
            compressed_size=len(payload),
            algorithm=AlgorithmName.LZW,
            payload=payload,
            metadata=metadata,
            duration=duration,
        )

    def _encode(self, data: bytes) -> tuple[bytes, bytes]:
        metadata = struct.pack(">Q", len(data))

        enc: dict[bytes, int] = {bytes([i]): i for i in range(256)}
        nc = LZW_INITIAL_DICT_SIZE  # 258
        cw = LZW_MIN_CODE_WIDTH     # 9

        bw = BitWriter()
        bw.write_bits(LZW_CLEAR_CODE, cw)

        if not data:
            bw.write_bits(LZW_EOI_CODE, cw)
            payload, _ = bw.flush()
            return payload, metadata

        buf = bytes([data[0]])

        for b in data[1:]:
            ext = buf + bytes([b])
            if ext in enc:
                buf = ext
            else:
                # Emit code for buf THEN add ext
                bw.write_bits(enc[buf], cw)
                if nc < LZW_MAX_DICT_SIZE:
                    enc[ext] = nc
                    nc += 1
                    # Encoder grows when nc STRICTLY exceeds the boundary
                    if nc > (1 << cw) and cw < LZW_MAX_CODE_WIDTH:
                        cw += 1
                else:
                    bw.write_bits(LZW_CLEAR_CODE, cw)
                    enc = {bytes([i]): i for i in range(256)}
                    nc = LZW_INITIAL_DICT_SIZE
                    cw = LZW_MIN_CODE_WIDTH
                buf = bytes([b])

        bw.write_bits(enc[buf], cw)
        bw.write_bits(LZW_EOI_CODE, cw)
        payload, _ = bw.flush()
        return payload, metadata

    # ------------------------------------------------------------------
    # Decompression
    # ------------------------------------------------------------------

    def decompress(self, payload: bytes, metadata: bytes) -> bytes:
        if len(metadata) < 8:
            raise DecompressionError(
                f"LZW metadata too short: {len(metadata)} bytes"
            )
        original_size = struct.unpack(">Q", metadata[:8])[0]

        if not payload:
            if original_size != 0:
                raise DecompressionError("LZW: empty payload for non-empty input")
            return b""

        result = self._decode(payload, original_size)
        if len(result) != original_size:
            raise DecompressionError(
                f"LZW: got {len(result)} bytes, expected {original_size}"
            )
        return result

    def _decode(self, payload: bytes, original_size: int) -> bytes:
        dec: dict[int, bytes] = {i: bytes([i]) for i in range(256)}
        nc = LZW_INITIAL_DICT_SIZE  # 258
        cw = LZW_MIN_CODE_WIDTH     # 9

        br = BitReader(payload, padding_bits=0)
        out = bytearray()

        # Expect initial CLEAR
        if br.bits_remaining < cw:
            raise DecompressionError("LZW: stream too short for initial CLEAR")
        first = br.read_bits(cw)
        if first != LZW_CLEAR_CODE:
            raise DecompressionError(
                f"LZW: expected CLEAR ({LZW_CLEAR_CODE}) as first code, got {first}"
            )

        dec = {i: bytes([i]) for i in range(256)}
        nc = LZW_INITIAL_DICT_SIZE
        cw = LZW_MIN_CODE_WIDTH
        prev: bytes | None = None

        while not br.is_exhausted:
            if br.bits_remaining < cw:
                break

            code = br.read_bits(cw)

            if code == LZW_EOI_CODE:
                break
            if code == LZW_CLEAR_CODE:
                dec = {i: bytes([i]) for i in range(256)}
                nc = LZW_INITIAL_DICT_SIZE
                cw = LZW_MIN_CODE_WIDTH
                prev = None
                continue

            if code in dec:
                entry = dec[code]
            elif code == nc and prev is not None:
                entry = prev + bytes([prev[0]])
            else:
                raise DecompressionError(
                    f"LZW: received code {code} but dictionary only has "
                    f"{nc} valid entries"
                )

            out.extend(entry)

            if prev is not None and nc < LZW_MAX_DICT_SIZE:
                dec[nc] = prev + bytes([entry[0]])
                nc += 1
                # Decoder grows when nc is AT OR ABOVE the boundary
                # (one step earlier than encoder, compensating for the
                #  one-step nc lag due to first code having no prev)
                if nc >= (1 << cw) and cw < LZW_MAX_CODE_WIDTH:
                    cw += 1

            prev = entry

        return bytes(out)
