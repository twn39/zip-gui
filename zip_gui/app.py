"""Main window — WinRAR / 7-Zip style archive manager."""

from __future__ import annotations

import os
import sys

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QFileDialog,
    QInputDialog,
    QMessageBox,
    QTreeView,
    QFileSystemModel,
    QToolBar,
    QStatusBar,
    QAbstractItemView,
    QMenu,
    QMenuBar,
    QSizePolicy,
    QHeaderView,
)
from PySide6.QtCore import Qt, QSize, QDir, QModelIndex
from PySide6.QtGui import QAction, QKeySequence

from zip_gui.style import load_stylesheet
from zip_gui.resources import Icons, Colors, icon as get_icon
from zip_gui.widgets import AddressBar
from zip_gui.archive_handler import (
    is_archive,
    list_contents,
    format_size,
    ArchiveFormat,
)
from zip_gui.archive_model import ArchiveModel, ArchiveSortProxyModel
from zip_gui.presenter import NavigationPresenter


class MainWindow(QMainWindow):
    """WinRAR / 7-Zip style archive manager main window (View)."""

    def __init__(self):
        super().__init__()
        self._init_ui()
        self.presenter = NavigationPresenter(
            self,
            self._archive_model,
            self._fs_model,
            self._archive_sort_proxy,
        )

        # Start at home directory
        home = QDir.homePath()
        self.presenter.navigate_to_dir(home)

        # Selection change updates status
        self._tree.selectionModel().selectionChanged.connect(self._update_status_count)

    # ──────────────────────────── UI Setup ────────────────────────────

    def _init_ui(self):
        self.setWindowTitle("ZipGUI — 压缩文件管理器")
        self.resize(1100, 720)
        self.setMinimumSize(800, 500)

        # --- Models ---
        self._fs_model = QFileSystemModel()
        self._fs_model.setRootPath(QDir.homePath())
        self._fs_model.setFilter(
            QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot | QDir.Filter.AllDirs
        )

        self._archive_model = ArchiveModel()
        self._archive_sort_proxy = ArchiveSortProxyModel()
        self._archive_sort_proxy.setSourceModel(self._archive_model)

        # --- Menu Bar ---
        self._create_menu_bar()

        # --- Toolbar ---
        self._create_toolbar()

        # --- Central Widget ---
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(4)

        # --- Address Bar ---
        self._address_bar = AddressBar()
        self._address_bar.up_btn.clicked.connect(self._go_up)
        self._address_bar.path_changed.connect(self._on_address_changed)
        layout.addWidget(self._address_bar)

        # --- Tree View ---
        self._tree = QTreeView()
        self._tree.setModel(self._fs_model)
        self._tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._tree.setSortingEnabled(True)
        self._tree.setAnimated(False)
        self._tree.setIndentation(20)
        self._tree.setAlternatingRowColors(True)
        self._tree.setRootIsDecorated(False)
        self._tree.setUniformRowHeights(True)

        # Column widths
        header = self._tree.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        self._tree.doubleClicked.connect(self._on_double_click)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._show_context_menu)

        layout.addWidget(self._tree)

        # --- Status Bar ---
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)

        self._progress_bar = QProgressBar()
        self._progress_bar.setMaximumWidth(220)
        self._progress_bar.setMaximumHeight(16)
        self._progress_bar.setVisible(False)
        self._status_bar.addPermanentWidget(self._progress_bar)

        self._status_label = QLabel("准备就绪")
        self._status_bar.addWidget(self._status_label)

        self._count_label = QLabel()
        self._status_bar.addPermanentWidget(self._count_label)

    def _create_menu_bar(self):
        """Build the menu bar."""
        menu_bar = self.menuBar()

        # --- File menu ---
        file_menu = menu_bar.addMenu("文件(&F)")

        new_action = QAction(get_icon(*Icons.NEW_ARCHIVE), "新建压缩包(&N)", self)
        new_action.setShortcut(QKeySequence("Ctrl+N"))
        new_action.triggered.connect(self._on_new_archive)
        file_menu.addAction(new_action)

        open_action = QAction(get_icon(*Icons.OPEN), "打开压缩包(&O)", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self._on_open_archive)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        exit_action = QAction(get_icon(*Icons.EXIT), "退出(&X)", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # --- Edit menu ---
        edit_menu = menu_bar.addMenu("编辑(&E)")

        select_all_action = QAction(get_icon(*Icons.SELECT_ALL), "全选(&A)", self)
        select_all_action.setShortcut(QKeySequence("Ctrl+A"))
        select_all_action.triggered.connect(self._select_all)
        edit_menu.addAction(select_all_action)

        edit_menu.addSeparator()

        rename_action = QAction(get_icon(*Icons.RENAME), "重命名(&R)", self)
        rename_action.setShortcut(QKeySequence("F2"))
        rename_action.triggered.connect(self._on_rename)
        edit_menu.addAction(rename_action)

        # --- Tools menu ---
        tools_menu = menu_bar.addMenu("工具(&T)")

        test_action = QAction(get_icon(*Icons.TEST), "测试压缩包(&T)", self)
        test_action.triggered.connect(self._on_test)
        tools_menu.addAction(test_action)

        # --- Help menu ---
        help_menu = menu_bar.addMenu("帮助(&H)")

        about_action = QAction(get_icon(*Icons.ABOUT), "关于(&A)", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _create_toolbar(self):
        """Build the main toolbar with WinRAR-style buttons."""
        toolbar = QToolBar("主工具栏")
        toolbar.setIconSize(QSize(28, 28))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self._act_add = QAction(get_icon(*Icons.ADD), "添加", self)
        self._act_add.setToolTip("压缩选中的文件/文件夹")
        self._act_add.triggered.connect(self._on_add)
        toolbar.addAction(self._act_add)

        self._act_extract = QAction(get_icon(*Icons.EXTRACT), "解压到", self)
        self._act_extract.setToolTip("解压选中的压缩文件")
        self._act_extract.triggered.connect(self._on_extract)
        toolbar.addAction(self._act_extract)

        toolbar.addSeparator()

        self._act_test = QAction(get_icon(*Icons.TEST), "测试", self)
        self._act_test.setToolTip("测试压缩包完整性")
        self._act_test.triggered.connect(self._on_test)
        toolbar.addAction(self._act_test)

        toolbar.addSeparator()

        self._act_copy = QAction(get_icon(*Icons.COPY), "复制", self)
        self._act_copy.setToolTip("复制选中项到其他位置")
        self._act_copy.triggered.connect(self._on_copy)
        toolbar.addAction(self._act_copy)

        self._act_move = QAction(get_icon(*Icons.MOVE), "移动", self)
        self._act_move.setToolTip("移动选中项到其他位置")
        self._act_move.triggered.connect(self._on_move)
        toolbar.addAction(self._act_move)

        self._act_delete = QAction(get_icon(*Icons.DELETE), "删除", self)
        self._act_delete.setToolTip("删除选中的文件")
        self._act_delete.triggered.connect(self._on_delete)
        toolbar.addAction(self._act_delete)

        toolbar.addSeparator()

        self._act_info = QAction(get_icon(*Icons.INFO), "信息", self)
        self._act_info.setToolTip("查看压缩包信息")
        self._act_info.triggered.connect(self._on_info)
        toolbar.addAction(self._act_info)

    # ──────────────────────── View Interface ────────────────────────

    def set_model(self, model):
        self._tree.setModel(model)

    def set_root_index(self, index):
        if index is None:
            self._tree.setRootIndex(self._archive_sort_proxy.mapFromSource(QModelIndex()))
        else:
            self._tree.setRootIndex(index)

    def set_sorting_enabled(self, enabled: bool):
        self._tree.setSortingEnabled(enabled)

    def reset_column_widths(self):
        header = self._tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

    def update_address_bar(self, path: str, in_archive: bool, archive_path: str, archive_internal: str):
        self._address_bar.set_path(
            path,
            in_archive=in_archive,
            archive_path=archive_path,
            archive_internal=archive_internal,
        )

    def get_address_path(self) -> str:
        return self._address_bar.get_path()

    def show_message(self, title: str, message: str, icon_type: str = "info"):
        if icon_type == "critical":
            QMessageBox.critical(self, title, message)
        elif icon_type == "warning":
            QMessageBox.warning(self, title, message)
        else:
            QMessageBox.information(self, title, message)

    def show_progress_bar(self, visible: bool):
        self._progress_bar.setVisible(visible)
        if visible:
            self._progress_bar.setValue(0)

    def set_progress_value(self, value: int):
        self._progress_bar.setValue(value)

    def set_status_text(self, text: str):
        self._status_label.setText(text)

    def prompt_save_dialog(self, title: str, default_path: str, filter_str: str) -> tuple[str, str]:
        return QFileDialog.getSaveFileName(self, title, default_path, filter_str)

    def prompt_directory_dialog(self, title: str) -> str:
        return QFileDialog.getExistingDirectory(self, title)

    def prompt_input_dialog(self, title: str, label: str, text: str) -> tuple[str, bool]:
        return QInputDialog.getText(self, title, label, text=text)

    def confirm_dialog(self, title: str, text: str) -> bool:
        reply = QMessageBox.question(
            self,
            title,
            text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    def get_selected_fs_paths(self) -> list[str]:
        return self._get_selected_fs_paths()

    def get_selected_archive_entries(self) -> list[str]:
        return self._get_selected_archive_entries()

    def update_action_states(self, is_filesystem: bool):
        self._act_add.setEnabled(is_filesystem)
        self._act_copy.setEnabled(is_filesystem)
        self._act_move.setEnabled(is_filesystem)
        self._act_delete.setEnabled(is_filesystem)

    def update_status_count(self):
        self._update_status_count()

    # ──────────────────────── Navigation Delegation ────────────────────────

    def _go_up(self):
        self.presenter.go_up()

    def _on_address_changed(self, path: str):
        self.presenter.on_address_changed(path)

    def _on_double_click(self, index: QModelIndex):
        if self.presenter.mode == "filesystem":
            is_dir = self._fs_model.isDir(index)
            file_path = self._fs_model.filePath(index)
            self.presenter.on_double_click(is_dir, file_path, None)
        else:
            source_idx = self._archive_sort_proxy.mapToSource(index)
            self.presenter.on_double_click(False, "", source_idx.row())

    # ──────────────────────── Actions Delegation ────────────────────────

    def _get_selected_fs_paths(self) -> list[str]:
        """Get selected filesystem paths."""
        indexes = self._tree.selectionModel().selectedRows()
        return [self._fs_model.filePath(i) for i in indexes]

    def _get_selected_archive_entries(self) -> list[str]:
        """Get selected archive entry names."""
        indexes = self._tree.selectionModel().selectedRows()
        entries = []
        for idx in indexes:
            source_idx = self._archive_sort_proxy.mapToSource(idx)
            entry = self._archive_model.entry_at(source_idx.row())
            if entry:
                entries.append(entry.filename)
        return entries

    def _on_add(self):
        self.presenter.on_add()

    def _on_extract(self):
        self.presenter.on_extract()

    def _on_test(self):
        self.presenter.on_test()

    def _on_copy(self):
        self.presenter.on_copy()

    def _on_move(self):
        self.presenter.on_move()

    def _on_delete(self):
        self.presenter.on_delete()

    def _on_rename(self):
        self.presenter.on_rename()

    def _on_info(self):
        self.presenter.on_info()

    def _on_new_archive(self):
        self.presenter.on_add()

    def _on_open_archive(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "打开压缩文件",
            self._address_bar.get_path(),
            "压缩文件 (*.zip *.tar *.tar.gz *.tgz *.tar.bz2 *.tar.xz *.gz *.bz2 *.xz);;所有文件 (*.*)",
        )
        if path:
            self.presenter.navigate_into_archive(path)

    def _select_all(self):
        self._tree.selectAll()

    def _on_about(self):
        QMessageBox.about(
            self,
            "关于 ZipGUI",
            "<h3>ZipGUI — 压缩文件管理器</h3>"
            "<p>版本 2.0.0</p>"
            "<p>一个简洁高效的压缩文件管理工具，<br>"
            "支持 ZIP、TAR、GZ、BZ2、XZ 格式。</p>"
            "<p>基于 PySide6 构建</p>"
            '<p><a href="https://github.com/twn39/zip-gui">GitHub</a></p>',
        )

    def _show_project_info(self):
        """Show project information dialog."""
        from importlib.metadata import metadata

        try:
            meta = metadata("zip_gui")
            name = meta["Name"] or "ZipGUI"
            version = meta["Version"] or "未知"
            home_page = meta["Home-page"] or ""
        except Exception:
            name = "ZipGUI"
            version = "未知"
            home_page = ""

        repo_url = home_page or "https://github.com/twn39/zip-gui"

        QMessageBox.about(
            self,
            "项目信息",
            f'<div style="text-align:center; margin-bottom:12px;">'
            f'<h2 style="margin-bottom:4px;">📦 {name}</h2>'
            f'<span style="color:#999; font-size:13px;">v{version}</span>'
            f'</div>'
            f'<hr style="border:none; border-top:1px solid #555; margin:8px 0 12px 0;">'
            f'<table cellspacing="6" style="font-size:13px;">'
            f'<tr><td style="color:#999;">描述</td>'
            f'<td>简洁高效的压缩文件管理工具</td></tr>'
            f'<tr><td style="color:#999;">格式</td>'
            f'<td>ZIP · TAR · GZ · BZ2 · XZ</td></tr>'
            f'<tr><td style="color:#999;">框架</td>'
            f'<td>Python + PySide6</td></tr>'
            f'<tr><td style="color:#999;">源码</td>'
            f'<td><a href="{repo_url}">{repo_url}</a></td></tr>'
            f'</table>',
        )

    def show_project_info(self):
        self._show_project_info()

    # ──────────────────────── Context Menu ────────────────────────

    def _show_context_menu(self, pos):
        """Show right-click context menu."""
        menu = QMenu(self)

        if self.presenter.mode == "filesystem":
            paths = self._get_selected_fs_paths()

            open_act = menu.addAction(get_icon(*Icons.OPEN), "打开")
            open_act.triggered.connect(
                lambda: self._on_double_click(self._tree.currentIndex())
            )

            menu.addSeparator()

            if paths and any(is_archive(p) for p in paths):
                extract_act = menu.addAction(get_icon(*Icons.EXTRACT), "解压到...")
                extract_act.triggered.connect(self._on_extract)

                test_act = menu.addAction(get_icon(*Icons.TEST), "测试压缩包")
                test_act.triggered.connect(self._on_test)

                menu.addSeparator()

            add_act = menu.addAction(get_icon(*Icons.ADD), "压缩...")
            add_act.triggered.connect(self._on_add)

            menu.addSeparator()

            copy_act = menu.addAction(get_icon(*Icons.COPY), "复制到...")
            copy_act.triggered.connect(self._on_copy)

            move_act = menu.addAction(get_icon(*Icons.MOVE), "移动到...")
            move_act.triggered.connect(self._on_move)

            rename_act = menu.addAction(get_icon(*Icons.RENAME), "重命名")
            rename_act.triggered.connect(self._on_rename)

            menu.addSeparator()

            delete_act = menu.addAction(get_icon(*Icons.DELETE), "删除")
            delete_act.triggered.connect(self._on_delete)

            menu.addSeparator()

            info_act = menu.addAction(get_icon(*Icons.INFO), "属性")
            info_act.triggered.connect(self._on_info)
        else:
            # Archive mode context menu
            extract_act = menu.addAction(get_icon(*Icons.EXTRACT), "解压选中文件...")
            extract_act.triggered.connect(self._on_extract)

            extract_all_act = menu.addAction(get_icon(*Icons.EXTRACT), "解压全部...")
            extract_all_act.triggered.connect(self._on_extract_all)

            menu.addSeparator()

            info_act = menu.addAction(get_icon(*Icons.INFO), "压缩包信息")
            info_act.triggered.connect(self._on_info)

        menu.exec(self._tree.viewport().mapToGlobal(pos))

    def _on_extract_all(self):
        self.presenter.on_extract_all()

    # ──────────────────────── Helpers ────────────────────────

    def _update_status_count(self):
        """Update status bar with selection count."""
        selected = len(self._tree.selectionModel().selectedRows())
        if self.presenter.mode == "filesystem":
            model = self._fs_model
            root = self._tree.rootIndex()
            total = model.rowCount(root)
            self._count_label.setText(f"{total} 个项目, 已选择 {selected} 个")
        else:
            total = self._archive_model.rowCount()
            self._count_label.setText(f"{total} 个条目, 已选择 {selected} 个")

    def closeEvent(self, event):
        """Handle window close event to cleanly shutdown background threads."""
        self.presenter.task_manager.shutdown()
        event.accept()


def run():
    app = QApplication(sys.argv)
    style_sheet = load_stylesheet()
    if style_sheet:
        app.setStyleSheet(style_sheet)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
