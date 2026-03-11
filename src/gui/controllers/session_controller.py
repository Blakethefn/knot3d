"""Controller for session lifecycle, examples, and recent files."""

from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore, QtWidgets

from src.gui.state import SessionState
from src.services.recent_files import RecentFilesStore
from src.services.session_store import SessionStore


class SessionController(QtCore.QObject):
    """Manage sessions, example loads, and recent files."""

    def __init__(
        self,
        window,
        state: SessionState,
        session_store: SessionStore,
        recent_files: RecentFilesStore,
        settings: QtCore.QSettings,
        parent: QtCore.QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.window = window
        self.state = state
        self.session_store = session_store
        self.recent_files = recent_files
        self.settings = settings
        self._auto_validate_timer = QtCore.QTimer(self)
        self._auto_validate_timer.setSingleShot(True)
        self._auto_validate_timer.setInterval(350)

    def bind_auto_validate(self, callback) -> None:
        """Attach the analysis-controller validation callback."""

        self._auto_validate_timer.timeout.connect(callback)

    def on_editor_changed(self, text: str) -> None:
        """Track editor edits and schedule optional validation."""

        self.state.pd_text = text
        self.state.mark_dirty()
        if bool(self.settings.value("preferences/auto_validate", False, bool)):
            self._auto_validate_timer.start()

    def load_example(self, name: str, pd_text: str) -> None:
        """Load a bundled example into the editor."""

        self.state.selected_example = name
        self.state.pd_text = pd_text
        self.state.mark_dirty()
        self.window.pd_editor.set_text(pd_text)
        self.window.status_widget.set_progress(f"Loaded example: {name}")
        self.window.log_console.append_log(f"Loaded example '{name}'.")

    def load_pd_file(self, path: str | Path) -> Path:
        """Load a PD input file into the editor."""

        source = Path(path)
        self.window.pd_editor.set_text(source.read_text(encoding="utf-8"))
        self.state.selected_example = source.stem
        self.state.mark_dirty()
        self.recent_files.add_recent_file("pd", source)
        self.window.log_console.append_log(f"Loaded PD file {source}.")
        return source

    def save_session(self, path: str | Path | None = None) -> Path | None:
        """Persist the current session."""

        target = Path(path) if path else self.state.session_path
        if target is None:
            filename, _ = QtWidgets.QFileDialog.getSaveFileName(
                self.window,
                "Save Session",
                str(Path("out") / "session.json"),
                "JSON Files (*.json)",
            )
            if not filename:
                return None
            target = Path(filename)

        self.state.camera_state = self.window.pyvista_view.camera_state()
        self.state.ui_state = self.window.serialized_ui_state()
        saved = self.session_store.save(self.state, target)
        self.state.mark_clean(saved)
        self.recent_files.add_recent_file("session", saved)
        self.window.status_widget.set_session(saved)
        self.window.log_console.append_log(f"Saved session to {saved}.")
        return saved

    def load_session(self, path: str | Path) -> SessionState:
        """Load a saved session and apply it to the UI."""

        loaded = self.session_store.load(path)
        self._copy_state(loaded)
        self.window.pd_editor.set_text(self.state.pd_text)
        self.window.status_widget.set_session(self.state.session_path)
        self.window.status_widget.set_selected_crossing(self.state.selected_crossing_index)
        self.window.status_widget.set_progress("Session loaded")
        if self.state.analysis_result:
            self.window.invariant_panel.set_payload(self.state.analysis_result)
            self.window.analysis_summary.set_results(self.state.analysis_result, self.state.unknotting_result)
            self.window.diagram_canvas.set_diagram(self.state.normalized_pd or self.state.pd_code, self.state.selected_crossing_index)
            self.window.set_raw_json_payloads(
                {
                    "analysis": self.state.analysis_result,
                    "unknotting": self.state.unknotting_result,
                    "crossing_changes": self.state.crossing_changes_result,
                }
            )
            self.window.crossing_table.set_candidates((self.state.crossing_changes_result or {}).get("candidates", []))
            if self.state.selected_crossing_index is not None:
                self.window.crossing_table.select_row(self.state.selected_crossing_index)
        if self.state.camera_state:
            self.window.pyvista_view.restore_camera_state(self.state.camera_state)
        if self.state.ui_state:
            self.window.restore_ui_state(self.state.ui_state)
        self.recent_files.add_recent_file("session", self.state.session_path or Path(path))
        self.window.log_console.append_log(f"Loaded session {path}.")
        return self.state

    def new_session(self) -> None:
        """Reset the current workbench state."""

        self._copy_state(SessionState())
        self.window.reset_for_new_session()
        self.window.log_console.append_log("Started a new session.")

    def _copy_state(self, other: SessionState) -> None:
        self.state.pd_text = other.pd_text
        self.state.pd_code = other.pd_code
        self.state.normalized_pd = other.normalized_pd
        self.state.validation_result = other.validation_result
        self.state.analysis_result = other.analysis_result
        self.state.unknotting_result = other.unknotting_result
        self.state.crossing_changes_result = other.crossing_changes_result
        self.state.selected_crossing_index = other.selected_crossing_index
        self.state.output_dir = other.output_dir
        self.state.session_path = other.session_path
        self.state.analysis_result_path = other.analysis_result_path
        self.state.unknotting_result_path = other.unknotting_result_path
        self.state.crossing_changes_result_path = other.crossing_changes_result_path
        self.state.selected_example = other.selected_example
        self.state.camera_state = other.camera_state
        self.state.ui_state = other.ui_state
        self.state.export_history = other.export_history
        self.state.dirty = other.dirty
