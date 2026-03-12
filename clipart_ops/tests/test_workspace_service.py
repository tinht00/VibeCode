from pathlib import Path

from clipart_ops.data.settings_store import SettingsStore
from clipart_ops.services.workspace_service import WorkspaceService


def test_create_topic_and_scan(tmp_path: Path) -> None:
    settings = SettingsStore(tmp_path / "state")
    service = WorkspaceService(settings)
    service.set_workspace_root(tmp_path / "workspace")

    topic = service.create_topic("Cute Bears")
    assert topic.root.exists()
    assert (topic.root / "01_master").exists()

    topics = service.scan_workspace()
    assert len(topics) == 1
    assert topics[0].name == "Cute Bears"


def test_move_to_trash(tmp_path: Path) -> None:
    settings = SettingsStore(tmp_path / "state")
    service = WorkspaceService(settings)
    workspace = tmp_path / "workspace"
    service.set_workspace_root(workspace)
    sample = workspace / "sample.txt"
    sample.write_text("demo", encoding="utf-8")

    trashed = service.move_to_trash(sample)
    assert trashed.exists()
    assert not sample.exists()
