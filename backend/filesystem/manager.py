"""
filesystem/manager.py — Temporary file and directory management.

All temporary workspaces used by the compressor are created and cleaned
up through this module to prevent permanent temp-file accumulation.
"""

from __future__ import annotations

import logging
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from config import LOGGER_NAME, TEMP_DIR_PREFIX

logger = logging.getLogger(LOGGER_NAME)


@contextmanager
def temporary_directory() -> Generator[Path, None, None]:
    """
    Context manager that creates a unique temporary directory and removes
    it (with all contents) on exit, even if an exception is raised.

    Usage:
        with temporary_directory() as tmp_dir:
            # work with tmp_dir
            ...
        # directory is gone here
    """
    tmp_path = Path(tempfile.mkdtemp(prefix=TEMP_DIR_PREFIX))
    logger.debug("Created temporary directory: %s", tmp_path)
    try:
        yield tmp_path
    finally:
        try:
            shutil.rmtree(tmp_path, ignore_errors=True)
            logger.debug("Cleaned up temporary directory: %s", tmp_path)
        except Exception as exc:
            logger.warning("Failed to clean up temporary directory %s: %s", tmp_path, exc)


def ensure_directory(path: Path) -> Path:
    """
    Create *path* and any missing parents.

    Args:
        path: Directory to create.

    Returns:
        The created (or pre-existing) path.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_write_file(dest: Path, data: bytes, conflict: str = "rename") -> Path:
    """
    Write *data* to *dest*, handling filename conflicts.

    Args:
        dest:     Target file path.
        data:     Bytes to write.
        conflict: Policy for existing files: "rename" (default) | "overwrite" | "skip".

    Returns:
        The actual path where data was written.
    """
    if dest.exists():
        if conflict == "overwrite":
            pass  # fall through to write
        elif conflict == "skip":
            logger.info("Skipping existing file: %s", dest)
            return dest
        else:
            # rename: add numeric suffix
            stem = dest.stem
            suffix = dest.suffix
            counter = 1
            while dest.exists():
                dest = dest.parent / f"{stem}_{counter}{suffix}"
                counter += 1

    ensure_directory(dest.parent)
    dest.write_bytes(data)
    return dest
