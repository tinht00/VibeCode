"""Dialogs phụ trợ cho ứng dụng."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from clipart_ops.domain.models import MetadataCandidate


class CandidateSelectionDialog(QDialog):
    """Dialog chọn candidate metadata đã sinh."""

    def __init__(self, candidates: list[MetadataCandidate], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Chọn metadata để duyệt")
        self.resize(960, 560)
        self.candidates = candidates
        self.selected_rank: int | None = None

        layout = QHBoxLayout(self)
        self.list_widget = QListWidget()
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setAcceptRichText(False)

        for candidate in candidates:
            item = QListWidgetItem(
                f"Candidate {candidate.rank} | SEO {candidate.scores.seo} | "
                f"Policy {candidate.scores.policy_safety}"
            )
            item.setData(Qt.ItemDataRole.UserRole, candidate.rank)
            self.list_widget.addItem(item)

        self.list_widget.currentRowChanged.connect(self._render_candidate)
        layout.addWidget(self.list_widget, 2)

        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Preview metadata"))
        right_layout.addWidget(self.preview, 1)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        right_layout.addWidget(button_box)
        layout.addLayout(right_layout, 3)

        if candidates:
            self.list_widget.setCurrentRow(0)

    def _render_candidate(self, row: int) -> None:
        if row < 0:
            self.preview.clear()
            self.selected_rank = None
            return
        candidate = self.candidates[row]
        self.selected_rank = candidate.rank
        self.preview.setPlainText(
            "\n".join(
                [
                    f"[Etsy title]\n{candidate.etsy_title}",
                    "",
                    f"[Etsy description]\n{candidate.etsy_description}",
                    "",
                    f"[Etsy tags]\n{', '.join(candidate.etsy_tags)}",
                    "",
                    f"[Pinterest title]\n{candidate.pinterest_title}",
                    "",
                    f"[Pinterest description]\n{candidate.pinterest_description}",
                    "",
                    f"[Pinterest keywords]\n{', '.join(candidate.pinterest_keywords)}",
                    "",
                    f"[Warnings]\n{'; '.join(candidate.warnings) or 'Không có'}",
                ]
            )
        )


class SettingsDialog(QDialog):
    """Dialog cài đặt app và kiểm tra secret."""

    def __init__(
        self,
        current_theme: str,
        drive_secret_path: str,
        recent_workspaces: list[Path],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Cài đặt")
        self.resize(760, 520)
        self.selected_workspace: Path | None = None

        layout = QVBoxLayout(self)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["auto", "dark", "light"])
        self.theme_combo.setCurrentText(current_theme if current_theme in {"auto", "dark", "light"} else "auto")

        drive_status = drive_secret_path if drive_secret_path and Path(drive_secret_path).exists() else "Chưa thấy file OAuth Google Drive"

        info = QTextEdit()
        info.setReadOnly(True)
        info.setPlainText(
            "\n".join(
                [
                    f"Drive OAuth: {drive_status}",
                    "",
                    "Metadata hiện được chuẩn bị theo mẫu nội bộ để bạn chỉnh bằng AI ngoài hoặc sửa tay trực tiếp.",
                    "Theme áp dụng cho toàn app sau khi lưu.",
                    "Workspace gần đây: chọn một mục rồi bấm Dùng workspace này nếu muốn chuyển nhanh.",
                ]
            )
        )

        layout.addWidget(QLabel("Theme"))
        layout.addWidget(self.theme_combo)
        layout.addWidget(info)

        layout.addWidget(QLabel("Workspace gần đây"))
        self.workspace_list = QListWidget()
        for path in recent_workspaces:
            item = QListWidgetItem(str(path))
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            self.workspace_list.addItem(item)
        self.workspace_list.itemDoubleClicked.connect(self._pick_workspace)
        layout.addWidget(self.workspace_list, 1)

        quick_button = QPushButton("Dùng workspace này")
        quick_button.clicked.connect(self._pick_workspace)
        layout.addWidget(quick_button)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _pick_workspace(self, *_args) -> None:
        item = self.workspace_list.currentItem()
        if item is None:
            return
        self.selected_workspace = Path(item.data(Qt.ItemDataRole.UserRole))

    def get_theme(self) -> str:
        return self.theme_combo.currentText()
