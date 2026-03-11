from __future__ import annotations

import json

from src.gui.state import SessionState
from src.services.session_store import SessionStore


def test_save_session(tmp_path):
    store = SessionStore()
    state = SessionState(pd_text="[]", pd_code=[], output_dir=tmp_path)
    target = store.save(state, tmp_path / "session.json")
    assert target.exists()


def test_load_session(tmp_path):
    store = SessionStore()
    state = SessionState(pd_text="[[1,5,2,4]]", pd_code=[[1, 5, 2, 4]], output_dir=tmp_path, selected_example="demo")
    target = store.save(state, tmp_path / "session.json")
    loaded = store.load(target)
    assert loaded.pd_text == state.pd_text
    assert loaded.selected_example == "demo"


def test_missing_optional_paths_ok(tmp_path):
    payload = {"version": 1, "pd_text": "[]", "pd_code": [], "analysis_result_path": "missing.json"}
    target = tmp_path / "session.json"
    target.write_text(json.dumps(payload), encoding="utf-8")
    loaded = SessionStore().load(target)
    assert loaded.analysis_result is None


def test_version_field_present(tmp_path):
    state = SessionState(pd_text="[]", pd_code=[], output_dir=tmp_path)
    target = SessionStore().save(state, tmp_path / "session.json")
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["version"] == 1


def test_selected_crossing_persisted(tmp_path):
    state = SessionState(pd_text="[]", pd_code=[], output_dir=tmp_path, selected_crossing_index=2)
    target = SessionStore().save(state, tmp_path / "session.json")
    loaded = SessionStore().load(target)
    assert loaded.selected_crossing_index == 2
