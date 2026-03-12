"""Controller for validation and background engine runs."""

from __future__ import annotations

import traceback
from pathlib import Path

from PySide6 import QtCore

from src.gui.state import RunRequest, SessionState
from src.gui.workers import AnalysisWorker, MeshWorker, UnknottingWorker
from src.services.engine_facade import EngineFacade, ValidationResult


class AnalysisController(QtCore.QObject):
    """Coordinate validation, analysis, unknotting, and mesh export runs."""

    validation_updated = QtCore.Signal(object)
    result_ready = QtCore.Signal(str, object)
    busy_changed = QtCore.Signal(bool)
    progress_updated = QtCore.Signal(str, int)
    error_occurred = QtCore.Signal(str)

    def __init__(
        self,
        window,
        state: SessionState,
        engine: EngineFacade,
        settings: QtCore.QSettings,
        *,
        use_threads: bool = True,
        parent: QtCore.QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.window = window
        self.state = state
        self.engine = engine
        self.settings = settings
        self.use_threads = use_threads
        self._active_thread: QtCore.QThread | None = None
        self._active_worker: QtCore.QObject | None = None
        self._active_mode: str | None = None

    @property
    def is_busy(self) -> bool:
        """Return whether a background job is active."""

        return self._active_thread is not None

    def validate_current_text(self, text: str | None = None) -> bool:
        """Validate the current PD editor text and update session state."""

        raw_text = text if text is not None else self.window.pd_editor.text()
        self.state.pd_text = raw_text
        try:
            result: ValidationResult = self.engine.validate_pd(raw_text)
        except Exception as exc:
            message = str(exc)
            self.state.validation_result = {"valid": False, "message": message}
            self.window.pd_editor.set_validation_message(message, is_error=True)
            self.window.run_panel.set_validation_message(message, is_error=True)
            self.window.status_widget.set_engine_state("validation error")
            self.error_occurred.emit(message)
            return False

        self.state.pd_code = result.pd_code
        self.state.normalized_pd = result.normalized_pd
        self.state.validation_result = result.to_dict()
        self.window.pd_editor.set_validation_message(result.message)
        self.window.run_panel.set_validation_message(result.message)
        self.window.status_widget.set_engine_state("validated")
        self.validation_updated.emit(result.to_dict())
        return True

    def run_analysis(self) -> None:
        """Kick off the shared analysis pipeline."""

        self._start_run("analyze")

    def run_unknotting_search(self) -> None:
        """Kick off the shared unknotting search."""

        self._start_run("unknotting_search")

    def run_mesh_export(self) -> None:
        """Kick off mesh export in a worker thread."""

        self._start_run("export_mesh")

    def cancel_active_job(self) -> None:
        """Request cooperative cancellation from the active worker."""

        worker = self._active_worker
        if worker is not None and hasattr(worker, "cancel"):
            worker.cancel()
            self.window.log_console.append_log("Cancellation requested.")
            self.window.progress_panel.set_progress("Cancelling...", self.window.progress_panel.progress_bar.value())

    def _start_run(self, mode: str) -> None:
        if self.is_busy:
            return
        if not self.validate_current_text():
            return

        output_prefix = self._output_prefix()
        request = RunRequest(mode=mode, pd_code=self.state.pd_code, output_prefix=str(output_prefix))
        if mode == "unknotting_search":
            worker = UnknottingWorker(self.engine, request)
            label = "Check Unknot"
        elif mode == "export_mesh":
            worker = MeshWorker(self.engine, request)
            label = "Export Mesh"
        else:
            worker = AnalysisWorker(self.engine, request)
            label = "Analyze"
        self.window.progress_panel.start_job(label, self._planned_stages(mode))
        if not self.use_threads:
            self._run_sync(mode, request, label)
            return
        self._launch_worker(worker, mode, label)

    def _output_prefix(self) -> Path:
        output_dir = self.state.output_dir or Path(str(self.settings.value("preferences/default_output_dir", "out")))
        base_name = self.state.selected_example or "workbench"
        return Path(output_dir) / base_name

    def _launch_worker(self, worker: QtCore.QObject, mode: str, label: str) -> None:
        thread = QtCore.QThread(self)
        self._active_thread = thread
        self._active_worker = worker
        self._active_mode = mode
        worker.moveToThread(thread)

        worker.signals.started.connect(lambda _: self._set_busy(True, label))
        worker.signals.progress.connect(self._on_progress)
        worker.signals.result.connect(self._on_result)
        worker.signals.error.connect(self._on_error)
        worker.signals.cancelled.connect(self._on_cancelled)
        worker.signals.finished.connect(self._on_finished)
        worker.signals.finished.connect(thread.quit)
        worker.signals.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.started.connect(worker.run)
        thread.start()

    def _run_sync(self, mode: str, request: RunRequest, label: str) -> None:
        self._active_mode = mode
        self._set_busy(True, label)
        try:
            if mode == "unknotting_search":
                result = self.engine.run_unknotting_search(request.pd_code, request.output_prefix, self._on_progress)
            elif mode == "export_mesh":
                result = self.engine.export_mesh(request.pd_code, request.output_prefix, self._on_progress)
            else:
                result = self.engine.analyze(request.pd_code, request.output_prefix, self._on_progress)
            self._on_result(mode, result)
        except Exception:
            self._on_error(mode, traceback.format_exc())
        finally:
            self._on_finished(mode)

    def _set_busy(self, busy: bool, job_name: str = "") -> None:
        self.window.set_busy(busy, job_name)
        self.busy_changed.emit(busy)

    def _on_progress(self, message: str, percent: int) -> None:
        self.window.progress_panel.set_progress(message, percent)
        self.window.status_widget.set_progress(message)
        self.window.log_console.append_log(message)
        self.progress_updated.emit(message, percent)

    def _on_result(self, mode: str, result: dict) -> None:
        if mode == "export_mesh":
            self.state.export_history.append({"kind": "mesh", "paths": result.get("mesh_outputs", {})})
            self.window.log_console.append_log("Mesh export completed.")
            self.window.progress_panel.mark_finished("Mesh export completed")
            self.result_ready.emit(mode, result)
            return

        self.state.analysis_result = result.get("analysis")
        self.state.unknotting_result = result.get("unknotting")
        self.state.crossing_changes_result = result.get("crossing_changes")
        self.state.analysis_result_path = Path(result["output_files"]["analysis_json"])
        if result["output_files"].get("unknotting_json"):
            self.state.unknotting_result_path = Path(result["output_files"]["unknotting_json"])
        if result["output_files"].get("crossing_changes_json"):
            self.state.crossing_changes_result_path = Path(result["output_files"]["crossing_changes_json"])
        self._apply_result_to_views(result)
        self.state.mark_dirty()
        self.result_ready.emit(mode, result)

    def _apply_result_to_views(self, result: dict) -> None:
        analysis = result.get("analysis")
        unknotting = result.get("unknotting")
        crossing_changes = result.get("crossing_changes") or {}
        normalized_pd = result.get("normalized_pd", self.state.normalized_pd)
        self.state.selected_crossing_index = None

        self.window.invariant_panel.set_payload(analysis)
        self.window.analysis_summary.set_results(analysis, unknotting)
        self.window.diagram_canvas.set_diagram(normalized_pd, self.state.selected_crossing_index)
        if bool(self.settings.value("preferences/auto_load_scene", True, bool)):
            self.window.pyvista_view.load_centerline(
                result.get("centerline", []),
                result.get("crossing_positions", []),
                result.get("strand_segments", []),
                result.get("tangents", []),
                result.get("normals", []),
                crossing_count=len(normalized_pd),
            )
        self.window.set_raw_json_payloads(
            {
                "analysis": analysis,
                "unknotting": unknotting,
                "crossing_changes": crossing_changes,
            }
        )
        self.window.crossing_table.set_candidates(crossing_changes.get("candidates", []))
        self.window.crossing_detail.set_candidate(None)
        self.window.comparison_view.clear_view()
        self.window.status_widget.set_selected_crossing(None)
        self.window.status_widget.set_engine_state("ready")
        self.window.status_widget.set_progress("Ready")
        self.window.log_console.append_log("Run completed successfully.")
        self.window.progress_panel.mark_finished("Completed")

    def _on_error(self, mode: str, error_text: str) -> None:
        self.window.log_console.append_log(f"{mode} failed:\n{error_text}")
        self.window.status_widget.set_engine_state("error")
        self.window.status_widget.set_progress("Error")
        self.window.progress_panel.mark_failed("Failed")
        self.error_occurred.emit(error_text)

    def _on_cancelled(self, mode: str) -> None:
        self.window.log_console.append_log(f"{mode} cancelled.")
        self.window.status_widget.set_engine_state("cancelled")
        self.window.status_widget.set_progress("Cancelled")
        self.window.progress_panel.mark_cancelled("Cancelled")

    def _on_finished(self, mode: str) -> None:
        self._set_busy(False)
        self._active_thread = None
        self._active_worker = None
        self._active_mode = None

    def _planned_stages(self, mode: str) -> list[str]:
        stages = [
            "Parsing PD code",
            "Building topology objects",
            "Computing classical invariants",
        ]
        compute_hfk = True
        engine_config = getattr(self.engine, "config", None)
        if engine_config is not None:
            compute_hfk = bool(getattr(getattr(engine_config, "invariants", None), "compute_hfk", True))
        if compute_hfk:
            stages.append("Computing knot Floer homology")
        if mode == "unknotting_search":
            stages.append("Checking unknot status")
        stages.extend(
            [
                "Rendering diagram",
                "Building 3D embedding",
            ]
        )
        if mode == "export_mesh":
            stages.append("Exporting mesh bundle")
        stages.append("Completed")
        return stages
