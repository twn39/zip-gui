from __future__ import annotations

import os
import shutil
from typing import TYPE_CHECKING

from zip_gui.archive_handler import (
    is_archive,
    list_contents,
    format_size,
)
from zip_gui.workers import PackWorker, UnpackWorker, TestWorker, FileOperationWorker
from zip_gui.task_manager import TaskManager

if TYPE_CHECKING:
    from zip_gui.archive_model import ArchiveModel
    from zip_gui.archive_handler import ArchiveFormat


class NavigationPresenter:
    """Presenter coordinating state, workers, and view actions."""

    def __init__(self, view, archive_model: ArchiveModel, fs_model, archive_sort_proxy):
        self.view = view
        self.archive_model = archive_model
        self.fs_model = fs_model
        self.archive_sort_proxy = archive_sort_proxy

        self.mode = "filesystem"  # "filesystem" or "archive"
        self.current_archive_path = ""
        self.task_manager = TaskManager()

    def navigate_to_dir(self, path: str):
        """Navigate to a filesystem directory."""
        self.mode = "filesystem"
        self.current_archive_path = ""
        self.view.set_model(self.fs_model)
        idx = self.fs_model.index(path)
        self.view.set_root_index(idx)
        self.view.set_sorting_enabled(True)
        self.view.reset_column_widths()

        self.view.update_address_bar(path, in_archive=False, archive_path="", archive_internal="")
        self.view.update_action_states(is_filesystem=True)
        self.view.update_status_count()

    def navigate_into_archive(self, archive_path: str):
        """Open an archive and show its contents."""
        try:
            info = list_contents(archive_path)
        except Exception as e:
            self.view.show_message("错误", f"无法打开压缩包:\n{e}", "critical")
            return

        self.mode = "archive"
        self.current_archive_path = archive_path
        self.archive_model.set_archive(info)

        self.view.set_model(self.archive_sort_proxy)
        # In archive mode, root index of proxy model maps to empty QModelIndex
        self.view.set_root_index(None)
        self.view.set_sorting_enabled(True)
        self.view.reset_column_widths()

        self.view.update_address_bar(
            archive_path,
            in_archive=True,
            archive_path=archive_path,
            archive_internal="",
        )
        self.view.update_action_states(is_filesystem=False)
        self.view.set_status_text(
            f"压缩包: {info.total_files} 个文件, "
            f"大小: {format_size(info.total_size)}, "
            f"压缩后: {format_size(info.total_compressed)}"
        )
        self.view.update_status_count()

    def go_up(self):
        """Navigate up one level."""
        if self.mode == "archive":
            if not self.archive_model.go_up():
                # Back to filesystem, go to directory containing archive
                parent_dir = os.path.dirname(self.current_archive_path)
                self.navigate_to_dir(parent_dir)
            else:
                internal = self.archive_model.current_path
                self.view.update_address_bar(
                    self.current_archive_path,
                    in_archive=True,
                    archive_path=self.current_archive_path,
                    archive_internal=internal,
                )
        else:
            current = self.view.get_address_path()
            parent = os.path.dirname(current)
            if parent and parent != current:
                self.navigate_to_dir(parent)

    def on_address_changed(self, path: str):
        """Handle address bar path changes."""
        if path.startswith("__archive_root__"):
            self.archive_model.navigate_to("")
            self.view.update_address_bar(
                self.current_archive_path,
                in_archive=True,
                archive_path=self.current_archive_path,
                archive_internal="",
            )
        elif path.startswith("__archive_internal__"):
            internal = path.replace("__archive_internal__", "")
            self.archive_model.navigate_to(internal)
            self.view.update_address_bar(
                self.current_archive_path,
                in_archive=True,
                archive_path=self.current_archive_path,
                archive_internal=internal,
            )
        elif os.path.isdir(path):
            self.navigate_to_dir(path)
        elif is_archive(path) and os.path.isfile(path):
            self.navigate_into_archive(path)

    def on_double_click(self, index_is_dir: bool, file_path: str, source_row: int | None):
        """Handle double-click on tree items."""
        if self.mode == "filesystem":
            if index_is_dir:
                if is_archive(file_path):
                    self.navigate_into_archive(file_path)
                else:
                    self.navigate_to_dir(file_path)
            else:
                if is_archive(file_path):
                    self.navigate_into_archive(file_path)
        else:
            # Archive mode
            if source_row is not None:
                entry = self.archive_model.entry_at(source_row)
                if entry and entry.is_dir:
                    self.archive_model.navigate_to(entry.filename)
                    self.view.update_address_bar(
                        self.current_archive_path,
                        in_archive=True,
                        archive_path=self.current_archive_path,
                        archive_internal=entry.filename,
                    )

    def on_add(self):
        """Create a new archive from selected files."""
        if self.task_manager.has_active_tasks():
            self.view.show_message("警告", "已有正在运行的任务，请等待其完成后再试", "warning")
            return

        if self.mode != "filesystem":
            self.view.show_message("提示", "请在文件系统视图中选择要压缩的文件")
            return

        paths = self.view.get_selected_fs_paths()
        if not paths:
            self.view.show_message("警告", "请先选择要打包的文件或文件夹", "warning")
            return

        default_name = os.path.basename(paths[0]) if len(paths) == 1 else "archive"
        current_dir = self.view.get_address_path()

        save_path, selected_filter = self.view.prompt_save_dialog(
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

        self.view.show_progress_bar(True)
        worker = PackWorker(paths, save_path, base_dir, fmt)
        worker.progress.connect(self.view.set_progress_value)
        worker.finished.connect(self._on_success)
        worker.error.connect(self._on_error)
        self.task_manager.start_task(worker)

    def on_extract(self):
        """Extract selected archive or extract selected entries from archive."""
        if self.task_manager.has_active_tasks():
            self.view.show_message("警告", "已有正在运行的任务，请等待其完成后再试", "warning")
            return

        if self.mode == "archive":
            entries = self.view.get_selected_archive_entries()
            dest = self.view.prompt_directory_dialog("选择解压目标文件夹")
            if not dest:
                return

            self.view.show_progress_bar(True)
            worker = UnpackWorker(
                self.current_archive_path, dest, entries if entries else None
            )
            worker.progress.connect(self.view.set_progress_value)
            worker.finished.connect(self._on_success)
            worker.error.connect(self._on_error)
            self.task_manager.start_task(worker)
        else:
            paths = self.view.get_selected_fs_paths()
            if not paths:
                self.view.show_message("警告", "请先选择要解压的压缩文件", "warning")
                return

            archive = paths[0]
            if not is_archive(archive):
                self.view.show_message("警告", "所选文件不是受支持的压缩格式", "warning")
                return

            dest = self.view.prompt_directory_dialog("选择解压目标文件夹")
            if not dest:
                return

            self.view.show_progress_bar(True)
            worker = UnpackWorker(archive, dest)
            worker.progress.connect(self.view.set_progress_value)
            worker.finished.connect(self._on_success)
            worker.error.connect(self._on_error)
            self.task_manager.start_task(worker)

    def on_extract_all(self):
        """Extract all files from current archive."""
        if self.task_manager.has_active_tasks():
            self.view.show_message("警告", "已有正在运行的任务，请等待其完成后再试", "warning")
            return

        if self.mode != "archive":
            return

        dest = self.view.prompt_directory_dialog("选择解压目标文件夹")
        if not dest:
            return

        self.view.show_progress_bar(True)
        worker = UnpackWorker(self.current_archive_path, dest)
        worker.progress.connect(self.view.set_progress_value)
        worker.finished.connect(self._on_success)
        worker.error.connect(self._on_error)
        self.task_manager.start_task(worker)

    def on_test(self):
        """Test archive integrity."""
        if self.task_manager.has_active_tasks():
            self.view.show_message("警告", "已有正在运行的任务，请等待其完成后再试", "warning")
            return

        if self.mode == "archive":
            archive = self.current_archive_path
        else:
            paths = self.view.get_selected_fs_paths()
            if not paths or not is_archive(paths[0]):
                self.view.show_message("警告", "请选择一个压缩文件进行测试", "warning")
                return
            archive = paths[0]

        self.view.set_status_text("正在测试压缩包...")
        worker = TestWorker(archive)
        worker.finished.connect(self._on_test_result)
        self.task_manager.start_task(worker)

    def _on_test_result(self, ok: bool, msg: str):
        if ok:
            self.view.show_message("测试结果", f"✅ {msg}")
            self.view.set_status_text(f"测试通过: {msg}")
        else:
            self.view.show_message("测试结果", f"❌ {msg}", "warning")
            self.view.set_status_text(f"测试失败: {msg}")

    def on_copy(self):
        """Copy selected files to another location."""
        if self.task_manager.has_active_tasks():
            self.view.show_message("警告", "已有正在运行的任务，请等待其完成后再试", "warning")
            return

        if self.mode != "filesystem":
            return
        paths = self.view.get_selected_fs_paths()
        if not paths:
            return

        dest = self.view.prompt_directory_dialog("选择复制目标文件夹")
        if not dest:
            return

        self.view.show_progress_bar(True)
        worker = FileOperationWorker("copy", paths, dest)
        worker.progress.connect(self.view.set_progress_value)
        worker.finished.connect(self._on_success)
        worker.error.connect(self._on_error)
        self.task_manager.start_task(worker)

    def on_move(self):
        """Move selected files to another location."""
        if self.task_manager.has_active_tasks():
            self.view.show_message("警告", "已有正在运行的任务，请等待其完成后再试", "warning")
            return

        if self.mode != "filesystem":
            return
        paths = self.view.get_selected_fs_paths()
        if not paths:
            return

        dest = self.view.prompt_directory_dialog("选择移动目标文件夹")
        if not dest:
            return

        self.view.show_progress_bar(True)
        worker = FileOperationWorker("move", paths, dest)
        worker.progress.connect(self.view.set_progress_value)
        worker.finished.connect(self._on_success)
        worker.error.connect(self._on_error)
        self.task_manager.start_task(worker)

    def on_delete(self):
        """Delete selected files."""
        if self.task_manager.has_active_tasks():
            self.view.show_message("警告", "已有正在运行的任务，请等待其完成后再试", "warning")
            return

        if self.mode != "filesystem":
            return
        paths = self.view.get_selected_fs_paths()
        if not paths:
            return

        names = "\n".join(os.path.basename(p) for p in paths[:10])
        if len(paths) > 10:
            names += f"\n... 及其他 {len(paths) - 10} 个项目"

        confirm = self.view.confirm_dialog(
            "确认删除",
            f"确定要删除以下 {len(paths)} 个项目吗？\n\n{names}"
        )

        if confirm:
            for path in paths:
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                except Exception as e:
                    self.view.show_message("错误", f"无法删除 {path}:\n{e}", "critical")
            self.view.set_status_text(f"已删除 {len(paths)} 个项目")

    def on_rename(self):
        """Rename selected file/folder."""
        if self.task_manager.has_active_tasks():
            self.view.show_message("警告", "已有正在运行的任务，请等待其完成后再试", "warning")
            return

        if self.mode != "filesystem":
            return
        paths = self.view.get_selected_fs_paths()
        if len(paths) != 1:
            self.view.show_message("警告", "请选择一个文件或文件夹进行重命名", "warning")
            return

        old_path = paths[0]
        old_name = os.path.basename(old_path)

        new_name, ok = self.view.prompt_input_dialog("重命名", "新名称:", old_name)

        if ok and new_name and new_name != old_name:
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            try:
                os.rename(old_path, new_path)
                self.view.set_status_text(f"已重命名: {old_name} → {new_name}")
            except Exception as e:
                self.view.show_message("错误", f"重命名失败:\n{e}", "critical")

    def on_info(self):
        """Show info."""
        if self.mode == "archive":
            archive = self.current_archive_path
        else:
            paths = self.view.get_selected_fs_paths()
            if not paths:
                self.view.show_project_info()
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
                self.view.show_message("压缩包信息", msg)
            except Exception as e:
                self.view.show_message("错误", f"无法读取压缩包信息:\n{e}", "critical")
        else:
            try:
                stat = os.stat(archive)
                msg = (
                    f"名称: {os.path.basename(archive)}\n"
                    f"大小: {format_size(stat.st_size)}\n"
                    f"路径: {archive}\n"
                    f"类型: {'文件夹' if os.path.isdir(archive) else '文件'}"
                )
                self.view.show_message("文件信息", msg)
            except Exception as e:
                self.view.show_message("错误", f"无法读取文件信息:\n{e}", "critical")

    def _on_success(self, message: str):
        self.view.show_progress_bar(False)
        self.view.set_status_text(message)
        self.view.show_message("成功", message)

    def _on_error(self, message: str):
        self.view.show_progress_bar(False)
        self.view.set_status_text(f"错误: {message}")
        self.view.show_message("失败", message, "critical")
