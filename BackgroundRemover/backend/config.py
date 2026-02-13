#!/usr/bin/env python3
"""
Config - Quản lý cấu hình tập trung cho ứng dụng.

Sử dụng biến môi trường và file .env để cấu hình.
Hỗ trợ phân biệt môi trường development và production.
"""

import os
from pathlib import Path
from typing import List


# === Đọc .env file nếu tồn tại ===
def _load_env_file() -> None:
    """
    Đọc file .env và nạp các biến môi trường.

    Chỉ nạp nếu biến chưa tồn tại (không ghi đè biến hệ thống).
    """
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return

    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Bỏ qua comment và dòng trống
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue

            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            # Chỉ nạp nếu biến chưa tồn tại trong môi trường
            if key not in os.environ:
                os.environ[key] = value


# Nạp .env khi import module
_load_env_file()


class Settings:
    """
    Cấu hình ứng dụng.

    Đọc giá trị từ biến môi trường, fallback về giá trị mặc định.

    Attributes:
        ENVIRONMENT: Môi trường chạy - "development" | "production"
        CORS_ORIGINS: Danh sách origins được phép gọi API
        SESSION_TTL_SECONDS: Thời gian sống session (giây)
        MAX_SESSIONS: Giới hạn tổng số session đồng thời
        LOG_LEVEL: Mức log - "DEBUG" | "INFO" | "WARNING" | "ERROR"
        HOST: Host lắng nghe
        PORT: Port lắng nghe
    """

    def __init__(self) -> None:
        """Khởi tạo Settings từ biến môi trường."""
        self.ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
        self.HOST: str = os.getenv("HOST", "0.0.0.0")
        self.PORT: int = int(os.getenv("PORT", "8000"))
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

        # CORS - Phân tách chuỗi bằng dấu phẩy
        cors_raw = os.getenv("CORS_ORIGINS", "http://localhost:5173")
        self.CORS_ORIGINS: List[str] = [
            origin.strip() for origin in cors_raw.split(",") if origin.strip()
        ]

        # Session
        self.SESSION_TTL_SECONDS: int = int(
            os.getenv("SESSION_TTL_SECONDS", "3600")
        )
        self.MAX_SESSIONS: int = int(os.getenv("MAX_SESSIONS", "100"))

    @property
    def is_development(self) -> bool:
        """Kiểm tra đang chạy môi trường development."""
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        """Kiểm tra đang chạy môi trường production."""
        return self.ENVIRONMENT == "production"


# Singleton instance - dùng chung cho toàn bộ ứng dụng
settings = Settings()
