"""Mesh and centerline export helpers."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import trimesh

from src.embedding_3d import build_embedding
from src.utils import ensure_parent_dir


def export_centerline_csv(centerline: np.ndarray, path: str | Path) -> Path:
    """Export centerline coordinates as CSV with x,y,z columns."""

    target = ensure_parent_dir(path)
    header = "x,y,z"
    np.savetxt(target, centerline, delimiter=",", header=header, comments="")
    return target


def export_meshes(pd_code: list[list[int]], output_prefix: str | Path, formats: tuple[str, ...] = ("obj", "stl", "glb")) -> dict[str, str]:
    """Export tube meshes and centerline CSV for a PD code."""

    prefix = Path(output_prefix)
    embedding = build_embedding(pd_code)
    mesh: trimesh.Trimesh = embedding.tube_mesh
    outputs: dict[str, str] = {}
    for fmt in formats:
        target = ensure_parent_dir(prefix.with_suffix(f".{fmt}"))
        mesh.export(target)
        outputs[fmt] = str(target)
    csv_path = export_centerline_csv(embedding.centerline, prefix.with_name(prefix.name + "_centerline.csv"))
    outputs["csv"] = str(csv_path)
    return outputs
