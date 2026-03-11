"""Primary run controls for validation, analysis, and exports."""

from __future__ import annotations

from PySide6 import QtCore, QtWidgets


class RunPanelWidget(QtWidgets.QWidget):
    """Expose the high-value workbench actions."""

    validate_requested = QtCore.Signal()
    analyze_requested = QtCore.Signal()
    unknot_requested = QtCore.Signal()
    mesh_requested = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.validation_label = QtWidgets.QLabel("No validation run yet.")
        self.validation_label.setWordWrap(True)

        self.validate_button = QtWidgets.QPushButton("Validate")
        self.analyze_button = QtWidgets.QPushButton("Analyze")
        self.unknot_button = QtWidgets.QPushButton("Check Unknot")
        self.mesh_button = QtWidgets.QPushButton("Export Mesh")

        for button in (
            self.validate_button,
            self.analyze_button,
            self.unknot_button,
            self.mesh_button,
        ):
            button.setMinimumHeight(32)
            layout.addWidget(button)

        layout.addWidget(self.validation_label)
        layout.addStretch(1)

        self.validate_button.clicked.connect(self.validate_requested)
        self.analyze_button.clicked.connect(self.analyze_requested)
        self.unknot_button.clicked.connect(self.unknot_requested)
        self.mesh_button.clicked.connect(self.mesh_requested)

    def set_validation_message(self, message: str, is_error: bool = False) -> None:
        """Update the validation summary line."""

        self.validation_label.setText(message)
        self.validation_label.setProperty("error", is_error)
        self.validation_label.style().unpolish(self.validation_label)
        self.validation_label.style().polish(self.validation_label)

    def set_busy(self, busy: bool) -> None:
        """Disable run controls while a background job is active."""

        self.validate_button.setEnabled(not busy)
        self.analyze_button.setEnabled(not busy)
        self.unknot_button.setEnabled(not busy)
        self.mesh_button.setEnabled(not busy)
