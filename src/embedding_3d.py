"""3D centerline and tube-mesh helpers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pyvista as pv
import trimesh

from src.config import VizConfig


@dataclass(frozen=True)
class Embedding3D:
    """Centerline and derived tube mesh."""

    centerline: np.ndarray
    tube_mesh: trimesh.Trimesh


def compute_centerline(pd_code: list[list[int]], config: VizConfig | None = None) -> np.ndarray:
    """Generate a deterministic closed 3D centerline for preview and export."""

    settings = config or VizConfig()
    if not pd_code:
        theta = np.linspace(0.0, 2.0 * np.pi, settings.centerline_base_samples, endpoint=True)
        points = np.column_stack((np.cos(theta), np.sin(theta), np.zeros_like(theta)))
        points[-1] = points[0]
        return points.astype(np.float64)

    crossings = len(pd_code)
    samples = max(settings.centerline_base_samples, crossings * settings.centerline_samples_per_crossing)
    theta = np.linspace(0.0, 2.0 * np.pi, samples, endpoint=True)
    p = max(2, crossings)
    q = p + 1
    r = p + 2
    radial = 2.0 + 0.35 * np.cos(q * theta)
    x = radial * np.cos(p * theta)
    y = radial * np.sin(p * theta)
    z = 0.45 * np.sin(r * theta)
    points = np.column_stack((x, y, z)).astype(np.float64)
    points[-1] = points[0]
    return points


def build_tube_polydata(centerline: np.ndarray, config: VizConfig | None = None) -> pv.PolyData:
    """Create a PyVista tube surface from a centerline."""

    settings = config or VizConfig()
    line = pv.lines_from_points(centerline, close=True)
    return line.tube(radius=settings.tube_radius, n_sides=settings.tube_sides, capping=True)


def polydata_to_trimesh(polydata: pv.PolyData) -> trimesh.Trimesh:
    """Convert triangulated PyVista polydata into a Trimesh mesh."""

    triangulated = polydata.triangulate()
    faces = triangulated.faces.reshape(-1, 4)[:, 1:4]
    mesh = trimesh.Trimesh(vertices=triangulated.points, faces=faces, process=True)
    return mesh


def build_embedding(pd_code: list[list[int]], config: VizConfig | None = None) -> Embedding3D:
    """Build both the centerline and a watertight tube mesh."""

    centerline = compute_centerline(pd_code, config)
    tube = build_tube_polydata(centerline, config)
    mesh = polydata_to_trimesh(tube)
    return Embedding3D(centerline=centerline, tube_mesh=mesh)
