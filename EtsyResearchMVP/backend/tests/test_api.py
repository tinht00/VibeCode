"""Kiểm thử API mức cơ bản."""

import pytest

from app.db.models import Listing, ListingTag, Shop


@pytest.mark.anyio
async def test_health_endpoint(client) -> None:
    """Health endpoint phải trả trạng thái ok."""

    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.anyio
async def test_listing_endpoints(client, db_session) -> None:
    """API listing phải trả được dữ liệu cơ bản."""

    shop = Shop(etsy_shop_id=10, name="Shop API", listing_active_count=1)
    listing = Listing(
        etsy_listing_id=12345,
        shop=shop,
        title="Teacher appreciation mug",
        description="Mô tả thử nghiệm cho listing",
        state="active",
        price_amount=19.99,
    )
    listing.tags = [ListingTag(tag="teacher mug"), ListingTag(tag="gift for teacher")]
    db_session.add_all([shop, listing])
    db_session.commit()

    list_response = await client.get("/api/listings")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    detail_response = await client.get(f"/api/listings/{listing.id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["title"] == "Teacher appreciation mug"

    audit_response = await client.post(f"/api/listings/{listing.id}/audit")
    assert audit_response.status_code == 200
    assert "overall_score" in audit_response.json()
