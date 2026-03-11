"""QSettings keys and GUI defaults."""

from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore

from src.services.compute_policy import ComputePreferences

ORGANIZATION_NAME = "Codex"
APPLICATION_NAME = "KnotWorkbench"
DEFAULT_OUTPUT_DIR = Path("out")

KEY_DEFAULT_OUTPUT_DIR = "preferences/default_output_dir"
KEY_AUTO_VALIDATE = "preferences/auto_validate"
KEY_SCREENSHOT_WIDTH = "preferences/screenshot_width"
KEY_SCREENSHOT_HEIGHT = "preferences/screenshot_height"
KEY_AUTO_LOAD_SCENE = "preferences/auto_load_scene"
KEY_PRESERVE_LAYOUT = "preferences/preserve_layout"
KEY_COMPUTE_BACKEND = "preferences/compute_backend"
KEY_CPU_MAX_USAGE = "preferences/cpu_max_usage"
KEY_GPU_MAX_USAGE = "preferences/gpu_max_usage"
KEY_WINDOW_GEOMETRY = "window/geometry"
KEY_WINDOW_STATE = "window/state"


def default_preferences() -> dict[str, object]:
    """Return the baseline preference values."""

    return {
        KEY_DEFAULT_OUTPUT_DIR: str(DEFAULT_OUTPUT_DIR),
        KEY_AUTO_VALIDATE: False,
        KEY_SCREENSHOT_WIDTH: 1600,
        KEY_SCREENSHOT_HEIGHT: 1000,
        KEY_AUTO_LOAD_SCENE: True,
        KEY_PRESERVE_LAYOUT: True,
        KEY_COMPUTE_BACKEND: "auto",
        KEY_CPU_MAX_USAGE: 100,
        KEY_GPU_MAX_USAGE: 100,
    }


def apply_default_preferences(settings: QtCore.QSettings) -> None:
    """Populate missing preference keys with default values."""

    for key, value in default_preferences().items():
        if settings.value(key) is None:
            settings.setValue(key, value)


def load_compute_preferences(settings: QtCore.QSettings) -> ComputePreferences:
    """Load and normalize compute preferences from QSettings."""

    return ComputePreferences.from_values(
        backend=str(settings.value(KEY_COMPUTE_BACKEND, "auto")),
        cpu_max_usage_percent=int(settings.value(KEY_CPU_MAX_USAGE, 100)),
        gpu_max_usage_percent=int(settings.value(KEY_GPU_MAX_USAGE, 100)),
    )
