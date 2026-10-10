"""
image/formats.py — Image format strategy and Pillow encoding helpers.

Determines the output format for each input image and provides
encoding functions that handle transparency correctly.

## Format Policy

| Input mode | Has transparency | Default output |
|---|---|---|
| JPEG (no alpha) | No | JPEG |
| PNG (RGBA/PA) | Yes | PNG (preserves alpha) |
| PNG (RGB/L) | No | JPEG |
| WEBP | Maybe | WEBP |
| Other | Varies | Convert to RGB → JPEG |

Key invariant:
    Images with transparency are NEVER silently converted to JPEG
    without an explicit background policy.
"""

from __future__ import annotations

import io

from PIL import Image, ImageOps

from exceptions import TransparencyConversionError, UnsupportedImageFormatError


# Formats that support transparency
_TRANSPARENT_FORMATS: frozenset[str] = frozenset({"PNG", "WEBP", "GIF"})
# Pillow modes that have an alpha channel
_ALPHA_MODES: frozenset[str] = frozenset({"RGBA", "LA", "PA"})


def detect_format(img: Image.Image, original_format: str | None = None) -> str:
    """
    Determine the recommended output format for *img*.

    Args:
        img:             Pillow Image.
        original_format: Format string from img.format ("JPEG", "PNG", etc.).

    Returns:
        Output format string ("JPEG", "PNG", "WEBP").
    """
    has_alpha = img.mode in _ALPHA_MODES

    if has_alpha:
        # Must use a format that supports transparency
        if original_format and original_format.upper() == "WEBP":
            return "WEBP"
        return "PNG"

    if original_format:
        fmt = original_format.upper()
        if fmt == "JPEG" or fmt == "JPG":
            return "JPEG"
        if fmt == "WEBP":
            return "WEBP"
        if fmt == "PNG":
            return "JPEG"  # No alpha → can use JPEG

    return "JPEG"  # Safe default


def prepare_image_for_encoding(
    img: Image.Image,
    output_format: str,
    background_color: tuple[int, int, int] | None = None,
) -> Image.Image:
    """
    Convert *img* to a mode compatible with *output_format*.

    Args:
        img:              Input Pillow image.
        output_format:    Target format ("JPEG", "PNG", "WEBP").
        background_color: RGB tuple to composite alpha onto (for JPEG).
                          Required when converting RGBA→JPEG.

    Returns:
        Converted Pillow image ready for saving.

    Raises:
        TransparencyConversionError: if RGBA→JPEG conversion requested
                                     without a background color.
    """
    fmt = output_format.upper()
    has_alpha = img.mode in _ALPHA_MODES

    if fmt == "JPEG":
        if has_alpha:
            if background_color is None:
                raise TransparencyConversionError(
                    f"Cannot convert a transparent image (mode={img.mode!r}) "
                    "to JPEG without specifying a background color."
                )
            # Composite onto background
            background = Image.new("RGB", img.size, background_color)
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[3])
            return background
        elif img.mode != "RGB":
            return img.convert("RGB")
        return img

    elif fmt == "PNG":
        # PNG supports all modes; RGBA is ideal for transparency
        if has_alpha and img.mode != "RGBA":
            return img.convert("RGBA")
        if not has_alpha and img.mode == "P":
            return img.convert("RGB")
        return img

    elif fmt == "WEBP":
        if has_alpha and img.mode != "RGBA":
            return img.convert("RGBA")
        elif not has_alpha and img.mode not in ("RGB", "RGBA", "L"):
            return img.convert("RGB")
        return img

    else:
        raise UnsupportedImageFormatError(f"Unsupported output format: {fmt!r}")


def encode_image(
    img: Image.Image,
    output_format: str,
    quality: int,
    optimize: bool = True,
    progressive: bool = False,
    preserve_exif: bool = False,
) -> bytes:
    """
    Encode *img* to bytes in *output_format* at the given *quality*.

    Args:
        img:            Pillow image (already mode-converted).
        output_format:  "JPEG", "PNG", "WEBP".
        quality:        Encoder quality (1-100 for JPEG/WEBP; ignored for PNG lossless).
        optimize:       Pass optimize=True to Pillow.
        progressive:    Enable progressive JPEG.
        preserve_exif:  Preserve EXIF metadata where supported.

    Returns:
        Encoded image bytes.
    """
    buf = io.BytesIO()
    fmt = output_format.upper()

    save_kwargs: dict = {"format": fmt, "optimize": optimize}

    if fmt == "JPEG":
        save_kwargs["quality"] = max(1, min(95, quality))
        save_kwargs["progressive"] = progressive
        if preserve_exif:
            try:
                exif = img.info.get("exif")
                if exif:
                    save_kwargs["exif"] = exif
            except Exception:
                pass  # EXIF preservation is best-effort

    elif fmt == "WEBP":
        save_kwargs["quality"] = max(1, min(100, quality))
        save_kwargs["method"] = 6   # Slower but better compression
        if img.mode == "RGBA":
            save_kwargs["lossless"] = False

    elif fmt == "PNG":
        # PNG is lossless; quality maps roughly to zlib compression level
        # quality > 80 → compress_level 6; higher quality = less compression
        compress_level = max(0, min(9, round((100 - quality) / 11)))
        save_kwargs["compress_level"] = compress_level
        save_kwargs.pop("optimize", None)  # not all PIL versions support for PNG
        if preserve_exif:
            try:
                pnginfo = img.info.get("pnginfo")
                if pnginfo:
                    save_kwargs["pnginfo"] = pnginfo
            except Exception:
                pass

    img.save(buf, **save_kwargs)
    return buf.getvalue()


def load_image(image_bytes: bytes) -> tuple[Image.Image, str]:
    """
    Load an image from bytes.

    Returns:
        (Pillow Image, format string e.g. "JPEG").

    Raises:
        UnsupportedImageFormatError: if Pillow cannot identify the format.
    """
    try:
        buf = io.BytesIO(image_bytes)
        img = Image.open(buf)
        img.load()  # Force decompression
        fmt = img.format or "UNKNOWN"
        # Apply EXIF orientation
        img = ImageOps.exif_transpose(img)
        return img, fmt
    except Exception as exc:
        raise UnsupportedImageFormatError(
            f"Cannot load image: {exc}"
        ) from exc
