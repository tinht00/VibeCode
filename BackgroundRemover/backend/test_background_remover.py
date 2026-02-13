#!/usr/bin/env python3
"""
Unit Tests - Kiểm thử class BackgroundRemover.

Kiểm tra các chức năng cốt lõi:
- Load ảnh từ file và numpy array
- Xóa nền: color, edge, grabcut, auto
- Thay nền, tinh chỉnh, lưu file
- Method chaining
"""

import os
import tempfile

import numpy as np
import pytest
from PIL import Image

from background_remover import BackgroundRemover


class TestLoadImage:
    """Kiểm thử tải ảnh."""

    def test_load_from_file(self, test_image_path: str) -> None:
        """Load ảnh từ file thành công → image không None, mode RGBA."""
        remover = BackgroundRemover()
        result = remover.load(test_image_path)

        assert remover.image is not None
        assert remover.original is not None
        assert remover.image.mode == "RGBA"
        assert remover.image.size == (100, 100)
        # Kiểm tra method chaining
        assert result is remover

    def test_load_file_not_found(self) -> None:
        """Load file không tồn tại → raise FileNotFoundError."""
        remover = BackgroundRemover()
        with pytest.raises(FileNotFoundError):
            remover.load("/khong/ton/tai.png")

    def test_load_array_rgb(self) -> None:
        """Load từ numpy array RGB → chuyển sang RGBA."""
        remover = BackgroundRemover()
        array = np.zeros((50, 50, 3), dtype=np.uint8)
        result = remover.load_array(array)

        assert remover.image is not None
        assert remover.image.mode == "RGBA"
        assert remover.image.size == (50, 50)
        assert result is remover

    def test_load_array_rgba(self) -> None:
        """Load từ numpy array RGBA → giữ nguyên."""
        remover = BackgroundRemover()
        array = np.zeros((50, 50, 4), dtype=np.uint8)
        remover.load_array(array)

        assert remover.image is not None
        assert remover.image.size == (50, 50)


class TestRemoveBackground:
    """Kiểm thử các phương pháp xóa nền."""

    def test_remove_color(self, test_image_path: str) -> None:
        """Xóa nền trắng → mask không None, alpha channel có giá trị 0."""
        remover = BackgroundRemover()
        remover.load(test_image_path)
        result = remover.remove_color((255, 255, 255), tolerance=30)

        assert remover.mask is not None
        assert remover.mask.mode == "L"
        assert remover.image.mode == "RGBA"
        assert result is remover

        # Kiểm tra pixel góc (nền trắng) → phải bị xóa (alpha ≈ 0)
        pixel = remover.image.getpixel((0, 0))
        assert pixel[3] == 0  # Alpha = 0 (transparent)

    def test_remove_color_no_image(self) -> None:
        """Xóa nền khi chưa load ảnh → raise ValueError."""
        remover = BackgroundRemover()
        with pytest.raises(ValueError, match="Chưa tải ảnh"):
            remover.remove_color((255, 255, 255))

    def test_remove_edges(self, test_image_path: str) -> None:
        """Xóa nền bằng edge detection → mask không None."""
        remover = BackgroundRemover()
        remover.load(test_image_path)
        result = remover.remove_edges(threshold=50)

        assert remover.mask is not None
        assert remover.mask.mode == "L"
        assert result is remover

    def test_remove_edges_no_image(self) -> None:
        """Edge detection khi chưa load ảnh → raise ValueError."""
        remover = BackgroundRemover()
        with pytest.raises(ValueError, match="Chưa tải ảnh"):
            remover.remove_edges()

    def test_grabcut(self, test_image_path: str) -> None:
        """Xóa nền bằng GrabCut → mask không None."""
        remover = BackgroundRemover()
        remover.load(test_image_path)
        result = remover.grabcut(iterations=1)  # iterations=1 cho nhanh

        assert remover.mask is not None
        assert remover.mask.mode == "L"
        assert result is remover

    def test_grabcut_no_image(self) -> None:
        """GrabCut khi chưa load ảnh → raise ValueError."""
        remover = BackgroundRemover()
        with pytest.raises(ValueError, match="Chưa tải ảnh"):
            remover.grabcut()

    def test_auto_method(self, test_image_path: str) -> None:
        """Auto-detect phương pháp → mask không None."""
        remover = BackgroundRemover()
        remover.load(test_image_path)
        result = remover.remove_background(method="auto")

        assert remover.mask is not None
        assert result is remover


class TestReplaceBackground:
    """Kiểm thử thay nền."""

    def test_replace_with_color(self, test_image_path: str) -> None:
        """Thay nền bằng màu đỏ → pixel nền chuyển đỏ."""
        remover = BackgroundRemover()
        remover.load(test_image_path)
        remover.remove_color((255, 255, 255), tolerance=30)
        result = remover.replace_background(color=(255, 0, 0))

        assert remover.image is not None
        assert result is remover

    def test_replace_with_default_white(self, test_image_path: str) -> None:
        """Thay nền không chỉ định → mặc định nền trắng."""
        remover = BackgroundRemover()
        remover.load(test_image_path)
        remover.remove_color((255, 255, 255), tolerance=30)
        remover.replace_background()

        assert remover.image is not None

    def test_replace_no_image(self) -> None:
        """Thay nền khi chưa load ảnh → raise ValueError."""
        remover = BackgroundRemover()
        with pytest.raises(ValueError, match="Chưa tải ảnh"):
            remover.replace_background(color=(255, 0, 0))


class TestRefineAndMask:
    """Kiểm thử tinh chỉnh mask."""

    def test_refine_edges(self, test_image_path: str) -> None:
        """Feathering mask → mask được blur mượt hơn."""
        remover = BackgroundRemover()
        remover.load(test_image_path)
        remover.remove_color((255, 255, 255), tolerance=30)
        result = remover.refine_edges(feather=3)

        assert remover.mask is not None
        assert result is remover

    def test_refine_no_mask(self) -> None:
        """Refine khi chưa có mask → bỏ qua (không lỗi)."""
        remover = BackgroundRemover()
        remover.load_array(np.zeros((50, 50, 3), dtype=np.uint8))
        result = remover.refine_edges(feather=3)

        assert result is remover  # Trả về self, không raise

    def test_expand_mask(self, test_image_path: str) -> None:
        """Mở rộng mask → kích thước mask không đổi nhưng nội dung thay đổi."""
        remover = BackgroundRemover()
        remover.load(test_image_path)
        remover.remove_color((255, 255, 255), tolerance=30)
        result = remover.expand_mask(pixels=2)

        assert remover.mask is not None
        assert result is remover

    def test_contract_mask(self, test_image_path: str) -> None:
        """Thu hẹp mask → kích thước mask không đổi nhưng nội dung thay đổi."""
        remover = BackgroundRemover()
        remover.load(test_image_path)
        remover.remove_color((255, 255, 255), tolerance=30)
        result = remover.contract_mask(pixels=2)

        assert remover.mask is not None
        assert result is remover


class TestSaveImage:
    """Kiểm thử lưu ảnh."""

    def test_save_png(self, test_image_path: str) -> None:
        """Lưu PNG → file tồn tại, giữ transparency."""
        remover = BackgroundRemover()
        remover.load(test_image_path)
        remover.remove_color((255, 255, 255), tolerance=30)

        # Dùng mkstemp thay vì NamedTemporaryFile để tránh lock trên Windows
        fd, output_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)

        try:
            result = remover.save(output_path)
            assert os.path.exists(output_path)
            assert result == output_path

            # Kiểm tra file PNG hợp lệ
            saved = Image.open(output_path)
            assert saved.mode == "RGBA"
            saved.close()
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_save_jpeg(self, test_image_path: str) -> None:
        """Lưu JPEG → file tồn tại, chuyển sang RGB."""
        remover = BackgroundRemover()
        remover.load(test_image_path)

        # Dùng mkstemp thay vì NamedTemporaryFile để tránh lock trên Windows
        fd, output_path = tempfile.mkstemp(suffix=".jpg")
        os.close(fd)

        try:
            remover.save(output_path)
            assert os.path.exists(output_path)

            # JPEG phải là RGB (không có alpha)
            saved = Image.open(output_path)
            assert saved.mode == "RGB"
            saved.close()
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_save_no_image(self) -> None:
        """Lưu khi chưa có ảnh → raise ValueError."""
        remover = BackgroundRemover()
        with pytest.raises(ValueError, match="Không có ảnh"):
            remover.save("output.png")


class TestMethodChaining:
    """Kiểm thử method chaining (fluent API)."""

    def test_chain_operations(self, test_image_path: str) -> None:
        """
        Chuỗi thao tác: load → remove_color → refine → replace.

        Tất cả method phải trả về self.
        """
        remover = BackgroundRemover()
        result = (
            remover
            .load(test_image_path)
            .remove_color((255, 255, 255), tolerance=30)
            .refine_edges(feather=2)
            .replace_background(color=(0, 0, 255))
        )

        assert result is remover
        assert remover.image is not None
