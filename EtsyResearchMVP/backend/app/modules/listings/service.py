"""Service đọc dữ liệu listing và recommendation."""

from sqlalchemy.orm import Session

from app.db.models import BenchmarkQuery, Listing, ListingAudit


def list_listings(
    db: Session,
    *,
    shop_id: int | None = None,
    state: str | None = None,
    score_lt: int | None = None,
    needs_attention: bool | None = None,
) -> list[Listing]:
    """Lấy danh sách listing có lọc cơ bản."""

    query = db.query(Listing).order_by(Listing.synced_at.desc())
    if shop_id is not None:
        query = query.filter(Listing.shop_id == shop_id)
    if state:
        query = query.filter(Listing.state == state)
    items = query.all()
    if score_lt is not None:
        items = [
            item
            for item in items
            if _latest_audit(item) is not None and _latest_audit(item).overall_score < score_lt
        ]
    if needs_attention is not None:
        items = [item for item in items if _needs_attention(item) == needs_attention]
    return items


def get_listing(db: Session, listing_id: int) -> Listing | None:
    """Lấy listing nội bộ theo id."""

    return db.query(Listing).filter(Listing.id == listing_id).one_or_none()


def build_recommendations(db: Session, listing: Listing) -> dict:
    """Tổng hợp recommendation mới nhất của listing."""

    audit = (
        db.query(ListingAudit)
        .filter(ListingAudit.listing_id == listing.id)
        .order_by(ListingAudit.created_at.desc())
        .first()
    )
    return {
        "listing_id": listing.id,
        "overall_score": audit.overall_score if audit else None,
        "recommendations": audit.recommendations_json if audit else [],
    }


def _latest_audit(listing: Listing) -> ListingAudit | None:
    """Lấy audit mới nhất trong relationship đã load hoặc từ danh sách."""

    if not listing.audits:
        return None
    return sorted(listing.audits, key=lambda item: item.created_at, reverse=True)[0]


def _needs_attention(listing: Listing) -> bool:
    """Xác định listing có cần chú ý sớm không."""

    audit = _latest_audit(listing)
    if audit is None:
        return True
    return audit.overall_score < 70


def has_benchmark(db: Session, listing: Listing) -> bool:
    """Kiểm tra listing đã có benchmark chưa thông qua shop."""

    return db.query(BenchmarkQuery).filter(BenchmarkQuery.shop_id == listing.shop_id).count() > 0
