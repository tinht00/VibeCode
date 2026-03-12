from pathlib import Path

from clipart_ops.data.settings_store import SettingsStore
from clipart_ops.services.bundle_service import BundleService
from clipart_ops.services.workspace_service import WorkspaceService


def test_create_bundle(tmp_path: Path) -> None:
    settings = SettingsStore(tmp_path / "state")
    workspace_service = WorkspaceService(settings)
    workspace_service.set_workspace_root(tmp_path / "workspace")
    topic = workspace_service.create_topic("Pastel Flowers")

    for index in range(30):
        (topic.paths.master / f"flower-{index:03d}.png").write_bytes(b"png")

    bundle_service = BundleService(workspace_service)
    manifest = bundle_service.create_bundle(topic.root)

    assert manifest.etsy_export_zip.endswith(".zip")
    assert (topic.root / manifest.etsy_export_zip).exists()
