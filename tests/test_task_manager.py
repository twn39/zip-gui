import pytest
import time
from PySide6.QtCore import QThread, Signal
from zip_gui.task_manager import TaskManager
from zip_gui.presenter import NavigationPresenter
from zip_gui.archive_model import ArchiveModel
from tests.test_presenter import MockView, DummyModel


class DummyWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, run_duration=0.05, fail=False):
        super().__init__()
        self.run_duration = run_duration
        self.fail = fail

    def run(self):
        time.sleep(self.run_duration)
        if self.fail:
            self.error.emit("Failed")
        else:
            self.finished.emit("Done")


def test_task_manager_success_lifecycle(qtbot):
    """Test TaskManager registers worker, prevents GC, and cleans up on success."""
    manager = TaskManager()
    worker = DummyWorker(run_duration=0.05)

    # Start task
    manager.start_task(worker)
    assert manager.has_active_tasks() is True
    assert worker in manager._active_workers

    # Wait for the worker to finish using qtbot
    with qtbot.waitSignal(worker.finished, timeout=1000):
        pass

    # Wait for cleanup slot execution
    qtbot.waitUntil(lambda: not manager.has_active_tasks(), timeout=1000)

    assert manager.has_active_tasks() is False
    assert worker not in manager._active_workers


def test_task_manager_error_lifecycle(qtbot):
    """Test TaskManager cleans up correctly when worker fails."""
    manager = TaskManager()
    worker = DummyWorker(run_duration=0.05, fail=True)

    manager.start_task(worker)
    assert manager.has_active_tasks() is True

    with qtbot.waitSignal(worker.error, timeout=1000):
        pass

    qtbot.waitUntil(lambda: not manager.has_active_tasks(), timeout=1000)
    assert manager.has_active_tasks() is False
    assert worker not in manager._active_workers


def test_task_manager_shutdown(qtbot):
    """Test TaskManager shutdown terminates running threads safely."""
    manager = TaskManager()
    worker = DummyWorker(run_duration=5.0)

    manager.start_task(worker)
    assert manager.has_active_tasks() is True

    # Shutdown should stop it quickly
    start_time = time.time()
    manager.shutdown()
    duration = time.time() - start_time

    assert duration < 3.0
    assert manager.has_active_tasks() is False
    assert worker not in manager._active_workers
    assert worker.isFinished() or not worker.isRunning()


def test_presenter_blocks_overlapping_tasks(qtbot):
    """Test NavigationPresenter prevents starting new tasks when one is running."""
    view = MockView()
    archive_model = ArchiveModel()
    fs_model = DummyModel()
    proxy = DummyModel()

    presenter = NavigationPresenter(view, archive_model, fs_model, proxy)

    # Start a long-running task
    dummy_worker = DummyWorker(run_duration=5.0)
    presenter.task_manager.start_task(dummy_worker)
    assert presenter.task_manager.has_active_tasks() is True

    # Try triggering another task (on_add)
    view.selected_fs_paths = ["file.txt"]
    view.save_dialog_result = ("archive.zip", "ZIP 文件 (*.zip)")

    presenter.on_add()

    # Verify task was rejected and warning was shown
    assert len(view.messages) == 1
    title, msg, icon = view.messages[0]
    assert title == "警告"
    assert "已有正在运行的任务" in msg
    assert icon == "warning"

    # Clean up
    presenter.task_manager.shutdown()
