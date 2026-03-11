"""Matplotlib rendering helpers."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from matplotlib.figure import Figure

from src.layout_2d import build_crossing_graph
from src.utils import ensure_parent_dir


def render_diagram(pd_code: list[list[int]], path: str | Path) -> Path:
    """Render a simple graph-based 2D diagram preview."""

    target = ensure_parent_dir(path)
    figure = Figure(figsize=(6, 6), dpi=180)
    axis = figure.add_subplot(111)
    axis.set_axis_off()

    if not pd_code:
        theta = np.linspace(0.0, 2.0 * np.pi, 240)
        axis.plot(np.cos(theta), np.sin(theta), color="#0f4c5c", linewidth=2.5)
        axis.text(0.0, 0.0, "unknot", ha="center", va="center")
        figure.tight_layout()
        figure.savefig(target, bbox_inches="tight")
        return target

    layout = build_crossing_graph(pd_code)
    xs = [layout.positions[node][0] for node in layout.graph.nodes]
    ys = [layout.positions[node][1] for node in layout.graph.nodes]
    axis.scatter(xs, ys, s=180, color="#0f4c5c")

    for node in layout.graph.nodes:
        x, y = layout.positions[node]
        axis.text(x, y, str(node), color="white", ha="center", va="center", fontsize=9)
        axis.text(x, y - 0.12, str(pd_code[node]), color="#102a43", ha="center", va="top", fontsize=7)

    for edge in layout.graph.edges:
        a, b = edge
        xa, ya = layout.positions[a]
        xb, yb = layout.positions[b]
        axis.plot([xa, xb], [ya, yb], color="#486581", linewidth=1.4, alpha=0.8)
        mx, my = (xa + xb) / 2.0, (ya + yb) / 2.0
        label = layout.edge_labels.get((a, b), layout.edge_labels.get((b, a), ""))
        axis.text(mx, my, label, fontsize=7, color="#7c2d12")

    figure.tight_layout()
    figure.savefig(target, bbox_inches="tight")
    return target
