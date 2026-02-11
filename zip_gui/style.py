"""Blender-inspired dark theme (Refined)."""

theme_style = """
/* === Global === */
QWidget {
    background-color: #333333;
    color: #EEEEEE;
    font-family: "Inter", "Segoe UI", "PingFang SC", sans-serif;
    font-size: 11pt;
    selection-background-color: #4772B3; /* Softer Blue selection */
    selection-color: #FFFFFF;
}

/* === Menu Bar === */
QMenuBar {
    background-color: #1D1D1D;
    border-bottom: 1px solid #111111;
    padding: 1px;
}

QMenuBar::item {
    background: transparent;
    padding: 6px 12px;
    border-radius: 4px;
    margin: 1px;
}

QMenuBar::item:selected {
    background-color: #4772B3;
}

QMenuBar::item:pressed {
    background-color: #355688;
}

QMenu {
    background-color: #282828;
    border: 1px solid #444444;
    border-radius: 6px;
    padding: 4px; /* Padding inside the menu container */
}

QMenu::item {
    padding: 4px 24px 4px 28px; /* Adjusted padding */
    border-radius: 4px; /* Rounded selection */
    margin: 2px; /* Margin around items */
}

QMenu::item:selected {
    background-color: #4772B3;
}

QMenu::separator {
    height: 4px; /* Use height to create a small gap instead of a line */
    background: transparent;
    margin: 0px;
}

QMenu::icon {
    padding-left: 10px;
    position: absolute;
    top: 1px;
    right: 1px;
    bottom: 1px;
    left: 10px; /* Adjust icon position */
}

/* === ToolBar === */
QToolBar {
    background-color: #282828;
    border-bottom: 1px solid #111111;
    spacing: 6px;
    padding: 6px 8px;
}

QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px 8px;
    color: #EEEEEE;
    font-size: 10pt;
}

QToolButton:hover {
    background-color: #444444;
    border: 1px solid #555555;
}

QToolButton:pressed {
    background-color: #4772B3;
    border: 1px solid #4772B3;
}

/* === Address Bar === */
#breadcrumb_container {
    background-color: #1D1D1D;
    border: 1px solid #111111;
    border-radius: 4px; /* Small rounded rect */
}

#breadcrumb_btn {
    background: transparent;
    border: none;
    border-radius: 3px;
    padding: 2px 10px;
    color: #CCCCCC;
    font-size: 10pt;
}

#breadcrumb_btn:hover {
    background-color: #444444;
    color: #FFFFFF;
}

#breadcrumb_sep {
    background: transparent;
    border: none;
    color: #888888;
    font-size: 11pt;
    padding: 0;
    margin: 0;
    font-weight: bold;
}

QPushButton#up_btn {
    background-color: #444444;
    border: 1px solid #111111;
    border-radius: 4px;
}

QPushButton#up_btn:hover {
    background-color: #555555;
    border: 1px solid #666666;
}

/* === Input Fields === */
QLineEdit {
    background-color: #1D1D1D;
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 4px 8px;
    color: #EEEEEE;
}

QLineEdit:focus {
    border: 1px solid #4772B3;
}

/* === Tree View (File List) === */
QTreeView {
    background-color: #282828;
    border: 1px solid #111111; /* Thinner border */
    border-radius: 4px;
    alternate-background-color: #2B2B2B;
    outline: none;
}

QTreeView::item {
    padding: 4px;
    border: none;
    border-radius: 2px;
}

QTreeView::item:hover {
    background-color: #3A3A3A;
}

QTreeView::item:selected {
    background-color: #4772B3; /* Softer Blue */
    color: #FFFFFF;
}

QTreeView::item:selected:!active {
    background-color: #3D3D3D; /* Dimmed when not focused */
}

QHeaderView {
    background-color: #282828;
    border: none;
}

QHeaderView::section {
    background-color: #282828;
    color: #CCCCCC;
    padding: 6px 10px;
    border: none;
    border-right: 1px solid #111111;
    border-bottom: 1px solid #111111; /* Reduced from 2px */
    font-weight: 600;
    font-size: 10pt;
}

QHeaderView::section:hover {
    background-color: #333333;
}

/* === Status Bar === */
QStatusBar {
    background: transparent; /* Remove background color */
    border-top: 1px solid #444444; /* Subtle separator */
    color: #CCCCCC;
    padding: 6px 12px; /* More padding */
    font-size: 10pt;
}

QStatusBar::item {
    border: none;
}

QStatusBar QLabel {
    background: transparent;
    padding: 0 4px;
}

/* === Progress Bar === */
QProgressBar {
    border: 1px solid #111111;
    border-radius: 4px;
    text-align: center;
    background-color: #1D1D1D;
    color: #FFFFFF;
}

QProgressBar::chunk {
    background-color: #4772B3;
    border-radius: 3px;
}

/* === Scroll Bars === */
QScrollBar:vertical {
    background: #242424;
    width: 12px;
    margin: 2px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background: #555555;
    min-height: 30px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #777777;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: #242424;
    height: 12px;
    margin: 2px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background: #555555;
    min-width: 30px;
    border-radius: 4px;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* === Buttons === */
QPushButton {
    background-color: #444444;
    border: 1px solid #222222;
    border-radius: 4px;
    padding: 6px 16px;
    color: #EEEEEE;
}

QPushButton:hover {
    background-color: #505050;
    border-color: #666666;
}

QPushButton:pressed {
    background-color: #4772B3;
    border-color: #4772B3;
}

/* === ToolTip === */
QToolTip {
    background-color: #1D1D1D;
    color: #EEEEEE;
    border: 1px solid #444444;
    padding: 4px;
}
"""


def load_stylesheet() -> str:
    return theme_style
