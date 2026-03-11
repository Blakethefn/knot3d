"""PD code editor widget with inline validation feedback."""

from __future__ import annotations

from PySide6 import QtCore, QtWidgets


class PDEditorWidget(QtWidgets.QWidget):
    """Text editor for PD input with inline error messaging."""

    content_changed = QtCore.Signal(str)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QtWidgets.QLabel("PD Code")
        title.setObjectName("sectionTitle")
        self.editor = QtWidgets.QPlainTextEdit()
        self.editor.setObjectName("pdEditor")
        self.editor.setPlaceholderText("Paste a PD code as JSON or a Python list literal.")
        self.error_label = QtWidgets.QLabel("")
        self.error_label.setObjectName("inlineError")
        self.error_label.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(self.editor, 1)
        layout.addWidget(self.error_label)

        self.editor.textChanged.connect(self._emit_change)

    def _emit_change(self) -> None:
        self.content_changed.emit(self.text())

    def text(self) -> str:
        """Return the current editor text."""

        return self.editor.toPlainText()

    def set_text(self, text: str) -> None:
        """Replace the editor contents."""

        self.editor.setPlainText(text)

    def set_validation_message(self, message: str, is_error: bool = False) -> None:
        """Update the inline validation message."""

        self.error_label.setText(message)
        self.error_label.setProperty("error", is_error)
        self.error_label.style().unpolish(self.error_label)
        self.error_label.style().polish(self.error_label)

    def clear_validation_message(self) -> None:
        """Clear the inline validation message."""

        self.set_validation_message("")
