"""Controller for crossing-candidate inspection and view synchronization."""

from __future__ import annotations

from PySide6 import QtCore

from src.gui.state import SessionState
from src.services.engine_facade import EngineFacade


class CrossingController(QtCore.QObject):
    """Synchronize crossing-table selection with the detail and view panes."""

    def __init__(self, window, state: SessionState, engine: EngineFacade, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self.window = window
        self.state = state
        self.engine = engine

    def select_candidate(self, candidate: dict) -> None:
        """Update views for the selected candidate."""

        crossing_indices = candidate.get("crossing_indices") or []
        selected_crossing = int(crossing_indices[0]) if crossing_indices else None
        self.state.selected_crossing_index = selected_crossing
        self.state.mark_dirty()
        self.window.crossing_detail.set_candidate(candidate)
        self.window.status_widget.set_selected_crossing(selected_crossing)
        self.window.diagram_canvas.highlight_crossing(selected_crossing)
        self.window.pyvista_view.highlight_crossing(selected_crossing)

        original_pd = self.state.normalized_pd or self.state.pd_code
        modified_pd = candidate.get("modified_pd")
        if modified_pd is None and selected_crossing is not None:
            preview = self.engine.build_crossing_candidate_preview(original_pd, selected_crossing)
            modified_pd = preview.get("modified_pd", [])
        self.window.comparison_view.set_comparison(original_pd, modified_pd or [], candidate)
