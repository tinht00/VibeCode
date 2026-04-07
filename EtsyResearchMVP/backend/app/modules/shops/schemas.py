"""Schemas liên quan đến shop."""

from datetime import datetime

from pydantic import BaseModel


class ShopResponse(BaseModel):
    """Thông tin shop trả ra UI."""

    id: int
    etsy_shop_id: int
    name: str
    currency_code: str | None
    listing_active_count: int
    updated_at: datetime
    last_sync_at: datetime | None


class SyncRunResponse(BaseModel):
    """Thông tin lịch sử sync."""

    id: int
    shop_id: int
    sync_type: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    summary_json: dict
    error_message: str | None
