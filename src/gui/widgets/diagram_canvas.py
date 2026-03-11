"""Embedded Matplotlib diagram canvas."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from PySide6 import QtWidgets

from src.layout_2d import build_crossing_graph
from src.utils import ensure_parent_dir


def draw_pd_diagram(
    axis,
    pd_code: list[list[int]],
    selected_crossing_index: int | None = None,
    title: str | None = None,
) -> None:
    """Draw a simple PD graph with optional crossing highlight."""

    axis.clear()
    axis.set_axis_off()
    if title:
        axis.set_title(title)

    if not pd_code:
        theta = np.linspace(0.0, 2.0 * np.pi, 240)
        axis.plot(np.cos(theta), np.sin(theta), color="#155e75", linewidth=2.4)
        axis.text(0.0, 0.0, "unknot", ha="center", va="center")
        return

    layout = build_crossing_graph(pd_code)
    for node in layout.graph.nodes:
        x, y = layout.positions[node]
        color = "#b42318" if node == selected_crossing_index else "#155e75"
        axis.scatter([x], [y], s=220, color=color, zorder=3)
        axis.text(x, y, str(node), color="white", ha="center", va="center", fontsize=9, zorder=4)

    for (a, b) in layout.graph.edges:
        xa, ya = layout.positions[a]
        xb, yb = layout.positions[b]
        axis.plot([xa, xb], [ya, yb], color="#475467", linewidth=1.5, alpha=0.9, zorder=1)
        label = layout.edge_labels.get((a, b), layout.edge_labels.get((b, a), ""))
        axis.text((xa + xb) / 2.0, (ya + yb) / 2.0, label, fontsize=7, color="#9a3412", zorder=2)


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
