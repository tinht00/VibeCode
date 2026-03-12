"""Mô hình dữ liệu cốt lõi cho workspace clipart."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PipelineStatus(str, Enum):
    """Các trạng thái pipeline chuẩn."""

    DRAFT = "draft"
    RAW_READY = "raw_ready"
    MASTER_READY = "master_ready"
    BUNDLE_READY = "bundle_ready"
    METADATA_READY = "metadata_ready"
    MARKETING_READY = "marketing_ready"
    DRIVE_READY = "drive_ready"
    PINTEREST_CSV_READY = "pinterest_csv_ready"
    PUBLISHED_PENDING = "published_pending"
    ERROR = "error"


class ArtifactType(str, Enum):
    """Loại file để filter trong explorer."""

    IMAGE = "image"
    CSV = "csv"
    MARKDOWN = "markdown"
    JSON = "json"
    OTHER = "other"


class TopicPaths(BaseModel):
    """Các đường dẫn chuẩn của một chủ đề."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    root: Path
    raw_ai: Path
    master: Path
    bundle_export: Path
    marketing_watermark: Path
    drive_sales: Path
    drive_marketing: Path
    metadata: Path


class TopicSummary(BaseModel):
    """Thông tin scan nhanh cho dashboard."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    slug: str
    root: Path
    paths: TopicPaths
    status: PipelineStatus = PipelineStatus.DRAFT
    raw_count: int = 0
    master_count: int = 0
    marketing_count: int = 0
    sample_images: list[Path] = Field(default_factory=list)
    etsy_listing_url: str = ""
    board_name: str = ""


class ListingContext(BaseModel):
    """Đầu vào để sinh metadata."""

    topic_name: str
    slug: str
    clipart_count: int
    style: list[str] = Field(default_factory=list)
    audience: list[str] = Field(default_factory=list)
    season: list[str] = Field(default_factory=list)
    product_type: str = "clipart bundle"
    language: str = "en-US"
    board_name: str = ""
    etsy_listing_url: str = ""


class CandidateScore(BaseModel):
    """Điểm chấm candidate metadata."""

    seo: int = 0
    policy_safety: int = 0
    clarity: int = 0


class MetadataCandidate(BaseModel):
    """Một candidate metadata Etsy/Pinterest."""

    rank: int
    etsy_title: str
    etsy_description: str
    etsy_tags: list[str]
    pinterest_title: str
    pinterest_description: str
    pinterest_keywords: list[str]
    scores: CandidateScore = Field(default_factory=CandidateScore)
    warnings: list[str] = Field(default_factory=list)


class ListingMetadata(BaseModel):
    """Tập candidate đã sinh cho một chủ đề."""

    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_mode: str = "manual_template"
    approved_candidate_rank: int | None = None
    candidates: list[MetadataCandidate] = Field(default_factory=list)


class DriveAsset(BaseModel):
    """Một file marketing đã upload lên Google Drive."""

    file_name: str
    local_path: str
    drive_file_id: str = ""
    web_view_link: str = ""
    web_content_link: str = ""
    resolved_media_url: str = ""
    media_url_status: str = "pending"
    mime_type: str = ""
    error: str = ""


class BundleManifest(BaseModel):
    """Thông tin bundle và trạng thái tổng hợp."""

    topic_name: str
    slug: str
    clipart_count: int
    status: PipelineStatus
    master_folder: str = "01_master"
    marketing_folder: str = "03_marketing_watermark"
    etsy_export_zip: str = ""
    drive_sales_folder: str = "04_drive_sales"
    drive_marketing_folder: str = "05_drive_marketing"
    etsy_listing_url: str = ""
    board_name: str = ""
    notes: list[str] = Field(default_factory=list)


class DirectoryEntry(BaseModel):
    """Một mục hiển thị trong explorer."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    path: Path
    is_dir: bool
    size: int = 0
    artifact_type: ArtifactType = ArtifactType.OTHER
    modified_at: datetime | None = None


class OperationRecord(BaseModel):
    """Log thao tác file để undo trong phiên hiện tại."""

    action: str
    source: str
    destination: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any] = Field(default_factory=dict)
