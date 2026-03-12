"""Embedded Matplotlib diagram canvas."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from PySide6 import QtWidgets

from src.utils import ensure_parent_dir
from src.viz_matplotlib import draw_diagram_axis


def draw_pd_diagram(
    axis,
    pd_code: list[list[int]],
    selected_crossing_index: int | None = None,
    title: str | None = None,
) -> None:
    """Draw a routed PD diagram with optional crossing highlight."""

    draw_diagram_axis(axis, pd_code, selected_crossing_index=selected_crossing_index, title=title)


class DiagramCanvasWidget(QtWidgets.QWidget):
    """Matplotlib-backed diagram view."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.figure = plt.Figure(figsize=(6, 6), dpi=120)
        self.axis = self.figure.add_subplot(111)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self._pd_code: list[list[int]] = []
        self._selected_crossing: int | None = None

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas, 1)
        self.render()

    def set_diagram(self, pd_code: list[list[int]], selected_crossing_index: int | None = None) -> None:
        """Render a new diagram."""

        self._pd_code = [list(crossing) for crossing in pd_code]
        self._selected_crossing = selected_crossing_index
        self.render()

    def highlight_crossing(self, selected_crossing_index: int | None) -> None:
        """Update only the highlighted crossing."""

        self._selected_crossing = selected_crossing_index
        self.render()

    def render(self) -> None:
        """Draw the current diagram state."""

        draw_pd_diagram(self.axis, self._pd_code, self._selected_crossing, "2D Diagram")
        self.figure.tight_layout()
        self.canvas.draw_idle()

    def save_png(self, path: str | Path) -> Path:
        """Export the current figure to PNG."""

        target = ensure_parent_dir(path)
        self.figure.savefig(target, bbox_inches="tight")
        return target
