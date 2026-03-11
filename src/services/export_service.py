"""Centralized export helpers for GUI actions."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import numpy as np

from src.gui.state import SessionState
from src.mesh_export import export_centerline_csv, export_meshes
from src.services.engine_facade import build_output_paths
from src.services.session_store import SessionStore
from src.utils import ensure_parent_dir, write_json


class ExportService:
    """Coordinate filesystem exports for the desktop application."""

    def __init__(self, session_store: SessionStore | None = None) -> None:
        self.session_store = session_store or SessionStore()

    def base_name_outputs(self, base_path: str | Path) -> dict[str, str]:
        """Apply the blueprint suffix convention to a chosen base path."""

        return build_output_paths(base_path)

    def export_analysis_json(self, result: dict[str, Any], path: str | Path) -> Path:
        """Write an analysis result payload."""

        write_json(path, result)
        return Path(path)

    def export_unknotting_json(self, result: dict[str, Any], path: str | Path) -> Path:
        """Write an unknotting result payload."""

        write_json(path, result)
        return Path(path)

    def export_crossing_changes_json(self, result: dict[str, Any], path: str | Path) -> Path:
        """Write a crossing-change result payload."""

        write_json(path, result)
        return Path(path)

    def export_diagram_png(self, diagram_widget: Any, path: str | Path) -> Path:
        """Ask the diagram widget to save itself."""

        target = ensure_parent_dir(path)
        diagram_widget.save_png(target)
        return target

    def export_screenshot(self, viewport_widget: Any, path: str | Path) -> Path:
        """Ask the 3D viewport widget to save a screenshot."""

        target = ensure_parent_dir(path)
        viewport_widget.export_screenshot(target)
        return target

    def export_centerline(self, centerline: list[list[float]] | np.ndarray, path: str | Path) -> Path:
        """Write centerline coordinates as CSV."""

        return export_centerline_csv(np.asarray(centerline, dtype=float), path)

    def export_mesh_bundle(self, pd_code: list[list[int]], base_path: str | Path) -> dict[str, str]:
        """Write the canonical mesh bundle from a PD code."""

        return export_meshes(pd_code, base_path)

    def export_session(self, state: SessionState, path: str | Path) -> Path:
        """Persist a GUI session."""

        return self.session_store.save(state, path)

    def copy_if_exists(self, source: str | Path | None, target: str | Path) -> Path:
        """Copy an existing file when a direct export is not needed."""

        if source is None:
            raise ValueError("No source artifact is available for export.")
        source_path = Path(source)
        if not source_path.exists():
            raise FileNotFoundError(source_path)
        target_path = ensure_parent_dir(target)
        shutil.copy2(source_path, target_path)
        return target_path
