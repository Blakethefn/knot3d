from __future__ import annotations


def test_accepts_json_literal(gui_window):
    gui_window.pd_editor.set_text("[[1,5,2,4],[3,1,4,6],[5,3,6,2]]")
    assert gui_window.controller.analysis.validate_current_text() is True


def test_accepts_python_literal(gui_window):
    gui_window.pd_editor.set_text("[(1,5,2,4),(3,1,4,6),(5,3,6,2)]")
    assert gui_window.controller.analysis.validate_current_text() is True


def test_invalid_input_shows_error(gui_window):
    gui_window.pd_editor.set_text("[[1,2,3]]")
    assert gui_window.controller.analysis.validate_current_text() is False
    assert gui_window.pd_editor.error_label.text()


def test_dirty_state_changes_on_edit(gui_window):
    gui_window.session_state.dirty = False
    gui_window.pd_editor.set_text("[[1,5,2,4],[3,1,4,6],[5,3,6,2]]")
    gui_window.controller.sessions.on_editor_changed(gui_window.pd_editor.text())
    assert gui_window.session_state.dirty is True
