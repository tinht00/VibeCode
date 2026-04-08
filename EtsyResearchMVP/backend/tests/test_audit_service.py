"""Kiểm thử audit service."""

from app.db.models import Listing, ListingAttribute, ListingImage, ListingTag, Shop
from app.modules.audits.service import run_listing_audit


def test_run_listing_audit_generates_findings(db_session) -> None:
    """Audit phải tạo findings khi listing còn yếu."""

    shop = Shop(etsy_shop_id=1, name="Shop test", listing_active_count=1)
    listing = Listing(
        etsy_listing_id=99,
        shop=shop,
        title="Mug",
        description="Ngắn",
        state="active",
        price_amount=10.0,
    )
    listing.tags = [ListingTag(tag="mug"), ListingTag(tag="mug")]
    listing.images = [ListingImage(rank=1)]
    listing.attributes = [ListingAttribute(property_name="material", values_json=["ceramic"])]
    db_session.add_all([shop, listing])
    db_session.flush()

    audit = run_listing_audit(db_session, listing)

    assert audit.overall_score < 100
    assert any(item["code"] == "TOO_FEW_TAGS" for item in audit.findings_json)
    assert any(item["code"] == "LOW_IMAGE_COUNT" for item in audit.findings_json)
