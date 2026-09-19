"""
archive/format.py — FCMP binary format constants and field sizes.

The FCMP v1 format layout is:

HEADER (11 bytes):
    [4]  Magic         b'FCMP'
    [1]  Version       0x01
    [2]  Global Flags  0x0000 (reserved)
    [4]  Entry Count   uint32 LE

PER ENTRY (sequential, self-describing):
    [2]  Path Length   uint16 LE
    [N]  Path          UTF-8 bytes (N = Path Length)
    [1]  Algorithm ID  uint8  (0=STORE, 1=RLE, 2=HUFFMAN, 3=LZW)
    [1]  Entry Flags   uint8  (reserved, 0x00)
    [8]  Original Size  uint64 LE
    [8]  Compressed Size uint64 LE
    [4]  Metadata Length uint32 LE
    [8]  Payload Length  uint64 LE
    [32] SHA-256        raw digest of original bytes
    [M]  Algorithm Metadata (M = Metadata Length)
    [P]  Compressed Payload (P = Payload Length)

All integer fields are little-endian unless otherwise specified.
"""

from __future__ import annotations

# Magic bytes
FCMP_MAGIC = b"FCMP"
FCMP_VERSION = 1

# Header field sizes
MAGIC_SIZE = 4
VERSION_SIZE = 1
FLAGS_SIZE = 2
ENTRY_COUNT_SIZE = 4
HEADER_SIZE = MAGIC_SIZE + VERSION_SIZE + FLAGS_SIZE + ENTRY_COUNT_SIZE  # = 11

# Per-entry fixed prefix field sizes (before variable path/metadata/payload)
PATH_LENGTH_SIZE = 2   # uint16
ALGO_ID_SIZE = 1       # uint8
ENTRY_FLAGS_SIZE = 1   # uint8
ORIGINAL_SIZE_SIZE = 8  # uint64
COMPRESSED_SIZE_SIZE = 8  # uint64
METADATA_LENGTH_SIZE = 4  # uint32
PAYLOAD_LENGTH_SIZE = 8   # uint64
SHA256_SIZE = 32           # bytes

# Total fixed per-entry overhead (excluding variable path, metadata, payload)
ENTRY_FIXED_SIZE = (
    PATH_LENGTH_SIZE
    + ALGO_ID_SIZE
    + ENTRY_FLAGS_SIZE
    + ORIGINAL_SIZE_SIZE
    + COMPRESSED_SIZE_SIZE
    + METADATA_LENGTH_SIZE
    + PAYLOAD_LENGTH_SIZE
    + SHA256_SIZE
)

# Safety limits (prevent malicious archives from causing massive allocations)
MAX_SAFE_PATH_LENGTH = 4096
MAX_SAFE_METADATA_LENGTH = 1 << 20   # 1 MiB
MAX_SAFE_PAYLOAD_LENGTH = 1 << 40    # 1 TiB (practical limit)
MAX_SAFE_ENTRY_COUNT = 65_535
