"""Sinh CSV Pinterest và hỗ trợ mở luồng import content."""

from __future__ import annotations

import csv
import webbrowser
from pathlib import Path

from clipart_ops.domain.models import DriveAsset, ListingMetadata
from clipart_ops.services.workspace_service import WorkspaceService


class PinterestService:
    """Tạo CSV Pinterest từ metadata đã duyệt và drive assets hợp lệ."""

    HEADERS = [
        "Title",
        "Media URL",
        "Pinterest board",
        "Description",
        "Link",
        "Publish date",
        "Keywords",
    ]

    def __init__(self, workspace_service: WorkspaceService) -> None:
        self.workspace_service = workspace_service

    def build_csv(self, topic_root: Path) -> Path:
        payload = self.workspace_service.read_json(topic_root / "listing_metadata.json")
        metadata = ListingMetadata.model_validate(payload)
        if metadata.approved_candidate_rank is None:
            raise ValueError("Cần duyệt một candidate metadata trước khi tạo CSV Pinterest.")
        candidate = next(item for item in metadata.candidates if item.rank == metadata.approved_candidate_rank)
        assets_payload = self.workspace_service.read_json(topic_root / "drive_assets.json")
        assets = [
            DriveAsset.model_validate(item)
            for item in assets_payload.get("assets", [])
            if item.get("media_url_status") == "valid"
        ]
        if not assets:
            raise ValueError("Chưa có drive assets hợp lệ để tạo CSV Pinterest.")

        context = self.workspace_service.load_listing_context(topic_root)
        csv_path = topic_root / "pinterest_export.csv"
        with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(self.HEADERS)
            for asset in assets:
                writer.writerow(
                    [
                        candidate.pinterest_title,
                        asset.resolved_media_url,
                        context.board_name or topic_root.name,
                        candidate.pinterest_description,
                        context.etsy_listing_url,
                        "",
                        ", ".join(candidate.pinterest_keywords),
                    ]
                )
        return csv_path

    def open_import_content(self) -> None:
        webbrowser.open("https://www.pinterest.com/settings/import-content/")

    def mark_uploaded_to_ui(self, topic_root: Path) -> None:
        bundle = self.workspace_service.load_bundle_manifest(topic_root)
        bundle.notes.append("CSV đã được mở trong luồng upload Pinterest UI.")
        self.workspace_service.write_json(
            topic_root / "bundle.json",
            bundle.model_dump(mode="json"),
        )
