"""Service OAuth và client Etsy."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    decrypt_value,
    encrypt_value,
    expires_in,
    generate_code_challenge,
    generate_code_verifier,
    generate_state_token,
    utc_now,
)
from app.db.models import EtsyConnection, Shop

logger = logging.getLogger(__name__)


@dataclass
class OAuthStatePayload:
    """Dữ liệu tạm lưu cho vòng đời OAuth."""

    state: str
    verifier: str
    created_at_ts: float


class OAuthStateStore:
    """Kho state in-memory cho vòng OAuth nội bộ."""

    def __init__(self) -> None:
        self._values: dict[str, OAuthStatePayload] = {}

    def create(self) -> OAuthStatePayload:
        """Sinh state mới và lưu verifier tương ứng."""

        state = generate_state_token()
        payload = OAuthStatePayload(
            state=state,
            verifier=generate_code_verifier(),
            created_at_ts=utc_now().timestamp(),
        )
        self._values[state] = payload
        return payload

    def pop(self, state: str) -> OAuthStatePayload | None:
        """Lấy và xóa state đã lưu."""

        return self._values.pop(state, None)


oauth_state_store = OAuthStateStore()


class EtsyApiError(RuntimeError):
    """Lỗi khi gọi Etsy API."""


class EtsyOAuthService:
    """Service xây URL OAuth và đổi code lấy token."""

    def build_authorization_response(self) -> tuple[str, str]:
        """Tạo URL OAuth và state cho frontend."""

        payload = oauth_state_store.create()
        params = urlencode(
            {
                "response_type": "code",
                "client_id": settings.etsy_client_id or settings.etsy_api_key,
                "redirect_uri": settings.etsy_redirect_uri,
                "scope": settings.etsy_scopes,
                "state": payload.state,
                "code_challenge": generate_code_challenge(payload.verifier),
                "code_challenge_method": "S256",
            }
        )
        return f"{settings.etsy_auth_url}?{params}", payload.state

    async def exchange_code_for_token(self, code: str, state: str) -> dict[str, Any]:
        """Đổi auth code thành access token bằng PKCE."""

        payload = oauth_state_store.pop(state)
        if payload is None:
            raise EtsyApiError("State OAuth không hợp lệ hoặc đã hết hạn.")

        data = {
            "grant_type": "authorization_code",
            "client_id": settings.etsy_client_id or settings.etsy_api_key,
            "redirect_uri": settings.etsy_redirect_uri,
            "code": code,
            "code_verifier": payload.verifier,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(settings.etsy_token_url, data=data)
        if response.status_code >= 400:
            raise EtsyApiError(f"Không thể đổi code lấy token: {response.text}")
        return response.json()

    async def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        """Refresh access token khi hết hạn."""

        data = {
            "grant_type": "refresh_token",
            "client_id": settings.etsy_client_id or settings.etsy_api_key,
            "refresh_token": refresh_token,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(settings.etsy_token_url, data=data)
        if response.status_code >= 400:
            raise EtsyApiError(f"Không thể refresh token: {response.text}")
        return response.json()


class EtsyApiClient:
    """Client nhỏ để gọi Etsy Open API."""

    def __init__(self, access_token: str) -> None:
        self._access_token = access_token

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "x-api-key": settings.etsy_api_key or settings.etsy_client_id,
        }

    async def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Gọi GET tới Etsy API."""

        url = f"{settings.etsy_api_base.rstrip('/')}/{path.lstrip('/')}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params, headers=self._headers)
        if response.status_code >= 400:
            logger.error(
                "Lỗi Etsy API",
                extra={
                    "status_code": response.status_code,
                    "endpoint": path,
                    "request_id": response.headers.get("x-request-id"),
                },
            )
            raise EtsyApiError(f"Gọi Etsy API thất bại tại {path}: {response.text}")
        return response.json()

    async def get_self_shops(self) -> list[dict[str, Any]]:
        """Lấy các shop của tài khoản đang đăng nhập."""

        payload = await self.get("/users/__SELF__/shops")
        return payload.get("results", [])

    async def get_shop(self, shop_id: int) -> dict[str, Any]:
        """Lấy thông tin chi tiết shop."""

        payload = await self.get(f"/shops/{shop_id}")
        results = payload.get("results")
        return results[0] if results else payload

    async def get_shop_listings(self, shop_id: int, state: str = "active") -> list[dict[str, Any]]:
        """Lấy listings của shop theo trạng thái."""

        payload = await self.get(f"/shops/{shop_id}/listings/{state}")
        return payload.get("results", [])

    async def get_listing_images(self, listing_id: int) -> list[dict[str, Any]]:
        """Lấy ảnh của listing."""

        payload = await self.get(f"/listings/{listing_id}/images")
        return payload.get("results", [])

    async def get_listing_inventory(self, listing_id: int) -> dict[str, Any]:
        """Lấy inventory của listing."""

        return await self.get(f"/listings/{listing_id}/inventory")

    async def search_active_listings(self, keywords: str, limit: int = 12) -> list[dict[str, Any]]:
        """Tìm listings công khai theo keyword cho benchmark."""

        payload = await self.get("/listings/active", params={"keywords": keywords, "limit": limit})
        return payload.get("results", [])


def upsert_connection(
    db: Session,
    *,
    shop_id: int,
    shop_name: str,
    access_token: str,
    refresh_token: str,
    scope: str,
    expires_in_seconds: int,
) -> EtsyConnection:
    """Tạo hoặc cập nhật kết nối Etsy trong DB."""

    connection = db.query(EtsyConnection).filter(EtsyConnection.shop_id == shop_id).one_or_none()
    if connection is None:
        connection = EtsyConnection(
            shop_id=shop_id,
            shop_name=shop_name,
            access_token_encrypted=encrypt_value(access_token),
            refresh_token_encrypted=encrypt_value(refresh_token),
            expires_at=expires_in(expires_in_seconds),
            scope=scope,
            status="active",
        )
        db.add(connection)
    else:
        connection.shop_name = shop_name
        connection.access_token_encrypted = encrypt_value(access_token)
        connection.refresh_token_encrypted = encrypt_value(refresh_token)
        connection.expires_at = expires_in(expires_in_seconds)
        connection.scope = scope
        connection.status = "active"

    shop = db.query(Shop).filter(Shop.etsy_shop_id == shop_id).one_or_none()
    if shop is None:
        shop = Shop(
            etsy_shop_id=shop_id,
            name=shop_name,
            connection=connection,
        )
        db.add(shop)
    else:
        shop.name = shop_name
        shop.connection = connection

    db.flush()
    return connection


def get_client_for_connection(connection: EtsyConnection) -> EtsyApiClient:
    """Khởi tạo EtsyApiClient từ kết nối đã lưu."""

    return EtsyApiClient(access_token=decrypt_value(connection.access_token_encrypted))
