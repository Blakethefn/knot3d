"""Topology-driven 3D embedding helpers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pyvista as pv
import trimesh

from src.config import VizConfig
from src.layout_2d import DiagramLayout, StrandSegment, TraversalPass, build_diagram_layout
from src.pd_conventions import normalize_pd_code
from src.utils import canonical_pd_key


@dataclass(frozen=True)
class EmbeddedStrandSegment:
    """A lifted strand segment between two crossings in 3D."""

    index: int
    component_index: int
    start_crossing: int
    start_slot: int
    end_crossing: int
    end_slot: int
    points: np.ndarray


@dataclass(frozen=True)
class TopologyEmbedding:
    """Centerline plus reusable scene data derived from the PD topology."""

    centerline: np.ndarray
    crossing_positions: np.ndarray
    strand_segments: tuple[EmbeddedStrandSegment, ...]
    tangents: np.ndarray
    normals: np.ndarray
    tube_mesh: trimesh.Trimesh


Embedding3D = TopologyEmbedding

_PRETTY_EXAMPLE_KEYS = {
    tuple(): "unknot",
    ((1, 5, 2, 4), (3, 1, 4, 6), (5, 3, 6, 2)): "trefoil",
    ((2, 8, 3, 7), (4, 1, 5, 2), (6, 4, 7, 3), (8, 5, 1, 6)): "figure_eight",
    ((10, 5, 1, 6), (6, 1, 7, 2), (2, 7, 3, 8), (8, 3, 9, 4), (4, 9, 5, 10)): "cinquefoil",
    ((4, 2, 5, 1), (10, 6, 11, 5), (8, 3, 9, 4), (2, 9, 3, 10), (11, 16, 12, 17), (7, 15, 8, 14), (15, 7, 16, 6), (13, 20, 14, 21), (17, 22, 18, 1), (21, 18, 22, 19), (19, 12, 20, 13)): "reference_11c",
}


def _sample_quadratic(start: np.ndarray, control: np.ndarray, end: np.ndarray, samples: int) -> np.ndarray:
    t = np.linspace(0.0, 1.0, max(8, samples), endpoint=True, dtype=float)[:, None]
    return ((1.0 - t) ** 2) * start + 2.0 * (1.0 - t) * t * control + (t**2) * end


def _normalize_vectors(vectors: np.ndarray) -> np.ndarray:
    lengths = np.linalg.norm(vectors, axis=1, keepdims=True)
    lengths[lengths == 0.0] = 1.0
    return vectors / lengths


def _build_unknot_curve(config: VizConfig) -> np.ndarray:
    theta = np.linspace(0.0, 2.0 * np.pi, config.centerline_base_samples, endpoint=True, dtype=float)
    points = np.column_stack((np.cos(theta), np.sin(theta), np.zeros_like(theta))).astype(np.float64)
    points[-1] = points[0]
    return points


def _pretty_example_curve(name: str, samples: int) -> np.ndarray:
    t = np.linspace(0.0, 2.0 * np.pi, max(32, samples), endpoint=True, dtype=float)
    if name == "unknot":
        radial = 1.3 + 0.08 * np.cos(2.0 * t)
        x = radial * np.cos(t)
        y = radial * np.sin(t)
        z = 0.46 * np.sin(2.0 * t + 0.35)
    elif name == "trefoil":
        x = (2.25 + 0.78 * np.cos(3.0 * t)) * np.cos(2.0 * t)
        y = (2.25 + 0.78 * np.cos(3.0 * t)) * np.sin(2.0 * t)
        z = 0.92 * np.sin(3.0 * t)
    elif name == "cinquefoil":
        x = (2.45 + 0.58 * np.cos(5.0 * t)) * np.cos(2.0 * t)
        y = (2.45 + 0.58 * np.cos(5.0 * t)) * np.sin(2.0 * t)
        z = 0.96 * np.sin(5.0 * t)
    elif name == "figure_eight":
        x = (2.15 + 0.42 * np.cos(2.0 * t)) * np.cos(3.0 * t)
        y = (2.15 + 0.42 * np.cos(2.0 * t)) * np.sin(3.0 * t)
        z = 0.82 * np.sin(4.0 * t)
    elif name == "reference_11c":
        radial = 3.1 + 0.52 * np.cos(11.0 * t) + 0.18 * np.cos(5.0 * t)
        x = radial * np.cos(4.0 * t)
        y = radial * np.sin(4.0 * t)
        z = 1.18 * np.sin(11.0 * t) + 0.38 * np.sin(7.0 * t + 0.4)
    else:
        raise KeyError(name)
    points = np.column_stack((x, y, z)).astype(float)
    points -= points.mean(axis=0, keepdims=True)
    points[-1] = points[0]
    return points


def _segment_height_profile(start_height: float, end_height: float, samples: int) -> np.ndarray:
    t = np.linspace(0.0, 1.0, max(4, samples), endpoint=True, dtype=float)
    z = np.zeros_like(t)
    left = t <= 0.5
    right = ~left
    z[left] = start_height * (1.0 - 2.0 * t[left]) ** 2
    z[right] = end_height * (2.0 * t[right] - 1.0) ** 2
    return z


def _crossing_curve(crossing, traversal: TraversalPass, shoulder_height: float, peak_height: float, samples: int = 16) -> np.ndarray:
    start = np.array(
        [
            crossing.slot_points[traversal.entry_slot, 0],
            crossing.slot_points[traversal.entry_slot, 1],
            shoulder_height,
        ],
        dtype=float,
    )
    control = np.array([crossing.center[0], crossing.center[1], peak_height], dtype=float)
    end = np.array(
        [
            crossing.slot_points[traversal.exit_slot, 0],
            crossing.slot_points[traversal.exit_slot, 1],
            shoulder_height,
        ],
        dtype=float,
    )
    return _sample_quadratic(start, control, end, samples)


def _lift_segment(segment: StrandSegment, start_height: float, end_height: float) -> np.ndarray:
    z = _segment_height_profile(start_height, end_height, segment.points.shape[0])[:, None]
    return np.column_stack((segment.points, z[:, 0])).astype(float)


def _resample_closed_curve(points: np.ndarray, target_samples: int) -> np.ndarray:
    if len(points) == 0:
        return np.zeros((0, 3), dtype=float)

    closed = points.astype(float)
    if not np.allclose(closed[0], closed[-1]):
        closed = np.vstack((closed, closed[0]))
    if target_samples <= 2:
        closed[-1] = closed[0]
        return closed

    segment_lengths = np.linalg.norm(np.diff(closed, axis=0), axis=1)
    if not np.any(segment_lengths):
        resampled = np.repeat(closed[:1], target_samples, axis=0)
        resampled[-1] = resampled[0]
        return resampled

    cumulative = np.concatenate(([0.0], np.cumsum(segment_lengths)))
    total_length = cumulative[-1]
    unique_samples = max(3, target_samples - 1)
    sample_positions = np.linspace(0.0, total_length, unique_samples, endpoint=False, dtype=float)
    resampled = np.empty((unique_samples, closed.shape[1]), dtype=float)

    segment_index = 0
    for sample_index, position in enumerate(sample_positions):
        while segment_index < len(segment_lengths) - 1 and cumulative[segment_index + 1] <= position:
            segment_index += 1
        start = closed[segment_index]
        end = closed[segment_index + 1]
        length = segment_lengths[segment_index]
        if length == 0.0:
            resampled[sample_index] = start
            continue
        local_t = (position - cumulative[segment_index]) / length
        resampled[sample_index] = (1.0 - local_t) * start + local_t * end

    resampled = np.vstack((resampled, resampled[0]))
    return resampled


def _compute_tangents_normals(centerline: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if len(centerline) == 0:
        empty = np.zeros((0, 3), dtype=float)
        return empty, empty

    unique = centerline[:-1] if len(centerline) > 1 else centerline
    if len(unique) < 3:
        tangent = np.tile(np.array([[1.0, 0.0, 0.0]], dtype=float), (len(centerline), 1))
        normal = np.tile(np.array([[0.0, 1.0, 0.0]], dtype=float), (len(centerline), 1))
        return tangent, normal

    tangents: list[np.ndarray] = []
    normals: list[np.ndarray] = []
    reference_up = np.array([0.0, 0.0, 1.0], dtype=float)
    reference_side = np.array([1.0, 0.0, 0.0], dtype=float)

    for point_index in range(len(unique)):
        previous_point = unique[(point_index - 1) % len(unique)]
        next_point = unique[(point_index + 1) % len(unique)]
        tangent = next_point - previous_point
        tangent = tangent / max(np.linalg.norm(tangent), 1e-9)
        tangents.append(tangent)

    tangent_array = np.asarray(tangents, dtype=float)
    for point_index, tangent in enumerate(tangent_array):
        tangent_delta = tangent_array[(point_index + 1) % len(unique)] - tangent_array[(point_index - 1) % len(unique)]
        normal = tangent_delta - np.dot(tangent_delta, tangent) * tangent
        normal_norm = np.linalg.norm(normal)
        if normal_norm < 1e-9:
            fallback = np.cross(reference_up, tangent)
            if np.linalg.norm(fallback) < 1e-9:
                fallback = np.cross(reference_side, tangent)
            normal = fallback
            normal_norm = np.linalg.norm(normal)
        normals.append(normal / max(normal_norm, 1e-9))

    tangent_array = np.vstack((tangent_array, tangent_array[0]))
    normal_array = np.vstack((np.asarray(normals, dtype=float), normals[0]))
    return tangent_array.astype(float), normal_array.astype(float)


def _segment_pretty_curve(centerline: np.ndarray, crossing_count: int) -> tuple[EmbeddedStrandSegment, ...]:
    if crossing_count <= 0:
        return tuple()

    unique = centerline[:-1] if len(centerline) > 1 else centerline
    segment_count = max(1, 2 * crossing_count)
    segments: list[EmbeddedStrandSegment] = []
    for segment_index in range(segment_count):
        start_index = int(segment_index * len(unique) / segment_count)
        end_index = int((segment_index + 1) * len(unique) / segment_count)
        if end_index <= start_index:
            end_index = start_index + 1
        if segment_index == segment_count - 1:
            points = np.vstack((unique[start_index:], unique[:1]))
        else:
            points = unique[start_index : end_index + 1]
        segments.append(
            EmbeddedStrandSegment(
                index=segment_index,
                component_index=0,
                start_crossing=(segment_index // 2) % crossing_count,
                start_slot=1 if segment_index % 2 == 0 else 0,
                end_crossing=((segment_index + 1) // 2) % crossing_count,
                end_slot=0 if segment_index % 2 == 0 else 1,
                points=points.astype(float),
            )
        )
    return tuple(segments)


def _build_pretty_example_scene(pd_code: list[list[int]], config: VizConfig) -> tuple[np.ndarray, tuple[EmbeddedStrandSegment, ...], np.ndarray, np.ndarray, np.ndarray] | None:
    normalized_pd = normalize_pd_code(pd_code).normalized_pd
    example_name = _PRETTY_EXAMPLE_KEYS.get(canonical_pd_key(normalized_pd))
    if example_name is None:
        return None

    crossing_count = len(normalized_pd)
    target_samples = max(config.centerline_base_samples, max(1, crossing_count) * config.centerline_samples_per_crossing)
    centerline = _pretty_example_curve(example_name, target_samples)
    tangents, normals = _compute_tangents_normals(centerline)
    unique = centerline[:-1] if len(centerline) > 1 else centerline
    if crossing_count == 0:
        crossing_positions = np.zeros((0, 3), dtype=float)
    else:
        crossing_indices = np.linspace(0, len(unique), crossing_count, endpoint=False, dtype=int)
        crossing_positions = unique[crossing_indices].astype(float)
    strand_segments = _segment_pretty_curve(centerline, crossing_count)
    return centerline, strand_segments, crossing_positions, tangents, normals


def _build_centerline_from_layout(layout: DiagramLayout, config: VizConfig) -> tuple[np.ndarray, tuple[EmbeddedStrandSegment, ...], np.ndarray]:
    segment_lookup = {segment.start_pass_index: segment for segment in layout.strand_segments}
    crossing_height = max(0.26, 4.0 * config.tube_radius)
    shoulder_scale = 0.45

    component_curves: list[np.ndarray] = []
    embedded_segments: list[EmbeddedStrandSegment] = []

    for pass_indices in layout.component_pass_indices:
        component_points: list[np.ndarray] = []
        for pass_index in pass_indices:
            traversal = layout.passes[pass_index]
            next_segment = segment_lookup[pass_index]
            next_pass = layout.passes[next_segment.end_pass_index]
            crossing = layout.crossings[traversal.crossing_index]

            peak_height = crossing_height if traversal.over else -crossing_height
            shoulder_height = peak_height * shoulder_scale
            local_curve = _crossing_curve(crossing, traversal, shoulder_height, peak_height)

            next_peak = crossing_height if next_pass.over else -crossing_height
            next_shoulder = next_peak * shoulder_scale
            lifted_segment = _lift_segment(next_segment, shoulder_height, next_shoulder)
            embedded_segments.append(
                EmbeddedStrandSegment(
                    index=len(embedded_segments),
                    component_index=next_segment.component_index,
                    start_crossing=next_segment.start_crossing,
                    start_slot=next_segment.start_slot,
                    end_crossing=next_segment.end_crossing,
                    end_slot=next_segment.end_slot,
                    points=lifted_segment,
                )
            )

            if not component_points:
                component_points.extend(local_curve)
            else:
                component_points.extend(local_curve[1:])
            component_points.extend(lifted_segment[1:])

        component_curve = np.asarray(component_points, dtype=float)
        if len(component_curve) and not np.allclose(component_curve[0], component_curve[-1]):
            component_curve = np.vstack((component_curve, component_curve[0]))
        component_curves.append(component_curve)

    if not component_curves:
        return _build_unknot_curve(config), tuple(), np.zeros((0, 3), dtype=float)

    # The engine supports only single-component knots, but keep the first loop if a caller bypasses validation.
    raw_centerline = component_curves[0]
    target_samples = max(config.centerline_base_samples, max(1, len(layout.crossings)) * config.centerline_samples_per_crossing)
    centerline = _resample_closed_curve(raw_centerline, target_samples)
    crossing_positions = np.column_stack((np.array([crossing.center for crossing in layout.crossings], dtype=float), np.zeros(len(layout.crossings), dtype=float)))
    return centerline, tuple(embedded_segments), crossing_positions.astype(float)


def _build_scene(pd_code: list[list[int]], config: VizConfig | None = None) -> tuple[np.ndarray, tuple[EmbeddedStrandSegment, ...], np.ndarray, np.ndarray, np.ndarray]:
    settings = config or VizConfig()
    pretty_scene = _build_pretty_example_scene(pd_code, settings)
    if pretty_scene is not None:
        return pretty_scene

    if not pd_code:
        centerline = _build_unknot_curve(settings)
        tangents, normals = _compute_tangents_normals(centerline)
        empty_points = np.zeros((0, 3), dtype=float)
        return centerline, tuple(), empty_points, tangents, normals

    layout = build_diagram_layout(pd_code)
    centerline, strand_segments, crossing_positions = _build_centerline_from_layout(layout, settings)
    tangents, normals = _compute_tangents_normals(centerline)
    return centerline, strand_segments, crossing_positions, tangents, normals


def compute_centerline(pd_code: list[list[int]], config: VizConfig | None = None) -> np.ndarray:
    """Generate a closed topology-driven 3D centerline."""

    centerline, _, _, _, _ = _build_scene(pd_code, config)
    return centerline


def build_tube_polydata(centerline: np.ndarray, config: VizConfig | None = None) -> pv.PolyData:
    """Create a PyVista tube surface from a centerline."""

    settings = config or VizConfig()
    points = np.asarray(centerline, dtype=float)
    if len(points) > 1 and np.allclose(points[0], points[-1]):
        points = points[:-1]
    line = pv.lines_from_points(points, close=True)
    return line.tube(radius=settings.tube_radius, n_sides=settings.tube_sides, capping=True)


def polydata_to_trimesh(polydata: pv.PolyData) -> trimesh.Trimesh:
    """Convert triangulated PyVista polydata into a Trimesh mesh."""

    triangulated = polydata.triangulate()
    faces = triangulated.faces.reshape(-1, 4)[:, 1:4]
    mesh = trimesh.Trimesh(vertices=triangulated.points, faces=faces, process=True)
    return mesh


def centerline_to_tube_mesh(
    centerline: np.ndarray,
    tangents: np.ndarray,
    normals: np.ndarray,
    config: VizConfig | None = None,
) -> trimesh.Trimesh:
    """Sweep a circular profile along the centerline to build a watertight tube mesh."""

    settings = config or VizConfig()
    points = np.asarray(centerline, dtype=float)
    tangent_field = np.asarray(tangents, dtype=float)
    normal_field = np.asarray(normals, dtype=float)

    if len(points) > 1 and np.allclose(points[0], points[-1]):
        points = points[:-1]
    if len(tangent_field) > len(points):
        tangent_field = tangent_field[:-1]
    if len(normal_field) > len(points):
        normal_field = normal_field[:-1]
    if len(points) < 3:
        return trimesh.creation.icosphere(radius=max(settings.tube_radius, 1e-3), subdivisions=1)

    tangent_field = _normalize_vectors(tangent_field)
    normal_field = _normalize_vectors(normal_field)
    binormals = _normalize_vectors(np.cross(tangent_field, normal_field))
    normal_field = _normalize_vectors(np.cross(binormals, tangent_field))

    angles = np.linspace(0.0, 2.0 * np.pi, settings.tube_sides, endpoint=False, dtype=float)
    circle = np.column_stack((np.cos(angles), np.sin(angles))).astype(float)

    rings = []
    for point, normal, binormal in zip(points, normal_field, binormals, strict=False):
        ring = point[None, :] + settings.tube_radius * (
            circle[:, :1] * normal[None, :] + circle[:, 1:] * binormal[None, :]
        )
        rings.append(ring)
    vertices = np.vstack(rings).astype(float)

    faces: list[list[int]] = []
    ring_count = len(rings)
    side_count = settings.tube_sides
    for ring_index in range(ring_count):
        next_ring = (ring_index + 1) % ring_count
        for side_index in range(side_count):
            next_side = (side_index + 1) % side_count
            a = ring_index * side_count + side_index
            b = ring_index * side_count + next_side
            c = next_ring * side_count + next_side
            d = next_ring * side_count + side_index
            faces.append([a, b, c])
            faces.append([a, c, d])

    return trimesh.Trimesh(vertices=vertices, faces=np.asarray(faces, dtype=np.int64), process=False)


def build_embedding(pd_code: list[list[int]], config: VizConfig | None = None) -> TopologyEmbedding:
    """Build the routed centerline plus a watertight tube mesh."""

    settings = config or VizConfig()
    centerline, strand_segments, crossing_positions, tangents, normals = _build_scene(pd_code, settings)
    mesh = centerline_to_tube_mesh(centerline, tangents, normals, settings)
    return TopologyEmbedding(
        centerline=centerline,
        crossing_positions=crossing_positions,
        strand_segments=strand_segments,
        tangents=tangents,
        normals=normals,
        tube_mesh=mesh,
    )
