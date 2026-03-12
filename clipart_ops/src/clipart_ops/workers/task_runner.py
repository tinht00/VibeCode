"""Worker runner dùng QRunnable để tránh block UI."""

from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal


class WorkerSignals(QObject):
    """Signals tiêu chuẩn cho background task."""

    finished = Signal(object)
    error = Signal(str)


class Worker(QRunnable):
    """Chạy một callable trong thread pool."""

    def __init__(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self) -> None:
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.finished.emit(result)
        except Exception as exc:
            self.signals.error.emit(str(exc))


class TaskRunner:
    """Wrapper cho QThreadPool."""

    def __init__(self) -> None:
        self.pool = QThreadPool.globalInstance()

    def submit(
        self,
        fn: Callable[..., Any],
        *args: Any,
        on_success: Callable[[Any], None] | None = None,
        on_error: Callable[[str], None] | None = None,
        **kwargs: Any,
    ) -> None:
        worker = Worker(fn, *args, **kwargs)
        if on_success:
            worker.signals.finished.connect(on_success)
        if on_error:
            worker.signals.error.connect(on_error)
        self.pool.start(worker)
