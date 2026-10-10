"""
binary/bit_writer.py — Bit-level writing utilities.

BitWriter accumulates individual bits and flushes them to bytes.
The high bit of each byte is written first (big-endian bit order).

Usage:
    bw = BitWriter()
    bw.write_bit(1)
    bw.write_bits(0b101, 3)
    data, padding = bw.flush()
"""

from __future__ import annotations

import io


class BitWriter:
    """
    Writes individual bits to an internal byte buffer.

    Bits are packed from the MSB of each byte downward (big-endian bit order).
    Call flush() to get the final bytes along with the number of padding bits
    appended to complete the last byte.
    """

    def __init__(self) -> None:
        self._buffer = io.BytesIO()
        self._current_byte: int = 0
        self._bits_in_current: int = 0   # how many bits are filled in _current_byte
        self._total_bits: int = 0

    # ------------------------------------------------------------------
    # Public write interface
    # ------------------------------------------------------------------

    def write_bit(self, bit: int) -> None:
        """Write a single bit (0 or 1)."""
        if bit not in (0, 1):
            raise ValueError(f"Bit must be 0 or 1, got {bit!r}")
        self._current_byte = (self._current_byte << 1) | bit
        self._bits_in_current += 1
        self._total_bits += 1
        if self._bits_in_current == 8:
            self._flush_byte()

    def write_bits(self, value: int, n_bits: int) -> None:
        """
        Write the lowest *n_bits* bits of *value*, MSB first.

        Args:
            value:  The integer whose bits are written.
            n_bits: Number of bits to write (must be >= 0).
        """
        if n_bits < 0:
            raise ValueError(f"n_bits must be non-negative, got {n_bits}")
        for shift in range(n_bits - 1, -1, -1):
            self.write_bit((value >> shift) & 1)

    def write_byte(self, byte: int) -> None:
        """Write all 8 bits of a byte, MSB first."""
        if not (0 <= byte <= 255):
            raise ValueError(f"Byte value out of range: {byte}")
        self.write_bits(byte, 8)

    # ------------------------------------------------------------------
    # Finalisation
    # ------------------------------------------------------------------

    def flush(self) -> tuple[bytes, int]:
        """
        Finalise the bit stream.

        Pads the last partial byte with zero bits on the right so that
        the total length is a whole number of bytes.

        Returns:
            (data_bytes, padding_bits)
            padding_bits: number of zero bits appended (0-7).
        """
        padding_bits = 0
        if self._bits_in_current > 0:
            padding_bits = 8 - self._bits_in_current
            # Shift left to fill the byte; zero bits are appended implicitly
            self._current_byte <<= padding_bits
            self._flush_byte()
        return self._buffer.getvalue(), padding_bits

    def get_bytes(self) -> bytes:
        """Return the complete byte string (does NOT flush a partial last byte)."""
        return self._buffer.getvalue()

    @property
    def total_bits(self) -> int:
        """Total number of data bits written so far (excluding padding)."""
        return self._total_bits

    @property
    def total_bytes_written(self) -> int:
        """Number of complete bytes written to the internal buffer."""
        return len(self._buffer.getvalue())

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _flush_byte(self) -> None:
        self._buffer.write(bytes([self._current_byte]))
        self._current_byte = 0
        self._bits_in_current = 0
