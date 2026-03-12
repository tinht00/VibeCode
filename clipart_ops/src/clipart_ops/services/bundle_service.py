"""Đóng gói bundle Etsy từ thư mục master."""

from __future__ import annotations

import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from clipart_ops.domain.models import BundleManifest, PipelineStatus
from clipart_ops.services.text_utils import slugify_text
from clipart_ops.services.workspace_service import WorkspaceService


class BundleService:
    """Tạo bundle Etsy và cập nhật manifest."""

    def __init__(self, workspace_service: WorkspaceService) -> None:
        self.workspace_service = workspace_service

    def create_bundle(self, topic_root: Path) -> BundleManifest:
        topic = self.workspace_service.scan_topic(topic_root)
        if topic.master_count < 30:
            raise ValueError("Cần ít nhất 30 ảnh trong 01_master để đóng gói Etsy.")

        export_root = topic.paths.bundle_export / topic.slug
        if export_root.exists():
            shutil.rmtree(export_root)
        export_root.mkdir(parents=True, exist_ok=True)

        images = self.workspace_service.find_images(topic.paths.master)
        for index, image in enumerate(images, start=1):
            new_name = f"{slugify_text(topic.name)}-{index:03d}{image.suffix.lower()}"
            shutil.copy2(image, export_root / new_name)

        zip_path = topic.paths.bundle_export / f"{slugify_text(topic.name)}-bundle.zip"
        with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as archive:
            for file_path in sorted(export_root.iterdir()):
                archive.write(file_path, arcname=file_path.name)

        bundle = self.workspace_service.load_bundle_manifest(topic_root)
        bundle.slug = slugify_text(topic.name)
        bundle.clipart_count = len(images)
        bundle.etsy_export_zip = str(zip_path.relative_to(topic_root))
        bundle.status = PipelineStatus.BUNDLE_READY
        self.workspace_service.write_json(
            topic_root / "bundle.json",
            bundle.model_dump(mode="json"),
        )
        return bundle
