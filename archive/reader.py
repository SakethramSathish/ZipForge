"""
archive/reader.py — Safe FCMP archive parser and extractor.

This module treats every archive as untrusted input.

Security checks performed:
- Magic validation
- Version check
- Entry count bounds
- Path length bounds
- Metadata length bounds
- Payload length bounds (verified against available bytes)
- Path traversal prevention
- SHA-256 integrity verification after decompression
- Malformed code rejection (delegated to algorithm decompressors)
"""

from __future__ import annotations

import io
import logging
from pathlib import Path

from archive.format import (
    FCMP_MAGIC,
    FCMP_VERSION,
    MAX_SAFE_ENTRY_COUNT,
    MAX_SAFE_METADATA_LENGTH,
    MAX_SAFE_PATH_LENGTH,
    MAX_SAFE_PAYLOAD_LENGTH,
    SHA256_SIZE,
)
from algorithms.registry import get_registry
from binary.serialization import (
    read_exact,
    read_u8,
    read_u16,
    read_u32,
    read_u64,
)
from config import LOGGER_NAME
from exceptions import (
    ArchiveFormatError,
    ArchiveTruncatedError,
    ArchiveVersionError,
    CorruptPayloadError,
    IntegrityError,
    MalformedArchiveError,
    UnsafePathError,
    UnsupportedAlgorithmError,
)
from filesystem.manager import ensure_directory, safe_write_file
from filesystem.security import safe_extraction_path
from integrity.hashing import IntegrityStatus, verify_hash
from models.archive import ArchiveEntry, ArchiveInspection, IntegrityStatus as ModelIntegrityStatus
from models.compression import ExtractionResult

logger = logging.getLogger(LOGGER_NAME)


class FCMPReader:
    """
    Parses and extracts FCMP archives safely.

    Usage:
        reader = FCMPReader(archive_bytes)
        inspection = reader.inspect()            # metadata only
        result = reader.extract(dest_path)       # full extraction
    """

    def __init__(self, data: bytes) -> None:
        self._data = data
        self._stream = io.BytesIO(data)
        self._version: int | None = None
        self._entry_count: int | None = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def inspect(self) -> ArchiveInspection:
        """
        Parse archive metadata WITHOUT decompressing payloads.

        Returns:
            ArchiveInspection with entry metadata and integrity status UNVERIFIED.

        Raises:
            ArchiveFormatError, ArchiveVersionError, MalformedArchiveError.
        """
        self._stream.seek(0)
        self._read_header()
        entries = []
        total_original = 0
        total_compressed = 0

        for _ in range(self._entry_count):  # type: ignore[arg-type]
            entry = self._read_entry(decompress=False)
            entries.append(entry)
            total_original += entry.original_size
            total_compressed += entry.compressed_size

        return ArchiveInspection(
            version=self._version,  # type: ignore[arg-type]
            entry_count=self._entry_count,  # type: ignore[arg-type]
            entries=entries,
            total_original=total_original,
            total_compressed=total_compressed,
        )

    def extract(
        self,
        destination: Path,
        conflict: str = "rename",
    ) -> ExtractionResult:
        """
        Decompress and extract all entries to *destination*.

        Args:
            destination: Target directory for extracted files.
            conflict:    Conflict policy ("rename" | "overwrite" | "skip").

        Returns:
            ExtractionResult with extracted paths and any failures.
        """
        import time
        start = time.perf_counter()

        self._stream.seek(0)
        self._read_header()
        ensure_directory(destination)

        extracted: list[str] = []
        failed: dict[str, str] = {}

        for i in range(self._entry_count):  # type: ignore[arg-type]
            try:
                entry = self._read_entry(decompress=True)
            except (ArchiveFormatError, MalformedArchiveError, ArchiveTruncatedError) as exc:
                logger.error("Failed to parse entry %d: %s", i, exc)
                failed[f"<entry {i}>"] = str(exc)
                break  # Cannot continue — stream position is unknown

            try:
                # Validate path and resolve safe extraction target
                output_path = safe_extraction_path(entry.path, destination)
                # Write file
                actual_path = safe_write_file(output_path, entry.payload, conflict=conflict)
                extracted.append(str(actual_path))
                logger.info(
                    "Extracted %r → %s  integrity=%s",
                    entry.path, actual_path, entry.integrity_status,
                )

                if entry.integrity_status == ModelIntegrityStatus.CORRUPTED:
                    failed[entry.path] = "Integrity check failed (SHA-256 mismatch)"

            except UnsafePathError as exc:
                logger.warning("Unsafe path rejected: %s", exc)
                failed[entry.path] = f"Unsafe path: {exc}"
            except IntegrityError as exc:
                logger.error("Integrity failure for %r: %s", entry.path, exc)
                failed[entry.path] = str(exc)
            except Exception as exc:
                logger.error("Failed to extract %r: %s", entry.path, exc)
                failed[entry.path] = str(exc)

        duration = time.perf_counter() - start
        return ExtractionResult(
            extracted_paths=extracted,
            failed_entries=failed,
            total_entries=self._entry_count or 0,  # type: ignore[arg-type]
            duration=duration,
        )

    def extract_to_memory(self) -> list[tuple[str, bytes]]:
        """
        Decompress all entries and return (path, data) pairs in memory.

        Returns:
            List of (stored_path, decompressed_bytes) for each entry.

        Raises:
            ArchiveFormatError, IntegrityError, MalformedArchiveError, etc.
        """
        self._stream.seek(0)
        self._read_header()
        results: list[tuple[str, bytes]] = []

        for _ in range(self._entry_count):  # type: ignore[arg-type]
            entry = self._read_entry(decompress=True)
            results.append((entry.path, entry.payload))

        return results

    # ------------------------------------------------------------------
    # Header parsing
    # ------------------------------------------------------------------

    def _read_header(self) -> None:
        """Parse and validate the archive header."""
        try:
            magic = read_exact(self._stream, 4)
        except EOFError:
            raise ArchiveTruncatedError("Archive too short to contain a header")

        if magic != FCMP_MAGIC:
            raise ArchiveFormatError(
                f"Invalid archive magic: expected {FCMP_MAGIC!r}, got {magic!r}. "
                "This is not a valid .fcmp archive."
            )

        try:
            version = read_u8(self._stream)
        except EOFError:
            raise ArchiveTruncatedError("Archive truncated at version field")

        if version != FCMP_VERSION:
            raise ArchiveVersionError(
                f"Unsupported archive version {version}. "
                f"Only version {FCMP_VERSION} is supported."
            )
        self._version = version

        try:
            _flags = read_u16(self._stream)   # global flags (reserved)
            entry_count = read_u32(self._stream)
        except EOFError:
            raise ArchiveTruncatedError("Archive truncated in header")

        if entry_count > MAX_SAFE_ENTRY_COUNT:
            raise MalformedArchiveError(
                f"Entry count {entry_count} exceeds safety limit {MAX_SAFE_ENTRY_COUNT}"
            )
        self._entry_count = entry_count
        logger.debug("Archive header: version=%d, entry_count=%d", version, entry_count)

    # ------------------------------------------------------------------
    # Entry parsing
    # ------------------------------------------------------------------

    def _read_entry(self, decompress: bool) -> ArchiveEntry:
        """Parse a single archive entry."""
        stream = self._stream
        remaining = len(self._data) - stream.tell()

        # --- Path ---
        try:
            path_length = read_u16(stream)
        except EOFError:
            raise ArchiveTruncatedError("Archive truncated reading path length")

        if path_length == 0 or path_length > MAX_SAFE_PATH_LENGTH:
            raise MalformedArchiveError(
                f"Invalid path length: {path_length}. "
                f"Must be 1-{MAX_SAFE_PATH_LENGTH}."
            )

        try:
            path_bytes = read_exact(stream, path_length)
        except EOFError:
            raise ArchiveTruncatedError(f"Archive truncated reading path ({path_length} bytes)")

        try:
            stored_path = path_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise MalformedArchiveError(f"Path is not valid UTF-8: {exc}") from exc

        # --- Fixed metadata fields ---
        try:
            algo_id = read_u8(stream)
            _entry_flags = read_u8(stream)
            original_size = read_u64(stream)
            compressed_size = read_u64(stream)
            metadata_length = read_u32(stream)
            payload_length = read_u64(stream)
        except EOFError:
            raise ArchiveTruncatedError(
                f"Archive truncated reading fixed fields for entry {stored_path!r}"
            )

        # --- Sanity checks ---
        self._validate_entry_fields(
            stored_path=stored_path,
            algo_id=algo_id,
            original_size=original_size,
            compressed_size=compressed_size,
            metadata_length=metadata_length,
            payload_length=payload_length,
        )

        # --- SHA-256 ---
        try:
            sha256_digest = read_exact(stream, SHA256_SIZE)
        except EOFError:
            raise ArchiveTruncatedError(
                f"Archive truncated reading SHA-256 for {stored_path!r}"
            )

        if len(sha256_digest) != SHA256_SIZE:
            raise MalformedArchiveError(
                f"SHA-256 digest too short for {stored_path!r}: "
                f"expected {SHA256_SIZE} bytes"
            )

        # --- Algorithm metadata ---
        try:
            algo_metadata = read_exact(stream, metadata_length)
        except EOFError:
            raise ArchiveTruncatedError(
                f"Archive truncated reading algorithm metadata for {stored_path!r}"
            )

        # --- Payload ---
        try:
            payload_bytes = read_exact(stream, payload_length)
        except EOFError:
            raise ArchiveTruncatedError(
                f"Archive truncated reading payload for {stored_path!r}"
            )

        # --- Decompress if requested ---
        if decompress:
            decompressed = self._decompress_entry(
                stored_path=stored_path,
                algo_id=algo_id,
                payload=payload_bytes,
                metadata=algo_metadata,
                expected_size=original_size,
            )
            integrity = self._check_integrity(decompressed, sha256_digest, stored_path)
            # payload field in ArchiveEntry holds decompressed data for extraction
            return ArchiveEntry(
                path=stored_path,
                algorithm=self._algo_id_to_name(algo_id),
                original_size=original_size,
                compressed_size=compressed_size,
                sha256_hex=sha256_digest.hex(),
                integrity_status=ModelIntegrityStatus(integrity.value),
                metadata=algo_metadata,
                payload=decompressed,
            )
        else:
            # Inspection mode: don't decompress, payload field is empty
            return ArchiveEntry(
                path=stored_path,
                algorithm=self._algo_id_to_name(algo_id),
                original_size=original_size,
                compressed_size=compressed_size,
                sha256_hex=sha256_digest.hex(),
                integrity_status=ModelIntegrityStatus.UNVERIFIED,
                metadata=algo_metadata,
                payload=b"",
            )

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    def _validate_entry_fields(
        self,
        stored_path: str,
        algo_id: int,
        original_size: int,
        compressed_size: int,
        metadata_length: int,
        payload_length: int,
    ) -> None:
        from config import ALGO_ID_TO_NAME
        if algo_id not in ALGO_ID_TO_NAME:
            raise UnsupportedAlgorithmError(
                f"Unknown algorithm ID {algo_id} in entry {stored_path!r}"
            )
        if original_size > MAX_SAFE_PAYLOAD_LENGTH:
            raise MalformedArchiveError(
                f"Original size {original_size} is unreasonably large for {stored_path!r}"
            )
        if compressed_size > MAX_SAFE_PAYLOAD_LENGTH:
            raise MalformedArchiveError(
                f"Compressed size {compressed_size} is unreasonably large for {stored_path!r}"
            )
        if metadata_length > MAX_SAFE_METADATA_LENGTH:
            raise MalformedArchiveError(
                f"Metadata length {metadata_length} exceeds limit for {stored_path!r}"
            )
        if payload_length > MAX_SAFE_PAYLOAD_LENGTH:
            raise MalformedArchiveError(
                f"Payload length {payload_length} is unreasonably large for {stored_path!r}"
            )
        # Verify we actually have enough bytes left
        available = len(self._data) - self._stream.tell()
        needed = 32 + metadata_length + payload_length  # SHA256 + meta + payload
        if available < needed:
            raise ArchiveTruncatedError(
                f"Archive truncated for entry {stored_path!r}: "
                f"need {needed} bytes, have {available}"
            )

    def _decompress_entry(
        self,
        stored_path: str,
        algo_id: int,
        payload: bytes,
        metadata: bytes,
        expected_size: int,
    ) -> bytes:
        """Decompress a payload using the specified algorithm."""
        registry = get_registry()
        try:
            algo = registry.get_by_id(algo_id)
        except UnsupportedAlgorithmError:
            raise UnsupportedAlgorithmError(
                f"Algorithm ID {algo_id} is not supported for {stored_path!r}"
            )

        try:
            decompressed = algo.decompress(payload, metadata)
        except Exception as exc:
            raise CorruptPayloadError(
                f"Decompression failed for {stored_path!r} "
                f"using {algo.name}: {exc}"
            ) from exc

        if len(decompressed) != expected_size:
            raise CorruptPayloadError(
                f"Decompressed size mismatch for {stored_path!r}: "
                f"got {len(decompressed)}, expected {expected_size}"
            )

        return decompressed

    @staticmethod
    def _check_integrity(
        data: bytes,
        stored_digest: bytes,
        path: str,
    ) -> IntegrityStatus:
        status = verify_hash(data, stored_digest)
        if status == IntegrityStatus.CORRUPTED:
            logger.error("Integrity check FAILED for %r", path)
        return status

    @staticmethod
    def _algo_id_to_name(algo_id: int) -> str:
        from config import ALGO_ID_TO_NAME
        return ALGO_ID_TO_NAME.get(algo_id, f"UNKNOWN({algo_id})")
