"""Service benchmark keyword."""

from __future__ import annotations

import re
from collections import Counter
from statistics import median

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import utc_now
from app.db.models import BenchmarkQuery, BenchmarkSnapshot, Listing
from app.modules.etsy_auth.service import EtsyApiClient

STOP_WORDS = {"the", "and", "for", "with", "gift", "etsy", "your", "from", "this", "that"}


def normalize_keyword(keyword: str) -> str:
    """Chuẩn hóa keyword người dùng nhập."""

    return re.sub(r"\s+", " ", keyword.strip().lower())


def extract_terms_from_titles(titles: list[str]) -> list[str]:
    """Rút ra cụm từ ngắn phổ biến từ tiêu đề benchmark."""

    counter: Counter[str] = Counter()
    for title in titles:
        words = [
            item
            for item in re.findall(r"[a-zA-Z0-9]+", title.lower())
            if len(item) > 2 and item not in STOP_WORDS
        ]
        counter.update(words)
    return [term for term, _ in counter.most_common(8)]


async def create_benchmark_for_listing(
    db: Session,
    *,
    listing: Listing,
    seed_keyword: str,
    client: EtsyApiClient,
) -> dict:
    """Tạo benchmark công khai cho listing theo keyword."""

    normalized = normalize_keyword(seed_keyword)
    if len(normalized) < settings.benchmark_min_keyword_length:
        raise ValueError("Keyword benchmark quá ngắn.")

    query = (
        db.query(BenchmarkQuery)
        .filter(
            BenchmarkQuery.shop_id == listing.shop_id,
            BenchmarkQuery.normalized_keyword == normalized,
        )
        .one_or_none()
    )
    if query is None:
        query = BenchmarkQuery(
            shop_id=listing.shop_id,
            seed_keyword=seed_keyword.strip(),
            normalized_keyword=normalized,
        )
        db.add(query)
        db.flush()

    db.query(BenchmarkSnapshot).filter(BenchmarkSnapshot.benchmark_query_id == query.id).delete()
    results = await client.search_active_listings(normalized)
    titles: list[str] = []
    prices: list[float] = []

    for result in results:
        price_payload = result.get("price") or {}
        price_amount = None
        if isinstance(price_payload, dict) and price_payload.get("amount") is not None:
            price_amount = float(price_payload["amount"] / price_payload["divisor"])
        elif result.get("price"):
            price_amount = float(result["price"])
        if price_amount is not None:
            prices.append(price_amount)
        titles.append(result.get("title") or "Không có tiêu đề")

    common_terms = extract_terms_from_titles(titles)

    for result in results:
        price_payload = result.get("price") or {}
        price_amount = None
        currency_code = result.get("currency_code")
        if isinstance(price_payload, dict) and price_payload.get("amount") is not None:
            price_amount = float(price_payload["amount"] / price_payload["divisor"])
            currency_code = price_payload.get("currency_code")
        elif result.get("price"):
            price_amount = float(result["price"])

        db.add(
            BenchmarkSnapshot(
                benchmark_query_id=query.id,
                listing_title=result.get("title") or "Không có tiêu đề",
                listing_url=result.get("url"),
                shop_name=result.get("shop_name"),
                price_amount=price_amount,
                currency_code=currency_code,
                image_url=result.get("MainImage", {}).get("url_fullxfull")
                if isinstance(result.get("MainImage"), dict)
                else result.get("image_url"),
                captured_at=utc_now(),
                derived_terms_json=common_terms,
            )
        )

    query.last_captured_at = utc_now()
    db.flush()
    return {
        "query_id": query.id,
        "seed_keyword": query.seed_keyword,
        "normalized_keyword": query.normalized_keyword,
        "snapshot_count": len(results),
        "median_price": median(prices) if prices else None,
        "common_terms": common_terms,
    }
