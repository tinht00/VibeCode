"""Chuẩn bị metadata Etsy/Pinterest theo mẫu nội bộ để chỉnh tiếp bằng AI ngoài."""

from __future__ import annotations

from pathlib import Path

from clipart_ops.domain.models import ListingContext, ListingMetadata, MetadataCandidate
from clipart_ops.services.validators import score_candidate
from clipart_ops.services.workspace_service import WorkspaceService


class MetadataService:
    """Tạo candidate metadata mẫu và xuất file Markdown/JSON."""

    def __init__(self, workspace_service: WorkspaceService) -> None:
        self.workspace_service = workspace_service

    def generate_for_topic(self, topic_root: Path) -> ListingMetadata:
        context = self.workspace_service.load_listing_context(topic_root)
        metadata = self._generate_template_candidates(context)
        metadata.source_mode = "manual_template"
        self.workspace_service.write_json(
            topic_root / "listing_metadata.json",
            metadata.model_dump(mode="json"),
        )
        return metadata

    def approve_candidate(self, topic_root: Path, rank: int) -> ListingMetadata:
        payload = self.workspace_service.read_json(topic_root / "listing_metadata.json")
        metadata = ListingMetadata.model_validate(payload)
        metadata.approved_candidate_rank = rank
        candidate = next(item for item in metadata.candidates if item.rank == rank)
        self.workspace_service.write_json(
            topic_root / "listing_metadata.json",
            metadata.model_dump(mode="json"),
        )
        self.workspace_service.write_text(
            topic_root / "etsy_listing_copy.md",
            self._render_etsy_markdown(candidate),
        )
        self.workspace_service.write_text(
            topic_root / "pinterest_copy.md",
            self._render_pinterest_markdown(candidate),
        )
        return metadata

    def _generate_template_candidates(self, context: ListingContext) -> ListingMetadata:
        base_keywords = [context.topic_name, *context.style, *context.season, *context.audience]
        deduped = [item for item in dict.fromkeys([item.strip() for item in base_keywords if item.strip()])]
        keyword_blob = ", ".join(deduped[:6]) or context.topic_name
        warning = (
            "Đây là khung metadata nội bộ của app. Bạn có thể sửa trực tiếp hoặc thay thế bằng nội dung từ Codex/AI ngoài trước khi dùng."
        )
        templates = [
            {
                "etsy_title": f"{context.topic_name} Clipart Bundle PNG, {context.clipart_count} Watercolor Elements for Crafts",
                "etsy_description": (
                    f"This {context.topic_name.lower()} clipart bundle includes {context.clipart_count} PNG files. "
                    f"Designed for crafters, planners, sublimation and small business projects. "
                    f"Style notes: {keyword_blob}."
                ),
                "etsy_tags": deduped[:13] or [context.topic_name, "clipart bundle", "png"],
                "pinterest_title": f"{context.topic_name} clipart bundle ideas for creative projects",
                "pinterest_description": (
                    f"Explore {context.topic_name.lower()} clipart with {context.clipart_count} high-quality PNG elements "
                    f"for planners, printables and handmade branding."
                ),
                "pinterest_keywords": deduped[:10] or [context.topic_name, "clipart", "png"],
            },
            {
                "etsy_title": f"{context.topic_name} PNG Set for Etsy Sellers, Printable Clipart Pack",
                "etsy_description": (
                    f"Premium {context.topic_name.lower()} clipart set with {context.clipart_count} transparent PNG files. "
                    f"Suitable for digital products, invitation design and creative business use."
                ),
                "etsy_tags": (deduped + ["transparent png", "etsy seller", "digital download"])[:13],
                "pinterest_title": f"{context.topic_name} PNG bundle for planners and printable shops",
                "pinterest_description": (
                    f"Save this {context.topic_name.lower()} PNG bundle for your next printable, planner or product mockup."
                ),
                "pinterest_keywords": (deduped + ["printable design", "planner clipart"])[:10],
            },
            {
                "etsy_title": f"{context.topic_name} Watercolor PNG Bundle for Printables and Branding",
                "etsy_description": (
                    f"A curated bundle of {context.clipart_count} {context.topic_name.lower()} PNG illustrations. "
                    f"Ideal for stickers, planners, branding and social media creatives."
                ),
                "etsy_tags": (deduped + ["branding kit", "watercolor png", "sticker design"])[:13],
                "pinterest_title": f"{context.topic_name} watercolor PNG set for branding and stickers",
                "pinterest_description": (
                    f"Use this {context.topic_name.lower()} watercolor clipart bundle to create stickers, planners and branded content."
                ),
                "pinterest_keywords": (deduped + ["sticker bundle", "branding elements"])[:10],
            },
        ]
        candidates = [
            score_candidate(
                MetadataCandidate(
                    rank=index,
                    etsy_title=item["etsy_title"],
                    etsy_description=item["etsy_description"],
                    etsy_tags=item["etsy_tags"],
                    pinterest_title=item["pinterest_title"],
                    pinterest_description=item["pinterest_description"],
                    pinterest_keywords=item["pinterest_keywords"],
                    warnings=[warning],
                )
            )
            for index, item in enumerate(templates, start=1)
        ]
        return ListingMetadata(candidates=candidates)

    def _render_etsy_markdown(self, candidate: MetadataCandidate) -> str:
        tags = ", ".join(candidate.etsy_tags)
        return (
            "# Etsy Metadata\n\n"
            f"## Title\n{candidate.etsy_title}\n\n"
            f"## Description\n{candidate.etsy_description}\n\n"
            f"## Tags\n{tags}\n"
        )

    def _render_pinterest_markdown(self, candidate: MetadataCandidate) -> str:
        keywords = ", ".join(candidate.pinterest_keywords)
        return (
            "# Pinterest Metadata\n\n"
            f"## Title\n{candidate.pinterest_title}\n\n"
            f"## Description\n{candidate.pinterest_description}\n\n"
            f"## Keywords\n{keywords}\n"
        )
