#!/usr/bin/env python3
"""
Background Remover - Xóa nền ảnh sử dụng nhiều phương pháp phân đoạn (segmentation).

Module cốt lõi cung cấp class BackgroundRemover với các method:
- remove_background: Tự động phát hiện và xóa nền
- remove_color: Xóa nền theo màu cụ thể
- remove_edges: Xóa nền bằng phát hiện cạnh (Edge Detection)
- grabcut: Xóa nền bằng thuật toán GrabCut (OpenCV)
- replace_background: Thay nền bằng màu hoặc ảnh khác
- refine_edges: Tinh chỉnh viền mask
"""

import os
from pathlib import Path
from typing import List, Optional, Tuple, Union
import io

import numpy as np
from PIL import Image, ImageFilter, ImageDraw
import cv2
try:
    from rembg import remove as rembg_remove
    from rembg import new_session as rembg_session
    HAS_REMBG = True
except ImportError:
    HAS_REMBG = False



class BackgroundRemover:
    """
    Lớp xử lý xóa nền ảnh.

    Hỗ trợ nhiều phương pháp: color-based, edge detection, GrabCut.
    Cho phép thay nền, tinh chỉnh mask, thêm bóng đổ, và xử lý hàng loạt.

    Attributes:
        image: Ảnh hiện tại (PIL Image, RGBA mode)
        original: Ảnh gốc ban đầu (PIL Image)
        mask: Mask phân tách foreground/background (PIL Image, L mode)
        filepath: Đường dẫn file ảnh gốc
    """

    def __init__(self) -> None:
        """Khởi tạo BackgroundRemover với trạng thái rỗng."""
        self.image: Optional[Image.Image] = None
        self.original: Optional[Image.Image] = None
        self.mask: Optional[Image.Image] = None
        self.filepath: Optional[str] = None

    def load(self, filepath: str) -> 'BackgroundRemover':
        """
        Tải ảnh từ file.

        Args:
            filepath: Đường dẫn tới file ảnh (jpg, png, webp, bmp)

        Returns:
            self để hỗ trợ method chaining

        Raises:
            FileNotFoundError: Nếu file không tồn tại
        """
        self.filepath = filepath
        self.image = Image.open(filepath).convert('RGBA')
        self.original = self.image.copy()
        self.mask = None
        return self

    def load_array(self, array: np.ndarray) -> 'BackgroundRemover':
        """
        Tải ảnh từ numpy array.

        Args:
            array: Mảng numpy (H, W, 3) hoặc (H, W, 4)

        Returns:
            self để hỗ trợ method chaining
        """
        if array.shape[-1] == 3:
            self.image = Image.fromarray(array).convert('RGBA')
        else:
            self.image = Image.fromarray(array)
        self.original = self.image.copy()
        self.mask = None
        return self

    def remove_background(self, method: str = "auto") -> 'BackgroundRemover':
        """
        Xóa nền ảnh bằng phương pháp chỉ định.

        Args:
            method: Phương pháp sử dụng - "auto" | "edge" | "grabcut" | "color"
                - "auto": Tự động phát hiện phương pháp tốt nhất
                - "edge": Sử dụng phát hiện cạnh (Canny Edge Detection)
                - "grabcut": Sử dụng thuật toán GrabCut của OpenCV
                - "color": Tự động phát hiện màu nền và xóa

        Returns:
            self để hỗ trợ method chaining
        """
        if method == "auto":
            # Ưu tiên dùng AI nếu có
            if HAS_REMBG:
                method = "ai"
            else:
                method = self._detect_best_method()

        if method == "ai":
            return self.remove_ai()
        elif method == "edge":
            return self.remove_edges()
        elif method == "grabcut":
            return self.grabcut()
        elif method == "color":
            bg_color = self._detect_background_color()
            return self.remove_color(bg_color, tolerance=30)
        else:
            if HAS_REMBG:
                return self.remove_ai()
            return self.grabcut()

    def _detect_best_method(self) -> str:
        """
        Phát hiện phương pháp xóa nền tốt nhất dựa trên đặc điểm ảnh.

        Phân tích 4 góc ảnh: nếu màu tương đồng → nền đơn sắc → dùng "color",
        ngược lại → nền phức tạp → dùng "grabcut".

        Returns:
            Tên phương pháp: "color" hoặc "grabcut"
        """
        img_array = np.array(self.image.convert('RGB'))
        h, w = img_array.shape[:2]

        # Lấy mẫu màu từ 4 góc ảnh
        corners = [
            img_array[0, 0],
            img_array[0, w - 1],
            img_array[h - 1, 0],
            img_array[h - 1, w - 1]
        ]

        # Tính phương sai màu các góc - phương sai thấp = nền đơn sắc
        corner_variance = np.var([np.mean(c) for c in corners])

        if corner_variance < 100:
            return "color"
        else:
            return "grabcut"

    def _detect_background_color(self) -> Tuple[int, int, int]:
        """
        Phát hiện màu nền chủ đạo từ các cạnh (viền) của ảnh.

        Lấy mẫu pixel từ 4 cạnh ảnh, tính màu trung bình.

        Returns:
            Tuple (R, G, B) màu nền chủ đạo
        """
        img_array = np.array(self.image.convert('RGB'))
        h, w = img_array.shape[:2]

        # Thu thập pixel từ 4 cạnh ảnh
        edge_pixels = []
        edge_pixels.extend(img_array[0, :].tolist())      # Cạnh trên
        edge_pixels.extend(img_array[h - 1, :].tolist())   # Cạnh dưới
        edge_pixels.extend(img_array[:, 0].tolist())        # Cạnh trái
        edge_pixels.extend(img_array[:, w - 1].tolist())    # Cạnh phải

        # Tính màu trung bình
        edge_pixels = np.array(edge_pixels)
        mean_color = np.mean(edge_pixels, axis=0).astype(int)

        return tuple(mean_color)

    def remove_color(
        self,
        color: Tuple[int, int, int],
        tolerance: int = 20
    ) -> 'BackgroundRemover':
        """
        Xóa nền dựa trên màu sắc cụ thể.

        Tính khoảng cách Euclidean giữa mỗi pixel và màu mục tiêu.
        Pixel nào gần hơn ngưỡng tolerance sẽ bị xóa (transparent).

        Args:
            color: Tuple (R, G, B) màu cần xóa
            tolerance: Ngưỡng chấp nhận (0-255), cao hơn = xóa rộng hơn

        Returns:
            self để hỗ trợ method chaining

        Raises:
            ValueError: Nếu chưa tải ảnh
        """
        if self.image is None:
            raise ValueError("Chưa tải ảnh. Hãy gọi load() trước.")

        img_array = np.array(self.image.convert('RGB'))

        # Tính khoảng cách Euclidean từ mỗi pixel tới màu mục tiêu
        diff = np.abs(img_array.astype(int) - np.array(color))
        distance = np.sqrt(np.sum(diff ** 2, axis=2))

        # Tạo mask: pixel xa hơn tolerance = foreground (255), gần hơn = background (0)
        mask = (distance > tolerance * np.sqrt(3)).astype(np.uint8) * 255
        self.mask = Image.fromarray(mask, mode='L')

        # Áp dụng mask vào alpha channel
        self.image.putalpha(self.mask)

        return self

    def remove_edges(self, threshold: int = 50) -> 'BackgroundRemover':
        """
        Xóa nền bằng phát hiện cạnh (Canny Edge Detection).

        Quy trình: Grayscale → Canny → Dilate → Tìm contour lớn nhất → Fill mask.

        Args:
            threshold: Ngưỡng phát hiện cạnh (0-255)

        Returns:
            self để hỗ trợ method chaining

        Raises:
            ValueError: Nếu chưa tải ảnh
        """
        if self.image is None:
            raise ValueError("Chưa tải ảnh. Hãy gọi load() trước.")

        img_array = np.array(self.image.convert('RGB'))

        # Chuyển sang grayscale
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        # Phát hiện cạnh bằng Canny
        edges = cv2.Canny(gray, threshold, threshold * 2)

        # Mở rộng cạnh (dilate) để lấp khoảng trống
        kernel = np.ones((5, 5), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=2)

        # Tìm contour và lấp đầy contour lớn nhất
        contours, _ = cv2.findContours(
            dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        mask = np.zeros_like(gray)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            cv2.drawContours(mask, [largest], -1, 255, -1)

        self.mask = Image.fromarray(mask, mode='L')
        self.image.putalpha(self.mask)

        return self

    def grabcut(
        self,
        rect: Optional[Tuple[int, int, int, int]] = None,
        iterations: int = 5
    ) -> 'BackgroundRemover':
        """
        Xóa nền bằng thuật toán GrabCut (OpenCV).

        GrabCut sử dụng mô hình Gaussian Mixture để phân tách foreground/background.
        Hiệu quả với ảnh có nền phức tạp.

        Args:
            rect: Hình chữ nhật bao quanh foreground (x, y, width, height).
                  Nếu None, tự động dùng toàn bộ ảnh trừ margin 10px.
            iterations: Số lần lặp GrabCut (nhiều hơn = chính xác hơn nhưng chậm hơn)

        Returns:
            self để hỗ trợ method chaining

        Raises:
            ValueError: Nếu chưa tải ảnh
        """
        if self.image is None:
            raise ValueError("Chưa tải ảnh. Hãy gọi load() trước.")

        img_array = np.array(self.image.convert('RGB'))
        h, w = img_array.shape[:2]

        # Mặc định: dùng rectangle nhỏ hơn ảnh 10px mỗi cạnh
        if rect is None:
            margin = 10
            rect = (margin, margin, w - 2 * margin, h - 2 * margin)

        # Khởi tạo mask và model cho GrabCut
        mask = np.zeros((h, w), np.uint8)
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)

        # Chạy GrabCut
        cv2.grabCut(
            img_array, mask, rect, bgd_model, fgd_model,
            iterations, cv2.GC_INIT_WITH_RECT
        )

        # Tạo mask nhị phân: 0,2 = background → 0; 1,3 = foreground → 255
        mask2 = np.where((mask == 2) | (mask == 0), 0, 255).astype('uint8')

        self.mask = Image.fromarray(mask2, mode='L')
        self.image.putalpha(self.mask)

        return self

    def replace_background(
        self,
        color: Optional[Tuple[int, int, int]] = None,
        image: Optional[str] = None
    ) -> 'BackgroundRemover':
        """
        Thay nền trong suốt bằng màu sắc hoặc ảnh khác.

        Args:
            color: Tuple (R, G, B) cho nền đơn sắc
            image: Đường dẫn tới ảnh nền thay thế
            Nếu cả hai đều None → dùng nền trắng mặc định

        Returns:
            self để hỗ trợ method chaining

        Raises:
            ValueError: Nếu chưa tải ảnh
        """
        if self.image is None:
            raise ValueError("Chưa tải ảnh. Hãy gọi load() trước.")

        if self.image.mode != 'RGBA':
            self.image = self.image.convert('RGBA')

        w, h = self.image.size

        if image:
            # Dùng ảnh nền, resize cho vừa
            bg = Image.open(image).convert('RGB')
            bg = bg.resize((w, h), Image.Resampling.LANCZOS)
        elif color:
            # Dùng màu đơn sắc
            bg = Image.new('RGB', (w, h), color)
        else:
            # Mặc định: nền trắng
            bg = Image.new('RGB', (w, h), (255, 255, 255))

        # Composite foreground lên background mới
        bg.paste(self.image, (0, 0), self.image)
        self.image = bg.convert('RGBA')

        return self

    def add_shadow(
        self,
        offset: Tuple[int, int] = (5, 5),
        blur: int = 10,
        opacity: int = 128
    ) -> 'BackgroundRemover':
        """
        Thêm bóng đổ (drop shadow) cho chủ thể.

        Args:
            offset: Độ lệch bóng (x, y) tính bằng pixel
            blur: Bán kính làm mờ bóng
            opacity: Độ mờ đục của bóng (0-255)

        Returns:
            self để hỗ trợ method chaining
        """
        if self.image is None or self.mask is None:
            return self

        w, h = self.image.size

        # Tạo bóng từ mask
        shadow = self.mask.copy()
        shadow = shadow.filter(ImageFilter.GaussianBlur(blur))

        # Tạo layer bóng
        shadow_layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        shadow_rgba = Image.new('RGBA', (w, h), (0, 0, 0, opacity))
        shadow_layer.paste(shadow_rgba, offset, shadow)

        # Composite: background + shadow + subject
        result = Image.new('RGBA', (w, h), (255, 255, 255, 255))
        result = Image.alpha_composite(result, shadow_layer)
        result = Image.alpha_composite(result, self.image)

        self.image = result
        return self

    def refine_edges(self, feather: int = 2) -> 'BackgroundRemover':
        """
        Tinh chỉnh viền mask bằng feathering (làm mượt viền).

        Áp dụng Gaussian Blur lên mask để tạo chuyển tiếp mềm mại
        giữa foreground và background.

        Args:
            feather: Bán kính feather (pixel). Lớn hơn = mềm hơn.

        Returns:
            self để hỗ trợ method chaining
        """
        if self.mask is None:
            return self

        # Gaussian Blur mask để tạo feathering
        blurred_mask = self.mask.filter(ImageFilter.GaussianBlur(feather))

        # Cập nhật alpha channel
        if self.image.mode == 'RGBA':
            r, g, b, _ = self.image.split()
            self.image = Image.merge('RGBA', (r, g, b, blurred_mask))

        self.mask = blurred_mask
        return self

    def expand_mask(self, pixels: int = 2) -> 'BackgroundRemover':
        """
        Mở rộng mask thêm số pixel chỉ định (dilate).

        Hữu ích khi muốn giữ thêm vùng viền xung quanh chủ thể.

        Args:
            pixels: Số pixel mở rộng

        Returns:
            self để hỗ trợ method chaining
        """
        if self.mask is None:
            return self

        mask_array = np.array(self.mask)
        kernel = np.ones((pixels * 2 + 1, pixels * 2 + 1), np.uint8)
        expanded = cv2.dilate(mask_array, kernel, iterations=1)

        self.mask = Image.fromarray(expanded, mode='L')

        if self.image.mode == 'RGBA':
            r, g, b, _ = self.image.split()
            self.image = Image.merge('RGBA', (r, g, b, self.mask))

        return self

    def contract_mask(self, pixels: int = 2) -> 'BackgroundRemover':
        """
        Thu hẹp mask bớt số pixel chỉ định (erode).

        Hữu ích khi muốn cắt bớt viền thừa xung quanh chủ thể.

        Args:
            pixels: Số pixel thu hẹp

        Returns:
            self để hỗ trợ method chaining
        """
        if self.mask is None:
            return self

        mask_array = np.array(self.mask)
        kernel = np.ones((pixels * 2 + 1, pixels * 2 + 1), np.uint8)
        contracted = cv2.erode(mask_array, kernel, iterations=1)

        self.mask = Image.fromarray(contracted, mode='L')

        if self.image.mode == 'RGBA':
            r, g, b, _ = self.image.split()
            self.image = Image.merge('RGBA', (r, g, b, self.mask))

        return self

    def save(self, filepath: str, quality: int = 95) -> str:
        """
        Lưu ảnh đã xử lý ra file.

        Tự động xử lý format dựa trên extension:
        - PNG/WEBP: Giữ transparency (alpha channel)
        - JPEG: Chuyển sang RGB, nền trắng (không hỗ trợ alpha)

        Args:
            filepath: Đường dẫn file đầu ra
            quality: Chất lượng ảnh (1-100), chỉ ảnh hưởng JPEG/WEBP

        Returns:
            Đường dẫn file đã lưu

        Raises:
            ValueError: Nếu không có ảnh để lưu
        """
        if self.image is None:
            raise ValueError("Không có ảnh để lưu")

        # Tạo thư mục nếu chưa có
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        ext = Path(filepath).suffix.lower()

        if ext in ['.jpg', '.jpeg']:
            # JPEG không hỗ trợ alpha, chuyển sang RGB với nền trắng
            rgb_image = Image.new('RGB', self.image.size, (255, 255, 255))
            if self.image.mode == 'RGBA':
                rgb_image.paste(self.image, mask=self.image.split()[3])
            else:
                rgb_image.paste(self.image)
            rgb_image.save(filepath, quality=quality)
        else:
            self.image.save(filepath, quality=quality)

        return filepath

    def get_image(self) -> Optional[Image.Image]:
        """Lấy ảnh đã xử lý (PIL Image)."""
        return self.image

    def get_mask(self) -> Optional[Image.Image]:
        """Lấy mask hiện tại (PIL Image, mode L)."""
        return self.mask

    def batch_process(
        self,
        input_dir: str,
        output_dir: str,
        method: str = "auto",
        **kwargs
    ) -> List[str]:
        """
        Xử lý hàng loạt nhiều ảnh trong thư mục.

        Args:
            input_dir: Thư mục chứa ảnh đầu vào
            output_dir: Thư mục lưu ảnh kết quả
            method: Phương pháp xóa nền ("auto" | "color" | "edge" | "grabcut")
            **kwargs: Tham số bổ sung cho phương pháp:
                - color: Tuple (R,G,B) cho method "color"
                - tolerance: Ngưỡng tolerance (mặc định 30)
                - threshold: Ngưỡng edge detection (mặc định 50)
                - iterations: Số lần lặp GrabCut (mặc định 5)
                - feather: Bán kính feather (tùy chọn)

        Returns:
            List đường dẫn các file đã xử lý thành công
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        processed: List[str] = []
        extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}

        for img_file in input_path.iterdir():
            if img_file.suffix.lower() not in extensions:
                continue

            try:
                self.load(str(img_file))

                if method == "color" and 'color' in kwargs:
                    self.remove_color(kwargs['color'], kwargs.get('tolerance', 30))
                elif method == "grabcut":
                    self.grabcut(iterations=kwargs.get('iterations', 5))
                elif method == "edge":
                    self.remove_edges(threshold=kwargs.get('threshold', 50))
                else:
                    self.remove_background(method=method)

                # Tinh chỉnh feather nếu được chỉ định
                if kwargs.get('feather'):
                    self.refine_edges(kwargs['feather'])

                # Xuất PNG để giữ transparency
                output_file = output_path / f"{img_file.stem}_nobg.png"
                self.save(str(output_file))
                processed.append(str(output_file))

                print(f"Đã xử lý: {img_file.name}")

            except Exception as e:
                print(f"Lỗi khi xử lý {img_file.name}: {e}")

        return processed
        return processed

    def remove_ai(self, model_name: str = "u2net", alpha_threshold: int = 0,
                   use_alpha_matting: bool = False) -> 'BackgroundRemover':
        """
        Xóa nền sử dụng AI (rembg / U-2-Net).
        
        Đây là phương pháp mạnh mẽ và chính xác nhất cho đa số trường hợp.
        
        Args:
            model_name: Tên model AI:
                - "u2net": Model mặc định, cân bằng tốc độ/chất lượng.
                - "u2netp": Nhẹ hơn, nhanh hơn, ít chính xác hơn.
                - "u2net_human_seg": Tối ưu cho ảnh người.
                - "isnet-general-use": Chính xác cao, chậm hơn.
                - "isnet-anime": Tối ưu cho ảnh anime/clipart/cartoon.
                - "silueta": Nhẹ nhất, nhanh nhất.
            alpha_threshold: Ngưỡng Alpha (0-255). Pixel có alpha < threshold 
                sẽ thành trong suốt hoàn toàn. Giúp loại bỏ bóng mờ (shadow).
                0 = không lọc, 128 = lọc mạnh (khuyến nghị 30-100 cho bóng mờ).
            use_alpha_matting: Bật alpha matting để có viền mượt hơn.
                Tốt cho tóc, lông thú. Chậm hơn.
            
        Returns:
            self
            
        Raises:
            ValueError: Nếu chưa tải ảnh
            ImportError: Nếu chưa cài đặt rembg
        """
        if self.image is None:
            raise ValueError("Chưa tải ảnh. Hãy gọi load() trước.")
            
        if not HAS_REMBG:
            raise ImportError("Chưa cài đặt thư viện 'rembg'. Vui lòng cài đặt: pip install rembg")
        
        try:
            # Tạo session với model đã chọn
            session = rembg_session(model_name)
            
            # Xử lý với session và tùy chọn alpha matting
            result = rembg_remove(
                self.image,
                session=session,
                alpha_matting=use_alpha_matting,
                alpha_matting_foreground_threshold=240 if use_alpha_matting else 240,
                alpha_matting_background_threshold=20 if use_alpha_matting else 10,
            )
            
            # Cập nhật image
            self.image = result
            
            # Cập nhật mask (lấy alpha channel)
            self.mask = self.image.split()[3]
            
            # Post-processing: Loại bỏ bóng mờ bằng Alpha Threshold
            if alpha_threshold > 0:
                self._apply_alpha_threshold(alpha_threshold)
            
        except Exception as e:
            print(f"Lỗi AI removal (model={model_name}): {e}")
            # Fallback về grabcut nếu lỗi
            return self.grabcut()
            
        return self
    
    def _apply_alpha_threshold(self, threshold: int = 50) -> None:
        """
        Post-processing: Loại bỏ bóng mờ bằng cách threshold + morphological cleanup.
        
        Quy trình:
        1. Binary threshold: alpha < threshold → 0 (trong suốt hoàn toàn)
        2. Morphological open (erode→dilate): Xóa vệt bóng nhỏ, lông nhông
        3. Gaussian blur nhẹ trên viền: Tạo anti-alias mượt mà
        
        Args:
            threshold: Ngưỡng alpha (0-255). 
                30-80: bóng nhẹ, 80-150: bóng trung bình, 150+: bóng đậm
        """
        if self.mask is None:
            return
        
        # Convert mask sang numpy để xử lý nhanh
        mask_np = np.array(self.mask)
        
        # Bước 1: Binary threshold - loại bỏ pixel bóng mờ
        mask_np[mask_np < threshold] = 0
        
        # Bước 2: Morphological opening - xóa các vùng bóng nhỏ lẻ
        # Erode (thu nhỏ) để xóa vệt mỏng → Dilate (mở rộng) để phục hồi viền
        kernel_size = max(3, threshold // 25)  # Kernel lớn hơn cho threshold cao
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (kernel_size, kernel_size)
        )
        mask_np = cv2.morphologyEx(mask_np, cv2.MORPH_OPEN, kernel)
        
        # Bước 3: Làm mượt viền bằng Gaussian blur nhẹ
        # Chỉ blur vùng viền (edge), không blur toàn bộ mask
        edges = cv2.Canny(mask_np, 50, 150)
        edges_dilated = cv2.dilate(edges, None, iterations=2)
        
        blurred = cv2.GaussianBlur(mask_np, (5, 5), 1.0)
        # Chỉ áp blur vào vùng viền, giữ nguyên nội dung bên trong
        mask_np = np.where(edges_dilated > 0, blurred, mask_np)
        
        # Cập nhật mask và image
        self.mask = Image.fromarray(mask_np)
        self.image = self.original.copy()
        self.image.putalpha(self.mask)

    def apply_mask(self, mask_image: Image.Image) -> 'BackgroundRemover':
        """
        Áp dụng mask từ bên ngoài (ví dụ: từ brush tool).

        Args:
            mask_image: PIL Image (mode L hoặc RGBA) chứa mask mới.

        Returns:
            self
        """
        if self.image is None:
            raise ValueError("Chưa tải ảnh. Hãy gọi load() trước.")

        # Đảm bảo mask cùng kích thước
        if mask_image.size != self.image.size:
            mask_image = mask_image.resize(self.image.size, Image.Resampling.LANCZOS)

        # Chuyển sang mode L (Grayscale)
        # Xử lý mask dựa trên mode ảnh
        if mask_image.mode == 'RGBA':
            self.mask = mask_image.split()[3] # Lấy Alpha channel làm mask
        elif mask_image.mode == 'LA':
            self.mask = mask_image.split()[1]
        elif mask_image.mode != 'L':
            self.mask = mask_image.convert('L')
        else:
            self.mask = mask_image

        # Áp dụng mask vào alpha channel của ảnh hiện tại
        # Lưu ý: self.image có thể đã bị thay đổi (ví dụ replace background), 
        # nên tốt nhất là áp dụng vào self.original copy nếu muốn reset, 
        # nhưng ở đây ta muốn tinh chỉnh kết quả hiện tại.
        # Tuy nhiên, để chính xác, ta nên lấy original và áp dụng mask mới.
        
        self.image = self.original.copy()
        self.image.putalpha(self.mask)

        return self
