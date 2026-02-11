"""QAbstractTableModel for displaying archive contents in a QTreeView."""

from __future__ import annotations

import os
from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, QSortFilterProxyModel
from PySide6.QtGui import QIcon
import qtawesome as qta

from zip_gui.archive_handler import ArchiveEntry, ArchiveInfo, format_size
from zip_gui.resources import Colors


class ArchiveModel(QAbstractTableModel):
    """Table model that presents archive entries for a specific directory level."""

    COLUMNS = ["名称", "大小", "压缩大小", "修改时间", "CRC", "类型"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._archive_info: ArchiveInfo | None = None
        self._all_entries: list[ArchiveEntry] = []
        self._current_entries: list[ArchiveEntry] = []
        self._current_path: str = ""  # Current directory inside archive

        # Icons
        self._folder_icon = qta.icon("fa5s.folder", color=Colors.YELLOW)
        self._file_icon = qta.icon("fa5s.file", color=Colors.WHITE)
        self._archive_icon = qta.icon("fa5s.file-archive", color=Colors.ORANGE)

    @property
    def current_path(self) -> str:
        return self._current_path

    @property
    def archive_path(self) -> str:
        return self._archive_info.path if self._archive_info else ""

    def set_archive(self, archive_info: ArchiveInfo) -> None:
        """Load archive contents into the model."""
        self.beginResetModel()
        self._archive_info = archive_info
        self._all_entries = archive_info.entries
        self._current_path = ""
        self._refresh_current_entries()
        self.endResetModel()

    def navigate_to(self, path: str) -> None:
        """Navigate to a subdirectory inside the archive."""
        self.beginResetModel()
        self._current_path = path
        self._refresh_current_entries()
        self.endResetModel()

    def go_up(self) -> bool:
        """Navigate up one level. Returns False if already at root."""
        if not self._current_path:
            return False
        # Remove trailing slash, then go to parent
        trimmed = self._current_path.rstrip("/")
        parent = os.path.dirname(trimmed)
        self.beginResetModel()
        self._current_path = (parent + "/") if parent else ""
        self._refresh_current_entries()
        self.endResetModel()
        return True

    def entry_at(self, row: int) -> ArchiveEntry | None:
        """Get the ArchiveEntry at the given row."""
        if 0 <= row < len(self._current_entries):
            return self._current_entries[row]
        return None

    def clear(self) -> None:
        """Clear all data."""
        self.beginResetModel()
        self._archive_info = None
        self._all_entries = []
        self._current_entries = []
        self._current_path = ""
        self.endResetModel()

    def _refresh_current_entries(self) -> None:
        """Filter entries to show only direct children of current_path."""
        self._current_entries = []
        seen_dirs: set[str] = set()

        prefix = self._current_path

        for entry in self._all_entries:
            if not entry.filename.startswith(prefix):
                continue

            relative = entry.filename[len(prefix):]
            if not relative or relative == "/":
                continue

            # Check if it's a direct child
            parts = relative.rstrip("/").split("/")
            if len(parts) == 1:
                # Direct child
                self._current_entries.append(entry)
            elif len(parts) > 1:
                # It's inside a subdirectory — add a virtual directory entry if not seen
                dir_name = parts[0] + "/"
                full_dir = prefix + dir_name
                if full_dir not in seen_dirs:
                    seen_dirs.add(full_dir)
                    # Calculate aggregated size for this directory
                    dir_size = sum(
                        e.file_size
                        for e in self._all_entries
                        if e.filename.startswith(full_dir) and not e.is_dir
                    )
                    dir_entry = ArchiveEntry(
                        filename=full_dir,
                        is_dir=True,
                        file_size=dir_size,
                    )
                    self._current_entries.append(dir_entry)

        # Sort: directories first, then by name
        self._current_entries.sort(
            key=lambda e: (0 if e.is_dir else 1, e.basename.lower())
        )

    # --- QAbstractTableModel interface ---

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._current_entries)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None

        entry = self._current_entries[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return entry.basename
            elif col == 1:
                return format_size(entry.file_size) if not entry.is_dir else ""
            elif col == 2:
                return format_size(entry.compress_size) if entry.compress_size and not entry.is_dir else ""
            elif col == 3:
                return entry.date_time.strftime("%Y-%m-%d %H:%M") if entry.date_time else ""
            elif col == 4:
                return entry.crc if not entry.is_dir else ""
            elif col == 5:
                if entry.is_dir:
                    return "文件夹"
                ext = os.path.splitext(entry.basename)[1]
                return f"{ext.upper()} 文件" if ext else "文件"

        elif role == Qt.ItemDataRole.DecorationRole and col == 0:
            if entry.is_dir:
                return self._folder_icon
            return self._file_icon

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (1, 2):
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter

        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.COLUMNS[section]
        return None


class ArchiveSortProxyModel(QSortFilterProxyModel):
    """Proxy model that sorts archive entries with directories first."""

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        source = self.sourceModel()
        if not isinstance(source, ArchiveModel):
            return super().lessThan(left, right)

        left_entry = source.entry_at(left.row())
        right_entry = source.entry_at(right.row())

        if left_entry and right_entry:
            # Directories always come first
            if left_entry.is_dir != right_entry.is_dir:
                return left_entry.is_dir

        return super().lessThan(left, right)
