"""
integrity/hashing.py — SHA-256 computation and verification.

All archive entries store a SHA-256 hash of the *original* (pre-compression)
bytes. On extraction the decompressed bytes are hashed and compared.
"""

from __future__ import annotations

import hashlib
import logging
from enum import Enum

from config import HASH_ALGORITHM, HASH_SIZE_BYTES, LOGGER_NAME
from exceptions import IntegrityError

logger = logging.getLogger(LOGGER_NAME)


class IntegrityStatus(str, Enum):
    VALID = "VALID"
    CORRUPTED = "CORRUPTED"
    UNVERIFIED = "UNVERIFIED"


def compute_hash(data: bytes) -> bytes:
    """
    Compute SHA-256 of *data* and return the 32-byte digest.

    Args:
        data: Raw bytes to hash.

    Returns:
        32-byte SHA-256 digest.
    """
    return hashlib.new(HASH_ALGORITHM, data).digest()


def compute_hash_hex(data: bytes) -> str:
    """Return the SHA-256 hex digest string (64 hex characters)."""
    return hashlib.new(HASH_ALGORITHM, data).hexdigest()


def verify_hash(data: bytes, expected_digest: bytes) -> IntegrityStatus:
    """
    Verify that *data* hashes to *expected_digest*.

    Args:
        data:            The decompressed bytes to verify.
        expected_digest: The 32-byte SHA-256 digest stored in the archive.

    Returns:
        IntegrityStatus.VALID or IntegrityStatus.CORRUPTED.
    """
    if len(expected_digest) != HASH_SIZE_BYTES:
        logger.warning(
            "Integrity check skipped: stored digest length %d != expected %d",
            len(expected_digest), HASH_SIZE_BYTES,
        )
        return IntegrityStatus.UNVERIFIED

    actual = compute_hash(data)
    if actual == expected_digest:
        return IntegrityStatus.VALID
    logger.error(
        "Integrity check FAILED: expected %s, got %s",
        expected_digest.hex(), actual.hex(),
    )
    return IntegrityStatus.CORRUPTED


def assert_integrity(data: bytes, expected_digest: bytes, entry_path: str = "") -> None:
    """
    Like verify_hash but raises IntegrityError on failure.

    Args:
        data:            The decompressed bytes.
        expected_digest: Stored SHA-256 digest.
        entry_path:      Path label for error messages.

    Raises:
        IntegrityError: if verification fails.
    """
    status = verify_hash(data, expected_digest)
    if status == IntegrityStatus.CORRUPTED:
        raise IntegrityError(
            f"Integrity verification failed for {entry_path!r}: "
            "SHA-256 digest does not match stored value. "
            "The archive entry may be corrupted."
        )
