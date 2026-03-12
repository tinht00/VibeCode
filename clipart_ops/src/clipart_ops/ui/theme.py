"""Theme helpers cho PySide6 UI."""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


LIGHT_QSS = """
QMainWindow, QWidget {
    color: #1f3347;
    font-size: 13px;
}
QMainWindow {
    background: #f3f7fb;
}
QWidget {
    selection-background-color: #d9ecff;
    selection-color: #17324d;
}
QToolBar {
    background: #f8fbfe;
    border: 0;
    spacing: 8px;
    padding: 10px 14px;
}
QToolButton, QPushButton {
    background: #ffffff;
    border: 1px solid #d6e4f0;
    border-radius: 14px;
    padding: 9px 14px;
    color: #25415d;
    font-weight: 600;
}
QToolButton:hover, QPushButton:hover {
    background: #f2f8ff;
    border: 1px solid #a9cdee;
}
QToolButton:pressed, QPushButton:pressed {
    background: #e8f2fc;
}
QPushButton:disabled, QToolButton:disabled {
    background: #f2f4f7;
    color: #93a5b8;
    border: 1px solid #e1e7ee;
}
#primaryActionButton {
    background: #58a6f0;
    color: #ffffff;
    border: 1px solid #6cb3f2;
    border-radius: 16px;
    padding: 12px 18px;
    font-size: 14px;
    font-weight: 700;
}
#primaryActionButton:hover {
    background: #469aeb;
    border: 1px solid #5ca8ef;
}
QGroupBox {
    background: #ffffff;
    border: 1px solid #e0e8f1;
    border-radius: 24px;
    margin-top: 16px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 6px;
    color: #5c728a;
}
#dashboardCard {
    background: #f8fbfe;
    border: 1px solid #e2ebf4;
    border-radius: 18px;
}
#subsectionTitle {
    font-size: 13px;
    font-weight: 700;
    color: #49627d;
    padding-left: 2px;
}
#metricSummary {
    color: #58708a;
}
#sectionTitle {
    font-size: 16px;
    font-weight: 700;
    color: #1d3954;
    padding-left: 2px;
}
#sectionHint {
    color: #7288a0;
    padding-left: 2px;
}
#workflowSummary {
    font-size: 13px;
    font-weight: 600;
    color: #3b536c;
}
#workflowStepsList {
    background: #f8fbfe;
    border: 1px solid #dfe8f1;
    border-radius: 16px;
    padding: 6px;
}
#workflowStepsList::item {
    background: #ffffff;
    border: 1px solid #e3ebf3;
    border-radius: 12px;
    padding: 8px 10px;
    margin: 4px 2px;
}
#workflowStepsList::item:hover {
    background: #f4f9ff;
    border: 1px solid #cfe0ef;
}
QLineEdit, QComboBox, QTextEdit, QTextBrowser, QListWidget, QTableWidget {
    background: #ffffff;
    border: 1px solid #dbe6f0;
    border-radius: 18px;
}
QScrollArea {
    background: transparent;
    border: 0;
}
QLineEdit, QComboBox {
    padding: 8px 12px;
}
QTextEdit, QTextBrowser, QListWidget, QTableWidget {
    alternate-background-color: #f7fbff;
}
QLineEdit:focus, QTextEdit:focus, QTextBrowser:focus, QListWidget:focus, QTableWidget:focus, QComboBox:focus {
    border: 1px solid #8fc0eb;
}
QHeaderView::section {
    background: #eef5fb;
    color: #39546f;
    border: 0;
    border-right: 1px solid #dfE8f1;
    border-bottom: 1px solid #dfe8f1;
    padding: 10px 8px;
}
QListWidget::item, QTableWidget::item {
    border-radius: 10px;
}
QListWidget::item:selected, QTableWidget::item:selected {
    background: #dfefff;
    color: #17324d;
}
QListWidget::item:hover, QTableWidget::item:hover {
    background: #f2f8ff;
}
#workspaceBrowser {
    padding: 12px;
}
#workspaceBrowser::item {
    background: #fcfdff;
    border: 1px solid #dfe8f1;
    border-radius: 26px;
    margin: 8px;
    padding: 14px;
}
#workspaceBrowser::item:selected {
    background: #e7f3ff;
    border: 1px solid #93c4ef;
}
#workspaceBrowser::item:hover {
    background: #f2f8ff;
    border: 1px solid #b9d8f3;
}
#largeIconBrowser {
    padding: 10px;
}
#largeIconBrowser::item {
    background: #fcfdff;
    border: 1px solid #e0e8f1;
    border-radius: 22px;
    margin: 8px;
    padding: 12px;
}
#largeIconBrowser::item:selected {
    background: #e8f4ff;
    border: 1px solid #9bc7ee;
}
#largeIconBrowser::item:hover {
    background: #f3f8fe;
    border: 1px solid #bedaf2;
}
QTabWidget::pane {
    border: 0;
    margin-top: 8px;
}
QTabBar::tab {
    background: #edf4fb;
    border: 1px solid #dbe6f0;
    border-top-left-radius: 14px;
    border-top-right-radius: 14px;
    color: #607890;
    padding: 9px 16px;
    margin-right: 6px;
}
QTabBar::tab:selected {
    background: #ffffff;
    color: #17324d;
    border-color: #aacbe8;
}
QTabBar::tab:hover:!selected {
    background: #f2f8ff;
}
QStatusBar {
    background: #f7fbff;
    color: #6b8197;
    border-top: 1px solid #dfe8f1;
}
QProgressBar {
    background: #edf4fb;
    border: 1px solid #d8e4ef;
    border-radius: 10px;
    text-align: center;
}
QProgressBar::chunk {
    background: #98ccf7;
    border-radius: 9px;
}
QSplitter::handle {
    background: #e6edf5;
}
QScrollBar:vertical, QScrollBar:horizontal {
    background: #f0f5fa;
    border-radius: 8px;
}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #bfd9ef;
    border-radius: 8px;
    min-height: 28px;
    min-width: 28px;
}
QScrollBar::add-line, QScrollBar::sub-line {
    background: none;
    border: none;
}
"""


DARK_QSS = """
QMainWindow, QWidget {
    color: #dce6f4;
    font-size: 13px;
}
QMainWindow {
    background: #0f1722;
}
QWidget {
    selection-background-color: #325b84;
    selection-color: #f4f7fb;
}
QToolBar {
    background: #121c2a;
    border: 0;
    spacing: 8px;
    padding: 10px 14px;
}
QToolButton, QPushButton {
    background: #172435;
    border: 1px solid #2c4058;
    border-radius: 14px;
    padding: 9px 14px;
    color: #d7e5f6;
    font-weight: 600;
}
QToolButton:hover, QPushButton:hover {
    background: #1d3046;
    border: 1px solid #567aa5;
}
QPushButton:disabled, QToolButton:disabled {
    background: #18212c;
    color: #7d90a5;
    border: 1px solid #283240;
}
#primaryActionButton {
    background: #3b79b7;
    color: #ffffff;
    border: 1px solid #5a98d5;
    border-radius: 16px;
    padding: 12px 18px;
    font-size: 14px;
    font-weight: 700;
}
#primaryActionButton:hover {
    background: #4c88c4;
}
QGroupBox {
    background: #162231;
    border: 1px solid #26384e;
    border-radius: 24px;
    margin-top: 16px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 6px;
    color: #a8bdd5;
}
#dashboardCard {
    background: #101b29;
    border: 1px solid #25384d;
    border-radius: 18px;
}
#subsectionTitle {
    font-size: 13px;
    font-weight: 700;
    color: #d3e0ef;
    padding-left: 2px;
}
#metricSummary {
    color: #cad8e8;
}
#sectionTitle {
    font-size: 16px;
    font-weight: 700;
    color: #e4edf8;
    padding-left: 2px;
}
#sectionHint {
    color: #95a8bd;
    padding-left: 2px;
}
#workflowSummary {
    font-size: 13px;
    font-weight: 600;
    color: #d2deec;
}
#workflowStepsList {
    background: #101a28;
    border: 1px solid #25384d;
    border-radius: 16px;
    padding: 6px;
}
#workflowStepsList::item {
    background: #172434;
    border: 1px solid #293d54;
    border-radius: 12px;
    padding: 8px 10px;
    margin: 4px 2px;
}
#workflowStepsList::item:hover {
    background: #1c2d42;
    border: 1px solid #3a5675;
}
QLineEdit, QComboBox, QTextEdit, QTextBrowser, QListWidget, QTableWidget {
    background: #0f1926;
    border: 1px solid #24364b;
    border-radius: 18px;
}
QScrollArea {
    background: transparent;
    border: 0;
}
QLineEdit, QComboBox {
    padding: 8px 12px;
}
QTextEdit, QTextBrowser, QListWidget, QTableWidget {
    alternate-background-color: #142133;
}
QLineEdit:focus, QTextEdit:focus, QTextBrowser:focus, QListWidget:focus, QTableWidget:focus, QComboBox:focus {
    border: 1px solid #7cadde;
}
QHeaderView::section {
    background: #1a283a;
    color: #d4e1f0;
    border: 0;
    border-right: 1px solid #24364b;
    border-bottom: 1px solid #24364b;
    padding: 10px 8px;
}
QListWidget::item:selected, QTableWidget::item:selected {
    background: #27496c;
    color: #f4f7fb;
}
QListWidget::item:hover, QTableWidget::item:hover {
    background: #1a2a3d;
}
#workspaceBrowser {
    padding: 12px;
}
#workspaceBrowser::item {
    background: #172536;
    border: 1px solid #2b3e56;
    border-radius: 26px;
    margin: 8px;
    padding: 14px;
}
#workspaceBrowser::item:selected {
    background: #264f76;
    border: 1px solid #7fb3e2;
}
#workspaceBrowser::item:hover {
    background: #1d3148;
    border: 1px solid #527aa3;
}
#largeIconBrowser {
    padding: 10px;
}
#largeIconBrowser::item {
    background: #172536;
    border: 1px solid #2b3e56;
    border-radius: 22px;
    margin: 8px;
    padding: 12px;
}
#largeIconBrowser::item:selected {
    background: #264d72;
    border: 1px solid #7caee0;
}
#largeIconBrowser::item:hover {
    background: #1d3148;
    border: 1px solid #557da5;
}
QTabWidget::pane {
    border: 0;
    margin-top: 8px;
}
QTabBar::tab {
    background: #182638;
    border: 1px solid #2a3d54;
    border-top-left-radius: 14px;
    border-top-right-radius: 14px;
    color: #afc3d8;
    padding: 9px 16px;
    margin-right: 6px;
}
QTabBar::tab:selected {
    background: #22344b;
    color: #e4edf8;
    border-color: #5d84ae;
}
QTabBar::tab:hover:!selected {
    background: #1b2d41;
}
QStatusBar {
    background: #121c2a;
    color: #99aeca;
    border-top: 1px solid #26384e;
}
QProgressBar {
    background: #172536;
    border: 1px solid #26384e;
    border-radius: 10px;
    text-align: center;
}
QProgressBar::chunk {
    background: #5c92c8;
    border-radius: 9px;
}
QSplitter::handle {
    background: #1b2738;
}
QScrollBar:vertical, QScrollBar:horizontal {
    background: #121c2a;
    border-radius: 8px;
}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #3d5d80;
    border-radius: 8px;
    min-height: 28px;
    min-width: 28px;
}
QScrollBar::add-line, QScrollBar::sub-line {
    background: none;
    border: none;
}
"""


def _apply_light_palette(app: QApplication) -> None:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#f3f7fb"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#1f3347"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#f7fbff"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#1f3347"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#25415d"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#d9ecff"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#17324d"))
    app.setPalette(palette)


def apply_theme(app: QApplication, theme: str) -> None:
    """Áp theme toàn app."""
    selected = theme if theme in {"auto", "dark", "light"} else "auto"
    resolved = "light" if selected == "auto" else selected
    if resolved == "dark":
        app.setStyleSheet(DARK_QSS)
        return

    _apply_light_palette(app)
    app.setStyleSheet(LIGHT_QSS)
