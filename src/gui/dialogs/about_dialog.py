"""About dialog for the desktop workbench."""

from __future__ import annotations

from PySide6 import QtWidgets


class AboutDialog(QtWidgets.QDialog):
    """Display a concise application overview and engine versions."""

    def __init__(self, versions: dict[str, str], parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("About Knot Workbench")
        layout = QtWidgets.QVBoxLayout(self)
        text = QtWidgets.QPlainTextEdit()
        text.setReadOnly(True)
        lines = [
            "Knot Workbench",
            "",
            "Native PySide6 desktop application around the shared topology engine.",
            "",
            "Runtime versions:",
            *[f"- {name}: {version}" for name, version in versions.items()],
        ]
        text.setPlainText("\n".join(lines))
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(text, 1)
        layout.addWidget(buttons)
