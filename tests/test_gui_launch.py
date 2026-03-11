from __future__ import annotations

import os

from src.gui.app import build_main_window, create_application


def test_gui_main_starts(qapp):
    app = create_application()
    window = build_main_window()
    assert app is not None
    assert window.windowTitle() == "Knot Workbench"
    window.close()


def test_gui_main_offscreen(qapp, monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("PYVISTA_OFF_SCREEN", "true")
    window = build_main_window()
    assert os.environ["QT_QPA_PLATFORM"] == "offscreen"
    window.close()
