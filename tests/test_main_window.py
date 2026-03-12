from __future__ import annotations

from PySide6 import QtGui, QtTest, QtWidgets


def test_window_constructs(gui_window):
    assert gui_window.windowTitle() == "Knot Workbench"


def test_required_docks_exist(gui_window):
    assert gui_window.input_dock.windowTitle() == "Input"
    assert gui_window.results_dock.windowTitle() == "Results"
    assert gui_window.bottom_dock.windowTitle() == "Progress / Logs"


def test_actions_exist(gui_window):
    assert gui_window.action_validate is not None
    assert gui_window.action_analyze is not None
    assert gui_window.action_unknot is not None
    assert gui_window.action_export_mesh is not None


def test_results_dock_uses_scroll_area(gui_window):
    assert isinstance(gui_window.results_dock.widget(), QtWidgets.QScrollArea)


def test_load_example_updates_editor(gui_window):
    gui_window.example_picker.select_example("trefoil")
    assert "[1, 5, 2, 4]" in gui_window.pd_editor.text()


def test_load_hundred_crossing_example_updates_editor(gui_window):
    gui_window.example_picker.select_example("hundred_crossing")
    assert "[135, 3, 136, 2]" in gui_window.pd_editor.text()


def test_validate_action_updates_status(gui_window):
    gui_window.pd_editor.set_text("[[1,5,2,4],[3,1,4,6],[5,3,6,2]]")
    gui_window.action_validate.trigger()
    assert "Valid PD" in gui_window.run_panel.validation_label.text()


def test_busy_state_disables_run_buttons(gui_window):
    gui_window.set_busy(True, "Analyze")
    assert gui_window.run_panel.analyze_button.isEnabled() is False
    gui_window.set_busy(False)
    assert gui_window.run_panel.analyze_button.isEnabled() is True


def test_cancel_action_enabled_when_running(gui_window):
    gui_window.set_busy(True, "Analyze")
    assert gui_window.action_cancel.isEnabled() is True
    gui_window.set_busy(False)
    assert gui_window.action_cancel.isEnabled() is False


def test_close_prompts_on_dirty_session(gui_window, monkeypatch):
    gui_window.session_state.dirty = True
    monkeypatch.setattr(QtWidgets.QMessageBox, "question", lambda *args, **kwargs: QtWidgets.QMessageBox.StandardButton.Cancel)
    event = QtGui.QCloseEvent()
    gui_window.closeEvent(event)
    assert event.isAccepted() is False


def test_result_labels_wrap_long_content(gui_window):
    assert gui_window.analysis_summary.conclusion_label.wordWrap() is True
    assert gui_window.invariant_panel._labels["alexander_polynomial"].wordWrap() is True
