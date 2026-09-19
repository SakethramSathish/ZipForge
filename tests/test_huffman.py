"""
tests/test_huffman.py — Unit tests for Huffman coding.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from algorithms.huffman import HuffmanAlgorithm
from exceptions import DecompressionError


@pytest.fixture
def huffman() -> HuffmanAlgorithm:
    return HuffmanAlgorithm()


class TestHuffmanCompression:
    def test_empty_input(self, huffman):
        result = huffman.compress(b"")
        assert result.original_size == 0
        assert result.payload == b""
        restored = huffman.decompress(result.payload, result.metadata)
        assert restored == b""

    def test_single_unique_byte(self, huffman):
        data = b"\x42" * 100
        result = huffman.compress(data)
        assert result.original_size == 100
        restored = huffman.decompress(result.payload, result.metadata)
        assert restored == data

    def test_two_unique_bytes(self, huffman):
        data = b"\x00\xFF" * 50
        result = huffman.compress(data)
        restored = huffman.decompress(result.payload, result.metadata)
        assert restored == data

    def test_all_256_bytes(self, huffman):
        data = bytes(range(256)) * 10
        result = huffman.compress(data)
        restored = huffman.decompress(result.payload, result.metadata)
        assert restored == data

    def test_text_compression(self, huffman):
        data = b"the quick brown fox jumps over the lazy dog" * 100
        result = huffman.compress(data)
        assert result.compressed_size < result.original_size
        restored = huffman.decompress(result.payload, result.metadata)
        assert restored == data

    def test_equal_frequencies(self, huffman):
        """All bytes with equal frequency should still roundtrip correctly."""
        data = bytes(list(range(16)) * 16)  # Each byte appears 16 times
        result = huffman.compress(data)
        restored = huffman.decompress(result.payload, result.metadata)
        assert restored == data

    def test_binary_data(self, huffman):
        import os
        data = bytes(range(256)) + b"\x00\xFF" * 128
        result = huffman.compress(data)
        restored = huffman.decompress(result.payload, result.metadata)
        assert restored == data

    def test_repetitive_achieves_compression(self, huffman):
        data = b"AAABBBCCC" * 200
        result = huffman.compress(data)
        assert result.reduction_percent > 20.0

    def test_metadata_format(self, huffman):
        """Metadata should be parseable."""
        result = huffman.compress(b"hello world")
        assert len(result.metadata) >= 3  # at minimum: 2 byte count + 1 padding

    def test_single_byte_input(self, huffman):
        data = b"\xAB"
        result = huffman.compress(data)
        restored = huffman.decompress(result.payload, result.metadata)
        assert restored == data

    def test_name_and_id(self, huffman):
        assert huffman.name == "HUFFMAN"
        assert huffman.algorithm_id == 2


class TestHuffmanDecompression:
    def test_malformed_metadata_too_short(self, huffman):
        with pytest.raises(DecompressionError):
            huffman.decompress(b"\x00", b"\x01")  # too short

    def test_roundtrip_property(self, huffman):
        """decompress(compress(data)) == data for various inputs."""
        test_cases = [
            b"",
            b"A",
            b"\xFF" * 500,
            b"Hello, World! 123" * 30,
            bytes(range(256)),
            bytes([0, 1] * 200),
        ]
        for data in test_cases:
            result = huffman.compress(data)
            restored = huffman.decompress(result.payload, result.metadata)
            assert restored == data, f"Roundtrip failed for input of length {len(data)}"
