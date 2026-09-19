"""
tests/conftest.py — Shared fixtures for the test suite.
"""

import sys
import os
from pathlib import Path

# Ensure project root is on sys.path so tests can import modules directly
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest


@pytest.fixture
def text_data() -> bytes:
    """Typical text — good for Huffman."""
    return b"Hello, World! This is a test of the file compressor. " * 100


@pytest.fixture
def repetitive_data() -> bytes:
    """Highly repetitive — ideal for RLE."""
    return b"AAAAAAAAAA" * 1000 + b"BBBBBBBB" * 500


@pytest.fixture
def random_data() -> bytes:
    """Pseudo-random — worst case for all compressors (STORE expected)."""
    import random
    rng = random.Random(42)
    return bytes(rng.randint(0, 255) for _ in range(4096))


@pytest.fixture
def empty_data() -> bytes:
    return b""


@pytest.fixture
def single_byte_data() -> bytes:
    return b"\xAB"


@pytest.fixture
def all_zeros_data() -> bytes:
    return b"\x00" * 256


@pytest.fixture
def all_bytes_data() -> bytes:
    """All 256 byte values once each."""
    return bytes(range(256))


@pytest.fixture
def json_data() -> bytes:
    """JSON-like text data."""
    import json
    obj = {
        "name": "test",
        "values": list(range(100)),
        "nested": {"a": 1, "b": 2, "c": "hello world"},
    }
    return json.dumps(obj, indent=2).encode() * 20


@pytest.fixture
def small_jpeg_image() -> bytes:
    """A minimal synthetic JPEG image (8x8 pixels)."""
    from PIL import Image
    import io
    img = Image.new("RGB", (64, 64), color=(128, 64, 192))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


@pytest.fixture
def small_png_image() -> bytes:
    """A minimal synthetic PNG image with transparency."""
    from PIL import Image
    import io
    img = Image.new("RGBA", (64, 64), color=(100, 150, 200, 180))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def small_webp_image() -> bytes:
    """A minimal synthetic WebP image."""
    from PIL import Image
    import io
    img = Image.new("RGB", (64, 64), color=(200, 100, 50))
    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=80)
    return buf.getvalue()
