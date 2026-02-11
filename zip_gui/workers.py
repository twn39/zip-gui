"""Background worker threads for archive operations."""

from __future__ import annotations

import os
import shutil

from PySide6.QtCore import QThread, Signal

from zip_gui import archive_handler


class PackWorker(QThread):
    """Worker thread to create a new archive."""

    finished = Signal(str)
    error = Signal(str)
    progress = Signal(int)

    def __init__(
        self,
        files: list[str],
        dest_path: str,
        base_dir: str,
        fmt: archive_handler.ArchiveFormat = "zip",
    ):
        super().__init__()
        self.files = files
        self.dest_path = dest_path
        self.base_dir = base_dir
        self.fmt = fmt

    def run(self):
        try:
            result = archive_handler.create_archive(
                files=self.files,
                dest_path=self.dest_path,
                base_dir=self.base_dir,
                fmt=self.fmt,
                progress_callback=self.progress.emit,
            )
            self.finished.emit(f"成功打包到: {result}")
        except Exception as e:
            self.error.emit(f"打包失败: {e}")


class UnpackWorker(QThread):
    """Worker thread to extract an archive."""

    finished = Signal(str)
    error = Signal(str)
    progress = Signal(int)

    def __init__(
        self,
        archive_path: str,
        dest_dir: str,
        entries: list[str] | None = None,
    ):
        super().__init__()
        self.archive_path = archive_path
        self.dest_dir = dest_dir
        self.entries = entries

    def run(self):
        try:
            os.makedirs(self.dest_dir, exist_ok=True)
            if self.entries:
                archive_handler.extract_files(
                    self.archive_path,
                    self.entries,
                    self.dest_dir,
                    progress_callback=self.progress.emit,
                )
            else:
                archive_handler.extract_all(
                    self.archive_path,
                    self.dest_dir,
                    progress_callback=self.progress.emit,
                )
            self.finished.emit(f"成功解压到: {self.dest_dir}")
        except Exception as e:
            self.error.emit(f"解压失败: {e}")


class TestWorker(QThread):
    """Worker thread to test archive integrity."""

    finished = Signal(bool, str)

    def __init__(self, archive_path: str):
        super().__init__()
        self.archive_path = archive_path

    def run(self):
        ok, msg = archive_handler.test_archive(self.archive_path)
        self.finished.emit(ok, msg)


class FileOperationWorker(QThread):
    """Worker thread for file copy/move operations."""

    finished = Signal(str)
    error = Signal(str)
    progress = Signal(int)

    def __init__(
        self,
        operation: str,  # "copy" or "move"
        sources: list[str],
        dest_dir: str,
    ):
        super().__init__()
        self.operation = operation
        self.sources = sources
        self.dest_dir = dest_dir

    def run(self):
        try:
            total = len(self.sources)
            for i, src in enumerate(self.sources):
                basename = os.path.basename(src)
                dest = os.path.join(self.dest_dir, basename)

                if self.operation == "copy":
                    if os.path.isdir(src):
                        shutil.copytree(src, dest, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src, dest)
                elif self.operation == "move":
                    shutil.move(src, dest)

                self.progress.emit(int((i + 1) / total * 100))

            op_name = "复制" if self.operation == "copy" else "移动"
            self.finished.emit(f"成功{op_name} {total} 个项目到: {self.dest_dir}")
        except Exception as e:
            op_name = "复制" if self.operation == "copy" else "移动"
            self.error.emit(f"{op_name}失败: {e}")
