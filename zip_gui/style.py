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
    background-color: #4D4D4D; 
    border: 1px solid #606060; 
    border-radius: 4px; 
    padding: 6px 12px; 
    color: #FFFFFF; 
    min-height: 22px; 
    min-width: 30px; 
    outline: none; 
}

QPushButton:hover {
    background-color: #5A5A5A; 
    border-color: #777777;
}

QPushButton:pressed {
    background-color: #636363; /* Darker/different shade when pressed */
}

QPushButton:disabled {
    background-color: #404040;
    color: #808080;
    border-color: #505050;
}

QPushButton#ActionButton {
    font-weight: bold;
    background-color: #3584e4; 
    color: #FFFFFF; 
    border: 1px solid #1e6fbf; 
    min-width: 100px; 
}
QPushButton#ActionButton:hover {
    background-color: #4991e9; 
    border-color: #3584e4;
}
QPushButton#ActionButton:pressed {
    background-color: #1e6fbf; 
    border-color: #15538c;
}
QPushButton#ActionButton:disabled {
    background-color: #77a8ec; 
    color: rgba(255, 255, 255, 0.7); 
    border-color: #5c8dd8;
}


QProgressBar {
    border: 1px solid #555555;
    border-radius: 5px;
    text-align: center;
    background-color: #3C3C3C;
    color: #E0E0E0;
    min-height: 20px;
}

QProgressBar::chunk {
    background-color: #50A0D0; 
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
    background-color: transparent;
    font-size: 10pt;
}
QRadioButton::indicator {
    width: 16px; 
    height: 16px;
    border: 1px solid #777777; 
    border-radius: 9px; 
    background-color: #3D3D3D; 
}
QRadioButton::indicator:checked {
    background-color: #3584e4; 
    border: 1px solid #3584e4; 
}
QRadioButton::indicator:unchecked:hover {
    border: 1px solid #3584e4; 
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
