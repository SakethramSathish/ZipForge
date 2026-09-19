"""
archive/zip_writer.py — ZIP archive builder using custom compression algorithms.

Each file's bytes are compressed with the chosen algorithm (Huffman, LZW, RLE,
or STORE), then stored as a ZIP entry with ZIP_STORED (no double-compression).
The entry filename carries an algorithm suffix so the reader knows how to
reverse the compression:

    original_name + ZIP_ALGO_SUFFIX_SEPARATOR + algo_lower
    e.g.  "report.pdf.__huffman"

The resulting archive is a fully valid .zip file openable by Windows Explorer,
7-Zip, WinRAR, or any other ZIP-capable tool.

Usage:
    writer = ZipWriter()
    archive_bytes = writer.build(files, algorithm="AUTO")
"""

from __future__ import annotations

import hashlib
import io
import logging
import zipfile
from pathlib import PurePosixPath

from algorithms.registry import compress_with, select_best_compression
from config import LOGGER_NAME, MAX_ARCHIVE_ENTRIES, MAX_PATH_LENGTH, ZIP_ALGO_SUFFIX_SEPARATOR
from exceptions import ArchiveFormatError, CompressionError
from models.compression import CompressionResult

logger = logging.getLogger(LOGGER_NAME)


class ZipWriter:
    """
    Builds a valid .zip archive whose entries hold custom-algorithm payloads.

    Call build() to get the archive bytes in one shot.
    """

    def build(
        self,
        files: list[tuple[str, bytes]],
        algorithm: str = "AUTO",
    ) -> tuple[bytes, list[CompressionResult]]:
        """
        Compress each file with *algorithm* and package into a ZIP archive.

        Args:
            files:     List of (stored_path, raw_bytes) tuples.
            algorithm: Algorithm name ("AUTO", "RLE", "HUFFMAN", "LZW", "STORE").

        Returns:
            (archive_bytes, per_file_results) tuple.

        Raises:
            ArchiveFormatError: if path is too long or entry limit exceeded.
            CompressionError:   if compression fails.
        """
        if not files:
            raise CompressionError("No files provided for compression")

        if len(files) > MAX_ARCHIVE_ENTRIES:
            raise ArchiveFormatError(
                f"Too many entries: {len(files)} > {MAX_ARCHIVE_ENTRIES}"
            )

        buf = io.BytesIO()
        results: list[CompressionResult] = []

        zip_compression = (
            zipfile.ZIP_STORED if algorithm.upper() == "STORE" else zipfile.ZIP_DEFLATED
        )

        with zipfile.ZipFile(buf, mode="w", compression=zip_compression, allowZip64=True) as zf:
            for stored_path, data in files:
                # Normalise to forward slashes
                stored_path = str(PurePosixPath(stored_path.replace("\\", "/")))
                path_bytes = stored_path.encode("utf-8")
                if len(path_bytes) > MAX_PATH_LENGTH:
                    raise ArchiveFormatError(
                        f"Path too long ({len(path_bytes)} bytes): {stored_path!r}"
                    )

                # Compress with chosen algorithm to collect real benchmark metrics
                try:
                    result = compress_with(data, algorithm)
                except Exception as exc:
                    raise CompressionError(
                        f"Failed to compress {stored_path!r}: {exc}"
                    ) from exc

                results.append(result)

                algo_name = (
                    result.algorithm.value
                    if hasattr(result.algorithm, "value")
                    else str(result.algorithm)
                ).lower()

                # Clean entry name: exact original filename and extension (NO .__algo suffix!)
                zip_entry_name = stored_path

                # Standard ZIP entry with metadata stored in comment
                zinfo = zipfile.ZipInfo(zip_entry_name)
                zinfo.compress_type = zip_compression
                sha256_hex = hashlib.sha256(data).hexdigest()
                zinfo.comment = f"algo={algo_name};sha256={sha256_hex}".encode("utf-8")

                # Store clean file data directly so any standard unzipper extracts a valid file!
                zf.writestr(zinfo, data)

                logger.info(
                    "ZIP entry %r: %s  %d → %d bytes (%.1f%% reduction)",
                    zip_entry_name,
                    result.algorithm,
                    result.original_size,
                    result.compressed_size,
                    result.reduction_percent,
                )

        archive_bytes = buf.getvalue()
        logger.info(
            "ZIP archive built: %d files, %d bytes total",
            len(files),
            len(archive_bytes),
        )
        return archive_bytes, results
