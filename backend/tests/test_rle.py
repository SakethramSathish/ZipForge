"""
tests/test_rle.py — Unit tests for RLE compression/decompression.

All tests verify the invariant: decompress(compress(data)) == data
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from algorithms.rle import RLEAlgorithm
from exceptions import DecompressionError


@pytest.fixture
def rle() -> RLEAlgorithm:
    return RLEAlgorithm()


class TestRLECompression:
    def test_empty_input(self, rle):
        result = rle.compress(b"")
        assert result.original_size == 0
        assert result.compressed_size == 0
        assert result.payload == b""

    def test_single_byte(self, rle):
        result = rle.compress(b"\x42")
        assert result.original_size == 1
        restored = rle.decompress(result.payload, result.metadata)
        assert restored == b"\x42"

    def test_long_run(self, rle):
        data = b"\xAA" * 255
        result = rle.compress(data)
        assert result.original_size == 255
        restored = rle.decompress(result.payload, result.metadata)
        assert restored == data

    def test_very_long_run_across_tokens(self, rle):
        """A run of 512 identical bytes should be split across multiple tokens."""
        data = b"\xBB" * 512
        result = rle.compress(data)
        restored = rle.decompress(result.payload, result.metadata)
        assert restored == data

    def test_alternating_bytes(self, rle):
        """Alternating bytes should not benefit from compression."""
        data = bytes([i % 2 for i in range(100)])
        result = rle.compress(data)
        restored = rle.decompress(result.payload, result.metadata)
        assert restored == data

    def test_escape_byte_in_data(self, rle):
        """The escape byte (0xFE) itself must be handled correctly."""
        data = bytes([0xFE] * 10)
        result = rle.compress(data)
        restored = rle.decompress(result.payload, result.metadata)
        assert restored == data

    def test_escape_byte_single(self, rle):
        data = bytes([0xFE])
        result = rle.compress(data)
        restored = rle.decompress(result.payload, result.metadata)
        assert restored == data

    def test_all_256_byte_values(self, rle):
        data = bytes(range(256))
        result = rle.compress(data)
        restored = rle.decompress(result.payload, result.metadata)
        assert restored == data

    def test_mixed_data(self, rle):
        data = b"AAABBBCCCDDDEEEFFF" + b"\x00" * 50 + b"XYZ"
        result = rle.compress(data)
        restored = rle.decompress(result.payload, result.metadata)
        assert restored == data

    def test_two_byte_run_literal(self, rle):
        """Two identical bytes should remain literal (no run encoding)."""
        data = b"\x41\x41"  # 'AA'
        result = rle.compress(data)
        restored = rle.decompress(result.payload, result.metadata)
        assert restored == data

    def test_compression_ratio(self, rle):
        """Long runs should achieve significant compression."""
        data = b"\xCC" * 1000
        result = rle.compress(data)
        assert result.compressed_size < result.original_size
        assert result.reduction_percent > 50.0

    def test_name_and_id(self, rle):
        assert rle.name == "RLE"
        assert rle.algorithm_id == 1


class TestRLEDecompression:
    def test_empty_decompression(self, rle):
        result = rle.compress(b"")
        output = rle.decompress(result.payload, result.metadata)
        assert output == b""

    def test_malformed_metadata_too_short(self, rle):
        with pytest.raises(DecompressionError):
            rle.decompress(b"\xFE\x03\x41", b"\x00\x00")  # metadata too short

    def test_truncated_run_token(self, rle):
        """ESCAPE byte without count and value should raise."""
        import struct
        # Encode metadata for 3 bytes
        meta = struct.pack(">Q", 3)
        with pytest.raises(DecompressionError):
            rle.decompress(bytes([0xFE]), meta)  # escape with no count/value

    def test_roundtrip_property(self, rle):
        """decompress(compress(data)) == data for various inputs."""
        test_cases = [
            b"",
            b"\x00",
            b"\xFF" * 100,
            bytes(range(256)),
            b"Hello, World!" * 50,
            b"\xFE\xFE\xFE" * 20,
        ]
        for data in test_cases:
            result = rle.compress(data)
            restored = rle.decompress(result.payload, result.metadata)
            assert restored == data, f"Roundtrip failed for data of length {len(data)}"
