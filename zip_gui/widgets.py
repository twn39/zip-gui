"""Custom widgets: AddressBar with breadcrumb navigation."""

from __future__ import annotations

import os

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSizePolicy,
)
from PySide6.QtCore import Signal, Qt
import qtawesome as qta

from zip_gui.resources import Colors


class AddressBar(QWidget):
    """Address bar with up button, path breadcrumbs, and editable path input."""

    path_changed = Signal(str)  # emitted when user navigates to a new path

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_path = ""
        self._in_archive = False
        self._archive_path = ""
        self._archive_internal_path = ""
        self._editing = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Up button
        self.up_btn = QPushButton()
        self.up_btn.setIcon(qta.icon("fa5s.arrow-up", color=Colors.WHITE))
        self.up_btn.setFixedSize(32, 28)
        self.up_btn.setToolTip("向上一级")
        self.up_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout.addWidget(self.up_btn)

        # Breadcrumb container
        self._breadcrumb_widget = QWidget()
        self._breadcrumb_layout = QHBoxLayout(self._breadcrumb_widget)
        self._breadcrumb_layout.setContentsMargins(4, 0, 4, 0)
        self._breadcrumb_layout.setSpacing(2)
        self._breadcrumb_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._breadcrumb_widget.setFixedHeight(28)
        self._breadcrumb_widget.setObjectName("breadcrumb_container")

        # Editable path input (initially hidden)
        self.path_edit = QLineEdit()
        self.path_edit.setFixedHeight(28)
        self.path_edit.hide()
        self.path_edit.returnPressed.connect(self._on_path_entered)

        layout.addWidget(self._breadcrumb_widget)
        layout.addWidget(self.path_edit)

        # Click breadcrumb area to switch to edit mode
        self._breadcrumb_widget.mousePressEvent = self._start_editing

    def set_path(self, path: str, in_archive: bool = False,
                 archive_path: str = "", archive_internal: str = "") -> None:
        """Update the displayed path."""
        self._current_path = path
        self._in_archive = in_archive
        self._archive_path = archive_path
        self._archive_internal_path = archive_internal
        self._rebuild_breadcrumbs()

    def get_path(self) -> str:
        return self._current_path

    def _start_editing(self, event=None):
        """Switch to editable text input mode."""
        self._editing = True
        self._breadcrumb_widget.hide()
        self.path_edit.show()
        self.path_edit.setText(self._current_path)
        self.path_edit.setFocus()
        self.path_edit.selectAll()

    def _on_path_entered(self):
        """Handle path input submission."""
        path = self.path_edit.text().strip()
        self._editing = False
        self.path_edit.hide()
        self._breadcrumb_widget.show()

        if path and os.path.exists(path):
            self._current_path = path
            self._in_archive = False
            self._rebuild_breadcrumbs()
            self.path_changed.emit(path)

    def _rebuild_breadcrumbs(self):
        """Rebuild breadcrumb buttons from the current path."""
        # Clear existing breadcrumbs
        while self._breadcrumb_layout.count():
            item = self._breadcrumb_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if self._in_archive:
            # Show: archive_path > internal > paths
            self._add_crumb("📦", self._archive_path, is_archive_root=True)
            if self._archive_internal_path:
                parts = self._archive_internal_path.rstrip("/").split("/")
                accumulated = ""
                for part in parts:
                    accumulated += part + "/"
                    self._add_separator()
                    self._add_crumb(part, accumulated, is_internal=True)
        else:
            # File system path breadcrumbs
            path = self._current_path
            if not path:
                return

            # Split path into components
            parts = []
            p = path
            while True:
                head, tail = os.path.split(p)
                if tail:
                    parts.insert(0, (tail, p))
                elif head:
                    parts.insert(0, (head, head))
                    break
                else:
                    break
                p = head

            # Only show the last few parts to avoid overflow
            max_parts = 6
            if len(parts) > max_parts:
                self._add_crumb("...", "")
                self._add_separator()
                parts = parts[-max_parts:]

            for i, (name, full_path) in enumerate(parts):
                if i > 0:
                    self._add_separator()
                self._add_crumb(name, full_path)

        # Add stretch at end
        self._breadcrumb_layout.addStretch()

    def _add_crumb(self, text: str, path: str,
                   is_archive_root: bool = False, is_internal: bool = False):
        btn = QPushButton(text)
        btn.setObjectName("breadcrumb_btn")
        btn.setFixedHeight(22)
        btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        if path:
            if is_archive_root:
                btn.clicked.connect(lambda checked, p=path: self._on_crumb_archive_root(p))
            elif is_internal:
                btn.clicked.connect(lambda checked, p=path: self._on_crumb_internal(p))
            else:
                btn.clicked.connect(lambda checked, p=path: self._on_crumb_clicked(p))

        self._breadcrumb_layout.addWidget(btn)

    def _add_separator(self):
        sep = QPushButton()
        # Set both normal and disabled color to ensure it shows up correctly
        sep.setIcon(qta.icon("fa5s.angle-right", color="#CCCCCC", color_disabled="#CCCCCC"))
        sep.setObjectName("breadcrumb_sep")
        sep.setFixedSize(16, 22)
        sep.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        sep.setEnabled(False)
        self._breadcrumb_layout.addWidget(sep)

    def _on_crumb_clicked(self, path: str):
        if path and path != self._current_path:
            self._current_path = path
            self._in_archive = False
            self._rebuild_breadcrumbs()
            self.path_changed.emit(path)

    def _on_crumb_archive_root(self, path: str):
        """Navigate to the root of the archive."""
        self._archive_internal_path = ""
        self._rebuild_breadcrumbs()
        self.path_changed.emit("__archive_root__")

    def _on_crumb_internal(self, internal_path: str):
        """Navigate to an internal path within the archive."""
        self._archive_internal_path = internal_path
        self._rebuild_breadcrumbs()
        self.path_changed.emit(f"__archive_internal__{internal_path}")

    def focusOutEvent(self, event):
        """Cancel editing on focus loss."""
        if self._editing:
            self._editing = False
            self.path_edit.hide()
            self._breadcrumb_widget.show()
        super().focusOutEvent(event)
