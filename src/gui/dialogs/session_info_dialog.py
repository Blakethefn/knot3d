"""Dialog showing current session metadata."""

from __future__ import annotations

import json

from PySide6 import QtWidgets

from src.gui.state import SessionState


class SessionInfoDialog(QtWidgets.QDialog):
    """Inspect the current session payload in a read-only dialog."""

    def __init__(self, state: SessionState, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Session Info")
        layout = QtWidgets.QVBoxLayout(self)
        text = QtWidgets.QPlainTextEdit()
        text.setReadOnly(True)
        payload = {
            "pd_code": state.pd_code,
            "selected_example": state.selected_example,
            "selected_crossing_index": state.selected_crossing_index,
            "output_dir": str(state.output_dir) if state.output_dir else None,
            "session_path": str(state.session_path) if state.session_path else None,
            "dirty": state.dirty,
        }
        text.setPlainText(json.dumps(payload, indent=2))
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(text, 1)
        layout.addWidget(buttons)
