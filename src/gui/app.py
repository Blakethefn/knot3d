"""Qt application bootstrap."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from src.gui.controllers import AppController
from src.gui.main_window import MainWindow
from src.gui.settings import APPLICATION_NAME, ORGANIZATION_NAME, apply_default_preferences
from src.gui.theme import apply_theme


def create_application() -> QtWidgets.QApplication:
    """Create or reuse the QApplication instance."""

    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setApplicationName(APPLICATION_NAME)
    icon_path = Path(__file__).resolve().parents[2] / "assets" / "icons" / "app_icon.png"
    if icon_path.exists():
        app.setWindowIcon(QtGui.QIcon(str(icon_path)))
    apply_theme(app)
    return app


def build_main_window() -> MainWindow:
    """Construct the main window and controller graph."""

    settings = QtCore.QSettings()
    apply_default_preferences(settings)
    window = MainWindow()
    controller = AppController(window, settings)
    window.controller = controller
    window.on_save_before_close = controller.sessions.save_session
    if bool(settings.value("preferences/preserve_layout", True, bool)):
        geometry = settings.value("window/geometry")
        dock_state = settings.value("window/state")
        if geometry:
            window.restoreGeometry(QtCore.QByteArray.fromBase64(bytes(geometry, "ascii")))
        if dock_state:
            window.restoreState(QtCore.QByteArray.fromBase64(bytes(dock_state, "ascii")))
    return window


def run() -> int:
    """Launch the desktop application."""

    app = create_application()
    window = build_main_window()
    window.show()
    result = app.exec()
    settings = QtCore.QSettings()
    if bool(settings.value("preferences/preserve_layout", True, bool)):
        settings.setValue("window/geometry", bytes(window.saveGeometry().toBase64()).decode("ascii"))
        settings.setValue("window/state", bytes(window.saveState().toBase64()).decode("ascii"))
    return result
