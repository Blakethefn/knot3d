"""PyVista rendering helpers."""

from __future__ import annotations

from pathlib import Path

import pyvista as pv

from src.config import VizConfig
from src.embedding_3d import build_tube_polydata
from src.utils import ensure_parent_dir


def render_3d_preview(centerline, path_prefix: str | Path, config: VizConfig | None = None) -> Path:
    """Render a 3D preview, preferring HTML and falling back to PNG."""

    settings = config or VizConfig()
    prefix = Path(path_prefix)
    target_html = ensure_parent_dir(prefix.with_name(prefix.name + "_3d.html"))
    tube = build_tube_polydata(centerline, settings)
    plotter = pv.Plotter(off_screen=settings.pyvista_off_screen)
    plotter.add_mesh(tube, color="#2f855a", smooth_shading=True)
    plotter.view_isometric()
    try:
        plotter.export_html(str(target_html))
        plotter.close()
        return target_html
    except Exception:
        target_png = ensure_parent_dir(prefix.with_name(prefix.name + "_3d.png"))
        plotter.screenshot(str(target_png))
        plotter.close()
        return target_png
