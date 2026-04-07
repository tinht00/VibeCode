"""Tạo schema ban đầu cho Etsy Research MVP."""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "etsy_connections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("shop_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("shop_name", sa.String(length=255), nullable=False),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scope", sa.String(length=512), nullable=False),
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_sync_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(length=32), nullable=False),
    )

    op.create_table(
        "shops",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("etsy_shop_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("currency_code", sa.String(length=8)),
        sa.Column("listing_active_count", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("connection_id", sa.Integer(), sa.ForeignKey("etsy_connections.id", ondelete="SET NULL")),
    )

    op.create_table(
        "listings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("etsy_listing_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("shop_id", sa.Integer(), sa.ForeignKey("shops.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("price_amount", sa.Float()),
        sa.Column("currency_code", sa.String(length=8)),
        sa.Column("taxonomy_id", sa.Integer()),
        sa.Column("who_made", sa.String(length=64)),
        sa.Column("when_made", sa.String(length=64)),
        sa.Column("is_personalizable", sa.Boolean(), nullable=False),
        sa.Column("url", sa.String(length=512)),
        sa.Column("updated_at_etsy", sa.DateTime(timezone=True)),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "listing_tags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("listing_id", sa.Integer(), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tag", sa.String(length=64), nullable=False),
    )

    op.create_table(
        "listing_images",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("listing_id", sa.Integer(), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("url_75x75", sa.String(length=512)),
        sa.Column("url_fullxfull", sa.String(length=512)),
        sa.Column("alt_text", sa.String(length=255)),
    )

    op.create_table(
        "listing_attributes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("listing_id", sa.Integer(), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("property_id", sa.Integer()),
        sa.Column("property_name", sa.String(length=128)),
        sa.Column("values_json", sa.JSON(), nullable=False),
    )

    op.create_table(
        "taxonomy_nodes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("etsy_taxonomy_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("full_path", sa.String(length=512), nullable=False),
        sa.Column("parent_id", sa.Integer()),
    )

    op.create_table(
        "listing_audits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("listing_id", sa.Integer(), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        sa.Column("title_score", sa.Integer(), nullable=False),
        sa.Column("tag_score", sa.Integer(), nullable=False),
        sa.Column("taxonomy_score", sa.Integer(), nullable=False),
        sa.Column("attribute_score", sa.Integer(), nullable=False),
        sa.Column("description_score", sa.Integer(), nullable=False),
        sa.Column("image_score", sa.Integer(), nullable=False),
        sa.Column("price_score", sa.Integer(), nullable=False),
        sa.Column("findings_json", sa.JSON(), nullable=False),
        sa.Column("recommendations_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "benchmark_queries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("shop_id", sa.Integer(), sa.ForeignKey("shops.id", ondelete="CASCADE"), nullable=False),
        sa.Column("seed_keyword", sa.String(length=255), nullable=False),
        sa.Column("normalized_keyword", sa.String(length=255), nullable=False),
        sa.Column("last_captured_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "benchmark_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("benchmark_query_id", sa.Integer(), sa.ForeignKey("benchmark_queries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("listing_title", sa.String(length=255), nullable=False),
        sa.Column("listing_url", sa.String(length=512)),
        sa.Column("shop_name", sa.String(length=255)),
        sa.Column("price_amount", sa.Float()),
        sa.Column("currency_code", sa.String(length=8)),
        sa.Column("image_url", sa.String(length=512)),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("derived_terms_json", sa.JSON(), nullable=False),
    )

    op.create_table(
        "sync_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("shop_id", sa.Integer(), sa.ForeignKey("shops.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sync_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("summary_json", sa.JSON(), nullable=False),
        sa.Column("error_message", sa.Text()),
    )


def downgrade() -> None:
    op.drop_table("sync_runs")
    op.drop_table("benchmark_snapshots")
    op.drop_table("benchmark_queries")
    op.drop_table("listing_audits")
    op.drop_table("taxonomy_nodes")
    op.drop_table("listing_attributes")
    op.drop_table("listing_images")
    op.drop_table("listing_tags")
    op.drop_table("listings")
    op.drop_table("shops")
    op.drop_table("etsy_connections")
