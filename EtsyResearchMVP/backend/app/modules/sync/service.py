"""Service đồng bộ shop và listings từ Etsy."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import EtsyConnection, Listing, ListingAttribute, ListingImage, ListingTag, Shop
from app.modules.etsy_auth.service import EtsyApiClient


def _parse_dt(value: str | None) -> datetime | None:
    """Parse datetime ISO nếu Etsy trả dạng chuỗi."""

    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def _clear_listing_children(db: Session, listing: Listing) -> None:
    """Xóa dữ liệu con cũ trước khi upsert mới."""

    db.query(ListingTag).filter(ListingTag.listing_id == listing.id).delete()
    db.query(ListingImage).filter(ListingImage.listing_id == listing.id).delete()
    db.query(ListingAttribute).filter(ListingAttribute.listing_id == listing.id).delete()


async def sync_connection_shops(
    db: Session,
    connection: EtsyConnection,
    client: EtsyApiClient,
) -> list[Shop]:
    """Sync các shop thuộc tài khoản vừa OAuth."""

    remote_shops = await client.get_self_shops()
    synced: list[Shop] = []
    for remote_shop in remote_shops:
        etsy_shop_id = int(remote_shop["shop_id"])
        shop = db.query(Shop).filter(Shop.etsy_shop_id == etsy_shop_id).one_or_none()
        if shop is None:
            shop = Shop(etsy_shop_id=etsy_shop_id, name=remote_shop["shop_name"])
            db.add(shop)
        shop.name = remote_shop["shop_name"]
        shop.currency_code = remote_shop.get("currency_code")
        shop.listing_active_count = int(remote_shop.get("active_listing_count", 0))
        shop.connection = connection
        synced.append(shop)
    db.flush()
    return synced


async def sync_shop_payload(db: Session, shop: Shop, client: EtsyApiClient) -> Shop:
    """Lấy thông tin shop mới nhất từ Etsy."""

    payload = await client.get_shop(shop.etsy_shop_id)
    shop.name = payload.get("shop_name") or payload.get("name") or shop.name
    shop.currency_code = payload.get("currency_code", shop.currency_code)
    shop.listing_active_count = int(payload.get("active_listing_count", shop.listing_active_count))
    shop.updated_at = datetime.now(UTC)
    db.flush()
    return shop


def _extract_attributes(products: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Chuẩn hóa products/inventory thành attributes lưu DB."""

    normalized: list[dict[str, Any]] = []
    for product in products:
        for prop in product.get("property_values", []):
            normalized.append(
                {
                    "property_id": prop.get("property_id"),
                    "property_name": prop.get("property_name"),
                    "values": [str(item) for item in prop.get("values", []) if item],
                }
            )
    return normalized


async def sync_shop_listings(db: Session, shop: Shop, client: EtsyApiClient) -> int:
    """Sync listings active và draft của shop."""

    total_synced = 0
    for state in ("active", "draft"):
        remote_listings = await client.get_shop_listings(shop.etsy_shop_id, state=state)
        for remote in remote_listings:
            listing = (
                db.query(Listing)
                .filter(Listing.etsy_listing_id == int(remote["listing_id"]))
                .one_or_none()
            )
            if listing is None:
                listing = Listing(
                    etsy_listing_id=int(remote["listing_id"]),
                    shop=shop,
                    title=remote.get("title") or "Listing chưa có tiêu đề",
                )
                db.add(listing)

            price_payload = remote.get("price")
            if isinstance(price_payload, dict) and price_payload.get("amount") is not None:
                price_amount = float(price_payload["amount"] / price_payload["divisor"])
                currency_code = price_payload.get("currency_code")
            else:
                price_amount = float(remote.get("price", 0) or 0)
                currency_code = remote.get("currency_code")

            listing.title = remote.get("title") or listing.title
            listing.description = remote.get("description") or ""
            listing.state = remote.get("state") or state
            listing.price_amount = price_amount
            listing.currency_code = currency_code
            listing.taxonomy_id = remote.get("taxonomy_id")
            listing.who_made = remote.get("who_made")
            listing.when_made = remote.get("when_made")
            listing.is_personalizable = bool(
                remote.get("is_personalizable") or remote.get("personalization_is_required")
            )
            listing.url = remote.get("url")
            listing.updated_at_etsy = _parse_dt(remote.get("updated_timestamp"))
            listing.synced_at = datetime.now(UTC)
            db.flush()

            _clear_listing_children(db, listing)

            for tag in remote.get("tags", []):
                db.add(ListingTag(listing=listing, tag=tag))

            for image_payload in await client.get_listing_images(listing.etsy_listing_id):
                db.add(
                    ListingImage(
                        listing=listing,
                        rank=int(image_payload.get("rank", 1)),
                        url_75x75=image_payload.get("url_75x75"),
                        url_fullxfull=image_payload.get("url_fullxfull"),
                        alt_text=image_payload.get("alt_text"),
                    )
                )

            inventory_payload = await client.get_listing_inventory(listing.etsy_listing_id)
            for normalized in _extract_attributes(inventory_payload.get("products", [])):
                db.add(
                    ListingAttribute(
                        listing=listing,
                        property_id=normalized["property_id"],
                        property_name=normalized["property_name"],
                        values_json=normalized["values"],
                    )
                )
            total_synced += 1

    if shop.connection:
        shop.connection.last_sync_at = datetime.now(UTC)
    db.flush()
    return total_synced
