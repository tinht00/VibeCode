"""SQLAlchemy models cho Etsy Research MVP."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.core.security import utc_now
from app.db.base import Base


class EtsyConnection(Base):
    """Kết nối OAuth với shop Etsy."""

    __tablename__ = "etsy_connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shop_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    shop_name: Mapped[str] = mapped_column(String(255), nullable=False)
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scope: Mapped[str] = mapped_column(String(512), nullable=False)
    connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)

    shop: Mapped["Shop"] = relationship(back_populates="connection")


class Shop(Base):
    """Thông tin shop được đồng bộ."""

    __tablename__ = "shops"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    etsy_shop_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    currency_code: Mapped[str | None] = mapped_column(String(8))
    listing_active_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    connection_id: Mapped[int | None] = mapped_column(
        ForeignKey("etsy_connections.id", ondelete="SET NULL")
    )

    connection: Mapped[EtsyConnection | None] = relationship(back_populates="shop")
    listings: Mapped[list["Listing"]] = relationship(back_populates="shop")
    benchmark_queries: Mapped[list["BenchmarkQuery"]] = relationship(back_populates="shop")
    sync_runs: Mapped[list["SyncRun"]] = relationship(back_populates="shop")


class Listing(Base):
    """Listing của shop Etsy."""

    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    etsy_listing_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    state: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    price_amount: Mapped[float | None] = mapped_column(Float)
    currency_code: Mapped[str | None] = mapped_column(String(8))
    taxonomy_id: Mapped[int | None] = mapped_column(Integer)
    who_made: Mapped[str | None] = mapped_column(String(64))
    when_made: Mapped[str | None] = mapped_column(String(64))
    is_personalizable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    url: Mapped[str | None] = mapped_column(String(512))
    updated_at_etsy: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    shop: Mapped[Shop] = relationship(back_populates="listings")
    tags: Mapped[list["ListingTag"]] = relationship(back_populates="listing")
    images: Mapped[list["ListingImage"]] = relationship(back_populates="listing")
    attributes: Mapped[list["ListingAttribute"]] = relationship(back_populates="listing")
    audits: Mapped[list["ListingAudit"]] = relationship(back_populates="listing")


class ListingTag(Base):
    """Tag của listing."""

    __tablename__ = "listing_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"))
    tag: Mapped[str] = mapped_column(String(64), nullable=False)

    listing: Mapped[Listing] = relationship(back_populates="tags")


class ListingImage(Base):
    """Thông tin ảnh của listing."""

    __tablename__ = "listing_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"))
    rank: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    url_75x75: Mapped[str | None] = mapped_column(String(512))
    url_fullxfull: Mapped[str | None] = mapped_column(String(512))
    alt_text: Mapped[str | None] = mapped_column(String(255))

    listing: Mapped[Listing] = relationship(back_populates="images")


class ListingAttribute(Base):
    """Thuộc tính khai báo theo taxonomy."""

    __tablename__ = "listing_attributes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"))
    property_id: Mapped[int | None] = mapped_column(Integer)
    property_name: Mapped[str | None] = mapped_column(String(128))
    values_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    listing: Mapped[Listing] = relationship(back_populates="attributes")


class TaxonomyNode(Base):
    """Node taxonomy của Etsy."""

    __tablename__ = "taxonomy_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    etsy_taxonomy_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_path: Mapped[str] = mapped_column(String(512), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(Integer)


class ListingAudit(Base):
    """Kết quả audit listing."""

    __tablename__ = "listing_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"))
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    title_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tag_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    taxonomy_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    attribute_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    description_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    image_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    price_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    findings_json: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    recommendations_json: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    listing: Mapped[Listing] = relationship(back_populates="audits")


class BenchmarkQuery(Base):
    """Từ khóa benchmark theo từng shop."""

    __tablename__ = "benchmark_queries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id", ondelete="CASCADE"))
    seed_keyword: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_keyword: Mapped[str] = mapped_column(String(255), nullable=False)
    last_captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    shop: Mapped[Shop] = relationship(back_populates="benchmark_queries")
    snapshots: Mapped[list["BenchmarkSnapshot"]] = relationship(back_populates="query")


class BenchmarkSnapshot(Base):
    """Snapshot benchmark cho một keyword."""

    __tablename__ = "benchmark_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    benchmark_query_id: Mapped[int] = mapped_column(
        ForeignKey("benchmark_queries.id", ondelete="CASCADE")
    )
    listing_title: Mapped[str] = mapped_column(String(255), nullable=False)
    listing_url: Mapped[str | None] = mapped_column(String(512))
    shop_name: Mapped[str | None] = mapped_column(String(255))
    price_amount: Mapped[float | None] = mapped_column(Float)
    currency_code: Mapped[str | None] = mapped_column(String(8))
    image_url: Mapped[str | None] = mapped_column(String(512))
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    derived_terms_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    query: Mapped[BenchmarkQuery] = relationship(back_populates="snapshots")


class SyncRun(Base):
    """Lịch sử chạy đồng bộ."""

    __tablename__ = "sync_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id", ondelete="CASCADE"))
    sync_type: Mapped[str] = mapped_column(String(32), default="manual", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    summary_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)

    shop: Mapped[Shop] = relationship(back_populates="sync_runs")
