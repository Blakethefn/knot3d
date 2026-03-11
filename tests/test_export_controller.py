from __future__ import annotations

import json

import pytest


def test_export_analysis(gui_window, wait_until, tmp_path):
    gui_window.pd_editor.set_text("[[1,5,2,4],[3,1,4,6],[5,3,6,2]]")
    gui_window.controller.analysis.run_analysis()
    wait_until(lambda: gui_window.session_state.analysis_result is not None)
    target = gui_window.controller.exports.export_analysis(tmp_path / "analysis.json")
    assert json.loads(target.read_text(encoding="utf-8"))["knot_name"] == "3_1"


def test_export_session(gui_window, tmp_path):
    target = gui_window.controller.exports.export_session(tmp_path / "session.json")
    assert target.exists()


def test_export_requires_data(gui_window, tmp_path):
    with pytest.raises(ValueError):
        gui_window.controller.exports.export_analysis(tmp_path / "analysis.json")


def test_base_name_suffixes_applied(gui_window, tmp_path):
    outputs = gui_window.controller.export_service.base_name_outputs(tmp_path / "bundle")
    assert outputs["analysis_json"].endswith("_analysis.json")
    assert outputs["crossing_changes_json"].endswith("_crossing_changes.json")
