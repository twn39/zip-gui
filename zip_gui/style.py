theme_style = """
QWidget {
    background-color: #2E2E2E;
    color: #E0E0E0;
    font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
    font-size: 12pt;
}

QGroupBox {
    border: 1px solid #444444;
    border-radius: 5px;
    margin-top: 1ex; /* leave space at the top for the title */
    font-weight: bold;
    color: #C0C0C0;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left; /* position at the top center */
    padding: 0 5px;
    background-color: #2E2E2E; /* Match background */
    left: 10px; /* Adjust horizontal position */
}


QLabel {
    color: #C0C0C0;
    padding: 2px;
}

QLineEdit {
    background-color: #3C3C3C;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 6px;
    color: #E0E0E0;
    min-height: 22px;
}

QLineEdit:focus {
    border: 1px solid #77AADD;
}

QComboBox {
    background-color: #3C3C3C;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 6px 10px 6px 6px;
    min-width: 6em;
    color: #E0E0E0;
    min-height: 22px;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left-width: 1px;
    border-left-color: #555555;
    border-left-style: solid;
    border-top-right-radius: 3px;
    border-bottom-right-radius: 3px;
    background-color: #424242;
}

QComboBox QAbstractItemView {
    background-color: #3C3C3C;
    border: 1px solid #555555;
    selection-background-color: #50A0D0;
    selection-color: #FFFFFF;
    color: #E0E0E0;
    padding: 4px;
}

QPushButton {
    background-color: #4A4A4A;
    border: 1px solid #606060;
    border-radius: 4px;
    padding: 6px 12px;
    color: #E0E0E0;
    min-width: 30px;
    min-height: 22px;
}

QPushButton:hover {
    background-color: #5A5A5A;
    border-color: #777777;
}

QPushButton:pressed {
    background-color: #6A6A6A;
}

QPushButton:disabled {
    background-color: #404040;
    color: #808080;
    border-color: #505050;
}

/* === 主操作按钮样式 (ActionButton) === */
/* 默认是打包按钮的绿色 */
QPushButton#ActionButton {
    font-weight: bold;
    background-color: #4CAF50; /* 主要绿色 */
    color: #FFFFFF; /* 白色文字 */
    min-width: 100px; /* 稍宽一点 */
}
QPushButton#ActionButton:hover {
    background-color: #66BB6A;
    color: #FFFFFF;
}
QPushButton#ActionButton:pressed {
    background-color: #388E3C;
    color: #FFFFFF;
}
QPushButton#ActionButton:disabled {
    background-color: #A5D6A7;
    color: #616161;
    border-color: #81C784;
}
/* 如果需要在解压模式下改变按钮颜色，可以在 switch_mode 中用 setStyleSheet 实现 */


QProgressBar {
    border: 1px solid #555555;
    border-radius: 5px;
    text-align: center;
    background-color: #3C3C3C;
    color: #E0E0E0;
    min-height: 20px;
}

QProgressBar::chunk {
    background-color: #50A0D0; /* 默认蓝色进度 */
    border-radius: 5px;
}

QLabel#StatusLabel {
    color: #A9A9A9;
    font-size: 10pt;
    padding: 5px;
}

QRadioButton {
    color: #C0C0C0;
    padding: 3px;
}
QRadioButton::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #555555;
    border-radius: 7px; /* 圆形 */
    background-color: #3C3C3C;
}
QRadioButton::indicator:checked {
    background-color: #50A0D0; /* 选中时的颜色 */
    border: 1px solid #77AADD;
}
QRadioButton::indicator:unchecked:hover {
    border: 1px solid #77AADD;
}
QRadioButton:disabled {
    color: #808080;
}
QRadioButton::indicator:disabled {
    border: 1px solid #404040;
    background-color: #404040;
}


QMessageBox { background-color: #333333; }
QMessageBox QLabel { color: #E0E0E0; font-size: 11pt; }
QMessageBox QPushButton {
    background-color: #4A4A4A; border: 1px solid #606060; border-radius: 4px;
    padding: 6px 12px; color: #E0E0E0; min-width: 70px; min-height: 22px;
}
QMessageBox QPushButton:hover { background-color: #5A5A5A; }
QMessageBox QPushButton:pressed { background-color: #6A6A6A; }

QToolTip {
    background-color: #424242; color: #E0E0E0; border: 1px solid #606060;
    padding: 4px; border-radius: 3px; opacity: 230; font-size: 10pt;
}

QFrame[frameShape="5"] { /* HLine specific style */
    border: none;
    border-top: 1px solid #444444; /* Line color */
    margin: 5px 0px; /* Add some vertical margin */
}
"""


def load_stylesheet() -> str:
    return theme_style
