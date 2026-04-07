"""Entry point FastAPI cho Etsy Research MVP."""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.base import Base
from app.db.models import ListingAudit
from app.db.session import engine, get_db
from app.modules.audits.service import run_listing_audit
from app.modules.benchmark.schemas import BenchmarkRequest
from app.modules.benchmark.service import create_benchmark_for_listing
from app.modules.etsy_auth.schemas import EtsyConnectionResponse, OAuthStartResponse
from app.modules.etsy_auth.service import EtsyApiClient, EtsyApiError, EtsyOAuthService, upsert_connection
from app.modules.listings.schemas import ListingDetailResponse, ListingSummaryResponse, RecommendationResponse
from app.modules.listings.service import build_recommendations, get_listing, has_benchmark, list_listings
from app.modules.shops.schemas import ShopResponse, SyncRunResponse
from app.modules.shops.service import build_client_for_shop, finish_sync_run, get_shop_by_id, list_shops, list_sync_runs, start_sync_run
from app.modules.sync.service import sync_connection_shops, sync_shop_listings, sync_shop_payload

setup_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Khởi tạo schema cục bộ khi chạy dev/test."""

    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Etsy Research MVP API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    """Endpoint health check."""

    return {"status": "ok", "service": "etsy-research-mvp-api"}


@app.get("/api/auth/etsy/start", response_model=OAuthStartResponse)
async def etsy_auth_start() -> OAuthStartResponse:
    """Tạo URL OAuth Etsy."""

    url, state = EtsyOAuthService().build_authorization_response()
    return OAuthStartResponse(authorization_url=url, state=state)


@app.get("/api/auth/etsy/callback", response_model=list[EtsyConnectionResponse])
async def etsy_auth_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db),
) -> list[EtsyConnectionResponse]:
    """Nhận callback OAuth và đồng bộ shop đầu tiên."""

    service = EtsyOAuthService()
    token_payload = await service.exchange_code_for_token(code=code, state=state)
    temp_client = EtsyApiClient(access_token=token_payload["access_token"])
    shops_payload = await temp_client.get_self_shops()
    responses: list[EtsyConnectionResponse] = []

    for remote_shop in shops_payload:
        connection = upsert_connection(
            db,
            shop_id=int(remote_shop["shop_id"]),
            shop_name=remote_shop["shop_name"],
            access_token=token_payload["access_token"],
            refresh_token=token_payload["refresh_token"],
            scope=token_payload.get("scope", settings.etsy_scopes),
            expires_in_seconds=int(token_payload.get("expires_in", 3600)),
        )
        synced_shops = await sync_connection_shops(db, connection, temp_client)
        for synced_shop in synced_shops:
            if synced_shop.etsy_shop_id == connection.shop_id:
                await sync_shop_payload(db, synced_shop, temp_client)
                await sync_shop_listings(db, synced_shop, temp_client)
        responses.append(
            EtsyConnectionResponse(
                shop_id=connection.shop_id,
                shop_name=connection.shop_name,
                scope=connection.scope,
                status=connection.status,
                connected_at=connection.connected_at,
                last_sync_at=connection.last_sync_at,
            )
        )
    db.commit()
    return responses


@app.get("/api/shops", response_model=list[ShopResponse])
async def shops(db: Session = Depends(get_db)) -> list[ShopResponse]:
    """Lấy danh sách shop đã kết nối."""

    return [
        ShopResponse(
            id=item.id,
            etsy_shop_id=item.etsy_shop_id,
            name=item.name,
            currency_code=item.currency_code,
            listing_active_count=item.listing_active_count,
            updated_at=item.updated_at,
            last_sync_at=item.connection.last_sync_at if item.connection else None,
        )
        for item in list_shops(db)
    ]


@app.get("/api/shops/{shop_id}", response_model=ShopResponse)
async def shop_detail(shop_id: int, db: Session = Depends(get_db)) -> ShopResponse:
    """Lấy chi tiết shop nội bộ."""

    item = get_shop_by_id(db, shop_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy shop.")
    return ShopResponse(
        id=item.id,
        etsy_shop_id=item.etsy_shop_id,
        name=item.name,
        currency_code=item.currency_code,
        listing_active_count=item.listing_active_count,
        updated_at=item.updated_at,
        last_sync_at=item.connection.last_sync_at if item.connection else None,
    )


@app.post("/api/shops/{shop_id}/sync")
async def sync_shop(shop_id: int, db: Session = Depends(get_db)) -> dict:
    """Đồng bộ shop và listings thủ công."""

    shop = get_shop_by_id(db, shop_id)
    if shop is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy shop.")
    run = start_sync_run(db, shop, sync_type="manual")
    try:
        client = build_client_for_shop(db, shop)
        await sync_shop_payload(db, shop, client)
        listing_count = await sync_shop_listings(db, shop, client)
        finish_sync_run(db, run, status="success", summary={"listing_count": listing_count})
        db.commit()
    except EtsyApiError as exc:
        finish_sync_run(db, run, status="failed", error_message=str(exc))
        db.commit()
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"message": "Đồng bộ shop thành công.", "sync_run_id": run.id}


@app.get("/api/listings", response_model=list[ListingSummaryResponse])
async def listings(
    shop_id: int | None = Query(default=None),
    state: str | None = Query(default=None),
    score_lt: int | None = Query(default=None),
    needs_attention: bool | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[ListingSummaryResponse]:
    """Lấy danh sách listing để hiển thị bảng dashboard."""

    items = list_listings(db, shop_id=shop_id, state=state, score_lt=score_lt, needs_attention=needs_attention)
    responses: list[ListingSummaryResponse] = []
    for item in items:
        latest_audit = (
            db.query(ListingAudit)
            .filter(ListingAudit.listing_id == item.id)
            .order_by(ListingAudit.created_at.desc())
            .first()
        )
        responses.append(
            ListingSummaryResponse(
                id=item.id,
                etsy_listing_id=item.etsy_listing_id,
                shop_id=item.shop_id,
                title=item.title,
                state=item.state,
                price_amount=item.price_amount,
                currency_code=item.currency_code,
                taxonomy_id=item.taxonomy_id,
                tag_count=len(item.tags),
                image_count=len(item.images),
                attribute_count=len(item.attributes),
                synced_at=item.synced_at,
                overall_score=latest_audit.overall_score if latest_audit else None,
                needs_attention=(latest_audit is None or latest_audit.overall_score < 70),
                has_benchmark=has_benchmark(db, item),
            )
        )
    return responses


@app.get("/api/listings/{listing_id}", response_model=ListingDetailResponse)
async def listing_detail(listing_id: int, db: Session = Depends(get_db)) -> ListingDetailResponse:
    """Lấy chi tiết một listing."""

    item = get_listing(db, listing_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy listing.")
    return ListingDetailResponse(
        id=item.id,
        etsy_listing_id=item.etsy_listing_id,
        shop_id=item.shop_id,
        title=item.title,
        description=item.description,
        state=item.state,
        price_amount=item.price_amount,
        currency_code=item.currency_code,
        taxonomy_id=item.taxonomy_id,
        who_made=item.who_made,
        when_made=item.when_made,
        is_personalizable=item.is_personalizable,
        url=item.url,
        synced_at=item.synced_at,
        tags=[tag.tag for tag in item.tags],
        images=[{"id": image.id, "rank": image.rank, "url_75x75": image.url_75x75, "url_fullxfull": image.url_fullxfull, "alt_text": image.alt_text} for image in item.images],
        attributes=[{"id": attr.id, "property_id": attr.property_id, "property_name": attr.property_name, "values_json": attr.values_json} for attr in item.attributes],
    )


@app.post("/api/listings/{listing_id}/audit")
async def audit_listing(listing_id: int, db: Session = Depends(get_db)) -> dict:
    """Chạy audit cho listing."""

    item = get_listing(db, listing_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy listing.")
    audit = run_listing_audit(db, item)
    db.commit()
    return {
        "listing_id": listing_id,
        "overall_score": audit.overall_score,
        "findings": audit.findings_json,
        "recommendations": audit.recommendations_json,
    }


@app.post("/api/listings/{listing_id}/benchmark")
async def benchmark_listing(
    listing_id: int,
    payload: BenchmarkRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Tạo benchmark theo seed keyword cho listing."""

    item = get_listing(db, listing_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy listing.")
    shop = get_shop_by_id(db, item.shop_id)
    if shop is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy shop của listing.")
    try:
        result = await create_benchmark_for_listing(
            db,
            listing=item,
            seed_keyword=payload.seed_keyword,
            client=build_client_for_shop(db, shop),
        )
        db.commit()
        return result
    except (ValueError, EtsyApiError) as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/listings/{listing_id}/recommendations", response_model=RecommendationResponse)
async def listing_recommendations(listing_id: int, db: Session = Depends(get_db)) -> RecommendationResponse:
    """Lấy recommendation mới nhất cho listing."""

    item = get_listing(db, listing_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy listing.")
    return RecommendationResponse(**build_recommendations(db, item))


@app.get("/api/sync-runs", response_model=list[SyncRunResponse])
async def sync_runs(db: Session = Depends(get_db)) -> list[SyncRunResponse]:
    """Lấy lịch sử sync gần nhất."""

    return [
        SyncRunResponse(
            id=item.id,
            shop_id=item.shop_id,
            sync_type=item.sync_type,
            status=item.status,
            started_at=item.started_at,
            finished_at=item.finished_at,
            summary_json=item.summary_json,
            error_message=item.error_message,
        )
        for item in list_sync_runs(db)
    ]
