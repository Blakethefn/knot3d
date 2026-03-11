"""Session persistence for the desktop workbench."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.gui.state import SessionState
from src.utils import as_jsonable, ensure_parent_dir, write_json


class SessionStore:
    """Save and restore GUI workbench sessions as JSON."""

    version = 1

    def save(self, state: SessionState, path: str | Path) -> Path:
        """Write a session file and return its resolved path."""

        target = ensure_parent_dir(path)
        payload = self._serialize(state, target)
        write_json(target, payload)
        return target

    def load(self, path: str | Path) -> SessionState:
        """Read a session file into a typed state object."""

        source = Path(path)
        payload = json.loads(source.read_text(encoding="utf-8"))
        analysis_result = self._load_optional_payload(payload, source, "analysis_result", "analysis_result_path")
        unknotting_result = self._load_optional_payload(payload, source, "unknotting_result", "unknotting_result_path")
        crossing_result = self._load_optional_payload(
            payload,
            source,
            "crossing_changes_result",
            "crossing_changes_result_path",
        )
        return SessionState(
            pd_text=payload.get("pd_text", ""),
            pd_code=payload.get("pd_code", []),
            normalized_pd=payload.get("normalized_pd", []),
            validation_result=payload.get("validation_result"),
            analysis_result=analysis_result,
            unknotting_result=unknotting_result,
            crossing_changes_result=crossing_result,
            selected_crossing_index=payload.get("selected_crossing_index"),
            output_dir=self._path_or_none(payload.get("output_dir"), source),
            session_path=source,
            selected_example=payload.get("selected_example"),
            camera_state=payload.get("camera_state"),
            ui_state=payload.get("ui_state", {}),
            export_history=payload.get("export_history", []),
            dirty=False,
        )

    def _serialize(self, state: SessionState, target: Path) -> dict[str, Any]:
        base = target.parent
        return {
            "version": self.version,
            "pd_text": state.pd_text,
            "pd_code": state.pd_code,
            "normalized_pd": state.normalized_pd,
            "validation_result": as_jsonable(state.validation_result),
            "analysis_result": as_jsonable(state.analysis_result),
            "unknotting_result": as_jsonable(state.unknotting_result),
            "crossing_changes_result": as_jsonable(state.crossing_changes_result),
            "analysis_result_path": self._relativize(state.analysis_result_path, base),
            "unknotting_result_path": self._relativize(state.unknotting_result_path, base),
            "crossing_changes_result_path": self._relativize(state.crossing_changes_result_path, base),
            "selected_crossing_index": state.selected_crossing_index,
            "output_dir": self._relativize(state.output_dir, base),
            "selected_example": state.selected_example,
            "camera_state": as_jsonable(state.camera_state),
            "ui_state": as_jsonable(state.ui_state),
            "export_history": as_jsonable(state.export_history),
        }

    def _load_optional_payload(
        self,
        payload: dict[str, Any],
        session_path: Path,
        inline_key: str,
        path_key: str,
    ) -> dict[str, Any] | None:
        inline_value = payload.get(inline_key)
        if inline_value is not None:
            return inline_value
        path_value = payload.get(path_key)
        if not path_value:
            return None
        candidate = self._path_or_none(path_value, session_path)
        if candidate is None or not candidate.exists():
            return None
        return json.loads(candidate.read_text(encoding="utf-8"))

    def _relativize(self, path: Path | None, base: Path) -> str | None:
        if path is None:
            return None
        try:
            return str(Path(path).resolve().relative_to(base.resolve()))
        except ValueError:
            return str(Path(path))

    def _path_or_none(self, value: str | None, session_path: Path) -> Path | None:
        if not value:
            return None
        candidate = Path(value)
        return candidate if candidate.is_absolute() else (session_path.parent / candidate).resolve()
