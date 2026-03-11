from __future__ import annotations

from src.gui.controllers import AppController
from src.gui.main_window import MainWindow
from src.gui.state import SessionState
from src.services import RecentFilesStore, SessionStore


def test_full_trefoil_analyze_from_ui(real_gui_window, wait_until):
    real_gui_window.example_picker.select_example("trefoil")
    wait_until(lambda: "[1, 5, 2, 4]" in real_gui_window.pd_editor.text(), timeout_ms=5000)
    real_gui_window.controller.analysis.run_analysis()
    wait_until(lambda: real_gui_window.session_state.analysis_result is not None, timeout_ms=30000)
    assert real_gui_window.invariant_panel._labels["crossing_number"].text() == "3"


def test_full_trefoil_unknotting_from_ui(real_gui_window, wait_until):
    real_gui_window.example_picker.select_example("trefoil")
    wait_until(lambda: "[1, 5, 2, 4]" in real_gui_window.pd_editor.text(), timeout_ms=5000)
    real_gui_window.run_panel.unknot_button.click()
    wait_until(lambda: real_gui_window.session_state.unknotting_result is not None, timeout_ms=30000)
    assert real_gui_window.session_state.unknotting_result["is_unknot"] is False
    assert real_gui_window.session_state.unknotting_result["recognition_method"] == "fast_filter"


def test_select_candidate_updates_views(real_gui_window, wait_until):
    real_gui_window.example_picker.select_example("trefoil")
    wait_until(lambda: "[1, 5, 2, 4]" in real_gui_window.pd_editor.text(), timeout_ms=5000)
    real_gui_window.run_panel.unknot_button.click()
    wait_until(lambda: real_gui_window.crossing_table.model.rowCount() > 0, timeout_ms=30000)
    real_gui_window.crossing_table.table.clearSelection()
    real_gui_window.crossing_table.select_row(0)
    wait_until(lambda: real_gui_window.crossing_detail.summary_label.text() != "No record selected.", timeout_ms=10000)
    assert real_gui_window.session_state.selected_crossing_index is None
    assert "Current diagram" in real_gui_window.comparison_view.meta_label.text()


def test_session_roundtrip(real_gui_window, qt_settings, tmp_path, wait_until, qapp):
    real_gui_window.example_picker.select_example("trefoil")
    wait_until(lambda: "[1, 5, 2, 4]" in real_gui_window.pd_editor.text(), timeout_ms=5000)
    real_gui_window.run_panel.analyze_button.click()
    wait_until(lambda: real_gui_window.session_state.analysis_result is not None, timeout_ms=30000)
    target = real_gui_window.controller.sessions.save_session(tmp_path / "session.json")
    real_gui_window.controller.sessions.new_session()
    assert real_gui_window.session_state.analysis_result is None
    real_gui_window.controller.sessions.load_session(target)
    assert real_gui_window.session_state.analysis_result is not None


def test_export_pipeline_from_ui(real_gui_window, wait_until, tmp_path):
    real_gui_window.example_picker.select_example("trefoil")
    wait_until(lambda: "[1, 5, 2, 4]" in real_gui_window.pd_editor.text(), timeout_ms=5000)
    real_gui_window.run_panel.analyze_button.click()
    wait_until(lambda: real_gui_window.session_state.analysis_result is not None, timeout_ms=30000)
    outputs = real_gui_window.controller.exports.export_results_bundle(tmp_path / "bundle")
    assert (tmp_path / "bundle_analysis.json").exists()
    assert (tmp_path / "bundle_diagram.png").exists()
    assert (tmp_path / "bundle_3d.png").exists()
    assert outputs["centerline_csv"].endswith("_centerline.csv")
