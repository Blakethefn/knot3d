"""Matplotlib rendering helpers for routed knot diagrams."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from matplotlib.figure import Figure

from src.layout_2d import build_diagram_layout, sample_crossing_pass
from src.utils import ensure_parent_dir

_DIAGRAM_COLOR = "#0f766e"
_OUTLINE_COLOR = "#0b1620"
_UNDER_COLOR = "#5f6c7b"
_HIGHLIGHT_COLOR = "#c2410c"
_LABEL_COLOR = "#102a43"


def _plot_polyline(axis, points: np.ndarray, *, color: str, outline: str = _OUTLINE_COLOR, linewidth: float = 3.2, zorder: int = 2) -> None:
    axis.plot(points[:, 0], points[:, 1], color=outline, linewidth=linewidth + 2.2, solid_capstyle="round", zorder=zorder)
    axis.plot(points[:, 0], points[:, 1], color=color, linewidth=linewidth, solid_capstyle="round", zorder=zorder + 1)


def draw_diagram_axis(
    axis,
    pd_code: list[list[int]],
    selected_crossing_index: int | None = None,
    title: str | None = None,
) -> None:
    """Draw a routed knot diagram onto a Matplotlib axis."""

    axis.clear()
    axis.set_axis_off()
    axis.set_aspect("equal", adjustable="box")
    if title:
        axis.set_title(title)

    if not pd_code:
        theta = np.linspace(0.0, 2.0 * np.pi, 240, endpoint=True)
        axis.plot(np.cos(theta), np.sin(theta), color=_DIAGRAM_COLOR, linewidth=3.0)
        axis.text(0.0, 0.0, "unknot", ha="center", va="center", color=_LABEL_COLOR)
        axis.set_xlim(-1.4, 1.4)
        axis.set_ylim(-1.4, 1.4)
        return

    layout = build_diagram_layout(pd_code)
    xmin, xmax, ymin, ymax = layout.bounds
    axis.set_xlim(xmin, xmax)
    axis.set_ylim(ymin, ymax)

    for segment in layout.strand_segments:
        _plot_polyline(axis, segment.points, color=_DIAGRAM_COLOR, linewidth=3.1, zorder=2)

    under_passes = [traversal for traversal in layout.passes if not traversal.over]
    over_passes = [traversal for traversal in layout.passes if traversal.over]
    for group, color, zorder in (
        (under_passes, _UNDER_COLOR, 4),
        (over_passes, _DIAGRAM_COLOR, 7),
    ):
        for traversal in group:
            crossing = layout.crossings[traversal.crossing_index]
            pass_color = _HIGHLIGHT_COLOR if traversal.crossing_index == selected_crossing_index else color
            for stroke in sample_crossing_pass(crossing, traversal):
                _plot_polyline(axis, stroke, color=pass_color, linewidth=3.3, zorder=zorder)

    for crossing in layout.crossings:
        highlight = crossing.index == selected_crossing_index
        radius = 0.22 if highlight else 0.16
        facecolor = "#fff7ed" if highlight else "#f8fafc"
        edgecolor = _HIGHLIGHT_COLOR if highlight else _OUTLINE_COLOR
        axis.add_patch(plt_circle(crossing.center, radius, facecolor=facecolor, edgecolor=edgecolor, linewidth=2.0, zorder=10))
        label_dx, label_dy = crossing.slot_vectors[1] * 0.38
        axis.text(
            crossing.center[0] + label_dx,
            crossing.center[1] + label_dy,
            str(crossing.index),
            fontsize=8,
            fontweight="bold" if highlight else "normal",
            ha="center",
            va="center",
            color=edgecolor,
            zorder=11,
        )


def plt_circle(center: np.ndarray, radius: float, **kwargs):
    """Create a lazily imported Matplotlib circle patch."""

    from matplotlib.patches import Circle

    return Circle(tuple(map(float, center)), radius, **kwargs)


def render_diagram(pd_code: list[list[int]], path: str | Path) -> Path:
    """Render a routed 2D diagram preview."""

    target = ensure_parent_dir(path)
    figure = Figure(figsize=(6.4, 6.2), dpi=180)
    axis = figure.add_subplot(111)
    draw_diagram_axis(axis, pd_code, title="Knot Diagram")
    figure.tight_layout()
    figure.savefig(target, bbox_inches="tight", facecolor="#f8fbff")
    return target
