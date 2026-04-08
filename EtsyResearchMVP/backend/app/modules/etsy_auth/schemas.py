"""Schemas cho OAuth Etsy."""

from datetime import datetime

from pydantic import BaseModel


class OAuthStartResponse(BaseModel):
    """URL khởi tạo OAuth."""

    authorization_url: str
    state: str


class EtsyConnectionResponse(BaseModel):
    """Thông tin kết nối Etsy trả ra frontend."""

    shop_id: int
    shop_name: str
    scope: str
    status: str
    connected_at: datetime
    last_sync_at: datetime | None
