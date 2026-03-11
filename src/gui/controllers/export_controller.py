"""Controller for export actions and guard rails."""

from __future__ import annotations

from pathlib import Path

from PySide6 import QtWidgets

from src.gui.state import SessionState
from src.services.export_service import ExportService


class ExportController:
    """Centralize export action handling."""

    def __init__(self, window, state: SessionState, export_service: ExportService) -> None:
        self.window = window
        self.state = state
        self.export_service = export_service

    def export_analysis(self, path: str | Path) -> Path:
        """Export analysis JSON."""

        if not self.state.analysis_result:
            raise ValueError("No analysis result is available.")
        return self.export_service.export_analysis_json(self.state.analysis_result, path)

    def export_session(self, path: str | Path) -> Path:
        """Export the current GUI session."""

        return self.export_service.export_session(self.state, path)

    def export_results_bundle(self, base_path: str | Path) -> dict[str, str]:
        """Export all available result types using the blueprint suffix convention."""

        outputs = self.export_service.base_name_outputs(base_path)
        if self.state.analysis_result:
            self.export_analysis(outputs["analysis_json"])
        if self.state.unknotting_result:
            self.export_service.export_unknotting_json(self.state.unknotting_result, outputs["unknotting_json"])
        if self.state.crossing_changes_result:
            self.export_service.export_crossing_changes_json(
                self.state.crossing_changes_result,
                outputs["crossing_changes_json"],
            )
        if self.state.normalized_pd:
            self.export_service.export_centerline(
                self.window.pyvista_view._centerline,  # noqa: SLF001 - shared widget-owned data
                outputs["centerline_csv"],
            )
            self.export_service.export_diagram_png(self.window.diagram_canvas, outputs["diagram_png"])
            self.export_service.export_screenshot(self.window.pyvista_view, outputs["preview_3d"])
        return outputs

    def export_diagram(self, path: str | Path) -> Path:
        """Export the currently rendered diagram."""

        return self.export_service.export_diagram_png(self.window.diagram_canvas, path)

    def export_screenshot(self, path: str | Path) -> Path:
        """Export the current 3D screenshot."""

        return self.export_service.export_screenshot(self.window.pyvista_view, path)

    def export_centerline(self, path: str | Path) -> Path:
        """Export the current centerline."""

        return self.export_service.export_centerline(self.window.pyvista_view._centerline, path)  # noqa: SLF001
