"""Embedded PyVista viewport."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6 import QtWidgets

from src.config import VizConfig
from src.utils import ensure_parent_dir

_LIGHTING_PRESETS: dict[str, dict[str, Any]] = {
    "Studio": {
        "background": "#f8fbff",
        "top": "#dbe7f4",
        "ambient": 0.28,
        "diffuse": 0.7,
        "specular": 0.42,
        "specular_power": 22.0,
    },
    "Blueprint": {
        "background": "#edf6ff",
        "top": "#c9ddf7",
        "ambient": 0.24,
        "diffuse": 0.66,
        "specular": 0.55,
        "specular_power": 28.0,
    },
    "Darkroom": {
        "background": "#0f172a",
        "top": "#1d3557",
        "ambient": 0.22,
        "diffuse": 0.62,
        "specular": 0.62,
        "specular_power": 34.0,
    },
}


def _estimate_crossing_points(centerline: np.ndarray, crossing_count: int) -> np.ndarray:
    if crossing_count <= 0 or len(centerline) == 0:
        return np.zeros((0, 3), dtype=float)
    indices = []
    limit = max(1, len(centerline) - 1)
    for crossing_index in range(crossing_count):
        position = int(round((crossing_index + 0.5) * limit / max(1, crossing_count)))
        indices.append(min(limit, position))
    return centerline[indices]


def _curve_curvature(centerline: np.ndarray, tangents: np.ndarray | None = None) -> np.ndarray:
    if len(centerline) == 0:
        return np.zeros((0,), dtype=float)
    if tangents is None or len(tangents) != len(centerline):
        points = centerline[:-1] if len(centerline) > 1 else centerline
        if len(points) < 3:
            return np.zeros((len(centerline),), dtype=float)
        local_tangents = []
        for point_index in range(len(points)):
            previous_point = points[(point_index - 1) % len(points)]
            next_point = points[(point_index + 1) % len(points)]
            tangent = next_point - previous_point
            tangent = tangent / max(np.linalg.norm(tangent), 1e-9)
            local_tangents.append(tangent)
        tangents = np.vstack((np.asarray(local_tangents, dtype=float), local_tangents[0]))

    curvature = np.linalg.norm(np.roll(tangents, -1, axis=0) - np.roll(tangents, 1, axis=0), axis=1)
    if np.allclose(curvature, 0.0):
        return np.zeros_like(curvature)
    return curvature / max(float(curvature.max()), 1e-9)


class PyVistaViewWidget(QtWidgets.QWidget):
    """QtInteractor-backed 3D viewport with scene metadata and lighting presets."""

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

        self.lighting_combo = QtWidgets.QComboBox(self)
        for preset_name in _LIGHTING_PRESETS:
            self.lighting_combo.addItem(preset_name)
        self.lighting_combo.currentTextChanged.connect(self._on_lighting_changed)
        self.scene_label = QtWidgets.QLabel("No scene loaded.")
        self.scene_label.setObjectName("viewportMeta")

        self._centerline = np.zeros((0, 3), dtype=float)
        self._crossing_positions = np.zeros((0, 3), dtype=float)
        self._strand_segments: list[dict[str, Any]] = []
        self._tangents = np.zeros((0, 3), dtype=float)
        self._normals = np.zeros((0, 3), dtype=float)
        self._curvature = np.zeros((0,), dtype=float)
        self._highlight_index: int | None = None
        self._highlight_actor = None
        self._tube_actor = None
        self._markers_actor = None

        header = QtWidgets.QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.addWidget(QtWidgets.QLabel("Lighting"))
        header.addWidget(self.lighting_combo)
        header.addStretch(1)
        header.addWidget(self.scene_label)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(header)
        if self.plotter is not None:
            layout.addWidget(self.plotter, 1)
        else:
            placeholder = QtWidgets.QFrame()
            placeholder.setMinimumHeight(260)
            placeholder.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
            layout.addWidget(placeholder, 1)
        layout.addWidget(self.message_label)

    def load_centerline(
        self,
        centerline: list[list[float]] | np.ndarray,
        crossing_positions: list[list[float]] | np.ndarray | None = None,
        strand_segments: list[dict[str, Any]] | None = None,
        tangents: list[list[float]] | np.ndarray | None = None,
        normals: list[list[float]] | np.ndarray | None = None,
        *,
        crossing_count: int | None = None,
    ) -> None:
        """Render a scene bundle produced by the engine."""

        self._centerline = np.asarray(centerline, dtype=float)
        self._crossing_positions = np.asarray(crossing_positions if crossing_positions is not None else [], dtype=float)
        if self._crossing_positions.size == 0 and crossing_count is not None:
            self._crossing_positions = _estimate_crossing_points(self._centerline, int(crossing_count))
        self._strand_segments = list(strand_segments or [])
        self._tangents = np.asarray(tangents if tangents is not None else [], dtype=float)
        self._normals = np.asarray(normals if normals is not None else [], dtype=float)
        self._curvature = _curve_curvature(self._centerline, self._tangents if len(self._tangents) else None)

        crossings = len(self._crossing_positions)
        strands = len(self._strand_segments)
        samples = max(0, len(self._centerline) - 1)
        self.scene_label.setText(f"{crossings} crossings | {strands} strands | {samples} samples")

        if self._headless or self.plotter is None:
            self._tube_actor = object() if len(self._centerline) else None
            self._markers_actor = object() if crossings else None
            return

        try:
            self.message_label.hide()
            self.plotter.clear()
            self._apply_lighting_preset(self.lighting_combo.currentText())
            if len(self._centerline) == 0:
                self._tube_actor = None
                self._markers_actor = None
                return

            settings = VizConfig()
            line = pv.lines_from_points(self._centerline, close=True)
            if len(self._curvature) == len(self._centerline):
                line["curvature"] = self._curvature
            tube = line.tube(radius=settings.tube_radius, n_sides=settings.tube_sides, capping=True)
            preset = _LIGHTING_PRESETS[self.lighting_combo.currentText()]
            mesh_kwargs = {
                "color": "#0f766e",
                "smooth_shading": True,
                "ambient": preset["ambient"],
                "diffuse": preset["diffuse"],
                "specular": preset["specular"],
                "specular_power": preset["specular_power"],
                "show_scalar_bar": False,
                "name": "tube",
            }
            if "curvature" in tube.point_data:
                mesh_kwargs.update({"scalars": "curvature", "cmap": "viridis"})
            self._tube_actor = self.plotter.add_mesh(tube, **mesh_kwargs)
            self.plotter.add_axes()

            if len(self._crossing_positions):
                self._markers_actor = self.plotter.add_points(
                    self._crossing_positions,
                    color="#f59e0b",
                    point_size=14,
                    render_points_as_spheres=True,
                    name="crossing_markers",
                )
            else:
                self._markers_actor = None
            self.plotter.view_isometric()
            self.plotter.reset_camera()
            self.highlight_crossing(self._highlight_index)
            self.plotter.render()
        except Exception as exc:
            self.message_label.setText(f"3D viewport unavailable: {exc}")
            self.message_label.show()

    def _apply_lighting_preset(self, preset_name: str) -> None:
        if self.plotter is None:
            return
        preset = _LIGHTING_PRESETS.get(preset_name, _LIGHTING_PRESETS["Studio"])
        self.plotter.set_background(preset["background"], top=preset["top"])

    def _on_lighting_changed(self, preset_name: str) -> None:
        if self.plotter is None:
            return
        self._apply_lighting_preset(preset_name)
        if len(self._centerline):
            self.load_centerline(
                self._centerline,
                self._crossing_positions,
                self._strand_segments,
                self._tangents,
                self._normals,
            )

    def highlight_crossing(self, crossing_index: int | None) -> None:
        """Highlight a selected crossing marker."""

        self._highlight_index = crossing_index
        if self._headless or self.plotter is None:
            self._highlight_actor = object() if crossing_index is not None else None
            return
        if self._highlight_actor is not None:
            self.plotter.remove_actor(self._highlight_actor)
            self._highlight_actor = None
        if crossing_index is None or len(self._crossing_positions) == 0:
            return
        if crossing_index < 0 or crossing_index >= len(self._crossing_positions):
            return
        sphere = pv.Sphere(radius=0.24, center=tuple(map(float, self._crossing_positions[crossing_index])))
        self._highlight_actor = self.plotter.add_mesh(
            sphere,
            color="#dc2626",
            opacity=0.88,
            smooth_shading=True,
            name="selected_crossing",
        )
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
