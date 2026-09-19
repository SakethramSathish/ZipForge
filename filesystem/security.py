"""
filesystem/security.py — Path sanitization and traversal prevention.

Every archive entry path must be validated before extraction.
This module provides the containment check used by the archive reader.

## Threat Model

A malicious archive could contain paths such as:
    ../../etc/passwd
    /absolute/path.txt
    C:\\Windows\\System32\\evil.dll
    normal/../../../escape.txt

These must all be rejected or safely normalized so that extracted files
never escape the chosen destination directory.

## Algorithm

1. Strip leading slashes and drive letters from the stored path.
2. Resolve the path against the destination directory using pathlib.
3. Verify the resolved path is within (a child of) the destination.
4. If not, raise UnsafePathError.

Normalisation uses pathlib.Path.resolve() which handles ../ sequences.
"""

from __future__ import annotations

import re
from pathlib import Path

from exceptions import UnsafePathError


# Regex that matches Windows drive letters like "C:\" or "C:/"
_DRIVE_LETTER_RE = re.compile(r"^[A-Za-z]:[\\/]?")


def sanitize_entry_path(stored_path: str) -> str:
    """
    Clean a stored archive path to a safe relative form.

    - Strips leading slashes (/, \).
    - Strips Windows drive letters (C:\, D:/).
    - Normalises separators to forward slash.
    - Rejects empty paths after normalisation.

    Args:
        stored_path: The raw path string from the archive.

    Returns:
        A cleaned relative path string (using forward slashes).

    Raises:
        UnsafePathError: if the path cannot be made safe.
    """
    if not stored_path:
        raise UnsafePathError("Archive entry path is empty")

    # Normalise backslashes to forward slashes first
    normalized = stored_path.replace("\\", "/")

    # Reject absolute paths (starting with / or // after drive removal)
    # Do this check BEFORE stripping the leading slash
    after_drive = _DRIVE_LETTER_RE.sub("", normalized)
    if after_drive.startswith("/"):
        raise UnsafePathError(
            f"Archive entry path {stored_path!r} is an absolute path and is unsafe"
        )

    # Remove Windows drive letters
    cleaned = _DRIVE_LETTER_RE.sub("", normalized)

    # Strip any remaining leading slashes (normalise)
    cleaned = cleaned.lstrip("/")

    if not cleaned:
        raise UnsafePathError(
            f"Archive entry path {stored_path!r} is unsafe (empty after normalisation)"
        )

    return cleaned


def safe_extraction_path(
    stored_path: str,
    destination: Path,
) -> Path:
    """
    Resolve *stored_path* inside *destination* and verify containment.

    Args:
        stored_path:  The raw path from the archive.
        destination:  The directory into which files are extracted.

    Returns:
        A resolved, safe Path within *destination*.

    Raises:
        UnsafePathError: if the resolved path would escape *destination*.
    """
    cleaned = sanitize_entry_path(stored_path)

    # Use os.path.normpath via pathlib for platform safety
    # We do NOT call resolve() on a non-existent path's parts that could
    # follow symlinks out of the destination.  Instead we:
    # 1. Build the candidate path
    # 2. Use str(Path.resolve()) on both to compare
    candidate = (destination / cleaned).resolve()
    dest_resolved = destination.resolve()

    try:
        candidate.relative_to(dest_resolved)
    except ValueError:
        raise UnsafePathError(
            f"Path traversal detected: {stored_path!r} resolves to "
            f"{candidate} which is outside {dest_resolved}"
        )

    return candidate


def contains_path_traversal(path_str: str) -> bool:
    """
    Quick check: does *path_str* contain traversal sequences?

    This is a fast pre-filter. Full validation must still use
    safe_extraction_path().
    """
    normalized = path_str.replace("\\", "/")
    parts = normalized.split("/")
    return ".." in parts or normalized.startswith("/")
