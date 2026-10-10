"""
binary/serialization.py — struct-based helpers for fixed-width field I/O.

Provides thin wrappers around `struct.pack`/`struct.unpack` for the
specific field types used in the FCMP archive format.

All multi-byte integers are little-endian.
"""

from __future__ import annotations

import struct
from io import RawIOBase


# Struct format strings (all little-endian)
_FMT_U8 = "<B"
_FMT_U16 = "<H"
_FMT_U32 = "<I"
_FMT_U64 = "<Q"

_SIZE_U8 = struct.calcsize(_FMT_U8)   # 1
_SIZE_U16 = struct.calcsize(_FMT_U16)  # 2
_SIZE_U32 = struct.calcsize(_FMT_U32)  # 4
_SIZE_U64 = struct.calcsize(_FMT_U64)  # 8


# ---------------------------------------------------------------------------
# Pack helpers (bytes → integer)
# ---------------------------------------------------------------------------

def pack_u8(value: int) -> bytes:
    return struct.pack(_FMT_U8, value)


def pack_u16(value: int) -> bytes:
    return struct.pack(_FMT_U16, value)


def pack_u32(value: int) -> bytes:
    return struct.pack(_FMT_U32, value)


def pack_u64(value: int) -> bytes:
    return struct.pack(_FMT_U64, value)


# ---------------------------------------------------------------------------
# Unpack helpers (integer → bytes)
# ---------------------------------------------------------------------------

def unpack_u8(data: bytes) -> int:
    if len(data) < _SIZE_U8:
        raise ValueError(f"Need {_SIZE_U8} byte(s) for u8, got {len(data)}")
    return struct.unpack(_FMT_U8, data[:_SIZE_U8])[0]


def unpack_u16(data: bytes) -> int:
    if len(data) < _SIZE_U16:
        raise ValueError(f"Need {_SIZE_U16} byte(s) for u16, got {len(data)}")
    return struct.unpack(_FMT_U16, data[:_SIZE_U16])[0]


def unpack_u32(data: bytes) -> int:
    if len(data) < _SIZE_U32:
        raise ValueError(f"Need {_SIZE_U32} byte(s) for u32, got {len(data)}")
    return struct.unpack(_FMT_U32, data[:_SIZE_U32])[0]


def unpack_u64(data: bytes) -> int:
    if len(data) < _SIZE_U64:
        raise ValueError(f"Need {_SIZE_U64} byte(s) for u64, got {len(data)}")
    return struct.unpack(_FMT_U64, data[:_SIZE_U64])[0]


# ---------------------------------------------------------------------------
# Stream-based read helpers (read exact N bytes from a file-like object)
# ---------------------------------------------------------------------------

def read_exact(stream: RawIOBase, n: int) -> bytes:
    """
    Read exactly *n* bytes from *stream*.

    Raises:
        EOFError: if the stream ends before *n* bytes are available.
    """
    buf = stream.read(n)
    if buf is None or len(buf) < n:
        got = len(buf) if buf else 0
        raise EOFError(f"Expected {n} bytes, got {got} (stream truncated)")
    return buf


def read_u8(stream: RawIOBase) -> int:
    return unpack_u8(read_exact(stream, _SIZE_U8))


def read_u16(stream: RawIOBase) -> int:
    return unpack_u16(read_exact(stream, _SIZE_U16))


def read_u32(stream: RawIOBase) -> int:
    return unpack_u32(read_exact(stream, _SIZE_U32))


def read_u64(stream: RawIOBase) -> int:
    return unpack_u64(read_exact(stream, _SIZE_U64))
