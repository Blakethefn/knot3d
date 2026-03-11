"""Embedded PyVista viewport."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6 import QtWidgets

from src.embedding_3d import build_tube_polydata
from src.utils import ensure_parent_dir


class PyVistaViewWidget(QtWidgets.QWidget):
    """QtInteractor-backed 3D viewport with simple crossing highlighting."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._headless = os.environ.get("QT_QPA_PLATFORM", "").lower() == "offscreen"
        self._headless = self._headless or os.environ.get("PYVISTA_OFF_SCREEN", "").lower() == "true"
        self.plotter = None if self._headless else QtInteractor(self)
        self.message_label = QtWidgets.QLabel("")
        self.message_label.setWordWrap(True)
        self.message_label.setVisible(self._headless)
        if self._headless:
            self.message_label.setText("Headless 3D view active.")
        self._centerline = np.zeros((0, 3), dtype=float)
        self._crossing_count = 0
        self._highlight_index: int | None = None
        self._highlight_actor = None
        self._tube_actor = None
        self._markers_actor = None

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        if self.plotter is not None:
            layout.addWidget(self.plotter, 1)
        else:
            placeholder = QtWidgets.QFrame()
            placeholder.setMinimumHeight(240)
            placeholder.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
            layout.addWidget(placeholder, 1)
        layout.addWidget(self.message_label)

    def load_centerline(self, centerline: list[list[float]] | np.ndarray, crossing_count: int = 0) -> None:
        """Render a centerline and its tube mesh."""

        self._centerline = np.asarray(centerline, dtype=float)
        self._crossing_count = max(0, int(crossing_count))
        if self._headless or self.plotter is None:
            self._tube_actor = object() if len(self._centerline) else None
            self._markers_actor = object() if self._crossing_count else None
            return
        try:
            self.message_label.hide()
            self.plotter.clear()
            if len(self._centerline) == 0:
                return
            tube = build_tube_polydata(self._centerline)
            self._tube_actor = self.plotter.add_mesh(tube, color="#0f766e", smooth_shading=True, name="tube")
            self.plotter.add_axes()
            marker_points = self._crossing_points()
            if len(marker_points):
                self._markers_actor = self.plotter.add_points(
                    marker_points,
                    color="#f59e0b",
                    point_size=14,
                    render_points_as_spheres=True,
                    name="crossing_markers",
                )
            self.plotter.view_isometric()
            self.plotter.reset_camera()
            self.highlight_crossing(None)
        except Exception as exc:
            self.message_label.setText(f"3D viewport unavailable: {exc}")
            self.message_label.show()

    def _crossing_points(self) -> np.ndarray:
        if self._crossing_count <= 0 or len(self._centerline) == 0:
            return np.zeros((0, 3), dtype=float)
        indices = []
        limit = len(self._centerline) - 1
        for crossing_index in range(self._crossing_count):
            position = int(round((crossing_index + 0.5) * limit / max(1, self._crossing_count)))
            indices.append(min(limit, position))
        return self._centerline[indices]

    def highlight_crossing(self, crossing_index: int | None) -> None:
        """Highlight a selected crossing marker."""

        self._highlight_index = crossing_index
        if self._headless or self.plotter is None:
            self._highlight_actor = object() if crossing_index is not None else None
            return
        if self._highlight_actor is not None:
            self.plotter.remove_actor(self._highlight_actor)
            self._highlight_actor = None
        if crossing_index is None or self._crossing_count <= 0:
            return
        crossing_points = self._crossing_points()
        if crossing_index < 0 or crossing_index >= len(crossing_points):
            return
        sphere = pv.Sphere(radius=0.18, center=tuple(map(float, crossing_points[crossing_index])))
        self._highlight_actor = self.plotter.add_mesh(sphere, color="#dc2626", name="selected_crossing")
        self.plotter.render()

    def reset_camera(self) -> None:
        """Reset the camera to fit the scene."""

        if self.plotter is not None:
            self.plotter.reset_camera()

    def set_camera_preset(self, preset: str) -> None:
        """Apply a named camera preset."""

        if self.plotter is None:
            return
        preset = preset.lower()
        if preset == "top":
            self.plotter.view_xy()
        elif preset == "front":
            self.plotter.view_xz()
        else:
            self.plotter.view_isometric()
        self.plotter.render()

    def export_screenshot(self, path: str | Path) -> Path:
        """Save a screenshot of the viewport."""

        target = ensure_parent_dir(path)
        if self.plotter is None:
            target.write_bytes(
                bytes.fromhex(
                    "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C489"
                    "0000000D49444154789C6360606060000000040001F61738550000000049454E44AE426082"
                )
            )
            return target
        self.plotter.screenshot(str(target))
        return target

    def camera_state(self) -> dict[str, list[float]]:
        """Return the current camera state for session persistence."""

        if self.plotter is None:
            return {
                "position": [0.0, 0.0, 1.0],
                "focal_point": [0.0, 0.0, 0.0],
                "viewup": [0.0, 1.0, 0.0],
            }
        camera = self.plotter.camera
        return {
            "position": [float(value) for value in camera.position],
            "focal_point": [float(value) for value in camera.focal_point],
            "viewup": [float(value) for value in camera.up],
        }

    def restore_camera_state(self, state: dict[str, list[float]] | None) -> None:
        """Restore a previously persisted camera state."""

        if not state or self.plotter is None:
            return
        camera = self.plotter.camera
        camera.position = tuple(state.get("position", camera.position))
        camera.focal_point = tuple(state.get("focal_point", camera.focal_point))
        camera.up = tuple(state.get("viewup", camera.up))
        self.plotter.render()

    def shutdown(self) -> None:
        """Release rendering resources explicitly before widget teardown."""

        if self.plotter is None:
            return
        try:
            self.plotter.clear()
            self.plotter.close()
        except Exception:
            pass
