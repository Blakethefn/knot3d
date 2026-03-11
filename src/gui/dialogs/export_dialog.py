"""Export dialog for choosing a base output path."""

from __future__ import annotations

from PySide6 import QtWidgets


class ExportDialog(QtWidgets.QDialog):
    """Collect a base path used to apply blueprint suffix rules."""

    def __init__(self, default_base_path: str, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Export Results")
        layout = QtWidgets.QVBoxLayout(self)
        self.base_path_edit = QtWidgets.QLineEdit(default_base_path)
        layout.addWidget(QtWidgets.QLabel("Base output path"))
        layout.addWidget(self.base_path_edit)
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @property
    def base_path(self) -> str:
        """Return the chosen base path."""

        return self.base_path_edit.text().strip()
