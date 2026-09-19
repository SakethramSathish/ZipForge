"""
application/compression_service.py — General file compression service.

This service layer orchestrates:
  - Reading input files
  - Choosing algorithms
  - Building ZIP archives (using our custom compression algorithms as payloads)
  - Returning results with metrics

Target-size strategy (compress_files_to_target):
  1. Try all lossless algorithms (Huffman, LZW, RLE, STORE) — fastest path.
  2. If the target is still not met AND a file is a recognised image format,
     fall back to *lossy* re-encoding using PIL (binary-search over quality
     levels). The re-encoded image is stored with STORE inside the ZIP so the
     reader gets the lower-quality image back directly.
  3. If even lossy cannot meet the target, return the smallest result found
     with status "BEST_EFFORT".

Status values returned:
  "ACHIEVED"       — lossless algorithms met the target
  "ACHIEVED_LOSSY" — target met only after lossy quality reduction
  "BEST_EFFORT"    — target could not be met; smallest possible returned

It has NO dependency on Streamlit.
"""

from __future__ import annotations

import io
import logging
import time
from pathlib import Path, PurePosixPath

from archive.zip_reader import ZipReader
from archive.zip_writer import ZipWriter
from config import LOGGER_NAME
from exceptions import ArchiveFormatError, CompressionError
from models.archive import ArchiveInspection
from models.compression import CompressionResult, ExtractionResult

logger = logging.getLogger(LOGGER_NAME)

# Algorithms tried during lossless target-size search (most compressive first)
_TARGET_SIZE_ALGO_ORDER = ["HUFFMAN", "LZW", "RLE", "STORE"]

# Image extensions that support lossy quality re-encoding via PIL
_LOSSY_IMAGE_EXTS = frozenset({".jpg", ".jpeg", ".png", ".webp", ".bmp"})

# Quality range for lossy binary-search
_LOSSY_QUALITY_MIN = 5
_LOSSY_QUALITY_MAX = 92
_LOSSY_QUALITY_ITERATIONS = 14


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_image(filename: str) -> bool:
    return Path(filename).suffix.lower() in _LOSSY_IMAGE_EXTS


def _lossy_reencode(
    data: bytes,
    filename: str,
    target_bytes: int,
    progress_callback=None,
    attempt_offset: int = 0,
    total_attempts: int = 1,
) -> tuple[bytes, str, int] | None:
    """
    Binary-search over JPEG/WEBP quality levels to find the highest quality
    that produces output <= target_bytes.

    Returns:
        (reencoded_bytes, format_lower, quality) — or None if the file is
        not a recognised image or PIL cannot open it.

    The returned bytes are the final image the user will receive; quality
    indicates the encoder quality used (1–95 scale).
    """
    try:
        from PIL import Image
    except ImportError:
        logger.warning("Pillow not available — cannot do lossy fallback")
        return None

    ext = Path(filename).suffix.lower()
    if ext not in _LOSSY_IMAGE_EXTS:
        return None

    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception as exc:
        logger.warning("Cannot open %r as image for lossy reencoding: %s", filename, exc)
        return None

    # Choose output format — prefer JPEG for photos, WEBP for transparency
    has_transparency = img.mode in ("RGBA", "LA", "P")
    out_fmt = "WEBP" if has_transparency else "JPEG"
    if out_fmt == "JPEG" and img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    lo, hi = _LOSSY_QUALITY_MIN, _LOSSY_QUALITY_MAX
    best_bytes: bytes | None = None
    best_quality: int = _LOSSY_QUALITY_MIN

    for i in range(_LOSSY_QUALITY_ITERATIONS):
        mid = (lo + hi) // 2

        buf = io.BytesIO()
        save_kwargs: dict = {"format": out_fmt, "optimize": True}
        if out_fmt == "JPEG":
            save_kwargs["quality"] = mid
        else:
            save_kwargs["quality"] = mid

        img.save(buf, **save_kwargs)
        candidate = buf.getvalue()
        candidate_size = len(candidate)

        if progress_callback:
            progress_callback(
                f"Lossy q={mid}",
                candidate_size,
                target_bytes,
                attempt_offset + i,
                total_attempts + _LOSSY_QUALITY_ITERATIONS,
            )

        if candidate_size <= target_bytes:
            best_bytes = candidate
            best_quality = mid
            lo = mid + 1  # try higher quality (less compression)
        else:
            hi = mid - 1

        if lo > hi:
            break

    if best_bytes is None:
        # Even at minimum quality we can't fit — return the absolute minimum
        buf = io.BytesIO()
        img.save(buf, format=out_fmt, quality=_LOSSY_QUALITY_MIN, optimize=True)
        best_bytes = buf.getvalue()
        best_quality = _LOSSY_QUALITY_MIN

    logger.info(
        "Lossy reencoding %r → %s q=%d: %d → %d bytes",
        filename, out_fmt, best_quality, len(data), len(best_bytes),
    )
    return best_bytes, out_fmt.lower(), best_quality


def _build_lossy_archive(
    files: list[tuple[str, bytes]],
    lossy_results: dict[str, tuple[bytes, str, int]],
) -> tuple[bytes, list[tuple[str, bytes]]]:
    """
    Build a ZIP archive where image files use their lossy-reencoded bytes
    (stored via STORE algorithm) and non-image files use lossless STORE.

    Args:
        files:         Original (path, data) pairs.
        lossy_results: Mapping path → (reencoded_bytes, fmt, quality).

    Returns:
        (ZIP archive bytes, replacement_files_list)
    """
    replacement: list[tuple[str, bytes]] = []
    for stored_path, data in files:
        norm = str(PurePosixPath(stored_path.replace("\\", "/")))
        if norm in lossy_results:
            reencoded, fmt, _ = lossy_results[norm]
            replacement.append((stored_path, reencoded))
        else:
            replacement.append((stored_path, data))

    writer = ZipWriter()
    archive_bytes, _ = writer.build(replacement, algorithm="STORE")
    return archive_bytes, replacement


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compress_files(
    files: list[tuple[str, bytes]],
    algorithm: str = "AUTO",
) -> tuple[bytes, list[CompressionResult], list[tuple[str, bytes]]]:
    """
    Compress one or more files into a standard .zip archive.

    Args:
        files:     List of (stored_path, file_bytes) tuples.
        algorithm: Algorithm name ("AUTO", "RLE", "HUFFMAN", "LZW", "STORE").

    Returns:
        Tuple of (archive_bytes, results, processed_files).
    """
    if not files:
        raise CompressionError("No files provided for compression")

    start_total = time.perf_counter()
    writer = ZipWriter()
    archive_bytes, results = writer.build(files, algorithm=algorithm)
    total_time = time.perf_counter() - start_total

    logger.info(
        "Archive created: %d files, %d bytes total, %.2f s",
        len(files), len(archive_bytes), total_time,
    )
    return archive_bytes, results, files


def compress_files_to_target(
    files: list[tuple[str, bytes]],
    target_size_bytes: int,
    progress_callback=None,
) -> tuple[bytes, list[CompressionResult], str, list[tuple[str, bytes]]]:
    """
    Compress files to fit within *target_size_bytes*, using lossless algorithms
    first and falling back to lossy image re-encoding when necessary.

    Returns:
        (archive_bytes, per_file_results, status, processed_files)
    """
    if not files:
        raise CompressionError("No files provided for compression")

    writer = ZipWriter()
    lossless_candidates: list[tuple[bytes, list[CompressionResult], str]] = []
    total_steps = len(_TARGET_SIZE_ALGO_ORDER) + _LOSSY_QUALITY_ITERATIONS
    step = 0

    # ── Phase 1: Lossless algorithms ────────────────────────────────────────
    for algo in _TARGET_SIZE_ALGO_ORDER:
        step += 1
        try:
            archive_bytes, results = writer.build(files, algorithm=algo)
            archive_size = len(archive_bytes)

            if progress_callback:
                progress_callback(algo, archive_size, target_size_bytes, step, total_steps)

            logger.info(
                "Target-size lossless attempt %s: %d bytes (target %d)",
                algo, archive_size, target_size_bytes,
            )
            lossless_candidates.append((archive_bytes, results, algo))

        except Exception as exc:
            logger.warning("Algorithm %s failed during target-size search: %s", algo, exc)

    if not lossless_candidates:
        raise CompressionError("All algorithms failed during target-size compression")

    # Check if any lossless result fits
    fitting_lossless = [
        (ab, res, algo)
        for ab, res, algo in lossless_candidates
        if len(ab) <= target_size_bytes
    ]

    if fitting_lossless:
        # Pick highest quality (largest archive) that still fits
        best_archive, best_results, _ = max(fitting_lossless, key=lambda t: len(t[0]))
        return best_archive, best_results, "ACHIEVED", files

    # ── Phase 2: Lossy fallback for image files ──────────────────────────────
    image_files = [(p, d) for p, d in files if _is_image(p)]
    if image_files:
        lossy_results: dict[str, tuple[bytes, str, int]] = {}

        def _lossy_cb(label, size, target, s, total):
            if progress_callback:
                progress_callback(label, size, target, s, total)

        for stored_path, data in image_files:
            norm = str(PurePosixPath(stored_path.replace("\\", "/")))
            result = _lossy_reencode(
                data, stored_path, target_size_bytes,
                progress_callback=_lossy_cb,
                attempt_offset=step,
                total_attempts=total_steps,
            )
            if result is not None:
                lossy_results[norm] = result

        if lossy_results:
            try:
                lossy_archive, replacement = _build_lossy_archive(files, lossy_results)
                lossy_size = len(lossy_archive)

                if progress_callback:
                    progress_callback("Lossy archive", lossy_size, target_size_bytes, total_steps, total_steps)

                # Build display metrics reflecting the actual compressed sizes
                lossy_display_results = []
                for (orig_p, orig_d), (repl_p, repl_d) in zip(files, replacement):
                    orig_sz = len(orig_d)
                    comp_sz = len(repl_d)
                    lossy_display_results.append(
                        CompressionResult(
                            original_size=orig_sz,
                            compressed_size=comp_sz,
                            algorithm=lossless_candidates[0][1][0].algorithm,
                            payload=b"",
                            metadata=b"",
                            duration=0.05,
                        )
                    )

                if lossy_size <= target_size_bytes:
                    return lossy_archive, lossy_display_results, "ACHIEVED_LOSSY", replacement
                else:
                    smallest_lossless = min(lossless_candidates, key=lambda t: len(t[0]))
                    if lossy_size < len(smallest_lossless[0]):
                        return lossy_archive, lossy_display_results, "BEST_EFFORT", replacement
                    else:
                        return smallest_lossless[0], smallest_lossless[1], "BEST_EFFORT", files
            except Exception as exc:
                logger.warning("Lossy archive build failed: %s", exc)

    # ── Phase 3: No option worked — return smallest lossless result ──────────
    best_archive, best_results, _ = min(lossless_candidates, key=lambda t: len(t[0]))
    return best_archive, best_results, "BEST_EFFORT", files


def decompress_to_memory(archive_bytes: bytes) -> list[tuple[str, bytes]]:
    """
    Extract all files from a .zip archive into memory.

    Returns:
        List of (path, decompressed_bytes) pairs.
    """
    reader = ZipReader(archive_bytes)
    return reader.extract_to_memory()


def inspect_archive(archive_bytes: bytes) -> ArchiveInspection:
    """
    Parse archive metadata without fully decompressing.

    Returns:
        ArchiveInspection with per-entry metadata.
    """
    reader = ZipReader(archive_bytes)
    return reader.inspect()
