"""Background worker for analysis runs."""

from __future__ import annotations

import traceback

from PySide6 import QtCore

from src.gui.state import RunRequest
from src.gui.workers.worker_signals import WorkerSignals
from src.services.engine_facade import EngineFacade


class AnalysisWorker(QtCore.QObject):
    """Run analysis in a worker thread."""

    def __init__(self, engine: EngineFacade, request: RunRequest) -> None:
        super().__init__()
        self.engine = engine
        self.request = request
        self.signals = WorkerSignals()
        self._cancel_requested = False

    @QtCore.Slot()
    def run(self) -> None:
        mode = self.request.mode
        self.signals.started.emit(mode)
        try:
            result = self.engine.analyze(
                self.request.pd_code,
                self.request.output_prefix,
                progress_callback=self._on_progress,
            )
            if self._cancel_requested:
                self.signals.cancelled.emit(mode)
            else:
                self.signals.result.emit(mode, result)
        except Exception:
            self.signals.error.emit(mode, traceback.format_exc())
        finally:
            self.signals.finished.emit(mode)

    def cancel(self) -> None:
        """Request cooperative cancellation."""

        self._cancel_requested = True

    def _on_progress(self, message: str, percent: int) -> None:
        if not self._cancel_requested:
            self.signals.progress.emit(message, percent)
