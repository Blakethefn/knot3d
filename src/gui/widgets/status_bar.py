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
        self.compute_label = QtWidgets.QLabel("Compute: CPU | 100%")
        layout.addWidget(self.session_label)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.crossing_label)
        layout.addWidget(self.engine_label)
        layout.addWidget(self.compute_label)

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

    def set_compute_runtime(self, runtime: dict[str, object] | None) -> None:
        """Update the compute runtime summary."""

        if runtime is None:
            self.compute_label.setText("Compute: CPU | 100%")
            return

        active_backend = str(runtime.get("active_backend", "cpu")).upper()
        cpu_percent = int(runtime.get("cpu_max_usage_percent", 100))
        cpu_threads = int(runtime.get("cpu_thread_limit", 1))
        logical_cpus = int(runtime.get("logical_cpu_count", cpu_threads))
        summary = f"Compute: {active_backend} | CPU {cpu_percent}% ({cpu_threads}/{logical_cpus})"
        if str(runtime.get("active_backend", "cpu")) == "gpu":
            gpu_percent = int(runtime.get("gpu_max_usage_percent", 100))
            summary += f" | GPU {gpu_percent}%"
        elif str(runtime.get("requested_backend", "cpu")) == "gpu" and not bool(runtime.get("gpu_available", False)):
            summary += " | GPU unavailable"
        self.compute_label.setText(summary)
