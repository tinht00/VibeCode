"""Schemas trả về cho listing."""

from datetime import datetime

from pydantic import BaseModel


class ListingSummaryResponse(BaseModel):
    """Dữ liệu tóm tắt listing cho bảng dashboard."""

    id: int
    etsy_listing_id: int
    shop_id: int
    title: str
    state: str
    price_amount: float | None
    currency_code: str | None
    taxonomy_id: int | None
    tag_count: int
    image_count: int
    attribute_count: int
    synced_at: datetime
    overall_score: int | None
    needs_attention: bool
    has_benchmark: bool


class ListingDetailResponse(BaseModel):
    """Dữ liệu chi tiết listing."""

    id: int
    etsy_listing_id: int
    shop_id: int
    title: str
    description: str
    state: str
    price_amount: float | None
    currency_code: str | None
    taxonomy_id: int | None
    who_made: str | None
    when_made: str | None
    is_personalizable: bool
    url: str | None
    synced_at: datetime
    tags: list[str]
    images: list[dict]
    attributes: list[dict]


class RecommendationResponse(BaseModel):
    """Gói recommendation cho listing."""

    listing_id: int
    overall_score: int | None
    recommendations: list[dict]
