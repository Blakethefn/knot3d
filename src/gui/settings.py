"""QSettings keys and GUI defaults."""

from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore

ORGANIZATION_NAME = "Codex"
APPLICATION_NAME = "KnotWorkbench"
DEFAULT_OUTPUT_DIR = Path("out")

KEY_DEFAULT_OUTPUT_DIR = "preferences/default_output_dir"
KEY_AUTO_VALIDATE = "preferences/auto_validate"
KEY_SCREENSHOT_WIDTH = "preferences/screenshot_width"
KEY_SCREENSHOT_HEIGHT = "preferences/screenshot_height"
KEY_AUTO_LOAD_SCENE = "preferences/auto_load_scene"
KEY_PRESERVE_LAYOUT = "preferences/preserve_layout"
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
    }


def apply_default_preferences(settings: QtCore.QSettings) -> None:
    """Populate missing preference keys with default values."""

    for key, value in default_preferences().items():
        if settings.value(key) is None:
            settings.setValue(key, value)
