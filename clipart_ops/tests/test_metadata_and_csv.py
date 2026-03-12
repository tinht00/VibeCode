from pathlib import Path

from clipart_ops.data.settings_store import SettingsStore
from clipart_ops.services.metadata_service import MetadataService
from clipart_ops.services.pinterest_service import PinterestService
from clipart_ops.services.workspace_service import WorkspaceService


def test_metadata_fallback_and_csv(tmp_path: Path) -> None:
    settings = SettingsStore(tmp_path / "state")
    workspace_service = WorkspaceService(settings)
    workspace_service.set_workspace_root(tmp_path / "workspace")
    topic = workspace_service.create_topic("Forest Animals")

    for index in range(30):
        (topic.paths.master / f"asset-{index:03d}.png").write_bytes(b"png")
        (topic.paths.marketing_watermark / f"asset-{index:03d}.png").write_bytes(b"png")

    metadata_service = MetadataService(workspace_service)
    metadata = metadata_service.generate_for_topic(topic.root)
    assert metadata.source_mode == "manual_template"
    assert len(metadata.candidates) == 3
    assert metadata.candidates[0].warnings

    metadata_service.approve_candidate(topic.root, 1)
    workspace_service.write_json(
        topic.root / "drive_assets.json",
        {
            "assets": [
                {
                    "file_name": "asset-000.png",
                    "local_path": str(topic.paths.marketing_watermark / "asset-000.png"),
                    "resolved_media_url": "https://example.com/asset-000.png",
                    "media_url_status": "valid",
                    "mime_type": "image/png",
                }
            ]
        },
    )
    workspace_service.update_listing_context(
        topic.root,
        {"board_name": "Forest Animals", "etsy_listing_url": "https://etsy.example/item"},
    )

    pinterest_service = PinterestService(workspace_service)
    csv_path = pinterest_service.build_csv(topic.root)

    content = csv_path.read_text(encoding="utf-8-sig")
    assert "Media URL" in content
    assert "https://example.com/asset-000.png" in content
