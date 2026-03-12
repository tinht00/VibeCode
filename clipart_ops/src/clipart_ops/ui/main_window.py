"""Main window với explorer, dashboard và editor."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

from markdown import markdown
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QFileInfo, QSize, Qt
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QFileIconProvider,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QScrollArea,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QTextEdit,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from clipart_ops.data.settings_store import SettingsStore
from clipart_ops.domain.models import ArtifactType, TopicSummary
from clipart_ops.services.bundle_service import BundleService
from clipart_ops.services.drive_service import DriveService
from clipart_ops.services.metadata_service import MetadataService
from clipart_ops.services.pinterest_service import PinterestService
from clipart_ops.services.workspace_service import WorkspaceService
from clipart_ops.ui.dialogs import CandidateSelectionDialog, SettingsDialog
from clipart_ops.ui.theme import apply_theme
from clipart_ops.workers.task_runner import TaskRunner


class MainWindow(QMainWindow):
    """Cửa sổ chính của ứng dụng desktop."""

    def __init__(
        self,
        settings_store: SettingsStore,
        workspace_service: WorkspaceService,
        bundle_service: BundleService,
        metadata_service: MetadataService,
        drive_service: DriveService,
        pinterest_service: PinterestService,
    ) -> None:
        super().__init__()
        self.settings_store = settings_store
        self.workspace_service = workspace_service
        self.bundle_service = bundle_service
        self.metadata_service = metadata_service
        self.drive_service = drive_service
        self.pinterest_service = pinterest_service
        self.task_runner = TaskRunner()
        self.icon_provider = QFileIconProvider()

        self.current_path: Path | None = None
        self.current_directory: Path | None = None
        self.current_topic: TopicSummary | None = None
        self.csv_headers: list[str] = []
        self.editor_dirty = False
        self.active_task_name: str | None = None
        self.primary_action_key: str | None = None
        self.log_expanded = False

        self.setWindowTitle("Clipart Ops")
        self.resize(1680, 960)

        self._build_actions()
        self._build_ui()
        self._restore_workspace()

    def _build_actions(self) -> None:
        toolbar = QToolBar("Thanh công cụ")
        self.addToolBar(toolbar)

        for label, slot in [
            ("Mở workspace", self.choose_workspace),
            ("Tạo chủ đề", self.create_topic),
            ("Refresh", self.refresh_workspace),
            ("Mở Explorer ngoài", self.open_in_system_explorer),
            ("Lưu file", self.save_current_file),
            ("Cài đặt", self.open_settings),
        ]:
            action = QAction(label, self)
            action.triggered.connect(slot)
            toolbar.addAction(action)

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(8)

        left_group = QGroupBox("Workspace")
        left_layout = QVBoxLayout(left_group)
        left_layout.setContentsMargins(10, 14, 10, 10)
        left_layout.setSpacing(10)
        self.workspace_path_label = QLabel("Chưa chọn workspace")
        self.workspace_path_label.setObjectName("sectionHint")
        self.workspace_path_label.setWordWrap(True)
        left_layout.addWidget(self.workspace_path_label)

        workspace_nav = QHBoxLayout()
        self.workspace_root_button = QPushButton("Về gốc")
        self.workspace_root_button.clicked.connect(self.go_workspace_root)
        workspace_nav.addWidget(self.workspace_root_button)
        self.workspace_up_button = QPushButton("Lên một cấp")
        self.workspace_up_button.clicked.connect(self.go_parent_directory)
        workspace_nav.addWidget(self.workspace_up_button)
        left_layout.addLayout(workspace_nav)

        self.workspace_browser = QListWidget()
        self.workspace_browser.setObjectName("workspaceBrowser")
        self.workspace_browser.setViewMode(QListWidget.ViewMode.IconMode)
        self.workspace_browser.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.workspace_browser.setMovement(QListWidget.Movement.Static)
        self.workspace_browser.setWrapping(True)
        self.workspace_browser.setWordWrap(True)
        self.workspace_browser.setSpacing(18)
        self.workspace_browser.setIconSize(QSize(132, 132))
        self.workspace_browser.setGridSize(QSize(208, 204))
        self.workspace_browser.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.workspace_browser.itemSelectionChanged.connect(self.on_workspace_item_selected)
        self.workspace_browser.itemDoubleClicked.connect(self.on_workspace_item_activated)
        left_layout.addWidget(self.workspace_browser, 1)
        left_group.setMinimumWidth(540)
        splitter.addWidget(left_group)

        middle_panel = QWidget()
        middle_layout = QVBoxLayout(middle_panel)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(10)
        self.topic_info = QLabel("Chưa chọn workspace")
        self.topic_info.setObjectName("sectionHint")
        self.topic_info.setWordWrap(True)
        middle_layout.addWidget(self.topic_info)

        self.file_list = QTableWidget(0, 4)
        self.file_list.setHorizontalHeaderLabels(["Tên", "Loại", "Kích thước", "Sửa lần cuối"])
        self.file_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.file_list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.file_list.itemSelectionChanged.connect(self.on_file_selected)

        self.large_icon_list = QListWidget()
        self.large_icon_list.setObjectName("largeIconBrowser")
        self.large_icon_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.large_icon_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.large_icon_list.setMovement(QListWidget.Movement.Static)
        self.large_icon_list.setWrapping(True)
        self.large_icon_list.setWordWrap(True)
        self.large_icon_list.setSpacing(12)
        self.large_icon_list.setIconSize(QSize(96, 96))
        self.large_icon_list.setGridSize(QSize(156, 148))
        self.large_icon_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.large_icon_list.itemSelectionChanged.connect(self.on_large_icon_selected)
        self.large_icon_list.itemDoubleClicked.connect(self.on_large_icon_activated)

        self.file_views = QTabWidget()
        self.file_views.addTab(self.file_list, "Danh sách")
        self.file_views.addTab(self.large_icon_list, "Biểu tượng lớn")
        self.preview_browser = QTextBrowser()
        self.raw_editor = QTextEdit()
        self.raw_editor.textChanged.connect(self._mark_editor_dirty)
        self.csv_table = QTableWidget(0, 0)
        self.csv_table.itemChanged.connect(self._mark_editor_dirty)
        self.file_views.addTab(self.preview_browser, "Xem trước")
        self.editor_panel = QWidget()
        self.editor_panel_layout = QVBoxLayout(self.editor_panel)
        self.editor_panel_layout.setContentsMargins(0, 0, 0, 0)
        self.editor_panel_layout.setSpacing(0)
        self.editor_panel_layout.addWidget(self.raw_editor)
        self.editor_panel_layout.addWidget(self.csv_table)
        self.file_views.addTab(self.editor_panel, "Chỉnh sửa")
        self.file_views.setCurrentIndex(1)
        file_group = QGroupBox("Nội dung thư mục")
        file_group_layout = QVBoxLayout(file_group)
        file_group_layout.setContentsMargins(10, 14, 10, 10)
        file_group_layout.addWidget(self.file_views)
        middle_layout.addWidget(file_group, 1)
        splitter.addWidget(middle_panel)

        inspector_panel = QWidget()
        inspector_layout = QVBoxLayout(inspector_panel)
        inspector_layout.setContentsMargins(0, 0, 0, 0)
        inspector_layout.setSpacing(10)
        self.dashboard_title = QLabel("Chủ đề")
        self.dashboard_title.setObjectName("sectionTitle")
        inspector_layout.addWidget(self.dashboard_title)
        self.dashboard = self._build_dashboard()
        self.dashboard_scroll = QScrollArea()
        self.dashboard_scroll.setObjectName("dashboardScroll")
        self.dashboard_scroll.setWidgetResizable(True)
        self.dashboard_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.dashboard_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.dashboard_scroll.setWidget(self.dashboard)
        inspector_layout.addWidget(self.dashboard_scroll, 1)
        splitter.addWidget(inspector_panel)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 6)
        splitter.setStretchFactor(2, 3)
        splitter.setSizes([500, 880, 420])
        layout.addWidget(splitter, 1)

        log_group = QGroupBox("Nhật ký hoạt động")
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(10, 14, 10, 10)
        log_header = QHBoxLayout()
        log_header.addWidget(QLabel("Xem log gần nhất của phiên làm việc"))
        log_header.addStretch(1)
        self.toggle_log_button = QPushButton("Mở rộng")
        self.toggle_log_button.clicked.connect(self.toggle_log_panel)
        log_header.addWidget(self.toggle_log_button)
        log_layout.addLayout(log_header)
        self.job_log = QListWidget()
        self.job_log.setMinimumHeight(72)
        self.job_log.setMaximumHeight(72)
        log_layout.addWidget(self.job_log)
        layout.addWidget(log_group, 0)

        self.setStatusBar(QStatusBar())
        self.busy_label = QLabel("")
        self.busy_progress = QProgressBar()
        self.busy_progress.setRange(0, 0)
        self.busy_progress.setFixedWidth(220)
        self.busy_progress.hide()
        self.statusBar().addPermanentWidget(self.busy_label)
        self.statusBar().addPermanentWidget(self.busy_progress)
        self.setCentralWidget(root)
        self._show_text_mode()
        self._apply_local_widget_tweaks()

    def _apply_local_widget_tweaks(self) -> None:
        self.file_list.setAlternatingRowColors(True)
        self.workspace_browser.setAlternatingRowColors(False)
        self.large_icon_list.setAlternatingRowColors(False)
        self.job_log.setAlternatingRowColors(True)
        self.preview_browser.setOpenExternalLinks(True)

    def _build_dashboard(self) -> QGroupBox:
        group = QGroupBox("Dashboard chủ đề")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(14, 18, 14, 14)
        layout.setSpacing(12)
        self.count_label = QLabel("raw: 0 | master: 0 | marketing: 0")
        self.count_label.setObjectName("metricSummary")
        layout.addWidget(self.count_label)

        context_card = QWidget()
        context_card.setObjectName("dashboardCard")
        form = QFormLayout(context_card)
        form.setContentsMargins(12, 12, 12, 12)
        form.setSpacing(10)
        self.board_input = QLineEdit()
        self.etsy_link_input = QLineEdit()
        form.addRow("Pinterest board", self.board_input)
        form.addRow("Etsy listing URL", self.etsy_link_input)
        layout.addWidget(context_card)

        workflow_card = QWidget()
        workflow_card.setObjectName("dashboardCard")
        workflow_layout = QVBoxLayout(workflow_card)
        workflow_layout.setContentsMargins(12, 12, 12, 12)
        workflow_layout.setSpacing(8)
        workflow_title = QLabel("Luồng tuần tự")
        workflow_title.setObjectName("subsectionTitle")
        workflow_layout.addWidget(workflow_title)
        self.workflow_summary_label = QLabel("Chọn một chủ đề để xem bước tiếp theo cần làm.")
        self.workflow_summary_label.setObjectName("workflowSummary")
        self.workflow_summary_label.setWordWrap(True)
        workflow_layout.addWidget(self.workflow_summary_label)
        self.workflow_steps_list = QListWidget()
        self.workflow_steps_list.setObjectName("workflowStepsList")
        self.workflow_steps_list.setMinimumHeight(98)
        self.workflow_steps_list.setMaximumHeight(150)
        self.workflow_steps_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.workflow_steps_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        workflow_layout.addWidget(self.workflow_steps_list)
        self.primary_action_button = QPushButton("Chọn một chủ đề")
        self.primary_action_button.setObjectName("primaryActionButton")
        self.primary_action_button.clicked.connect(self.run_primary_action)
        self.primary_action_button.setMinimumHeight(42)
        workflow_layout.addWidget(self.primary_action_button)
        layout.addWidget(workflow_card)

        action_card = QWidget()
        action_card.setObjectName("dashboardCard")
        action_layout = QVBoxLayout(action_card)
        action_layout.setContentsMargins(12, 12, 12, 12)
        action_layout.setSpacing(8)
        action_title = QLabel("Thao tác khác")
        action_title.setObjectName("subsectionTitle")
        action_layout.addWidget(action_title)

        self.bundle_button = QPushButton("Đóng gói Etsy")
        self.bundle_button.clicked.connect(self.create_bundle)
        self.metadata_button = QPushButton("Chuẩn bị metadata")
        self.metadata_button.clicked.connect(self.generate_metadata)
        self.drive_button = QPushButton("Upload Drive marketing")
        self.drive_button.clicked.connect(self.upload_drive_assets)
        self.csv_button = QPushButton("Tạo CSV Pinterest")
        self.csv_button.clicked.connect(self.create_pinterest_csv)
        self.open_pinterest_button = QPushButton("Mở luồng upload Pinterest")
        self.open_pinterest_button.clicked.connect(self.open_pinterest_upload)
        save_context_button = QPushButton("Lưu context chủ đề")
        save_context_button.clicked.connect(self.save_topic_context)

        buttons = [
            self.bundle_button,
            self.metadata_button,
            self.drive_button,
            self.csv_button,
            self.open_pinterest_button,
            save_context_button,
        ]
        action_grid = QGridLayout()
        action_grid.setHorizontalSpacing(8)
        action_grid.setVerticalSpacing(8)
        for index, button in enumerate(buttons):
            button.setMinimumHeight(40)
            action_grid.addWidget(button, index // 2, index % 2)
        action_layout.addLayout(action_grid)
        layout.addWidget(action_card)
        return group

    def _restore_workspace(self) -> None:
        root = self.workspace_service.get_workspace_root()
        if root and root.exists():
            self.load_workspace(root)

    def choose_workspace(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Chọn workspace root")
        if path:
            self.load_workspace(Path(path))

    def load_workspace(self, root: Path) -> None:
        self.workspace_service.set_workspace_root(root)
        self.topic_info.setText(f"Workspace: {root}")
        self.browse_workspace_directory(root)

    def refresh_workspace(self) -> None:
        if not self.workspace_service.get_workspace_root():
            return
        target = self.current_directory or self.workspace_service.get_workspace_root()
        if target is not None:
            self.browse_workspace_directory(target)
        self.job_log.addItem("Đã refresh workspace.")

    def create_topic(self) -> None:
        if self.workspace_service.get_workspace_root() is None:
            self.choose_workspace()
            if self.workspace_service.get_workspace_root() is None:
                return
        name, accepted = QInputDialog.getText(self, "Tạo chủ đề", "Tên chủ đề:")
        if accepted and name.strip():
            topic = self.workspace_service.create_topic(name)
            self.job_log.addItem(f"Đã tạo chủ đề: {topic.name}")
            self.refresh_workspace()

    def browse_workspace_directory(self, path: Path) -> None:
        if not path.exists() or not path.is_dir():
            return
        self.current_directory = path
        self.current_path = path
        self.workspace_path_label.setText(str(path))
        self.topic_info.setText(str(path))
        self._load_directory(path)
        self._load_topic_dashboard(path)

    def _load_directory(self, path: Path) -> None:
        entries = self.workspace_service.list_directory(path)
        self._populate_workspace_browser(entries)
        self.file_list.blockSignals(True)
        self.file_list.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            name_item = QTableWidgetItem(entry.path.name)
            name_item.setData(Qt.ItemDataRole.UserRole, str(entry.path))
            self.file_list.setItem(row, 0, name_item)
            self.file_list.setItem(row, 1, QTableWidgetItem(entry.artifact_type.value))
            self.file_list.setItem(row, 2, QTableWidgetItem("" if entry.is_dir else str(entry.size)))
            modified = entry.modified_at.isoformat(timespec="seconds") if entry.modified_at else ""
            self.file_list.setItem(row, 3, QTableWidgetItem(modified))
        self.file_list.blockSignals(False)
        self._populate_large_icon_view(entries)
        self._show_text_mode()
        self.preview_browser.setPlainText(f"Thư mục: {path}")
        self.raw_editor.clear()

    def _find_topic_root(self, path: Path) -> Path | None:
        workspace_root = self.workspace_service.get_workspace_root()
        if workspace_root is None or path == workspace_root:
            return None
        candidate = path if path.is_dir() else path.parent
        while candidate != workspace_root.parent:
            if candidate.parent == workspace_root:
                return candidate
            if candidate == workspace_root:
                return None
            candidate = candidate.parent
        return None

    def _load_topic_dashboard(self, path: Path) -> None:
        topic_root = self._find_topic_root(path)
        if topic_root is None:
            self.current_topic = None
            self.count_label.setText(self._render_count_summary(0, 0, 0, "draft"))
            self.board_input.clear()
            self.etsy_link_input.clear()
            self._update_workflow_panel()
            return
        topic = self.workspace_service.scan_topic(topic_root)
        context = self.workspace_service.load_listing_context(topic_root)
        self.current_topic = topic
        self.count_label.setText(
            self._render_count_summary(
                topic.raw_count,
                topic.master_count,
                topic.marketing_count,
                topic.status.value,
            )
        )
        self.board_input.setText(context.board_name)
        self.etsy_link_input.setText(context.etsy_listing_url)
        self._update_workflow_panel(topic_root, topic)

    def on_file_selected(self) -> None:
        items = self.file_list.selectedItems()
        if items:
            path = Path(items[0].data(Qt.ItemDataRole.UserRole))
            if path.is_file():
                self.load_file(path)

    def on_workspace_item_selected(self) -> None:
        item = self.workspace_browser.currentItem()
        if item is None:
            return
        path = Path(item.data(Qt.ItemDataRole.UserRole))
        self.current_path = path
        if path.is_file():
            self.load_file(path)
            self._load_topic_dashboard(path.parent)
        else:
            self._show_text_mode()
            self.preview_browser.setPlainText(f"Thư mục: {path}")
            self.raw_editor.clear()
            self._load_topic_dashboard(path)

    def on_workspace_item_activated(self, item: QListWidgetItem) -> None:
        path = Path(item.data(Qt.ItemDataRole.UserRole))
        if path.is_dir():
            self.browse_workspace_directory(path)
        else:
            self.load_file(path)

    def on_large_icon_selected(self) -> None:
        item = self.large_icon_list.currentItem()
        if item is None:
            return
        path = Path(item.data(Qt.ItemDataRole.UserRole))
        self.current_path = path
        if path.is_dir():
            self._show_text_mode()
            self.preview_browser.setPlainText(f"Thư mục: {path}")
            self.raw_editor.clear()
            return
        self.load_file(path)

    def on_large_icon_activated(self, item: QListWidgetItem) -> None:
        path = Path(item.data(Qt.ItemDataRole.UserRole))
        if path.is_dir():
            self.browse_workspace_directory(path)
            return
        self.load_file(path)

    def load_file(self, path: Path) -> None:
        self.current_path = path
        artifact_type = self.workspace_service.detect_artifact_type(path)
        if artifact_type == ArtifactType.IMAGE:
            self._show_text_mode()
            self.preview_browser.setHtml(f"<img src='{path.as_uri()}' style='max-width:100%;' />")
            self.raw_editor.setPlainText("")
            return
        if artifact_type == ArtifactType.CSV:
            self._show_csv_mode()
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.reader(handle))
            headers = rows[0] if rows else []
            data_rows = rows[1:] if len(rows) > 1 else []
            self.csv_headers = headers
            self.csv_table.blockSignals(True)
            self.csv_table.setColumnCount(len(headers))
            self.csv_table.setHorizontalHeaderLabels(headers)
            self.csv_table.setRowCount(len(data_rows))
            for row_index, row in enumerate(data_rows):
                for col_index, value in enumerate(row):
                    self.csv_table.setItem(row_index, col_index, QTableWidgetItem(value))
            self.csv_table.blockSignals(False)
            self.preview_browser.setPlainText("\n".join([",".join(headers), *[",".join(row) for row in data_rows[:10]]]))
            self.editor_dirty = False
            return

        self._show_text_mode()
        content = self.workspace_service.read_text(path)
        self.raw_editor.blockSignals(True)
        self.raw_editor.setPlainText(content)
        self.raw_editor.blockSignals(False)
        if artifact_type == ArtifactType.MARKDOWN:
            self.preview_browser.setHtml(markdown(content))
        elif artifact_type == ArtifactType.JSON:
            try:
                formatted = json.dumps(json.loads(content), ensure_ascii=False, indent=2)
                self.raw_editor.setPlainText(formatted)
                self.preview_browser.setHtml(f"<pre>{formatted}</pre>")
            except json.JSONDecodeError:
                self.preview_browser.setPlainText("JSON không hợp lệ.")
        else:
            self.preview_browser.setPlainText(content)
        self.editor_dirty = False

    def save_current_file(self) -> None:
        if self.current_path is None or not self.current_path.is_file():
            return
        artifact_type = self.workspace_service.detect_artifact_type(self.current_path)
        if artifact_type == ArtifactType.CSV:
            with self.current_path.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(self.csv_headers)
                for row_index in range(self.csv_table.rowCount()):
                    row = [
                        self.csv_table.item(row_index, col_index).text() if self.csv_table.item(row_index, col_index) else ""
                        for col_index in range(self.csv_table.columnCount())
                    ]
                    writer.writerow(row)
        else:
            self.workspace_service.write_text(self.current_path, self.raw_editor.toPlainText())
        self.statusBar().showMessage("Đã lưu file.", 3000)
        self.editor_dirty = False

    def save_topic_context(self) -> None:
        if self.current_topic is None:
            return
        self.workspace_service.update_listing_context(
            self.current_topic.root,
            {
                "board_name": self.board_input.text().strip(),
                "etsy_listing_url": self.etsy_link_input.text().strip(),
                "clipart_count": self.current_topic.master_count,
            },
        )
        self.job_log.addItem(f"Đã lưu listing context cho {self.current_topic.name}.")

    def create_bundle(self) -> None:
        if self.current_topic is None:
            return
        self.task_runner.submit(
            self.bundle_service.create_bundle,
            self.current_topic.root,
            on_success=lambda result: self._handle_success(f"Đã đóng gói bundle: {result.etsy_export_zip}"),
            on_error=self._handle_error,
        )

    def generate_metadata(self) -> None:
        if self.current_topic is None:
            return
        self.save_topic_context()
        self._set_busy_state(
            True,
            "Đang chuẩn bị metadata...",
            button=self.metadata_button,
            button_text="Đang chuẩn bị metadata...",
        )
        self.task_runner.submit(
            self.metadata_service.generate_for_topic,
            self.current_topic.root,
            on_success=self._select_metadata_candidate,
            on_error=self._handle_error,
        )

    def _select_metadata_candidate(self, metadata) -> None:
        self._set_busy_state(False)
        self.job_log.addItem(
            "App đã tạo khung metadata nội bộ. Bạn có thể duyệt ngay hoặc chỉnh tiếp bằng AI ngoài sau khi lưu."
        )
        self.statusBar().showMessage(
            "Đã chuẩn bị khung metadata để bạn chỉnh bằng AI ngoài hoặc sửa tay.",
            6000,
        )
        dialog = CandidateSelectionDialog(metadata.candidates, self)
        if dialog.exec() and dialog.selected_rank is not None and self.current_topic is not None:
            approved = self.metadata_service.approve_candidate(self.current_topic.root, dialog.selected_rank)
            self.job_log.addItem(f"Đã duyệt candidate {approved.approved_candidate_rank} cho {self.current_topic.name}.")
        self.refresh_workspace()

    def upload_drive_assets(self) -> None:
        if self.current_topic is None:
            return
        self.task_runner.submit(
            self.drive_service.upload_marketing_assets,
            self.current_topic.root,
            on_success=lambda assets: self._handle_success(f"Đã sync {len(assets)} asset marketing lên Google Drive."),
            on_error=self._handle_error,
        )

    def create_pinterest_csv(self) -> None:
        if self.current_topic is None:
            return
        self.task_runner.submit(
            self.pinterest_service.build_csv,
            self.current_topic.root,
            on_success=lambda csv_path: self._handle_success(f"Đã tạo CSV Pinterest: {csv_path.name}"),
            on_error=self._handle_error,
        )

    def open_pinterest_upload(self) -> None:
        self.pinterest_service.open_import_content()
        if self.current_topic is not None:
            self.pinterest_service.mark_uploaded_to_ui(self.current_topic.root)
            self._update_workflow_panel(self.current_topic.root, self.current_topic)
        self.job_log.addItem("Đã mở Pinterest Import Content trong trình duyệt.")

    def open_in_system_explorer(self) -> None:
        if self.current_path is not None:
            target = self.current_path if self.current_path.is_dir() else self.current_path.parent
            os.startfile(str(target))

    def open_settings(self) -> None:
        dialog = SettingsDialog(
            current_theme=self.settings_store.get_value("theme", "auto"),
            drive_secret_path=self.drive_service.client_secret,
            recent_workspaces=self.settings_store.list_recent_workspaces(),
            parent=self,
        )
        if dialog.exec():
            theme = dialog.get_theme()
            self.settings_store.set_value("theme", theme)
            app = QApplication.instance()
            if app is not None:
                apply_theme(app, theme)
            if dialog.selected_workspace and dialog.selected_workspace.exists():
                self.load_workspace(dialog.selected_workspace)
            self.job_log.addItem("Đã cập nhật cài đặt giao diện.")

    def _show_text_mode(self) -> None:
        self.preview_browser.show()
        self.raw_editor.show()
        self.csv_table.hide()
        self.file_views.setCurrentIndex(2)

    def _show_csv_mode(self) -> None:
        self.raw_editor.hide()
        self.csv_table.show()
        self.file_views.setCurrentIndex(3)

    def _mark_editor_dirty(self) -> None:
        self.editor_dirty = True

    def _populate_large_icon_view(self, entries) -> None:
        self.large_icon_list.blockSignals(True)
        self.large_icon_list.clear()
        for entry in entries:
            item = QListWidgetItem(self._build_entry_icon(entry.path, entry.artifact_type), entry.path.name)
            item.setData(Qt.ItemDataRole.UserRole, str(entry.path))
            item.setToolTip(str(entry.path))
            item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
            self.large_icon_list.addItem(item)
        self.large_icon_list.blockSignals(False)

    def _populate_workspace_browser(self, entries) -> None:
        self.workspace_browser.blockSignals(True)
        self.workspace_browser.clear()
        for entry in entries:
            item = QListWidgetItem(self._build_entry_icon(entry.path, entry.artifact_type), entry.path.name)
            item.setData(Qt.ItemDataRole.UserRole, str(entry.path))
            item.setToolTip(str(entry.path))
            item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
            self.workspace_browser.addItem(item)
        self.workspace_browser.blockSignals(False)

    def _build_entry_icon(self, path: Path, artifact_type: ArtifactType) -> QIcon:
        if artifact_type == ArtifactType.IMAGE and path.exists():
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                return QIcon(
                    pixmap.scaled(
                        96,
                        96,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
        return self.icon_provider.icon(QFileInfo(str(path)))

    def _render_count_summary(self, raw_count: int, master_count: int, marketing_count: int, status: str) -> str:
        status_text = status.replace("_", " ")
        return (
            "<div style='display:flex;gap:8px;flex-wrap:wrap;'>"
            f"<span style='padding:6px 10px;border-radius:999px;background:#122033;color:#d9e8ff;'>Raw: <b>{raw_count}</b></span>"
            f"<span style='padding:6px 10px;border-radius:999px;background:#122033;color:#d9e8ff;'>Master: <b>{master_count}</b></span>"
            f"<span style='padding:6px 10px;border-radius:999px;background:#122033;color:#d9e8ff;'>Marketing: <b>{marketing_count}</b></span>"
            f"<span style='padding:6px 10px;border-radius:999px;background:#1b3655;color:#9ed0ff;'>Trạng thái: <b>{status_text}</b></span>"
            "</div>"
        )

    def go_workspace_root(self) -> None:
        root = self.workspace_service.get_workspace_root()
        if root is not None:
            self.browse_workspace_directory(root)

    def go_parent_directory(self) -> None:
        root = self.workspace_service.get_workspace_root()
        if self.current_directory is None or root is None:
            return
        if self.current_directory == root:
            return
        parent = self.current_directory.parent
        if parent.exists():
            self.browse_workspace_directory(parent)

    def toggle_log_panel(self) -> None:
        self.log_expanded = not self.log_expanded
        if self.log_expanded:
            self.job_log.setMinimumHeight(150)
            self.job_log.setMaximumHeight(180)
            self.toggle_log_button.setText("Thu gọn")
            return
        self.job_log.setMinimumHeight(72)
        self.job_log.setMaximumHeight(72)
        self.toggle_log_button.setText("Mở rộng")

    def _handle_success(self, message: str) -> None:
        self._set_busy_state(False)
        self.job_log.addItem(message)
        self.statusBar().showMessage(message, 5000)
        self.refresh_workspace()
        if self.current_topic:
            refreshed_topic = self.workspace_service.scan_topic(self.current_topic.root)
            self.current_topic = refreshed_topic
            self._load_topic_dashboard(self.current_topic.root)

    def _handle_error(self, message: str) -> None:
        self._set_busy_state(False)
        self.job_log.addItem(f"Lỗi: {message}")
        QMessageBox.critical(self, "Lỗi", message)

    def _set_busy_state(
        self,
        is_busy: bool,
        label: str = "",
        button: QPushButton | None = None,
        button_text: str | None = None,
    ) -> None:
        self.active_task_name = label if is_busy else None
        self.busy_label.setText(label if is_busy else "")
        self.busy_progress.setVisible(is_busy)

        buttons = [
            self.primary_action_button,
            self.bundle_button,
            self.metadata_button,
            self.drive_button,
            self.csv_button,
            self.open_pinterest_button,
        ]
        for item in buttons:
            item.setEnabled(not is_busy)

        if button is None:
            self.metadata_button.setText("Chuẩn bị metadata")
            return

        if is_busy and button_text:
            button.setText(button_text)
            return

        self.metadata_button.setText("Chuẩn bị metadata")

    def _update_workflow_panel(self, topic_root: Path | None = None, topic: TopicSummary | None = None) -> None:
        if topic_root is None or topic is None:
            self.workflow_summary_label.setText("Chọn một chủ đề để xem bước tiếp theo cần làm.")
            self._populate_workflow_steps([])
            self.primary_action_key = None
            self.primary_action_button.setEnabled(False)
            self.primary_action_button.setText("Chọn một chủ đề")
            return

        metadata_payload = self.workspace_service.read_json(topic_root / "listing_metadata.json")
        approved_rank = metadata_payload.get("approved_candidate_rank")
        bundle = self.workspace_service.load_bundle_manifest(topic_root)
        bundle_ready = bool(bundle.etsy_export_zip and (topic_root / bundle.etsy_export_zip).exists())

        assets_payload = self.workspace_service.read_json(topic_root / "drive_assets.json")
        valid_assets = [item for item in assets_payload.get("assets", []) if item.get("media_url_status") == "valid"]
        csv_ready = (topic_root / "pinterest_export.csv").exists()
        upload_opened = any("CSV đã được mở" in note for note in bundle.notes)

        if topic.master_count < 30:
            next_key = "open_master_folder"
            summary = "Bước tiếp theo: hoàn thiện ít nhất 30 ảnh bán trong thư mục 01_master."
            action_text = "Mở 01_master"
        elif not approved_rank:
            next_key = "generate_metadata"
            summary = "Bước tiếp theo: tạo khung metadata rồi chỉnh tiếp bằng Codex hoặc AI ngoài nếu cần."
            action_text = "Chuẩn bị metadata"
        elif not bundle_ready:
            next_key = "create_bundle"
            summary = "Bước tiếp theo: đóng gói bundle Etsy từ ảnh trong 01_master."
            action_text = "Đóng gói Etsy"
        elif topic.marketing_count == 0:
            next_key = "open_marketing_folder"
            summary = "Bước tiếp theo: thêm ảnh watermark vào 03_marketing_watermark để chuẩn bị marketing."
            action_text = "Mở 03_marketing_watermark"
        elif not valid_assets:
            next_key = "upload_drive_assets"
            summary = "Bước tiếp theo: upload ảnh marketing lên Google Drive để tạo Media URL hợp lệ."
            action_text = "Upload Drive marketing"
        elif not csv_ready:
            next_key = "create_pinterest_csv"
            summary = "Bước tiếp theo: tạo file CSV Pinterest từ metadata đã duyệt và ảnh marketing hợp lệ."
            action_text = "Tạo CSV Pinterest"
        else:
            next_key = "open_pinterest_upload"
            summary = "Bước tiếp theo: mở màn hình Pinterest Import Content và upload file CSV."
            action_text = "Mở luồng upload Pinterest"
            if upload_opened:
                summary = "Luồng chính đã hoàn tất tới bước mở Pinterest. Bạn có thể kiểm tra và upload batch tiếp theo."

        steps = [
            (
                "Đủ 30 ảnh trong 01_master",
                topic.master_count >= 30,
                next_key == "open_master_folder",
                f"Hiện có {topic.master_count}/30 ảnh đạt chuẩn.",
            ),
            (
                "Chuẩn bị và duyệt metadata",
                bool(approved_rank),
                next_key == "generate_metadata",
                "Tạo 3 khung metadata rồi chọn 1 bản chính thức để tiếp tục.",
            ),
            (
                "Đóng gói bundle Etsy",
                bundle_ready,
                next_key == "create_bundle",
                "Sinh thư mục export đã đổi tên và file ZIP bán hàng.",
            ),
            (
                "Chuẩn bị ảnh watermark",
                topic.marketing_count > 0,
                next_key == "open_marketing_folder",
                f"Hiện có {topic.marketing_count} ảnh marketing.",
            ),
            (
                "Upload Drive marketing",
                bool(valid_assets),
                next_key == "upload_drive_assets",
                f"Có {len(valid_assets)} media URL hợp lệ.",
            ),
            (
                "Tạo CSV Pinterest",
                csv_ready,
                next_key == "create_pinterest_csv",
                "Sinh file CSV đúng cột để upload hàng loạt.",
            ),
            (
                "Mở upload Pinterest",
                upload_opened,
                next_key == "open_pinterest_upload",
                "Chuyển sang Pinterest Import Content để upload batch.",
            ),
        ]

        self.workflow_summary_label.setText(summary)
        self.primary_action_key = next_key
        self.primary_action_button.setEnabled(True)
        self.primary_action_button.setText(action_text)
        self._populate_workflow_steps(steps)

    def _populate_workflow_steps(self, steps: list[tuple[str, bool, bool, str]]) -> None:
        self.workflow_steps_list.clear()
        if not steps:
            self.workflow_steps_list.addItem("Luồng đề xuất sẽ hiện ở đây.")
            return
        for index, (title, done, is_current, detail) in enumerate(steps, start=1):
            if done:
                prefix = "Da xong"
            elif is_current:
                prefix = "Dang lam"
            else:
                prefix = "Cho sau"
            item = QListWidgetItem(f"{index}. {title} | {prefix}\n{detail}")
            if done:
                item.setData(Qt.ItemDataRole.UserRole, "done")
            elif is_current:
                item.setData(Qt.ItemDataRole.UserRole, "current")
            else:
                item.setData(Qt.ItemDataRole.UserRole, "pending")
            self.workflow_steps_list.addItem(item)

    def run_primary_action(self) -> None:
        if self.primary_action_key == "open_master_folder" and self.current_topic is not None:
            os.startfile(str(self.current_topic.paths.master))
        elif self.primary_action_key == "generate_metadata":
            self.generate_metadata()
        elif self.primary_action_key == "create_bundle":
            self.create_bundle()
        elif self.primary_action_key == "open_marketing_folder" and self.current_topic is not None:
            os.startfile(str(self.current_topic.paths.marketing_watermark))
        elif self.primary_action_key == "upload_drive_assets":
            self.upload_drive_assets()
        elif self.primary_action_key == "create_pinterest_csv":
            self.create_pinterest_csv()
        elif self.primary_action_key == "open_pinterest_upload":
            self.open_pinterest_upload()
