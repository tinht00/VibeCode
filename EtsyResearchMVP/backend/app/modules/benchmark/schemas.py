"""Schemas cho benchmark keyword."""

from pydantic import BaseModel, Field


class BenchmarkRequest(BaseModel):
    """Payload tạo benchmark cho listing."""

    seed_keyword: str = Field(min_length=3, max_length=255)


class BenchmarkResponse(BaseModel):
    """Kết quả benchmark trả ra UI."""

    query_id: int
    seed_keyword: str
    normalized_keyword: str
    snapshot_count: int
    median_price: float | None
    common_terms: list[str]
