"""Preferences dialog backed by QSettings."""

from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore, QtWidgets

from src.gui import settings as gui_settings
from src.services.compute_policy import ComputePreferences, detect_compute_devices, resolve_compute_runtime


class PreferencesDialog(QtWidgets.QDialog):
    """Edit persistent GUI preferences."""

    def __init__(self, settings: QtCore.QSettings, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Preferences")
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        layout = QtWidgets.QFormLayout(self)
        self.output_dir_edit = QtWidgets.QLineEdit()
        self.auto_validate_checkbox = QtWidgets.QCheckBox("Auto-run validation on edit")
        self.auto_load_scene_checkbox = QtWidgets.QCheckBox("Auto-load 3D scene after analysis")
        self.preserve_layout_checkbox = QtWidgets.QCheckBox("Preserve last window layout")
        self.compute_device_combo = QtWidgets.QComboBox()
        self._available_devices = detect_compute_devices()
        for dev in self._available_devices:
            self.compute_device_combo.addItem(dev["name"], dev["id"])
        self.cpu_usage_spin = QtWidgets.QSpinBox()
        self.cpu_usage_spin.setRange(1, 100)
        self.cpu_usage_spin.setSuffix("%")
        self.gpu_usage_spin = QtWidgets.QSpinBox()
        self.gpu_usage_spin.setRange(1, 100)
        self.gpu_usage_spin.setSuffix("%")
        self.compute_summary_label = QtWidgets.QLabel()
        self.compute_summary_label.setWordWrap(True)
        self.width_spin = QtWidgets.QSpinBox()
        self.width_spin.setRange(320, 8192)
        self.height_spin = QtWidgets.QSpinBox()
        self.height_spin.setRange(240, 8192)
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addRow("Default output dir", self.output_dir_edit)
        layout.addRow(self.auto_validate_checkbox)
        layout.addRow(self.auto_load_scene_checkbox)
        layout.addRow(self.preserve_layout_checkbox)
        layout.addRow("Compute device", self.compute_device_combo)
        layout.addRow("CPU max usage", self.cpu_usage_spin)
        layout.addRow("GPU max usage", self.gpu_usage_spin)
        layout.addRow(self.compute_summary_label)
        layout.addRow("Screenshot width", self.width_spin)
        layout.addRow("Screenshot height", self.height_spin)
        layout.addRow(buttons)

        self.compute_device_combo.currentIndexChanged.connect(self._update_compute_summary)
        self.compute_device_combo.currentIndexChanged.connect(self._update_usage_visibility)
        self.cpu_usage_spin.valueChanged.connect(self._update_compute_summary)
        self.gpu_usage_spin.valueChanged.connect(self._update_compute_summary)

    def _load(self) -> None:
        self.output_dir_edit.setText(str(self.settings.value(gui_settings.KEY_DEFAULT_OUTPUT_DIR)))
        self.auto_validate_checkbox.setChecked(bool(self.settings.value(gui_settings.KEY_AUTO_VALIDATE, False, bool)))
        self.auto_load_scene_checkbox.setChecked(bool(self.settings.value(gui_settings.KEY_AUTO_LOAD_SCENE, True, bool)))
        self.preserve_layout_checkbox.setChecked(bool(self.settings.value(gui_settings.KEY_PRESERVE_LAYOUT, True, bool)))
        compute = gui_settings.load_compute_preferences(self.settings)
        saved_device = str(self.settings.value(gui_settings.KEY_COMPUTE_DEVICE, "cpu"))
        index = self.compute_device_combo.findData(saved_device)
        if index < 0:
            # Saved device no longer available; map backend preference to best match
            if compute.backend == "gpu":
                # Pick first GPU if available
                for i in range(self.compute_device_combo.count()):
                    if str(self.compute_device_combo.itemData(i)).startswith(("cuda:", "opencl:", "gpu:")):
                        index = i
                        break
            if index < 0:
                index = 0  # fall back to CPU
        self.compute_device_combo.setCurrentIndex(index)
        self.cpu_usage_spin.setValue(compute.cpu_max_usage_percent)
        self.gpu_usage_spin.setValue(compute.gpu_max_usage_percent)
        self.width_spin.setValue(int(self.settings.value(gui_settings.KEY_SCREENSHOT_WIDTH, 1600)))
        self.height_spin.setValue(int(self.settings.value(gui_settings.KEY_SCREENSHOT_HEIGHT, 1000)))
        self._update_usage_visibility()
        self._update_compute_summary()

    def accept(self) -> None:
        """Persist preferences then close."""

        self.settings.setValue(gui_settings.KEY_DEFAULT_OUTPUT_DIR, self.output_dir_edit.text() or str(Path("out")))
        self.settings.setValue(gui_settings.KEY_AUTO_VALIDATE, self.auto_validate_checkbox.isChecked())
        self.settings.setValue(gui_settings.KEY_AUTO_LOAD_SCENE, self.auto_load_scene_checkbox.isChecked())
        self.settings.setValue(gui_settings.KEY_PRESERVE_LAYOUT, self.preserve_layout_checkbox.isChecked())
        device_id = str(self.compute_device_combo.currentData())
        self.settings.setValue(gui_settings.KEY_COMPUTE_DEVICE, device_id)
        # Derive backend from the selected device for the compute policy
        backend = "gpu" if device_id.startswith(("cuda:", "opencl:", "gpu:")) else "cpu"
        self.settings.setValue(gui_settings.KEY_COMPUTE_BACKEND, backend)
        self.settings.setValue(gui_settings.KEY_CPU_MAX_USAGE, self.cpu_usage_spin.value())
        self.settings.setValue(gui_settings.KEY_GPU_MAX_USAGE, self.gpu_usage_spin.value())
        self.settings.setValue(gui_settings.KEY_SCREENSHOT_WIDTH, self.width_spin.value())
        self.settings.setValue(gui_settings.KEY_SCREENSHOT_HEIGHT, self.height_spin.value())
        super().accept()

    def _update_compute_summary(self) -> None:
        device_id = str(self.compute_device_combo.currentData())
        backend = "gpu" if device_id.startswith(("cuda:", "opencl:", "gpu:")) else "cpu"
        compute = ComputePreferences.from_values(
            backend=backend,
            cpu_max_usage_percent=self.cpu_usage_spin.value(),
            gpu_max_usage_percent=self.gpu_usage_spin.value(),
        )
        runtime = resolve_compute_runtime(compute)
        details = [f"Device: {self.compute_device_combo.currentText()}"]
        details.append(f"CPU limit: {runtime.cpu_thread_limit} of {runtime.logical_cpu_count} logical threads")
        if backend == "gpu" and not runtime.gpu_available:
            details.append("(GPU not available — will fall back to CPU)")
        elif backend == "gpu":
            details.append(f"GPU usage: {runtime.gpu_max_usage_percent}%")
        self.compute_summary_label.setText(" | ".join(details))

    def _update_usage_visibility(self) -> None:
        device_id = str(self.compute_device_combo.currentData())
        is_gpu = device_id.startswith(("cuda:", "opencl:", "gpu:"))
        self.gpu_usage_spin.setEnabled(is_gpu)
        self.cpu_usage_spin.setEnabled(True)
