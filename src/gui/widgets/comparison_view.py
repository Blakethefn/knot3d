"""Side-by-side comparison view for recognition previews."""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from PySide6 import QtWidgets

from src.gui.widgets.diagram_canvas import draw_pd_diagram


class ComparisonViewWidget(QtWidgets.QWidget):
    """Compare original and selected diagrams side by side."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.figure = plt.Figure(figsize=(8, 4), dpi=120)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.meta_label = QtWidgets.QLabel("No record selected.")
        self.meta_label.setWordWrap(True)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.meta_label)
        layout.addWidget(self.canvas, 1)
        self.clear_view()

    def clear_view(self) -> None:
        """Reset the comparison view."""

        self.figure.clear()
        left = self.figure.add_subplot(121)
        right = self.figure.add_subplot(122)
        draw_pd_diagram(left, [], title="Original")
        draw_pd_diagram(right, [], title="Modified")
        self.canvas.draw_idle()

    def set_comparison(self, original_pd: list[list[int]], modified_pd: list[list[int]], candidate: dict | None) -> None:
        """Render the original and modified diagrams for a record."""

        self.figure.clear()
        left = self.figure.add_subplot(121)
        right = self.figure.add_subplot(122)
        selected = None
        if candidate and candidate.get("crossing_indices"):
            selected = int(candidate["crossing_indices"][0])
        draw_pd_diagram(left, original_pd, selected_crossing_index=selected, title="Original")
        draw_pd_diagram(right, modified_pd, title="Modified")
        if candidate:
            crossing_indices = candidate.get("crossing_indices") or []
            prefix = f"Candidate {candidate.get('candidate_index', '--')}" if crossing_indices else "Current diagram"
            self.meta_label.setText(
                f"{prefix} | "
                f"Crossings {crossing_indices} | "
                f"Status {candidate.get('full_check_status', '--')} | "
                f"Unknot {candidate.get('is_unknot', '--')}"
            )
        else:
            self.meta_label.setText("No record selected.")
        self.figure.tight_layout()
        self.canvas.draw_idle()
