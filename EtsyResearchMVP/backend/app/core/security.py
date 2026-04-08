"""Hàm hỗ trợ mã hóa, PKCE và state."""

import base64
import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def _derive_fernet_key() -> bytes:
    """Dẫn xuất khóa Fernet ổn định từ secret ứng dụng nếu chưa cấu hình riêng."""

    if settings.app_encryption_key:
        return settings.app_encryption_key.encode("utf-8")

    digest = hashlib.sha256(settings.app_secret_key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def get_cipher() -> Fernet:
    """Trả về cipher dùng để mã hóa token Etsy."""

    return Fernet(_derive_fernet_key())


def encrypt_value(value: str) -> str:
    """Mã hóa chuỗi nhạy cảm trước khi lưu DB."""

    return get_cipher().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_value(value: str) -> str:
    """Giải mã chuỗi nhạy cảm từ DB."""

    try:
        return get_cipher().decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Không thể giải mã dữ liệu nhạy cảm.") from exc


def generate_state_token() -> str:
    """Sinh state token ngẫu nhiên cho OAuth."""

    return secrets.token_urlsafe(32)


def generate_code_verifier() -> str:
    """Sinh code verifier theo chuẩn PKCE."""

    return secrets.token_urlsafe(64)


def generate_code_challenge(verifier: str) -> str:
    """Sinh code challenge từ verifier."""

    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")


def utc_now() -> datetime:
    """Trả về thời gian hiện tại theo UTC."""

    return datetime.now(UTC)


def expires_in(seconds: int) -> datetime:
    """Trả về thời điểm hết hạn dựa trên số giây."""

    return utc_now() + timedelta(seconds=seconds)
