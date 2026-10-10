"""
archive/writer.py — FCMP archive serializer.

Writes one or more compressed entries into the binary FCMP format.

Usage:
    writer = FCMPWriter()
    writer.add_entry(path, original_data, algorithm="AUTO")
    archive_bytes = writer.build()
"""

from __future__ import annotations

import logging
from pathlib import PurePosixPath

from archive.format import (
    FCMP_MAGIC,
    FCMP_VERSION,
    SHA256_SIZE,
)
from algorithms.registry import compress_with
from binary.serialization import (
    pack_u8,
    pack_u16,
    pack_u32,
    pack_u64,
)
from config import LOGGER_NAME, MAX_ARCHIVE_ENTRIES, MAX_PATH_LENGTH
from exceptions import ArchiveFormatError, CompressionError
from integrity.hashing import compute_hash

logger = logging.getLogger(LOGGER_NAME)


class FCMPWriter:
    """
    Builds a FCMP v1 archive from individual file entries.

    Call add_entry() for each file, then build() to get the bytes.
    """

    def __init__(self) -> None:
        self._entries: list[bytes] = []

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def add_entry(
        self,
        stored_path: str,
        data: bytes,
        algorithm: str = "AUTO",
    ) -> None:
        """
        Add a file to the archive.

        Args:
            stored_path: Relative path to store in the archive
                         (forward-slash separated).
            data:        Raw file bytes.
            algorithm:   Compression algorithm name or "AUTO".

        Raises:
            ArchiveFormatError: if the path is too long or entry limit reached.
            CompressionError:   if compression fails.
        """
        if len(self._entries) >= MAX_ARCHIVE_ENTRIES:
            raise ArchiveFormatError(
                f"Archive entry limit reached ({MAX_ARCHIVE_ENTRIES})"
            )

        # Normalise path separators to forward slash
        stored_path = str(PurePosixPath(stored_path.replace("\\", "/")))

        path_bytes = stored_path.encode("utf-8")
        if len(path_bytes) > MAX_PATH_LENGTH:
            raise ArchiveFormatError(
                f"Path too long ({len(path_bytes)} bytes): {stored_path!r}"
            )

        # Compute integrity hash BEFORE compression
        sha256_digest = compute_hash(data)
        assert len(sha256_digest) == SHA256_SIZE

        # Compress
        try:
            result = compress_with(data, algorithm)
        except Exception as exc:
            raise CompressionError(
                f"Failed to compress {stored_path!r} with {algorithm}: {exc}"
            ) from exc

        logger.info(
            "Compressed %r: %s  %d → %d bytes  (%.1f%% reduction)",
            stored_path,
            result.algorithm,
            result.original_size,
            result.compressed_size,
            result.reduction_percent,
        )

        # Serialize the entry
        entry = self._serialize_entry(
            path_bytes=path_bytes,
            algo_id=result.algorithm_id if hasattr(result, 'algorithm_id') else self._resolve_algo_id(result.algorithm.value),
            original_size=result.original_size,
            compressed_size=result.compressed_size,
            sha256_digest=sha256_digest,
            metadata=result.metadata,
            payload=result.payload,
        )
        self._entries.append(entry)

    def build(self) -> bytes:
        """
        Serialize all entries into a complete FCMP archive.

        Returns:
            Complete archive as bytes.
        """
        entry_count = len(self._entries)
        header = (
            FCMP_MAGIC
            + pack_u8(FCMP_VERSION)
            + pack_u16(0)               # global flags (reserved)
            + pack_u32(entry_count)
        )
        return header + b"".join(self._entries)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_algo_id(algo_name: str) -> int:
        from config import ALGO_NAME_TO_ID
        algo_id = ALGO_NAME_TO_ID.get(algo_name.upper())
        if algo_id is None:
            raise ArchiveFormatError(f"Unknown algorithm name: {algo_name!r}")
        return algo_id

    @staticmethod
    def _serialize_entry(
        path_bytes: bytes,
        algo_id: int,
        original_size: int,
        compressed_size: int,
        sha256_digest: bytes,
        metadata: bytes,
        payload: bytes,
    ) -> bytes:
        """
        Serialize a single archive entry to bytes.

        Layout:
            [2]  path_length
            [N]  path
            [1]  algorithm_id
            [1]  entry_flags  (0x00)
            [8]  original_size
            [8]  compressed_size
            [4]  metadata_length
            [8]  payload_length
            [32] sha256
            [M]  metadata
            [P]  payload
        """
        return (
            pack_u16(len(path_bytes))
            + path_bytes
            + pack_u8(algo_id)
            + pack_u8(0x00)             # entry flags (reserved)
            + pack_u64(original_size)
            + pack_u64(compressed_size)
            + pack_u32(len(metadata))
            + pack_u64(len(payload))
            + sha256_digest
            + metadata
            + payload
        )
