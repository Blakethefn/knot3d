"""Bottom-dock progress panel."""

from __future__ import annotations

from PySide6 import QtCore, QtWidgets


class ProgressPanelWidget(QtWidgets.QWidget):
    """Show active job state, progress, and cancellation."""

    cancel_requested = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.job_label = QtWidgets.QLabel("Idle")
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.cancel_button = QtWidgets.QPushButton("Cancel Active Job")
        self.cancel_button.setEnabled(False)
        layout.addWidget(self.job_label, 2)
        layout.addWidget(self.progress_bar, 2)
        layout.addWidget(self.cancel_button)
        self.cancel_button.clicked.connect(self.cancel_requested)

    def set_progress(self, message: str, percent: int) -> None:
        """Update the progress bar and status text."""

        self.job_label.setText(message)
        self.progress_bar.setValue(percent)

    def set_busy(self, busy: bool, job_name: str | None = None) -> None:
        """Toggle busy state."""

        self.cancel_button.setEnabled(busy)
        if busy and job_name:
            self.job_label.setText(job_name)
        elif not busy:
            self.job_label.setText("Idle")
            self.progress_bar.setValue(0)
