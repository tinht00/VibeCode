"""Nghiệp vụ scan workspace và quản lý file local."""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from clipart_ops.data.settings_store import SettingsStore
from clipart_ops.domain.models import (
    ArtifactType,
    BundleManifest,
    DirectoryEntry,
    ListingContext,
    PipelineStatus,
    TopicPaths,
    TopicSummary,
)
from clipart_ops.services.text_utils import slugify_text

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
TEXT_SUFFIXES = {".md", ".txt"}
CSV_SUFFIXES = {".csv"}
JSON_SUFFIXES = {".json"}


class WorkspaceService:
    """Cung cấp các thao tác local cho workspace và chủ đề."""

    STANDARD_FOLDERS = (
        "00_raw_ai",
        "01_master",
        "02_bundle_export",
        "03_marketing_watermark",
        "04_drive_sales",
        "05_drive_marketing",
        "06_metadata",
    )

    def __init__(self, settings_store: SettingsStore) -> None:
        self.settings_store = settings_store
        self.workspace_root: Path | None = None

    def set_workspace_root(self, root: Path) -> None:
        root.mkdir(parents=True, exist_ok=True)
        self.workspace_root = root
        self.settings_store.set_value("workspace_root", str(root))
        self.settings_store.add_recent_workspace(root)
        (root / ".clipart_ops_trash").mkdir(exist_ok=True)

    def get_workspace_root(self) -> Path | None:
        if self.workspace_root:
            return self.workspace_root
        stored = self.settings_store.get_value("workspace_root")
        if stored:
            path = Path(stored)
            if path.exists():
                self.workspace_root = path
        return self.workspace_root

    def ensure_topic_structure(self, topic_root: Path) -> TopicPaths:
        topic_root.mkdir(parents=True, exist_ok=True)
        for folder_name in self.STANDARD_FOLDERS:
            (topic_root / folder_name).mkdir(exist_ok=True)
        return self.build_topic_paths(topic_root)

    def build_topic_paths(self, topic_root: Path) -> TopicPaths:
        return TopicPaths(
            root=topic_root,
            raw_ai=topic_root / "00_raw_ai",
            master=topic_root / "01_master",
            bundle_export=topic_root / "02_bundle_export",
            marketing_watermark=topic_root / "03_marketing_watermark",
            drive_sales=topic_root / "04_drive_sales",
            drive_marketing=topic_root / "05_drive_marketing",
            metadata=topic_root / "06_metadata",
        )

    def create_topic(self, name: str) -> TopicSummary:
        topic_root = self.require_workspace_root() / name.strip()
        paths = self.ensure_topic_structure(topic_root)
        context = ListingContext(
            topic_name=name.strip(),
            slug=slugify_text(name),
            clipart_count=0,
            board_name=name.strip(),
        )
        self.write_json(topic_root / "listing_context.json", context.model_dump())
        manifest = BundleManifest(
            topic_name=name.strip(),
            slug=slugify_text(name),
            clipart_count=0,
            status=PipelineStatus.DRAFT,
            board_name=name.strip(),
        )
        self.write_json(topic_root / "bundle.json", manifest.model_dump(mode="json"))
        return TopicSummary(
            name=name.strip(),
            slug=context.slug,
            root=topic_root,
            paths=paths,
            board_name=context.board_name,
        )

    def scan_workspace(self) -> list[TopicSummary]:
        topics = []
        for path in sorted(self.require_workspace_root().iterdir()):
            if path.is_dir() and not path.name.startswith(".clipart_ops_"):
                topics.append(self.scan_topic(path))
        return topics

    def scan_topic(self, topic_root: Path) -> TopicSummary:
        paths = self.ensure_topic_structure(topic_root)
        bundle = self.load_bundle_manifest(topic_root)
        raw_images = self.find_images(paths.raw_ai)
        master_images = self.find_images(paths.master)
        marketing_images = self.find_images(paths.marketing_watermark)
        status = self.compute_status(len(master_images), len(marketing_images), bundle)
        bundle.status = status
        bundle.clipart_count = len(master_images)
        self.write_json(topic_root / "bundle.json", bundle.model_dump(mode="json"))
        return TopicSummary(
            name=topic_root.name,
            slug=bundle.slug or slugify_text(topic_root.name),
            root=topic_root,
            paths=paths,
            status=status,
            raw_count=len(raw_images),
            master_count=len(master_images),
            marketing_count=len(marketing_images),
            sample_images=(master_images or raw_images or marketing_images)[:9],
            etsy_listing_url=bundle.etsy_listing_url,
            board_name=bundle.board_name or topic_root.name,
        )

    def compute_status(
        self,
        master_count: int,
        marketing_count: int,
        bundle: BundleManifest,
    ) -> PipelineStatus:
        if master_count >= 30:
            if bundle.etsy_export_zip:
                if marketing_count > 0:
                    return PipelineStatus.MARKETING_READY
                return PipelineStatus.BUNDLE_READY
            return PipelineStatus.MASTER_READY
        if master_count > 0:
            return PipelineStatus.RAW_READY
        return PipelineStatus.DRAFT

    def require_workspace_root(self) -> Path:
        root = self.get_workspace_root()
        if root is None:
            raise ValueError("Chưa chọn workspace root")
        return root

    def list_directory(self, path: Path) -> list[DirectoryEntry]:
        entries = []
        for item in sorted(path.iterdir(), key=lambda candidate: (not candidate.is_dir(), candidate.name.lower())):
            stat = item.stat()
            entries.append(
                DirectoryEntry(
                    path=item,
                    is_dir=item.is_dir(),
                    size=0 if item.is_dir() else stat.st_size,
                    artifact_type=self.detect_artifact_type(item),
                    modified_at=datetime.fromtimestamp(stat.st_mtime),
                )
            )
        return entries

    def detect_artifact_type(self, path: Path) -> ArtifactType:
        suffix = path.suffix.lower()
        if suffix in IMAGE_SUFFIXES:
            return ArtifactType.IMAGE
        if suffix in CSV_SUFFIXES:
            return ArtifactType.CSV
        if suffix in TEXT_SUFFIXES:
            return ArtifactType.MARKDOWN if suffix == ".md" else ArtifactType.OTHER
        if suffix in JSON_SUFFIXES:
            return ArtifactType.JSON
        return ArtifactType.OTHER

    def read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def read_json(self, path: Path) -> dict:
        if not path.exists():
            return {}
        return json.loads(self.read_text(path))

    def write_json(self, path: Path, payload: dict) -> None:
        self.write_text(path, json.dumps(payload, ensure_ascii=False, indent=2))

    def load_bundle_manifest(self, topic_root: Path) -> BundleManifest:
        path = topic_root / "bundle.json"
        if path.exists():
            return BundleManifest.model_validate(self.read_json(path))
        return BundleManifest(
            topic_name=topic_root.name,
            slug=slugify_text(topic_root.name),
            clipart_count=0,
            status=PipelineStatus.DRAFT,
            board_name=topic_root.name,
        )

    def load_listing_context(self, topic_root: Path) -> ListingContext:
        path = topic_root / "listing_context.json"
        if path.exists():
            return ListingContext.model_validate(self.read_json(path))
        master_count = len(self.find_images(topic_root / "01_master"))
        context = ListingContext(
            topic_name=topic_root.name,
            slug=slugify_text(topic_root.name),
            clipart_count=master_count,
            board_name=topic_root.name,
        )
        self.write_json(path, context.model_dump())
        return context

    def update_listing_context(self, topic_root: Path, payload: dict) -> ListingContext:
        merged = self.load_listing_context(topic_root).model_dump()
        merged.update(payload)
        context = ListingContext.model_validate(merged)
        self.write_json(topic_root / "listing_context.json", context.model_dump())
        bundle = self.load_bundle_manifest(topic_root)
        bundle.etsy_listing_url = context.etsy_listing_url
        bundle.board_name = context.board_name
        self.write_json(topic_root / "bundle.json", bundle.model_dump(mode="json"))
        return context

    def find_images(self, folder: Path) -> list[Path]:
        if not folder.exists():
            return []
        return [path for path in sorted(folder.iterdir()) if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES]

    def create_folder(self, parent: Path, name: str) -> Path:
        target = parent / name.strip()
        target.mkdir(parents=True, exist_ok=False)
        return target

    def rename_path(self, source: Path, new_name: str) -> Path:
        target = source.with_name(new_name.strip())
        source.rename(target)
        return target

    def move_to_trash(self, source: Path) -> Path:
        trash_root = self.require_workspace_root() / ".clipart_ops_trash" / datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        trash_root.mkdir(parents=True, exist_ok=True)
        target = trash_root / source.name
        shutil.move(str(source), str(target))
        return target

    def copy_paths(self, sources: list[Path], destination_dir: Path) -> list[Path]:
        copied = []
        for source in sources:
            target = destination_dir / source.name
            if source.is_dir():
                shutil.copytree(source, target, dirs_exist_ok=True)
            else:
                shutil.copy2(source, target)
            copied.append(target)
        return copied

    def move_paths(self, sources: list[Path], destination_dir: Path) -> list[Path]:
        moved = []
        for source in sources:
            target = destination_dir / source.name
            shutil.move(str(source), str(target))
            moved.append(target)
        return moved
