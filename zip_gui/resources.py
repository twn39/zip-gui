"""Centralized icon and color definitions using qtawesome."""

import qtawesome as qta
from PySide6.QtGui import QIcon


# --- Color Palette ---
class Colors:
    # Blender Dark Theme Palette
    BACKGROUND = "#333333"
    PANEL_BG = "#282828"
    HEADER_BG = "#1D1D1D"
    TEXT = "#EEEEEE"
    TEXT_SUB = "#CCCCCC"
    
    # Accents
    ORANGE = "#EB7D00"  # Blender Selection / Active
    BLUE = "#5E81AC"    # Optional cool accent
    GREEN = "#7FB068"   # Success / Add
    RED = "#CC6666"     # Error / Delete
    YELLOW = "#EBCB8B"  # Warning / Folder
    
    WHITE = "#FFFFFF"
    GREY = "#727272"
    
    # Mappings for existing code
    ACCENT = ORANGE
    CYAN = BLUE
    PURPLE = "#B48EAD"


# --- Icon definitions ---
def icon(name: str, color: str = Colors.WHITE) -> QIcon:
    """Create a qtawesome icon with the given name and color."""
    return qta.icon(name, color=color)


class Icons:
    """All toolbar / menu / context menu icons."""

    # Toolbar
    ADD = ("fa5s.plus-circle", Colors.GREEN)
    EXTRACT = ("fa5s.external-link-alt", Colors.BLUE)
    TEST = ("fa5s.check-circle", Colors.YELLOW)
    COPY = ("fa5s.copy", Colors.CYAN)
    MOVE = ("fa5s.arrows-alt", Colors.ORANGE)
    DELETE = ("fa5s.trash-alt", Colors.RED)
    INFO = ("fa5s.info-circle", Colors.WHITE)
    RENAME = ("fa5s.pencil-alt", Colors.YELLOW)

    # Navigation
    UP = ("fa5s.arrow-up", Colors.WHITE)
    BACK = ("fa5s.arrow-left", Colors.WHITE)
    FORWARD = ("fa5s.arrow-right", Colors.WHITE)
    HOME = ("fa5s.home", Colors.WHITE)
    REFRESH = ("fa5s.sync-alt", Colors.WHITE)

    # File types
    FOLDER = ("fa5s.folder", Colors.YELLOW)
    FOLDER_OPEN = ("fa5s.folder-open", Colors.YELLOW)
    FILE = ("fa5s.file", Colors.WHITE)
    ARCHIVE = ("fa5s.file-archive", Colors.ORANGE)

    # Menu
    NEW_ARCHIVE = ("fa5s.file-archive", Colors.GREEN)
    OPEN = ("fa5s.folder-open", Colors.BLUE)
    EXIT = ("fa5s.sign-out-alt", Colors.RED)
    SELECT_ALL = ("fa5s.check-double", Colors.WHITE)
    SETTINGS = ("fa5s.cog", Colors.GREY)
    ABOUT = ("fa5s.question-circle", Colors.BLUE)

    @classmethod
    def get(cls, attr: str) -> QIcon:
        """Get a QIcon by attribute name."""
        icon_def = getattr(cls, attr)
        return qta.icon(icon_def[0], color=icon_def[1])
