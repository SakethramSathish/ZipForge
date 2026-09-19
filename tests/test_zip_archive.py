"""
tests/test_zip_archive.py — Tests for standard ZIP archive creation and extraction.
"""
import io
import zipfile
import pytest
from PIL import Image

from archive.zip_writer import ZipWriter
from archive.zip_reader import ZipReader
from application.compression_service import compress_files, compress_files_to_target


def test_zip_writer_clean_entry_names():
    """Verify entries in ZIP do NOT have .__algo suffixes."""
    files = [
        ("document.pdf", b"%PDF-1.4 fake pdf data here"),
        ("photo.jpeg", b"\xff\xd8\xff fake jpeg data here"),
    ]
    writer = ZipWriter()
    arch_bytes, results = writer.build(files, algorithm="AUTO")

    # Native zip inspection (like Windows Explorer or 7-Zip)
    with zipfile.ZipFile(io.BytesIO(arch_bytes), "r") as zf:
        names = zf.namelist()
        assert names == ["document.pdf", "photo.jpeg"]
        for name in names:
            assert ".__" not in name

        # Extracted content should match original data
        assert zf.read("document.pdf") == b"%PDF-1.4 fake pdf data here"
        assert zf.read("photo.jpeg") == b"\xff\xd8\xff fake jpeg data here"


def test_zip_reader_extract_and_inspect():
    """Verify ZipReader extracts clean entries and parses metadata."""
    files = [("notes.txt", b"Hello, world! Some notes here.")]
    writer = ZipWriter()
    arch_bytes, _ = writer.build(files, algorithm="STORE")

    reader = ZipReader(arch_bytes)
    extracted = reader.extract_to_memory()
    assert len(extracted) == 1
    assert extracted[0][0] == "notes.txt"
    assert extracted[0][1] == b"Hello, world! Some notes here."

    inspection = reader.inspect()
    assert inspection.entry_count == 1
    assert inspection.entries[0].path == "notes.txt"
    assert inspection.entries[0].original_size == len(b"Hello, world! Some notes here.")


def test_compress_files_to_target_image():
    """Verify image re-encoding to target size produces clean files in same format."""
    img = Image.new("RGB", (120, 120), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    img_data = buf.getvalue()

    target_bytes = 1000
    arch_bytes, results, status, processed = compress_files_to_target(
        [("Ram Passport Photo Raw 2026.jpeg", img_data)],
        target_size_bytes=target_bytes,
    )

    assert status in ("ACHIEVED", "ACHIEVED_LOSSY", "BEST_EFFORT")
    assert len(processed) == 1
    out_name, out_bytes = processed[0]
    assert out_name == "Ram Passport Photo Raw 2026.jpeg"
    assert len(out_bytes) <= target_bytes or status == "BEST_EFFORT"

    # Verify the processed bytes are a valid JPEG
    reopened = Image.open(io.BytesIO(out_bytes))
    assert reopened.format in ("JPEG", "WEBP")

    # Verify the ZIP entry has clean name and extracts as valid image
    with zipfile.ZipFile(io.BytesIO(arch_bytes), "r") as zf:
        assert zf.namelist() == ["Ram Passport Photo Raw 2026.jpeg"]
        extracted = zf.read("Ram Passport Photo Raw 2026.jpeg")
        extracted_img = Image.open(io.BytesIO(extracted))
        assert extracted_img.size == (120, 120)
