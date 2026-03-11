"""Top-level controller that wires the workbench together."""

from __future__ import annotations

from pathlib import Path

from PySide6 import QtWidgets

from src.gui import settings as gui_settings
from src.gui.controllers.analysis_controller import AnalysisController
from src.gui.controllers.crossing_controller import CrossingController
from src.gui.controllers.export_controller import ExportController
from src.gui.controllers.session_controller import SessionController
from src.gui.dialogs import AboutDialog, PreferencesDialog, SessionInfoDialog
from src.gui.state import SessionState
from src.services import EngineFacade, ExportService, RecentFilesStore, SessionStore


class AppController:
    """Own the subcontrollers and bind UI actions."""

    def __init__(
        self,
        window,
        settings,
        *,
        state: SessionState | None = None,
        engine: EngineFacade | None = None,
        export_service: ExportService | None = None,
        session_store: SessionStore | None = None,
        recent_files: RecentFilesStore | None = None,
        use_threads: bool = True,
    ) -> None:
        self.window = window
        self.settings = settings
        self.state = state or SessionState(output_dir=Path(str(settings.value("preferences/default_output_dir", "out"))))
        self.window.session_state = self.state

        self.engine = engine or EngineFacade()
        self.export_service = export_service or ExportService()
        self.session_store = session_store or SessionStore()
        self.recent_files = recent_files or RecentFilesStore()
        self._apply_compute_preferences(log_to_ui=False)

        self.analysis = AnalysisController(window, self.state, self.engine, settings, use_threads=use_threads)
        self.crossings = CrossingController(window, self.state, self.engine)
        self.exports = ExportController(window, self.state, self.export_service)
        self.sessions = SessionController(window, self.state, self.session_store, self.recent_files, settings)
        self.sessions.bind_auto_validate(self.analysis.validate_current_text)
        self.window.on_save_before_close = self.sessions.save_session

        self._bind_ui()

    def _bind_ui(self) -> None:
        self.window.example_picker.example_loaded.connect(self.sessions.load_example)
        self.window.pd_editor.content_changed.connect(self.sessions.on_editor_changed)
        self.window.run_panel.validate_requested.connect(self.analysis.validate_current_text)
        self.window.run_panel.analyze_requested.connect(self.analysis.run_analysis)
        self.window.run_panel.unknot_requested.connect(self.analysis.run_unknotting_search)
        self.window.run_panel.mesh_requested.connect(self.analysis.run_mesh_export)
        self.window.progress_panel.cancel_requested.connect(self.analysis.cancel_active_job)
        self.window.crossing_table.candidate_selected.connect(self.crossings.select_candidate)

        self.window.action_validate.triggered.connect(lambda checked=False: self.analysis.validate_current_text())
        self.window.action_analyze.triggered.connect(lambda checked=False: self.analysis.run_analysis())
        self.window.action_unknot.triggered.connect(lambda checked=False: self.analysis.run_unknotting_search())
        self.window.action_export_mesh.triggered.connect(lambda checked=False: self.analysis.run_mesh_export())
        self.window.action_cancel.triggered.connect(lambda checked=False: self.analysis.cancel_active_job())
        self.window.action_new_session.triggered.connect(lambda checked=False: self.sessions.new_session())
        self.window.action_save_session.triggered.connect(lambda checked=False: self.sessions.save_session())
        self.window.action_session_info.triggered.connect(lambda checked=False: self.show_session_info())
        self.window.action_preferences.triggered.connect(lambda checked=False: self.show_preferences())
        self.window.action_about.triggered.connect(lambda checked=False: self.show_about())

        self.window.action_export_results.triggered.connect(lambda checked=False: self._export_results_dialog())
        self.window.action_export_screenshot.triggered.connect(lambda checked=False: self._export_screenshot_dialog())
        self.window.action_export_diagram.triggered.connect(lambda checked=False: self._export_diagram_dialog())
        self.window.export_results_button.clicked.connect(lambda checked=False: self._export_results_dialog())
        self.window.export_screenshot_button.clicked.connect(lambda checked=False: self._export_screenshot_dialog())
        self.window.export_session_button.clicked.connect(lambda checked=False: self.sessions.save_session())

        self.window.action_reset_layout.triggered.connect(lambda checked=False: self.window.reset_layout())
        self.window.action_reset_camera.triggered.connect(lambda checked=False: self.window.pyvista_view.reset_camera())
        self.window.action_camera_top.triggered.connect(lambda checked=False: self.window.pyvista_view.set_camera_preset("top"))
        self.window.action_camera_front.triggered.connect(lambda checked=False: self.window.pyvista_view.set_camera_preset("front"))
        self.window.action_camera_iso.triggered.connect(lambda checked=False: self.window.pyvista_view.set_camera_preset("isometric"))
        self.window.action_open_session.triggered.connect(lambda checked=False: self._open_session_dialog())
        self.window.action_open_pd.triggered.connect(lambda checked=False: self._open_pd_dialog())

        for name, action in self.window.example_actions.items():
            action.triggered.connect(lambda checked=False, example=name: self.window.example_picker.select_example(example))

    def show_about(self) -> None:
        """Open the About dialog."""

        dialog = AboutDialog(self.engine.get_engine_versions(), self.window)
        dialog.exec()

    def show_preferences(self) -> None:
        """Open the Preferences dialog."""

        dialog = PreferencesDialog(self.settings, self.window)
        if dialog.exec():
            self.state.output_dir = Path(str(self.settings.value(gui_settings.KEY_DEFAULT_OUTPUT_DIR, "out")))
            self._apply_compute_preferences(log_to_ui=True)

    def show_session_info(self) -> None:
        """Open the session info dialog."""

        SessionInfoDialog(self.state, self.window).exec()

    def _export_results_dialog(self) -> None:
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.window,
            "Export Result Bundle",
            str(Path("out") / (self.state.selected_example or "workbench")),
            "All Files (*)",
        )
        if filename:
            self.exports.export_results_bundle(filename)

    def _export_screenshot_dialog(self) -> None:
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.window,
            "Export Screenshot",
            str(Path("out") / "viewport.png"),
            "PNG Files (*.png)",
        )
        if filename:
            self.exports.export_screenshot(filename)

    def _export_diagram_dialog(self) -> None:
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.window,
            "Export Diagram",
            str(Path("out") / "diagram.png"),
            "PNG Files (*.png)",
        )
        if filename:
            self.exports.export_diagram(filename)

    def _open_session_dialog(self) -> None:
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.window,
            "Open Session",
            str(Path("out")),
            "JSON Files (*.json)",
        )
        if filename:
            self.sessions.load_session(filename)

    def _open_pd_dialog(self) -> None:
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.window,
            "Open PD File",
            str(Path(".")),
            "PD Files (*.json *.txt);;All Files (*)",
        )
        if filename:
            self.sessions.load_pd_file(filename)

    def _apply_compute_preferences(self, *, log_to_ui: bool) -> None:
        """Apply persisted compute preferences to the active engine."""

        runtime: dict[str, object] | None = None
        if hasattr(self.engine, "update_compute_preferences"):
            runtime = self.engine.update_compute_preferences(gui_settings.load_compute_preferences(self.settings))
        elif hasattr(self.engine, "get_compute_runtime"):
            runtime = self.engine.get_compute_runtime()

        self.window.status_widget.set_compute_runtime(runtime)
        if log_to_ui and runtime is not None:
            summary = self.window.status_widget.compute_label.text().replace("Compute: ", "", 1)
            self.window.log_console.append_log(f"Compute preferences updated: {summary}.")
