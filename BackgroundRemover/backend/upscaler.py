import os
import cv2
from cv2 import dnn_superres
import requests
from pathlib import Path
from PIL import Image
import numpy as np

class Upscaler:
    """
    Class xử lý nâng cấp độ phân giải ảnh (Super Resolution) sử dụng OpenCV DNN.
    Hỗ trợ các model: EDSR, ESPCN, FSRCNN, LapSRN.
    Mặc định sử dụng EDSR (x4) cho chất lượng tốt nhất.
    """
    
    MODELS_DIR = Path("models")
    MODELS_URL = {
        "EDSR_x4": "https://github.com/Saafke/EDSR_Tensorflow/raw/master/models/EDSR_x4.pb",
        "EDSR_x3": "https://github.com/Saafke/EDSR_Tensorflow/raw/master/models/EDSR_x3.pb",
        "ESPCN_x4": "https://github.com/fannymonori/TF-ESPCN/raw/master/export/ESPCN_x4.pb",
        "FSRCNN_x4": "https://github.com/Saafke/FSRCNN_Tensorflow/raw/master/models/FSRCNN_x4.pb"
    }

    def __init__(self, model_name="EDSR_x4", scale=4):
        self.model_name = model_name
        self.scale = scale
        self.upscaler = None
        self._initialize_model()

    def _initialize_model(self):
        """Khởi tạo model, tự động tải nếu chưa có."""
        self.MODELS_DIR.mkdir(exist_ok=True)
        model_path = self.MODELS_DIR / f"{self.model_name}.pb"

        if not model_path.exists():
            print(f"🔄 Đang tải model {self.model_name}...")
            url = self.MODELS_URL.get(self.model_name)
            if not url:
                raise ValueError(f"Không tìm thấy URL cho model {self.model_name}")
            
            response = requests.get(url, stream=True)
            with open(model_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✅ Đã tải model {self.model_name}")

        try:
            self.upscaler = dnn_superres.DnnSuperResImpl_create()
            self.upscaler.readModel(str(model_path))
            
            # Set model name và scale
            # Tên model trong OpenCV function phải khớp với tên file weight gốc
            model_type = self.model_name.split('_')[0].lower() # edsr, espcn...
            self.upscaler.setModel(model_type, self.scale)
            
            # Thử set backend là CUDA nếu có (tùy chọn)
            # self.upscaler.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
            # self.upscaler.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
            
        except Exception as e:
            print(f"❌ Lỗi khởi tạo Upscaler: {e}")
            self.upscaler = None

    def process(self, image: Image.Image) -> Image.Image:
        """
        Nâng cấp ảnh PIL Image.
        """
        if self.upscaler is None:
            # Fallback: Resize thông thường nếu model lỗi
            print("⚠️ Upscaler chưa init, dùng Lanczos resize.")
            new_size = (image.width * self.scale, image.height * self.scale)
            return image.resize(new_size, Image.Resampling.LANCZOS)

        # Convert PIL -> OpenCV (RGB -> BGR)
        img_np = np.array(image)
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR) if image.mode == 'RGBA' else cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        
        # Upscale
        result_bgr = self.upscaler.upsample(img_bgr)
        
        # Convert OpenCV -> PIL (BGR -> RGB)
        result_rgb = cv2.cvtColor(result_bgr, cv2.COLOR_BGR2RGB)
        result_pil = Image.fromarray(result_rgb)
        
        # Nếu ảnh gốc có alpha, cần resize alpha channel và merge lại
        if image.mode == 'RGBA':
            alpha = image.split()[3]
            new_size = result_pil.size
            alpha_resized = alpha.resize(new_size, Image.Resampling.LANCZOS)
            result_pil.putalpha(alpha_resized)
            
        return result_pil
