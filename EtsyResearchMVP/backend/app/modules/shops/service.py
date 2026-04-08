"""Service cho shop và sync."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.db.models import EtsyConnection, Shop, SyncRun
from app.modules.etsy_auth.service import EtsyApiClient, EtsyApiError, get_client_for_connection


def list_shops(db: Session) -> list[Shop]:
    """Lấy danh sách shop đã kết nối."""

    return db.query(Shop).order_by(Shop.updated_at.desc()).all()


def get_shop_by_id(db: Session, shop_id: int) -> Shop | None:
    """Lấy shop nội bộ theo id."""

    return db.query(Shop).filter(Shop.id == shop_id).one_or_none()


def list_sync_runs(db: Session) -> list[SyncRun]:
    """Lấy lịch sử sync mới nhất."""

    return db.query(SyncRun).order_by(SyncRun.started_at.desc()).limit(50).all()


def start_sync_run(db: Session, shop: Shop, sync_type: str) -> SyncRun:
    """Tạo record sync run trước khi gọi Etsy."""

    run = SyncRun(shop=shop, sync_type=sync_type, status="running")
    db.add(run)
    db.flush()
    return run


def finish_sync_run(
    db: Session,
    run: SyncRun,
    *,
    status: str,
    summary: dict | None = None,
    error_message: str | None = None,
) -> None:
    """Đánh dấu sync run hoàn tất."""

    run.status = status
    run.summary_json = summary or {}
    run.error_message = error_message
    run.finished_at = datetime.now(UTC)
    db.flush()


def get_active_connection(db: Session, shop: Shop) -> EtsyConnection:
    """Lấy kết nối Etsy đang hoạt động của shop."""

    if shop.connection is None or shop.connection.status != "active":
        raise EtsyApiError("Shop chưa có kết nối Etsy hoạt động.")
    return shop.connection


def build_client_for_shop(db: Session, shop: Shop) -> EtsyApiClient:
    """Khởi tạo client Etsy từ shop."""

    connection = get_active_connection(db, shop)
    return get_client_for_connection(connection)
