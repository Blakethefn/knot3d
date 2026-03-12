"""Bottom-dock progress panel."""

from __future__ import annotations

from PySide6 import QtCore, QtWidgets


class ProgressPanelWidget(QtWidgets.QWidget):
    """Show active job state, progress, cancellation, and visible stage tracking."""

    cancel_requested = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._stages: list[str] = []
        self._stage_labels: list[QtWidgets.QLabel] = []

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        top_row = QtWidgets.QHBoxLayout()
        self.job_label = QtWidgets.QLabel("Idle")
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.cancel_button = QtWidgets.QPushButton("Cancel Active Job")
        self.cancel_button.setEnabled(False)
        top_row.addWidget(self.job_label, 2)
        top_row.addWidget(self.progress_bar, 2)
        top_row.addWidget(self.cancel_button)

        self.stage_box = QtWidgets.QGroupBox("Active Computations")
        self.stage_layout = QtWidgets.QVBoxLayout(self.stage_box)
        self.stage_layout.setContentsMargins(8, 8, 8, 8)
        self.stage_layout.setSpacing(4)
        self._empty_label = QtWidgets.QLabel("No active computation.")
        self.stage_layout.addWidget(self._empty_label)

        layout.addLayout(top_row)
        layout.addWidget(self.stage_box)
        self.cancel_button.clicked.connect(self.cancel_requested)

    def start_job(self, job_name: str, stages: list[str]) -> None:
        """Initialize the visible stage plan for a run."""

        self.job_label.setText(job_name)
        self.progress_bar.setValue(0)
        self._clear_stage_labels()
        self._stages = list(stages)
        self._stage_labels = []

        if not self._stages:
            self._empty_label.setText("Waiting for progress updates...")
            self._empty_label.show()
            return

        self._empty_label.hide()
        for stage in self._stages:
            label = QtWidgets.QLabel()
            self._stage_labels.append(label)
            self.stage_layout.addWidget(label)
        self._render_stage_states(active_index=None)

    def set_progress(self, message: str, percent: int) -> None:
        """Update the progress bar, active status text, and stage tracker."""

        self.job_label.setText(message)
        self.progress_bar.setValue(percent)
        active_index = self._ensure_stage(message)
        self._render_stage_states(active_index=active_index)

    def set_busy(self, busy: bool, job_name: str | None = None) -> None:
        """Toggle busy state."""

        self.cancel_button.setEnabled(busy)
        if busy:
            if job_name:
                self.job_label.setText(job_name)
            return
        self.job_label.setText("Idle")
        self.progress_bar.setValue(0)

    def mark_finished(self, message: str = "Completed") -> None:
        """Mark all visible stages as complete."""

        if self._stages:
            self._render_stage_states(active_index=len(self._stages) - 1, terminal_state="done")
        else:
            self._empty_label.setText("No active computation.")
            self._empty_label.show()
        self.job_label.setText(message)

    def mark_failed(self, message: str = "Failed") -> None:
        """Mark the current stage as failed."""

        if self._stage_labels:
            self._render_stage_states(active_index=self._current_stage_index(), terminal_state="failed")
        self.job_label.setText(message)

    def mark_cancelled(self, message: str = "Cancelled") -> None:
        """Mark the current stage as cancelled."""

        if self._stage_labels:
            self._render_stage_states(active_index=self._current_stage_index(), terminal_state="cancelled")
        self.job_label.setText(message)

    def stage_texts(self) -> list[str]:
        """Return the current visible stage labels for tests."""

        return [label.text() for label in self._stage_labels]

    def _ensure_stage(self, message: str) -> int:
        if not self._stages:
            self.start_job(self.job_label.text(), [message])
            return 0

        try:
            return self._stages.index(message)
        except ValueError:
            self._stages.append(message)
            label = QtWidgets.QLabel()
            self._stage_labels.append(label)
            self.stage_layout.addWidget(label)
            return len(self._stages) - 1

    def _render_stage_states(self, active_index: int | None, terminal_state: str | None = None) -> None:
        if not self._stage_labels:
            return

        for index, label in enumerate(self._stage_labels):
            if terminal_state == "done":
                prefix = "[x]"
            elif terminal_state in {"failed", "cancelled"} and index == (active_index if active_index is not None else -1):
                prefix = "[!]" if terminal_state == "failed" else "[-]"
            elif active_index is not None and index < active_index:
                prefix = "[x]"
            elif active_index is not None and index == active_index:
                prefix = "[>]"
            else:
                prefix = "[ ]"
            label.setText(f"{prefix} {self._stages[index]}")

    def _clear_stage_labels(self) -> None:
        for label in self._stage_labels:
            self.stage_layout.removeWidget(label)
            label.deleteLater()
        self._stage_labels = []
        self._stages = []
        self._empty_label.setText("No active computation.")
        self._empty_label.show()

    def _current_stage_index(self) -> int:
        for index, label in enumerate(self._stage_labels):
            if label.text().startswith("[>]"):
                return index
        return max(0, len(self._stage_labels) - 1)
