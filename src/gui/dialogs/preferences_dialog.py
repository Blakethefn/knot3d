"""Preferences dialog backed by QSettings."""

from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore, QtWidgets

from src.gui import settings as gui_settings


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
        layout.addRow("Screenshot width", self.width_spin)
        layout.addRow("Screenshot height", self.height_spin)
        layout.addRow(buttons)

    def _load(self) -> None:
        self.output_dir_edit.setText(str(self.settings.value(gui_settings.KEY_DEFAULT_OUTPUT_DIR)))
        self.auto_validate_checkbox.setChecked(bool(self.settings.value(gui_settings.KEY_AUTO_VALIDATE, False, bool)))
        self.auto_load_scene_checkbox.setChecked(bool(self.settings.value(gui_settings.KEY_AUTO_LOAD_SCENE, True, bool)))
        self.preserve_layout_checkbox.setChecked(bool(self.settings.value(gui_settings.KEY_PRESERVE_LAYOUT, True, bool)))
        self.width_spin.setValue(int(self.settings.value(gui_settings.KEY_SCREENSHOT_WIDTH, 1600)))
        self.height_spin.setValue(int(self.settings.value(gui_settings.KEY_SCREENSHOT_HEIGHT, 1000)))

    def accept(self) -> None:
        """Persist preferences then close."""

        self.settings.setValue(gui_settings.KEY_DEFAULT_OUTPUT_DIR, self.output_dir_edit.text() or str(Path("out")))
        self.settings.setValue(gui_settings.KEY_AUTO_VALIDATE, self.auto_validate_checkbox.isChecked())
        self.settings.setValue(gui_settings.KEY_AUTO_LOAD_SCENE, self.auto_load_scene_checkbox.isChecked())
        self.settings.setValue(gui_settings.KEY_PRESERVE_LAYOUT, self.preserve_layout_checkbox.isChecked())
        self.settings.setValue(gui_settings.KEY_SCREENSHOT_WIDTH, self.width_spin.value())
        self.settings.setValue(gui_settings.KEY_SCREENSHOT_HEIGHT, self.height_spin.value())
        super().accept()
