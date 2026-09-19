"""
archive/zip_reader.py — ZIP archive reader for custom-algorithm payloads.

Reads .zip archives created by ZipWriter. Each entry's filename encodes the
algorithm used:

    original_name + ZIP_ALGO_SUFFIX_SEPARATOR + algo_lower
    e.g.  "report.pdf.__huffman"

The entry's packed content is:
    [32]  SHA-256 digest of original bytes
    [4]   metadata_length (little-endian uint32)
    [M]   algorithm metadata
    [P]   compressed payload

Usage:
    reader = ZipReader(zip_bytes)
    files = reader.extract_to_memory()      # -> list[(original_path, bytes)]
    inspection = reader.inspect()           # -> ArchiveInspection
"""

from __future__ import annotations

import hashlib
import io
import logging
import zipfile

from algorithms.registry import get_registry
from config import LOGGER_NAME, ZIP_ALGO_SUFFIX_SEPARATOR
from exceptions import ArchiveFormatError, IntegrityError
from models.archive import ArchiveEntry, ArchiveInspection, IntegrityStatus

logger = logging.getLogger(LOGGER_NAME)

_SHA256_SIZE = 32
_META_LEN_SIZE = 4


def _split_entry_name(zip_entry_name: str) -> tuple[str, str]:
    """
    Split a ZIP entry name into (original_path, algo_name).

    Returns ("STORE") if the entry has no algorithm suffix (backwards compat /
    plain ZIP entries).
    """
    sep = ZIP_ALGO_SUFFIX_SEPARATOR
    if sep in zip_entry_name:
        idx = zip_entry_name.rfind(sep)
        return zip_entry_name[:idx], zip_entry_name[idx + len(sep):]
    return zip_entry_name, "store"


def _decompress_entry(packed: bytes, algo_name: str) -> tuple[bytes, bytes, str]:
    """
    Decompress a packed ZIP entry.

    Args:
        packed:    Raw bytes stored in the ZIP entry.
        algo_name: Algorithm name string (e.g. "huffman").

    Returns:
        (original_bytes, sha256_digest_bytes, algo_upper)

    Raises:
        ArchiveFormatError: if the packed data is malformed.
        IntegrityError:     if SHA-256 verification fails.
    """
    if len(packed) < _SHA256_SIZE + _META_LEN_SIZE:
        raise ArchiveFormatError(
            f"ZIP entry too small to contain header ({len(packed)} bytes)"
        )

    sha256_stored = packed[:_SHA256_SIZE]
    meta_len = int.from_bytes(packed[_SHA256_SIZE: _SHA256_SIZE + _META_LEN_SIZE], "little")
    offset = _SHA256_SIZE + _META_LEN_SIZE

    if offset + meta_len > len(packed):
        raise ArchiveFormatError(
            f"Metadata length {meta_len} overruns entry size {len(packed)}"
        )

    metadata = packed[offset: offset + meta_len]
    payload = packed[offset + meta_len:]

    registry = get_registry()
    algo_upper = algo_name.upper()
    try:
        algo = registry.get_by_name(algo_upper)
    except Exception as exc:
        raise ArchiveFormatError(f"Unknown algorithm in ZIP entry: {algo_name!r}") from exc

    try:
        original_bytes = algo.decompress(payload, metadata)
    except Exception as exc:
        raise ArchiveFormatError(
            f"Decompression failed for algorithm {algo_upper!r}: {exc}"
        ) from exc

    # Verify integrity
    actual_sha256 = hashlib.sha256(original_bytes).digest()
    if actual_sha256 != sha256_stored:
        raise IntegrityError(
            f"SHA-256 mismatch for entry — archive may be corrupted"
        )

    return original_bytes, sha256_stored, algo_upper


def _parse_comment(comment_bytes: bytes) -> tuple[str, str | None]:
    """Parse algo and sha256 from ZipInfo comment if present."""
    if not comment_bytes:
        return "STORE", None
    try:
        text = comment_bytes.decode("utf-8", errors="ignore")
        algo = "STORE"
        sha256 = None
        for part in text.split(";"):
            if part.startswith("algo="):
                algo = part[len("algo="):].upper()
            elif part.startswith("sha256="):
                sha256 = part[len("sha256="):]
        return algo, sha256
    except Exception:
        return "STORE", None


class ZipReader:
    """Reads .zip archives produced by ZipWriter or standard ZIP tools."""

    def __init__(self, zip_bytes: bytes) -> None:
        self._zip_bytes = zip_bytes
        self._validate()

    def _validate(self) -> None:
        if not zipfile.is_zipfile(io.BytesIO(self._zip_bytes)):
            raise ArchiveFormatError(
                "Not a valid ZIP archive. Please upload a .zip file."
            )

    def extract_to_memory(self) -> list[tuple[str, bytes]]:
        """
        Decompress all entries and return (original_path, original_bytes) pairs.

        Raises:
            ArchiveFormatError: if any entry is malformed.
            IntegrityError:     if any entry fails SHA-256 verification.
        """
        results: list[tuple[str, bytes]] = []
        with zipfile.ZipFile(io.BytesIO(self._zip_bytes), "r") as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue

                data = zf.read(info.filename)
                sep = ZIP_ALGO_SUFFIX_SEPARATOR

                if sep in info.filename:
                    # Legacy format: packed entry with .__algo suffix
                    original_path, algo_name = _split_entry_name(info.filename)
                    original_bytes, _, _ = _decompress_entry(data, algo_name)
                    results.append((original_path, original_bytes))
                    logger.info(
                        "Extracted %r (%d bytes) via legacy %s",
                        original_path, len(original_bytes), algo_name.upper()
                    )
                else:
                    # Clean standard ZIP entry
                    algo_name, expected_sha = _parse_comment(info.comment)
                    if expected_sha:
                        actual_sha = hashlib.sha256(data).hexdigest()
                        if actual_sha.lower() != expected_sha.lower():
                            raise IntegrityError(
                                f"SHA-256 mismatch for entry {info.filename!r} — archive may be corrupted"
                            )
                    results.append((info.filename, data))
                    logger.info(
                        "Extracted %r (%d bytes) via %s",
                        info.filename, len(data), algo_name
                    )
        return results

    def inspect(self) -> ArchiveInspection:
        """
        Parse metadata from all ZIP entries without fully decompressing.

        Returns:
            ArchiveInspection with per-entry metadata.
        """
        entries: list[ArchiveEntry] = []
        total_original = 0
        total_compressed = 0

        with zipfile.ZipFile(io.BytesIO(self._zip_bytes), "r") as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue

                sep = ZIP_ALGO_SUFFIX_SEPARATOR
                if sep in info.filename:
                    # Legacy format
                    packed = zf.read(info.filename)
                    original_path, algo_name = _split_entry_name(info.filename)

                    if len(packed) < _SHA256_SIZE + _META_LEN_SIZE:
                        entries.append(ArchiveEntry(
                            path=original_path,
                            algorithm=algo_name.upper(),
                            original_size=0,
                            compressed_size=info.compress_size or len(packed),
                            sha256_hex="",
                            integrity_status=IntegrityStatus.UNVERIFIED,
                        ))
                        continue

                    sha256_stored = packed[:_SHA256_SIZE]
                    meta_len = int.from_bytes(
                        packed[_SHA256_SIZE: _SHA256_SIZE + _META_LEN_SIZE], "little"
                    )
                    offset = _SHA256_SIZE + _META_LEN_SIZE
                    payload_size = max(0, len(packed) - offset - meta_len)

                    try:
                        original_bytes, _, _ = _decompress_entry(packed, algo_name)
                        orig_size = len(original_bytes)
                        integrity = IntegrityStatus.VALID
                    except Exception:
                        orig_size = 0
                        integrity = IntegrityStatus.UNVERIFIED

                    total_original += orig_size
                    total_compressed += payload_size

                    entries.append(ArchiveEntry(
                        path=original_path,
                        algorithm=algo_name.upper(),
                        original_size=orig_size,
                        compressed_size=payload_size,
                        sha256_hex=sha256_stored.hex(),
                        integrity_status=integrity,
                    ))
                else:
                    # Clean standard ZIP entry
                    algo_name, sha_hex = _parse_comment(info.comment)
                    if not sha_hex:
                        data = zf.read(info.filename)
                        sha_hex = hashlib.sha256(data).hexdigest()

                    orig_size = info.file_size
                    comp_size = info.compress_size or orig_size
                    total_original += orig_size
                    total_compressed += comp_size

                    entries.append(ArchiveEntry(
                        path=info.filename,
                        algorithm=algo_name,
                        original_size=orig_size,
                        compressed_size=comp_size,
                        sha256_hex=sha_hex,
                        integrity_status=IntegrityStatus.VALID,
                    ))

        return ArchiveInspection(
            version=1,
            entry_count=len(entries),
            entries=entries,
            total_original=total_original,
            total_compressed=total_compressed,
        )
