"""
AutoTabloide AI - Dark Theme QSS
================================
Estética Adobe-like com tema dark profissional.
"""

from PySide6.QtWidgets import QApplication


DARK_THEME_QSS = """
/* === Global === */
QMainWindow, QWidget {
    background-color: #0D0D0D;
    color: #E0E0E0;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}

/* === Sidebar === */
QFrame#sidebar {
    background-color: #1A1A2E;
    border-right: 1px solid #2D2D44;
    min-width: 200px;
    max-width: 200px;
}

QPushButton.nav-button {
    background-color: transparent;
    color: #A0A0A0;
    border: none;
    border-radius: 8px;
    padding: 12px 16px;
    text-align: left;
    font-size: 14px;
    margin: 2px 8px;
}

QPushButton.nav-button:hover {
    background-color: #2D2D44;
    color: #FFFFFF;
}

QPushButton.nav-button:checked {
    background-color: #6C5CE7;
    color: #FFFFFF;
}

/* === Status Bar === */
QStatusBar {
    background-color: #1A1A2E;
    color: #808080;
    border-top: 1px solid #2D2D44;
    padding: 4px;
}

/* === Scroll Bars === */
QScrollBar:vertical {
    background-color: #1A1A2E;
    width: 12px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #3D3D5C;
    border-radius: 6px;
    min-height: 30px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #6C5CE7;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background-color: #1A1A2E;
    height: 12px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background-color: #3D3D5C;
    border-radius: 6px;
    min-width: 30px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #6C5CE7;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* === Content Area === */
QFrame#content-area {
    background-color: #0D0D0D;
}

/* === Labels === */
QLabel.title {
    font-size: 24px;
    font-weight: bold;
    color: #FFFFFF;
}

QLabel.subtitle {
    font-size: 14px;
    color: #808080;
}

QLabel.card-value {
    font-size: 36px;
    font-weight: bold;
    color: #6C5CE7;
}

/* === Cards === */
QFrame.card {
    background-color: #1A1A2E;
    border: 1px solid #2D2D44;
    border-radius: 12px;
    padding: 16px;
}

QFrame.card:hover {
    border-color: #6C5CE7;
}

/* === Buttons === */
QPushButton {
    background-color: #6C5CE7;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #5B4BD5;
}

QPushButton:pressed {
    background-color: #4A3AC4;
}

QPushButton:disabled {
    background-color: #3D3D5C;
    color: #808080;
}

QPushButton.secondary {
    background-color: transparent;
    border: 1px solid #6C5CE7;
    color: #6C5CE7;
}

QPushButton.secondary:hover {
    background-color: #6C5CE722;
}

QPushButton.danger {
    background-color: #E74C3C;
}

QPushButton.danger:hover {
    background-color: #C0392B;
}

/* === Inputs === */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #16213e;
    border: 1px solid #2D2D44;
    border-radius: 6px;
    padding: 8px 12px;
    color: #E0E0E0;
    selection-background-color: #6C5CE7;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #6C5CE7;
}

/* === Table View === */
QTableView, QListView, QTreeView {
    background-color: #0D0D0D;
    border: 1px solid #2D2D44;
    border-radius: 8px;
    gridline-color: #2D2D44;
    selection-background-color: #6C5CE744;
}

QTableView::item, QListView::item, QTreeView::item {
    padding: 8px;
}

QTableView::item:selected, QListView::item:selected, QTreeView::item:selected {
    background-color: #6C5CE744;
}

QHeaderView::section {
    background-color: #1A1A2E;
    color: #A0A0A0;
    padding: 10px;
    border: none;
    border-bottom: 1px solid #2D2D44;
    font-weight: bold;
}

/* === Tab Widget === */
QTabWidget::pane {
    border: 1px solid #2D2D44;
    border-radius: 8px;
    background-color: #0D0D0D;
}

QTabBar::tab {
    background-color: #1A1A2E;
    color: #A0A0A0;
    padding: 10px 20px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #6C5CE7;
    color: #FFFFFF;
}

QTabBar::tab:hover:!selected {
    background-color: #2D2D44;
}

/* === Progress Bar === */
QProgressBar {
    background-color: #1A1A2E;
    border: none;
    border-radius: 6px;
    height: 8px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #6C5CE7;
    border-radius: 6px;
}

/* === Splitter === */
QSplitter::handle {
    background-color: #2D2D44;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}

/* === Menu === */
QMenuBar {
    background-color: #1A1A2E;
    border-bottom: 1px solid #2D2D44;
}

QMenuBar::item {
    padding: 8px 12px;
}

QMenuBar::item:selected {
    background-color: #2D2D44;
}

QMenu {
    background-color: #1A1A2E;
    border: 1px solid #2D2D44;
    border-radius: 8px;
    padding: 4px;
}

QMenu::item {
    padding: 8px 24px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #6C5CE7;
}

QMenu::separator {
    height: 1px;
    background-color: #2D2D44;
    margin: 4px 8px;
}

/* === Tooltip === */
QToolTip {
    background-color: #1A1A2E;
    color: #E0E0E0;
    border: 1px solid #6C5CE7;
    border-radius: 4px;
    padding: 6px;
}

/* === Dialog === */
QDialog {
    background-color: #0D0D0D;
}

/* === ComboBox === */
QComboBox {
    background-color: #16213e;
    border: 1px solid #2D2D44;
    border-radius: 6px;
    padding: 8px 12px;
    color: #E0E0E0;
}

QComboBox:hover {
    border-color: #6C5CE7;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #1A1A2E;
    border: 1px solid #2D2D44;
    selection-background-color: #6C5CE7;
}

/* === SpinBox === */
QSpinBox, QDoubleSpinBox {
    background-color: #16213e;
    border: 1px solid #2D2D44;
    border-radius: 6px;
    padding: 8px;
    color: #E0E0E0;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #6C5CE7;
}

/* === GroupBox === */
QGroupBox {
    border: 1px solid #2D2D44;
    border-radius: 8px;
    margin-top: 16px;
    padding-top: 16px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: #6C5CE7;
}
"""


def apply_theme(app: QApplication) -> None:
    """Aplica o tema dark à aplicação."""
    app.setStyleSheet(DARK_THEME_QSS)
