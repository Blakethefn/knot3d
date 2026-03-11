"""Status bar helper widget."""

from __future__ import annotations

from pathlib import Path

from PySide6 import QtWidgets


class StatusBarWidget(QtWidgets.QWidget):
    """Compact status strip for session and selection state."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.session_label = QtWidgets.QLabel("Session: unsaved")
        self.progress_label = QtWidgets.QLabel("Ready")
        self.crossing_label = QtWidgets.QLabel("Selected crossing: none")
        self.engine_label = QtWidgets.QLabel("Engine: idle")
        layout.addWidget(self.session_label)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.crossing_label)
        layout.addWidget(self.engine_label)

    def set_session(self, path: Path | None) -> None:
        """Update the session path text."""

        self.session_label.setText(f"Session: {path}" if path else "Session: unsaved")

    def set_progress(self, text: str) -> None:
        """Update the status progress text."""

        self.progress_label.setText(text)

    def set_selected_crossing(self, crossing_index: int | None) -> None:
        """Update the selected crossing text."""

        label = "none" if crossing_index is None else str(crossing_index)
        self.crossing_label.setText(f"Selected crossing: {label}")

    def set_engine_state(self, text: str) -> None:
        """Update the engine state text."""

        self.engine_label.setText(f"Engine: {text}")
