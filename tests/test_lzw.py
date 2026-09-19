"""
tests/test_lzw.py — Unit tests for LZW compression/decompression.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from algorithms.lzw import LZWAlgorithm
from exceptions import DecompressionError


@pytest.fixture
def lzw() -> LZWAlgorithm:
    return LZWAlgorithm()


class TestLZWCompression:
    def test_empty_input(self, lzw):
        result = lzw.compress(b"")
        assert result.original_size == 0
        restored = lzw.decompress(result.payload, result.metadata)
        assert restored == b""

    def test_single_byte(self, lzw):
        data = b"\x42"
        result = lzw.compress(data)
        restored = lzw.decompress(result.payload, result.metadata)
        assert restored == data

    def test_simple_text(self, lzw):
        data = b"TOBEORNOTTOBEORTOBEORNOT"
        result = lzw.compress(data)
        restored = lzw.decompress(result.payload, result.metadata)
        assert restored == data

    def test_repetitive_data_compresses(self, lzw):
        data = b"ABABABABABABABABAB" * 100
        result = lzw.compress(data)
        assert result.compressed_size < result.original_size
        restored = lzw.decompress(result.payload, result.metadata)
        assert restored == data

    def test_all_256_bytes(self, lzw):
        data = bytes(range(256))
        result = lzw.compress(data)
        restored = lzw.decompress(result.payload, result.metadata)
        assert restored == data

    def test_kwkwk_pattern(self, lzw):
        """
        The KwKwK edge case: decoder receives a code it hasn't added yet.
        Input: ababab... where each new pair creates a dictionary entry
        that the encoder uses before the decoder has added it.
        """
        # A pattern guaranteed to trigger KwKwK: repeated character
        data = b"\xAA" * 300
        result = lzw.compress(data)
        restored = lzw.decompress(result.payload, result.metadata)
        assert restored == data

    def test_long_text_data(self, lzw):
        data = b"the quick brown fox jumps over the lazy dog " * 50
        result = lzw.compress(data)
        restored = lzw.decompress(result.payload, result.metadata)
        assert restored == data

    def test_binary_data(self, lzw):
        data = bytes(range(256)) * 4
        result = lzw.compress(data)
        restored = lzw.decompress(result.payload, result.metadata)
        assert restored == data

    def test_name_and_id(self, lzw):
        assert lzw.name == "LZW"
        assert lzw.algorithm_id == 3

    def test_metadata_format(self, lzw):
        """Metadata must be exactly 8 bytes (original size)."""
        result = lzw.compress(b"test data")
        assert len(result.metadata) == 8


class TestLZWDecompression:
    def test_malformed_metadata_short(self, lzw):
        with pytest.raises(DecompressionError):
            lzw.decompress(b"\x00\x00", b"\x00\x00")  # metadata too short

    def test_roundtrip_property(self, lzw):
        """decompress(compress(data)) == data for various inputs."""
        test_cases = [
            b"",
            b"A",
            b"\xFF" * 1000,
            b"ABCABCABC" * 100,
            bytes(range(256)),
            b"Hello! This is LZW test data. " * 40,
        ]
        for data in test_cases:
            result = lzw.compress(data)
            restored = lzw.decompress(result.payload, result.metadata)
            assert restored == data, f"Roundtrip failed for data length {len(data)}"
