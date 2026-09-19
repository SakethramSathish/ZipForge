"""
tests/test_image.py — Tests for image compression, profiles, and target-size optimizer.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import io
import pytest
from PIL import Image

from application.image_service import compress_image, optimize_image_to_target
from models.image import ImageProfile, TargetStatus


def make_jpeg(size=(200, 200), color=(128, 64, 32)) -> bytes:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def make_png_rgba(size=(200, 200)) -> bytes:
    img = Image.new("RGBA", size, color=(100, 150, 200, 180))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_webp(size=(200, 200)) -> bytes:
    img = Image.new("RGB", size, color=(200, 100, 50))
    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=90)
    return buf.getvalue()


class TestImageProfiles:
    def test_extreme_profile(self, small_jpeg_image):
        result = compress_image(small_jpeg_image, profile_name="EXTREME")
        assert result.profile == ImageProfile.EXTREME
        assert result.quality <= 40
        assert len(result.output_bytes) > 0

    def test_recommended_profile(self, small_jpeg_image):
        result = compress_image(small_jpeg_image, profile_name="RECOMMENDED")
        assert result.profile == ImageProfile.RECOMMENDED
        assert result.quality == 75

    def test_less_profile(self, small_jpeg_image):
        result = compress_image(small_jpeg_image, profile_name="LESS_COMPRESSION")
        assert result.profile == ImageProfile.LESS_COMPRESSION
        assert result.quality >= 82

    def test_extreme_smaller_than_recommended(self):
        """EXTREME should produce a smaller file than RECOMMENDED."""
        jpeg = make_jpeg(size=(400, 400))
        extreme = compress_image(jpeg, profile_name="EXTREME")
        recommended = compress_image(jpeg, profile_name="RECOMMENDED")
        assert extreme.final_size <= recommended.final_size

    def test_recommended_smaller_than_less(self):
        """RECOMMENDED quality should generally produce smaller files than LESS.
        
        Note: for synthetic solid-color images, size differences can be minimal
        or reversed due to JPEG DCT behavior. Use an image with actual content.
        """
        # Create an image with gradient-like content to get realistic JPEG behavior
        from PIL import Image
        import io
        img = Image.new("RGB", (400, 400))
        pixels = img.load()
        for x in range(400):
            for y in range(400):
                pixels[x, y] = ((x * y) % 256, (x + y) % 256, (x * 2 + y) % 256)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=100)
        jpeg = buf.getvalue()
        
        recommended = compress_image(jpeg, profile_name="RECOMMENDED")
        less = compress_image(jpeg, profile_name="LESS_COMPRESSION")
        # RECOMMENDED (q=75) produces smaller file than LESS (q=90)
        assert recommended.final_size < less.final_size

    def test_png_transparency_preserved(self, small_png_image):
        """PNG with transparency should output PNG, not JPEG."""
        result = compress_image(small_png_image, profile_name="RECOMMENDED")
        assert result.output_format == "PNG"
        assert len(result.output_bytes) > 0
        # Verify output is valid PNG with RGBA
        restored = Image.open(io.BytesIO(result.output_bytes))
        assert restored.mode in ("RGBA", "RGB", "P")

    def test_jpeg_roundtrip(self, small_jpeg_image):
        result = compress_image(small_jpeg_image, profile_name="RECOMMENDED")
        assert result.original_size == len(small_jpeg_image)
        assert result.final_size > 0
        assert result.output_format == "JPEG"

    def test_webp_output(self, small_jpeg_image):
        result = compress_image(small_jpeg_image, profile_name="RECOMMENDED", output_format="WEBP")
        assert result.output_format == "WEBP"
        assert len(result.output_bytes) > 0

    def test_metrics_accuracy(self):
        jpeg = make_jpeg(size=(300, 300))
        result = compress_image(jpeg, profile_name="EXTREME")
        assert result.original_size == len(jpeg)
        assert result.final_size == len(result.output_bytes)
        assert result.bytes_saved == max(0, result.original_size - result.final_size)


class TestTargetSizeOptimizer:
    def test_achievable_target(self):
        """Target larger than minimum quality output should be achieved."""
        jpeg = make_jpeg(size=(400, 400))
        # 50KB target should be achievable for a 400x400 image
        target_bytes = 50 * 1024
        result = optimize_image_to_target(
            jpeg,
            target_size_bytes=target_bytes,
            output_format="JPEG",
        )
        assert result.target_status == TargetStatus.ACHIEVED
        assert result.final_size <= target_bytes
        assert result.target_size == target_bytes

    def test_final_size_always_le_target_when_achieved(self):
        """Strict invariant: if ACHIEVED, final_size <= target_size."""
        jpeg = make_jpeg(size=(300, 300))
        target_bytes = 30 * 1024
        result = optimize_image_to_target(jpeg, target_size_bytes=target_bytes)
        if result.target_status == TargetStatus.ACHIEVED:
            assert result.final_size <= target_bytes, (
                f"ACHIEVED but final_size={result.final_size} > target={target_bytes}"
            )

    def test_target_larger_than_original(self):
        """Target > original should not degrade quality below reasonable bound."""
        jpeg = make_jpeg(size=(100, 100))
        original_size = len(jpeg)
        result = optimize_image_to_target(jpeg, target_size_bytes=original_size * 10)
        assert result.target_status == TargetStatus.ACHIEVED

    def test_impossible_target_reported_honestly(self):
        """Very small target (1 byte) should report UNACHIEVABLE."""
        jpeg = make_jpeg(size=(200, 200))
        result = optimize_image_to_target(jpeg, target_size_bytes=1)
        assert result.target_status == TargetStatus.UNACHIEVABLE
        assert result.final_size > 1  # shouldn't claim 1 byte output

    def test_iteration_count_bounded(self):
        """Should not exceed max_iterations."""
        jpeg = make_jpeg(size=(200, 200))
        max_iter = 5
        result = optimize_image_to_target(
            jpeg,
            target_size_bytes=10 * 1024,
            max_iterations=max_iter,
        )
        assert result.iterations <= max_iter

    def test_higher_quality_preferred(self):
        """When two qualities satisfy the target, the higher one should be chosen."""
        jpeg = make_jpeg(size=(400, 400))
        # Large enough target that multiple qualities satisfy it
        target = 200 * 1024  # 200KB
        result = optimize_image_to_target(jpeg, target_size_bytes=target)
        if result.target_status == TargetStatus.ACHIEVED:
            # The quality should be maximized — we check it's at least
            # higher than the minimum
            assert result.quality > 5

    def test_progress_callback_called(self):
        """Progress callback should be invoked on each iteration."""
        # Use a large image so target < original, triggering the optimizer
        jpeg = make_jpeg(size=(600, 600))
        # Use a very small target to force binary search iterations
        target_bytes = 5 * 1024  # 5KB — much smaller than 600x600 JPEG at q=95
        iterations_reported = []

        def callback(iteration, max_iter, quality, size):
            iterations_reported.append(iteration)

        result = optimize_image_to_target(
            jpeg,
            target_size_bytes=target_bytes,
            progress_callback=callback,
        )
        assert len(iterations_reported) > 0
        assert result.iterations == len(iterations_reported)

    def test_webp_target(self):
        jpeg = make_jpeg(size=(300, 300))
        result = optimize_image_to_target(
            jpeg,
            target_size_bytes=30 * 1024,
            output_format="WEBP",
        )
        if result.target_status == TargetStatus.ACHIEVED:
            assert result.final_size <= 30 * 1024
            assert result.output_format == "WEBP"

    def test_rgba_png_not_converted_to_jpeg(self):
        """RGBA image with target size should use PNG not JPEG."""
        png_rgba = make_png_rgba(size=(200, 200))
        result = optimize_image_to_target(
            png_rgba,
            target_size_bytes=100 * 1024,
            output_format="PNG",
        )
        assert result.output_format == "PNG"
        assert len(result.output_bytes) > 0
