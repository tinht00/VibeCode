"""Cấu hình ứng dụng backend."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Tập hợp cấu hình ứng dụng."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Etsy Research MVP API"
    environment: Literal["development", "test", "production"] = "development"
    app_base_url: str = "http://localhost:5173"
    api_base_url: str = "http://localhost:8000"
    app_secret_key: str = Field(
        default="dev-secret-key-please-change",
        description="Secret nội bộ để ký state và dẫn xuất khóa mã hóa mặc định.",
    )
    app_encryption_key: str | None = Field(
        default=None,
        description="Khóa Fernet dạng base64 để mã hóa token Etsy.",
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173"],
        description="Danh sách origin được phép gọi API.",
    )
    postgres_url: str = "sqlite:///./etsy_research_mvp.db"
    etsy_api_key: str = ""
    etsy_client_id: str = ""
    etsy_redirect_uri: str = "http://localhost:8000/api/auth/etsy/callback"
    etsy_scopes: str = "shops_r listings_r transactions_r"
    etsy_auth_url: str = "https://www.etsy.com/oauth/connect"
    etsy_token_url: str = "https://api.etsy.com/v3/public/oauth/token"
    etsy_api_base: str = "https://openapi.etsy.com/v3/application"
    sync_interval_hours: int = 6
    min_listing_images: int = 5
    benchmark_min_keyword_length: int = 3


@lru_cache
def get_settings() -> Settings:
    """Trả về singleton cấu hình ứng dụng."""

    return Settings()


settings = get_settings()
