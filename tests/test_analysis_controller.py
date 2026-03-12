from __future__ import annotations


def test_analyze_flow(gui_window, wait_until):
    gui_window.pd_editor.set_text("[[1,5,2,4],[3,1,4,6],[5,3,6,2]]")
    gui_window.controller.analysis.run_analysis()
    wait_until(lambda: gui_window.session_state.analysis_result is not None)
    assert "analyze" in gui_window.controller.engine.calls


def test_unknotting_flow(gui_window, wait_until):
    gui_window.pd_editor.set_text("[[1,5,2,4],[3,1,4,6],[5,3,6,2]]")
    gui_window.controller.analysis.run_unknotting_search()
    wait_until(lambda: gui_window.session_state.unknotting_result is not None)
    assert "unknotting_search" in gui_window.controller.engine.calls


def test_error_flow(gui_window, wait_until):
    errors = []
    gui_window.controller.analysis.error_occurred.connect(errors.append)
    gui_window.controller.engine.fail_mode = "analyze"
    gui_window.pd_editor.set_text("[[1,5,2,4],[3,1,4,6],[5,3,6,2]]")
    gui_window.controller.analysis.run_analysis()
    wait_until(lambda: bool(errors))
    assert "failed" in errors[0]


def test_result_updates_state(gui_window, wait_until):
    gui_window.pd_editor.set_text("[[1,5,2,4],[3,1,4,6],[5,3,6,2]]")
    gui_window.controller.analysis.run_analysis()
    wait_until(lambda: gui_window.session_state.analysis_result is not None)
    assert gui_window.session_state.analysis_result["knot_name"] == "3_1"


def test_progress_updates_status_bar(gui_window, wait_until):
    seen = []
    gui_window.controller.analysis.progress_updated.connect(lambda message, percent: seen.append((message, percent)))
    gui_window.controller.engine.delay_seconds = 0.2
    gui_window.pd_editor.set_text("[[1,5,2,4],[3,1,4,6],[5,3,6,2]]")
    gui_window.controller.analysis.run_analysis()
    wait_until(lambda: bool(seen))
    assert seen[0][0] == "Starting"


def test_analyze_shows_visible_computation_steps(gui_window, wait_until):
    gui_window.pd_editor.set_text("[[1,5,2,4],[3,1,4,6],[5,3,6,2]]")
    gui_window.controller.analysis.run_analysis()
    wait_until(lambda: gui_window.session_state.analysis_result is not None)
    assert any("Parsing PD code" in text for text in gui_window.progress_panel.stage_texts())


def test_unknot_check_shows_visible_computation_steps(gui_window, wait_until):
    gui_window.pd_editor.set_text("[[1,5,2,4],[3,1,4,6],[5,3,6,2]]")
    gui_window.controller.analysis.run_unknotting_search()
    wait_until(lambda: gui_window.session_state.unknotting_result is not None)
    assert any("Checking unknot status" in text for text in gui_window.progress_panel.stage_texts())
