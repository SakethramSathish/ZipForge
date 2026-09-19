"""
tests/test_bit_io.py — Unit tests for BitWriter and BitReader.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from binary.bit_writer import BitWriter
from binary.bit_reader import BitReader
from exceptions import DecompressionError


class TestBitWriter:
    def test_write_zero_bits(self):
        bw = BitWriter()
        data, padding = bw.flush()
        assert data == b""
        assert padding == 0

    def test_write_single_bit_zero(self):
        bw = BitWriter()
        bw.write_bit(0)
        data, padding = bw.flush()
        assert len(data) == 1
        assert padding == 7

    def test_write_single_bit_one(self):
        bw = BitWriter()
        bw.write_bit(1)
        data, padding = bw.flush()
        assert data == bytes([0b10000000])
        assert padding == 7

    def test_write_full_byte(self):
        bw = BitWriter()
        bw.write_bits(0b10110011, 8)
        data, padding = bw.flush()
        assert data == bytes([0b10110011])
        assert padding == 0

    def test_write_two_bytes(self):
        bw = BitWriter()
        bw.write_bits(0xFF, 8)
        bw.write_bits(0x00, 8)
        data, padding = bw.flush()
        assert data == bytes([0xFF, 0x00])
        assert padding == 0

    def test_write_9_bits(self):
        bw = BitWriter()
        # Write 9 bits: 101010101 = 0xAA | 0x80 in two bytes (7 bits padding)
        bw.write_bits(0b101010101, 9)
        data, padding = bw.flush()
        assert len(data) == 2
        assert padding == 7

    def test_invalid_bit_value(self):
        bw = BitWriter()
        with pytest.raises(ValueError):
            bw.write_bit(2)

    def test_total_bits_tracking(self):
        bw = BitWriter()
        bw.write_bits(0xFF, 8)
        bw.write_bit(1)
        assert bw.total_bits == 9


class TestBitReader:
    def test_read_empty(self):
        br = BitReader(b"", padding_bits=0)
        assert br.is_exhausted
        assert br.bits_remaining == 0

    def test_read_single_bit(self):
        br = BitReader(bytes([0b10000000]), padding_bits=7)
        assert br.read_bit() == 1
        assert br.is_exhausted

    def test_read_full_byte(self):
        br = BitReader(bytes([0b10110011]), padding_bits=0)
        value = br.read_bits(8)
        assert value == 0b10110011

    def test_read_write_roundtrip(self):
        """BitWriter then BitReader should reproduce the same bits."""
        bw = BitWriter()
        bits = [1, 0, 1, 1, 0, 0, 1, 0, 1]
        for b in bits:
            bw.write_bit(b)
        data, padding = bw.flush()

        br = BitReader(data, padding_bits=padding)
        read_bits = [br.read_bit() for _ in range(len(bits))]
        assert read_bits == bits
        assert br.is_exhausted

    def test_read_past_end_raises(self):
        br = BitReader(bytes([0xFF]), padding_bits=0)
        br.read_bits(8)
        with pytest.raises(DecompressionError):
            br.read_bit()

    def test_invalid_padding_raises(self):
        with pytest.raises(ValueError):
            BitReader(b"\x00", padding_bits=8)

    def test_bits_remaining(self):
        br = BitReader(bytes([0xFF, 0x00]), padding_bits=0)
        assert br.bits_remaining == 16
        br.read_bits(4)
        assert br.bits_remaining == 12

    def test_peek_bit(self):
        br = BitReader(bytes([0b11000000]), padding_bits=6)
        assert br.peek_bit() == 1
        assert br.peek_bit() == 1  # unchanged
        br.read_bit()
        assert br.peek_bit() == 1

    def test_write_7_read_7(self):
        """Non-byte-aligned stream: write 7 bits, read them back."""
        bw = BitWriter()
        bw.write_bits(0b1010101, 7)
        data, padding = bw.flush()
        assert padding == 1

        br = BitReader(data, padding_bits=padding)
        result = br.read_bits(7)
        assert result == 0b1010101
        assert br.is_exhausted
