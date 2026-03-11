"""Timestamped log console widget."""

from __future__ import annotations

from datetime import datetime

from PySide6 import QtWidgets


class LogConsoleWidget(QtWidgets.QPlainTextEdit):
    """Read-only log console for background job updates."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumBlockCount(500)

    def append_log(self, message: str) -> None:
        """Append a timestamped log line."""

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.appendPlainText(f"[{timestamp}] {message}")
