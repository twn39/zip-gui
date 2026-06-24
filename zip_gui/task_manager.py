from __future__ import annotations

import logging
from PySide6.QtCore import QObject, QThread

logger = logging.getLogger(__name__)


class TaskManager(QObject):
    """Manages the lifecycle of active QThread background workers to prevent GC."""

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._active_workers: set[QThread] = set()

    def start_task(self, worker: QThread) -> None:
        """Register the worker thread, connect cleanup signals, and start it."""
        self._active_workers.add(worker)

        # Connect finished and error signals to cleanup
        # We use keyword-argument binding to capture the exact worker reference in Python
        worker.finished.connect(lambda *args, w=worker: self._cleanup_worker(w))
        if hasattr(worker, "error"):
            worker.error.connect(lambda *args, w=worker: self._cleanup_worker(w))

        worker.start()

    def has_active_tasks(self) -> bool:
        """Check if there are any active background tasks running."""
        # Clean up any threads that are no longer running just in case
        finished_workers = [w for w in self._active_workers if w.isFinished()]
        for w in finished_workers:
            self._cleanup_worker(w)
        return len(self._active_workers) > 0

    def _cleanup_worker(self, worker: QThread) -> None:
        """Discard the worker from the active set and schedule it for deletion."""
        if worker in self._active_workers:
            self._active_workers.discard(worker)
            worker.deleteLater()

    def shutdown(self) -> None:
        """Safely terminate and join all running thread tasks on application exit."""
        active = list(self._active_workers)
        self._active_workers.clear()

        for worker in active:
            if worker.isRunning():
                worker.requestInterruption()
                worker.quit()
                # Wait up to 2 seconds for clean exit, otherwise force terminate
                if not worker.wait(2000):
                    logger.warning(f"Worker {worker} did not stop in time, forcing termination.")
                    worker.terminate()
                    worker.wait()
