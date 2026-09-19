"""
binary/bit_reader.py — Bit-level reading utilities.

BitReader reads individual bits from a byte string in the same
big-endian bit order used by BitWriter (MSB of each byte first).

Usage:
    br = BitReader(data, padding_bits=2)
    bit = br.read_bit()
    value = br.read_bits(5)
"""

from __future__ import annotations

from exceptions import DecompressionError


class BitReader:
    """
    Reads individual bits from a byte sequence.

    Bits are extracted from the MSB of each byte downward.
    The *padding_bits* parameter tells the reader how many
    trailing zero bits in the last byte are padding (not data).
    """

    def __init__(self, data: bytes, padding_bits: int = 0) -> None:
        if not (0 <= padding_bits <= 7):
            raise ValueError(f"padding_bits must be 0-7, got {padding_bits}")
        self._data = data
        self._padding_bits = padding_bits
        # Total number of data bits available
        self._total_bits: int = len(data) * 8 - padding_bits
        self._pos: int = 0  # current bit position (0-indexed from MSB)

    # ------------------------------------------------------------------
    # Public read interface
    # ------------------------------------------------------------------

    def read_bit(self) -> int:
        """
        Read and return the next data bit (0 or 1).

        Raises:
            DecompressionError: if there are no more bits to read.
        """
        if self._pos >= self._total_bits:
            raise DecompressionError(
                f"Attempted to read past end of bit stream "
                f"(pos={self._pos}, total_bits={self._total_bits})"
            )
        byte_index = self._pos >> 3          # self._pos // 8
        bit_index = 7 - (self._pos & 0x07)  # MSB first
        bit = (self._data[byte_index] >> bit_index) & 1
        self._pos += 1
        return bit

    def read_bits(self, n_bits: int) -> int:
        """
        Read *n_bits* bits and return them as an unsigned integer (MSB first).

        Args:
            n_bits: Number of bits to read (>= 0).

        Returns:
            Integer value of the read bits.

        Raises:
            DecompressionError: if the stream is exhausted.
        """
        if n_bits < 0:
            raise ValueError(f"n_bits must be non-negative, got {n_bits}")
        result = 0
        for _ in range(n_bits):
            result = (result << 1) | self.read_bit()
        return result

    def read_byte(self) -> int:
        """Read 8 bits and return as an unsigned byte value (0-255)."""
        return self.read_bits(8)

    # ------------------------------------------------------------------
    # Status / navigation
    # ------------------------------------------------------------------

    @property
    def bits_remaining(self) -> int:
        """Number of data bits not yet read."""
        return self._total_bits - self._pos

    @property
    def is_exhausted(self) -> bool:
        """True when all data bits have been read."""
        return self._pos >= self._total_bits

    @property
    def position(self) -> int:
        """Current bit position (0-indexed from start)."""
        return self._pos

    def peek_bit(self) -> int:
        """
        Return the next bit without advancing the position.

        Raises:
            DecompressionError: if the stream is exhausted.
        """
        if self._pos >= self._total_bits:
            raise DecompressionError("Cannot peek: bit stream exhausted")
        byte_index = self._pos >> 3
        bit_index = 7 - (self._pos & 0x07)
        return (self._data[byte_index] >> bit_index) & 1
