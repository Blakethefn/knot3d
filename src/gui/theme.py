"""Theme and stylesheet helpers for the GUI."""

from __future__ import annotations

from pathlib import Path

from PySide6 import QtWidgets


def stylesheet_path() -> Path:
    """Return the application stylesheet path."""

    return Path(__file__).resolve().parents[2] / "assets" / "styles" / "app.qss"


def apply_theme(app: QtWidgets.QApplication) -> None:
    """Apply the bundled palette and stylesheet."""

    app.setStyle("Fusion")
    path = stylesheet_path()
    if path.exists():
        app.setStyleSheet(path.read_text(encoding="utf-8"))
