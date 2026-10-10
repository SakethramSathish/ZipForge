"""
config.py — Application-wide constants for Build Your Own File Compressor.

All magic numbers, limits, and tuneable parameters are centralized here.
Do not scatter literals throughout the codebase.
"""

# ---------------------------------------------------------------------------
# Archive format
# ---------------------------------------------------------------------------
ARCHIVE_MAGIC: bytes = b"FCMP"
ARCHIVE_VERSION: int = 1
ARCHIVE_HEADER_SIZE: int = 11  # magic(4) + version(1) + flags(2) + count(4)
ARCHIVE_EXTENSION: str = ".zip"

# ZIP hybrid format — algorithm suffix appended to filenames inside the ZIP
# e.g. "report.pdf.__huffman" means the payload is Huffman-compressed
ZIP_ALGO_SUFFIX_SEPARATOR: str = ".__"

MAX_ARCHIVE_ENTRIES: int = 65_535
MAX_PATH_LENGTH: int = 4096       # bytes (UTF-8 encoded path)
MAX_METADATA_SIZE: int = 1 << 20  # 1 MiB per entry metadata block
MAX_ORIGINAL_SIZE: int = 1 << 40  # 1 TiB hard sanity cap

# Algorithm IDs stored in the archive
ALGO_ID_STORE: int = 0
ALGO_ID_RLE: int = 1
ALGO_ID_HUFFMAN: int = 2
ALGO_ID_LZW: int = 3

ALGO_ID_TO_NAME: dict[int, str] = {
    ALGO_ID_STORE: "STORE",
    ALGO_ID_RLE: "RLE",
    ALGO_ID_HUFFMAN: "HUFFMAN",
    ALGO_ID_LZW: "LZW",
}
ALGO_NAME_TO_ID: dict[str, int] = {v: k for k, v in ALGO_ID_TO_NAME.items()}

# ---------------------------------------------------------------------------
# RLE
# ---------------------------------------------------------------------------
RLE_MAX_RUN: int = 255          # Maximum run count in a single RLE token
RLE_ESCAPE_BYTE: int = 0xFE    # Escape byte for literal runs in enhanced RLE

# ---------------------------------------------------------------------------
# Huffman
# ---------------------------------------------------------------------------
HUFFMAN_MAX_CODE_LENGTH: int = 32   # Maximum allowed Huffman code bit length

# ---------------------------------------------------------------------------
# LZW
# ---------------------------------------------------------------------------
LZW_MIN_CODE_WIDTH: int = 9
LZW_MAX_CODE_WIDTH: int = 16
LZW_CLEAR_CODE: int = 256           # Signals dictionary reset
LZW_EOI_CODE: int = 257             # End of information
LZW_INITIAL_DICT_SIZE: int = 258    # 256 literals + CLEAR + EOI
LZW_MAX_DICT_SIZE: int = 1 << 16   # 65536 entries

# ---------------------------------------------------------------------------
# Image compression
# ---------------------------------------------------------------------------
# Profile quality values (tuned; see docs/IMAGE_OPTIMIZATION.md)
IMAGE_EXTREME_QUALITY: int = 30
IMAGE_EXTREME_QUALITY_MIN: int = 15
IMAGE_EXTREME_QUALITY_MAX: int = 40

IMAGE_RECOMMENDED_QUALITY: int = 75
IMAGE_RECOMMENDED_QUALITY_MIN: int = 60
IMAGE_RECOMMENDED_QUALITY_MAX: int = 85

IMAGE_LESS_QUALITY: int = 90
IMAGE_LESS_QUALITY_MIN: int = 82
IMAGE_LESS_QUALITY_MAX: int = 95

DEFAULT_IMAGE_PROFILE: str = "RECOMMENDED"

# Supported input/output image formats
SUPPORTED_INPUT_FORMATS: frozenset[str] = frozenset({"JPEG", "JPG", "PNG", "WEBP", "BMP", "GIF"})
SUPPORTED_OUTPUT_FORMATS: frozenset[str] = frozenset({"JPEG", "PNG", "WEBP"})

# ---------------------------------------------------------------------------
# Target-size optimizer
# ---------------------------------------------------------------------------
TARGET_SIZE_MIN_QUALITY: int = 5
TARGET_SIZE_MAX_QUALITY: int = 95
TARGET_SIZE_MAX_ITERATIONS: int = 12
TARGET_SIZE_TOLERANCE_BYTES: int = 0   # strict: final <= target
TARGET_SIZE_DEFAULT_FORMAT: str = "JPEG"

# ---------------------------------------------------------------------------
# Integrity
# ---------------------------------------------------------------------------
HASH_ALGORITHM: str = "sha256"
HASH_SIZE_BYTES: int = 32

# ---------------------------------------------------------------------------
# Filesystem / temp
# ---------------------------------------------------------------------------
TEMP_DIR_PREFIX: str = "fcmp_"

# ---------------------------------------------------------------------------
# Compression levels (maps UI level → algorithm name for file compression)
# ---------------------------------------------------------------------------
COMPRESSION_LEVEL_EXTREME: str = "AUTO"       # tries all, picks smallest
COMPRESSION_LEVEL_RECOMMENDED: str = "AUTO"   # same — best ratio
COMPRESSION_LEVEL_LESS: str = "STORE"         # no compression, max fidelity

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOGGER_NAME: str = "file_compressor"
