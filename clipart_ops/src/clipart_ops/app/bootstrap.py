"""Khởi tạo QApplication và MainWindow."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from clipart_ops.app.env_loader import load_env_file
from clipart_ops.data.settings_store import SettingsStore
from clipart_ops.services.bundle_service import BundleService
from clipart_ops.services.drive_service import DriveService
from clipart_ops.services.metadata_service import MetadataService
from clipart_ops.services.pinterest_service import PinterestService
from clipart_ops.services.workspace_service import WorkspaceService
from clipart_ops.ui.main_window import MainWindow
from clipart_ops.ui.theme import apply_theme


def run() -> int:
    """Chạy ứng dụng desktop."""
    project_root = Path(__file__).resolve().parents[3]
    load_env_file(project_root / ".env")
    load_env_file(project_root / ".env.local")

    app = QApplication(sys.argv)
    app.setApplicationName("Clipart Ops")
    app.setOrganizationName("Tinht00")

    state_dir = project_root / ".clipart_ops_state"
    settings_store = SettingsStore(state_dir)
    apply_theme(app, settings_store.get_value("theme", "auto"))
    workspace_service = WorkspaceService(settings_store)
    bundle_service = BundleService(workspace_service)
    metadata_service = MetadataService(workspace_service)
    drive_service = DriveService(workspace_service)
    pinterest_service = PinterestService(workspace_service)

    window = MainWindow(
        settings_store=settings_store,
        workspace_service=workspace_service,
        bundle_service=bundle_service,
        metadata_service=metadata_service,
        drive_service=drive_service,
        pinterest_service=pinterest_service,
    )
    window.show()
    return app.exec()
