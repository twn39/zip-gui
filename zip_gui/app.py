"""Main window — WinRAR / 7-Zip style archive manager."""

from __future__ import annotations

import os
import shutil
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
import qtawesome as qta

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
from zip_gui.workers import PackWorker, UnpackWorker, TestWorker, FileOperationWorker


class MainWindow(QMainWindow):
    """WinRAR / 7-Zip style archive manager main window."""

    def __init__(self):
        super().__init__()
        self._worker = None  # Keep reference to prevent GC
        self._mode = "filesystem"  # "filesystem" or "archive"
        self._current_archive_path = ""
        self._init_ui()

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

        # Start at home directory
        home = QDir.homePath()
        self._navigate_to_dir(home)

        # Selection change updates status
        self._tree.selectionModel().selectionChanged.connect(self._update_status_count)

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

    # ──────────────────────── Navigation ────────────────────────

    def _navigate_to_dir(self, path: str):
        """Navigate to a filesystem directory."""
        self._mode = "filesystem"
        self._current_archive_path = ""
        self._tree.setModel(self._fs_model)
        idx = self._fs_model.index(path)
        self._tree.setRootIndex(idx)
        self._tree.setSortingEnabled(True)

        # Re-set column widths after model change
        header = self._tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        self._address_bar.set_path(path)
        self._update_action_states()
        self._update_status_count()

        # Reconnect selection model
        self._tree.selectionModel().selectionChanged.connect(self._update_status_count)

    def _navigate_into_archive(self, archive_path: str):
        """Open an archive and show its contents."""
        try:
            info = list_contents(archive_path)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开压缩包:\n{e}")
            return

        self._mode = "archive"
        self._current_archive_path = archive_path
        self._archive_model.set_archive(info)

        self._tree.setModel(self._archive_sort_proxy)
        self._tree.setRootIndex(self._archive_sort_proxy.mapFromSource(QModelIndex()))
        self._tree.setSortingEnabled(True)

        # Re-set column widths
        header = self._tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        self._address_bar.set_path(
            archive_path,
            in_archive=True,
            archive_path=archive_path,
            archive_internal="",
        )
        self._update_action_states()
        self._status_label.setText(
            f"压缩包: {info.total_files} 个文件, "
            f"大小: {format_size(info.total_size)}, "
            f"压缩后: {format_size(info.total_compressed)}"
        )

        # Reconnect selection model
        self._tree.selectionModel().selectionChanged.connect(self._update_status_count)

    def _go_up(self):
        """Navigate up one level."""
        if self._mode == "archive":
            if not self._archive_model.go_up():
                # Back to filesystem, go to directory containing archive
                parent_dir = os.path.dirname(self._current_archive_path)
                self._navigate_to_dir(parent_dir)
            else:
                internal = self._archive_model.current_path
                self._address_bar.set_path(
                    self._current_archive_path,
                    in_archive=True,
                    archive_path=self._current_archive_path,
                    archive_internal=internal,
                )
        else:
            current = self._address_bar.get_path()
            parent = os.path.dirname(current)
            if parent and parent != current:
                self._navigate_to_dir(parent)

    def _on_address_changed(self, path: str):
        """Handle address bar path changes."""
        if path.startswith("__archive_root__"):
            self._archive_model.navigate_to("")
            self._address_bar.set_path(
                self._current_archive_path,
                in_archive=True,
                archive_path=self._current_archive_path,
                archive_internal="",
            )
        elif path.startswith("__archive_internal__"):
            internal = path.replace("__archive_internal__", "")
            self._archive_model.navigate_to(internal)
            self._address_bar.set_path(
                self._current_archive_path,
                in_archive=True,
                archive_path=self._current_archive_path,
                archive_internal=internal,
            )
        elif os.path.isdir(path):
            self._navigate_to_dir(path)
        elif is_archive(path) and os.path.isfile(path):
            self._navigate_into_archive(path)

    def _on_double_click(self, index: QModelIndex):
        """Handle double-click on tree items."""
        if self._mode == "filesystem":
            if self._fs_model.isDir(index):
                path = self._fs_model.filePath(index)
                if is_archive(path):
                    self._navigate_into_archive(path)
                else:
                    self._navigate_to_dir(path)
            else:
                file_path = self._fs_model.filePath(index)
                if is_archive(file_path):
                    self._navigate_into_archive(file_path)
        else:
            # Archive mode
            source_idx = self._archive_sort_proxy.mapToSource(index)
            entry = self._archive_model.entry_at(source_idx.row())
            if entry and entry.is_dir:
                self._archive_model.navigate_to(entry.filename)
                self._address_bar.set_path(
                    self._current_archive_path,
                    in_archive=True,
                    archive_path=self._current_archive_path,
                    archive_internal=entry.filename,
                )

    # ──────────────────────── Actions ────────────────────────

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
        """Create a new archive from selected files."""
        if self._mode != "filesystem":
            QMessageBox.information(self, "提示", "请在文件系统视图中选择要压缩的文件")
            return

        paths = self._get_selected_fs_paths()
        if not paths:
            QMessageBox.warning(self, "警告", "请先选择要打包的文件或文件夹")
            return

        default_name = os.path.basename(paths[0]) if len(paths) == 1 else "archive"
        current_dir = self._address_bar.get_path()

        save_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "保存压缩文件",
            os.path.join(current_dir, default_name),
            "ZIP 文件 (*.zip);;TAR.GZ 文件 (*.tar.gz);;TAR.BZ2 文件 (*.tar.bz2);;TAR.XZ 文件 (*.tar.xz);;TAR 文件 (*.tar)",
        )

        if not save_path:
            return

        # Determine format from filter
        fmt: ArchiveFormat = "zip"
        if "tar.gz" in selected_filter:
            fmt = "tar.gz"
        elif "tar.bz2" in selected_filter:
            fmt = "tar.bz2"
        elif "tar.xz" in selected_filter:
            fmt = "tar.xz"
        elif "tar" in selected_filter and "gz" not in selected_filter:
            fmt = "tar"

        base_dir = current_dir

        self._show_progress()
        self._worker = PackWorker(paths, save_path, base_dir, fmt)
        self._worker.progress.connect(self._progress_bar.setValue)
        self._worker.finished.connect(self._on_success)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_extract(self):
        """Extract selected archive or extract selected entries from archive."""
        if self._mode == "archive":
            # Extract selected entries (or all if none selected)
            entries = self._get_selected_archive_entries()
            dest = QFileDialog.getExistingDirectory(self, "选择解压目标文件夹")
            if not dest:
                return

            self._show_progress()
            self._worker = UnpackWorker(
                self._current_archive_path, dest, entries if entries else None
            )
            self._worker.progress.connect(self._progress_bar.setValue)
            self._worker.finished.connect(self._on_success)
            self._worker.error.connect(self._on_error)
            self._worker.start()
        else:
            # Filesystem mode — extract selected archive file
            paths = self._get_selected_fs_paths()
            if not paths:
                QMessageBox.warning(self, "警告", "请先选择要解压的压缩文件")
                return

            archive = paths[0]
            if not is_archive(archive):
                QMessageBox.warning(self, "警告", "所选文件不是受支持的压缩格式")
                return

            dest = QFileDialog.getExistingDirectory(self, "选择解压目标文件夹")
            if not dest:
                return

            self._show_progress()
            self._worker = UnpackWorker(archive, dest)
            self._worker.progress.connect(self._progress_bar.setValue)
            self._worker.finished.connect(self._on_success)
            self._worker.error.connect(self._on_error)
            self._worker.start()

    def _on_test(self):
        """Test archive integrity."""
        if self._mode == "archive":
            archive = self._current_archive_path
        else:
            paths = self._get_selected_fs_paths()
            if not paths or not is_archive(paths[0]):
                QMessageBox.warning(self, "警告", "请选择一个压缩文件进行测试")
                return
            archive = paths[0]

        self._status_label.setText("正在测试压缩包...")
        self._worker = TestWorker(archive)
        self._worker.finished.connect(self._on_test_result)
        self._worker.start()

    def _on_test_result(self, ok: bool, msg: str):
        if ok:
            QMessageBox.information(self, "测试结果", f"✅ {msg}")
            self._status_label.setText(f"测试通过: {msg}")
        else:
            QMessageBox.warning(self, "测试结果", f"❌ {msg}")
            self._status_label.setText(f"测试失败: {msg}")

    def _on_copy(self):
        """Copy selected files to another location."""
        if self._mode != "filesystem":
            return
        paths = self._get_selected_fs_paths()
        if not paths:
            return

        dest = QFileDialog.getExistingDirectory(self, "选择复制目标文件夹")
        if not dest:
            return

        self._show_progress()
        self._worker = FileOperationWorker("copy", paths, dest)
        self._worker.progress.connect(self._progress_bar.setValue)
        self._worker.finished.connect(self._on_success)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_move(self):
        """Move selected files to another location."""
        if self._mode != "filesystem":
            return
        paths = self._get_selected_fs_paths()
        if not paths:
            return

        dest = QFileDialog.getExistingDirectory(self, "选择移动目标文件夹")
        if not dest:
            return

        self._show_progress()
        self._worker = FileOperationWorker("move", paths, dest)
        self._worker.progress.connect(self._progress_bar.setValue)
        self._worker.finished.connect(self._on_success)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_delete(self):
        """Delete selected files."""
        if self._mode != "filesystem":
            return
        paths = self._get_selected_fs_paths()
        if not paths:
            return

        names = "\n".join(os.path.basename(p) for p in paths[:10])
        if len(paths) > 10:
            names += f"\n... 及其他 {len(paths) - 10} 个项目"

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除以下 {len(paths)} 个项目吗？\n\n{names}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            for path in paths:
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"无法删除 {path}:\n{e}")
            self._status_label.setText(f"已删除 {len(paths)} 个项目")

    def _on_rename(self):
        """Rename selected file/folder."""
        if self._mode != "filesystem":
            return
        paths = self._get_selected_fs_paths()
        if len(paths) != 1:
            QMessageBox.warning(self, "警告", "请选择一个文件或文件夹进行重命名")
            return

        old_path = paths[0]
        old_name = os.path.basename(old_path)

        new_name, ok = QInputDialog.getText(
            self, "重命名", "新名称:", text=old_name
        )

        if ok and new_name and new_name != old_name:
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            try:
                os.rename(old_path, new_path)
                self._status_label.setText(f"已重命名: {old_name} → {new_name}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"重命名失败:\n{e}")

    def _on_info(self):
        """Show archive info."""
        if self._mode == "archive":
            archive = self._current_archive_path
        else:
            paths = self._get_selected_fs_paths()
            if not paths:
                return
            archive = paths[0]

        if is_archive(archive):
            try:
                info = list_contents(archive)
                ratio = (
                    f"{info.total_compressed / info.total_size * 100:.1f}%"
                    if info.total_size > 0
                    else "N/A"
                )
                msg = (
                    f"文件: {os.path.basename(archive)}\n"
                    f"格式: {info.format.upper()}\n"
                    f"文件数: {info.total_files}\n"
                    f"原始大小: {format_size(info.total_size)}\n"
                    f"压缩大小: {format_size(info.total_compressed)}\n"
                    f"压缩率: {ratio}"
                )
                QMessageBox.information(self, "压缩包信息", msg)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法读取压缩包信息:\n{e}")
        else:
            # Show file/dir info
            try:
                stat = os.stat(archive)
                msg = (
                    f"名称: {os.path.basename(archive)}\n"
                    f"大小: {format_size(stat.st_size)}\n"
                    f"路径: {archive}\n"
                    f"类型: {'文件夹' if os.path.isdir(archive) else '文件'}"
                )
                QMessageBox.information(self, "文件信息", msg)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法读取文件信息:\n{e}")

    def _on_new_archive(self):
        """Create a new empty archive (user selects files then creates)."""
        self._on_add()

    def _on_open_archive(self):
        """Open an archive file via dialog."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "打开压缩文件",
            self._address_bar.get_path(),
            "压缩文件 (*.zip *.tar *.tar.gz *.tgz *.tar.bz2 *.tar.xz *.gz *.bz2 *.xz);;所有文件 (*.*)",
        )
        if path:
            self._navigate_into_archive(path)

    def _select_all(self):
        """Select all items in the tree view."""
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

    # ──────────────────────── Context Menu ────────────────────────

    def _show_context_menu(self, pos):
        """Show right-click context menu."""
        menu = QMenu(self)

        if self._mode == "filesystem":
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
        """Extract all files from current archive."""
        if self._mode != "archive":
            return

        dest = QFileDialog.getExistingDirectory(self, "选择解压目标文件夹")
        if not dest:
            return

        self._show_progress()
        self._worker = UnpackWorker(self._current_archive_path, dest)
        self._worker.progress.connect(self._progress_bar.setValue)
        self._worker.finished.connect(self._on_success)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    # ──────────────────────── Helpers ────────────────────────

    def _show_progress(self):
        self._progress_bar.setVisible(True)
        self._progress_bar.setValue(0)

    def _hide_progress(self):
        self._progress_bar.setVisible(False)

    def _on_success(self, message: str):
        self._hide_progress()
        self._status_label.setText(message)
        QMessageBox.information(self, "成功", message)

    def _on_error(self, message: str):
        self._hide_progress()
        self._status_label.setText(f"错误: {message}")
        QMessageBox.critical(self, "失败", message)

    def _update_action_states(self):
        """Enable/disable toolbar actions based on current mode."""
        is_fs = self._mode == "filesystem"
        self._act_add.setEnabled(is_fs)
        self._act_copy.setEnabled(is_fs)
        self._act_move.setEnabled(is_fs)
        self._act_delete.setEnabled(is_fs)

    def _update_status_count(self):
        """Update status bar with selection count."""
        selected = len(self._tree.selectionModel().selectedRows())
        if self._mode == "filesystem":
            model = self._fs_model
            root = self._tree.rootIndex()
            total = model.rowCount(root)
            self._count_label.setText(f"{total} 个项目, 已选择 {selected} 个")
        else:
            total = self._archive_model.rowCount()
            self._count_label.setText(f"{total} 个条目, 已选择 {selected} 个")


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
