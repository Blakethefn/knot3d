"""Planar knot-diagram layout helpers derived from PD connectivity."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from spherogram import Link

from src.pd_conventions import normalize_pd_code

_SLOT_ANGLE_OFFSETS = np.deg2rad(np.array([-135.0, -45.0, 45.0, 135.0], dtype=float))


@dataclass(frozen=True)
class CrossingLayout:
    """A single crossing positioned in the plane with cyclic slot anchors."""

    index: int
    center: np.ndarray
    slot_points: np.ndarray
    slot_vectors: np.ndarray
    under_slots: tuple[int, int] = (0, 2)
    over_slots: tuple[int, int] = (1, 3)


@dataclass(frozen=True)
class TraversalPass:
    """One oriented traversal of a crossing along the knot component."""

    index: int
    component_index: int
    crossing_index: int
    entry_slot: int
    exit_slot: int
    over: bool


@dataclass(frozen=True)
class StrandSegment:
    """A routed arc between consecutive crossings along a knot component."""

    index: int
    component_index: int
    start_crossing: int
    start_slot: int
    end_crossing: int
    end_slot: int
    start_pass_index: int
    end_pass_index: int
    label: int
    points: np.ndarray


@dataclass(frozen=True)
class DiagramLayout:
    """Crossing placements plus routed strand arcs for diagram rendering."""

    crossings: tuple[CrossingLayout, ...]
    passes: tuple[TraversalPass, ...]
    strand_segments: tuple[StrandSegment, ...]
    component_pass_indices: tuple[tuple[int, ...], ...]
    bounds: tuple[float, float, float, float]


def _normalize_vectors(vectors: np.ndarray) -> np.ndarray:
    lengths = np.linalg.norm(vectors, axis=1, keepdims=True)
    lengths[lengths == 0.0] = 1.0
    return vectors / lengths


def _sample_cubic(start: np.ndarray, control1: np.ndarray, control2: np.ndarray, end: np.ndarray, samples: int) -> np.ndarray:
    t = np.linspace(0.0, 1.0, max(4, samples), endpoint=True, dtype=float)[:, None]
    omt = 1.0 - t
    return (omt**3) * start + 3.0 * (omt**2) * t * control1 + 3.0 * omt * (t**2) * control2 + (t**3) * end


def _crossing_order(component_entries: list[list], crossing_count: int) -> list[int]:
    first_seen: dict[int, tuple[int, int]] = {}
    for component_index, entries in enumerate(component_entries):
        for order_index, entry in enumerate(entries):
            crossing_index = int(entry.crossing.label)
            first_seen.setdefault(crossing_index, (component_index, order_index))
    return sorted(range(crossing_count), key=lambda crossing_index: first_seen.get(crossing_index, (crossing_count, crossing_index)))


def _arrange_crossings(order: list[int]) -> np.ndarray:
    crossing_count = len(order)
    if crossing_count == 0:
        return np.zeros((0, 2), dtype=float)
    if crossing_count == 1:
        return np.zeros((1, 2), dtype=float)

    angles = np.linspace(-0.5 * math.pi, 1.5 * math.pi, crossing_count, endpoint=False, dtype=float)
    base_radius = max(2.8, 0.65 * crossing_count)
    radial_jitter = 0.38 * np.sin(3.0 * angles) + 0.24 * np.cos(2.0 * angles)
    positions = np.zeros((crossing_count, 2), dtype=float)

    for placement_index, crossing_index in enumerate(order):
        radius = base_radius + radial_jitter[placement_index]
        angle = angles[placement_index]
        positions[crossing_index] = np.array(
            [
                radius * math.cos(angle),
                1.05 * radius * math.sin(angle),
            ],
            dtype=float,
        )
    return positions


def _build_crossings(centers: np.ndarray) -> tuple[CrossingLayout, ...]:
    crossings: list[CrossingLayout] = []
    crossing_count = len(centers)
    slot_radius = 0.34 if crossing_count < 8 else 0.3

    for crossing_index, center in enumerate(centers):
        if np.allclose(center, 0.0):
            base_angle = -0.5 * math.pi
        else:
            base_angle = math.atan2(float(center[1]), float(center[0])) + 0.5 * math.pi
        slot_angles = base_angle + _SLOT_ANGLE_OFFSETS
        slot_vectors = np.column_stack((np.cos(slot_angles), np.sin(slot_angles))).astype(float)
        slot_points = center[None, :] + slot_radius * slot_vectors
        crossings.append(
            CrossingLayout(
                index=crossing_index,
                center=center.astype(float),
                slot_points=slot_points,
                slot_vectors=slot_vectors,
            )
        )
    return tuple(crossings)


def _resolve_exit_slot(crossing, entry_slot: int) -> int:
    for start_slot, end_slot in crossing.directions:
        if int(start_slot) == entry_slot:
            return int(end_slot)
    raise ValueError(f"Could not resolve an exit slot for crossing {crossing!r} entry {entry_slot}.")


def _segment_points(
    start_crossing: CrossingLayout,
    start_slot: int,
    end_crossing: CrossingLayout,
    end_slot: int,
) -> np.ndarray:
    start = start_crossing.slot_points[start_slot]
    end = end_crossing.slot_points[end_slot]
    distance = float(np.linalg.norm(end - start))
    handle = max(0.72, 0.28 * distance)
    control1 = start + start_crossing.slot_vectors[start_slot] * handle
    control2 = end + end_crossing.slot_vectors[end_slot] * handle
    return _sample_cubic(start, control1, control2, end, samples=max(14, int(distance * 4.0)))


def build_diagram_layout(pd_code: list[list[int]]) -> DiagramLayout:
    """Build a routed diagram layout that preserves PD strand connectivity."""

    if not pd_code:
        return DiagramLayout(crossings=(), passes=(), strand_segments=(), component_pass_indices=(), bounds=(-1.0, 1.0, -1.0, 1.0))

    normalized_pd = normalize_pd_code(pd_code).normalized_pd
    link = Link(normalized_pd)
    component_entries = [list(component) for component in link.link_components]
    order = _crossing_order(component_entries, len(link.crossings))
    centers = _arrange_crossings(order)
    crossings = _build_crossings(centers)

    passes: list[TraversalPass] = []
    component_pass_indices: list[tuple[int, ...]] = []
    for component_index, entries in enumerate(component_entries):
        local_indices: list[int] = []
        for entry in entries:
            crossing_index = int(entry.crossing.label)
            entry_slot = int(entry.strand_index)
            exit_slot = _resolve_exit_slot(entry.crossing, entry_slot)
            pass_index = len(passes)
            passes.append(
                TraversalPass(
                    index=pass_index,
                    component_index=component_index,
                    crossing_index=crossing_index,
                    entry_slot=entry_slot,
                    exit_slot=exit_slot,
                    over=entry_slot != 0,
                )
            )
            local_indices.append(pass_index)
        component_pass_indices.append(tuple(local_indices))

    routed_segments: list[StrandSegment] = []
    for component_index, pass_indices in enumerate(component_pass_indices):
        if not pass_indices:
            continue
        for local_index, pass_index in enumerate(pass_indices):
            current_pass = passes[pass_index]
            next_pass_index = pass_indices[(local_index + 1) % len(pass_indices)]
            next_pass = passes[next_pass_index]
            start_crossing = crossings[current_pass.crossing_index]
            end_crossing = crossings[next_pass.crossing_index]
            label = int(link.crossings[current_pass.crossing_index].strand_labels[current_pass.exit_slot]) + 1
            points = _segment_points(start_crossing, current_pass.exit_slot, end_crossing, next_pass.entry_slot)
            routed_segments.append(
                StrandSegment(
                    index=len(routed_segments),
                    component_index=component_index,
                    start_crossing=current_pass.crossing_index,
                    start_slot=current_pass.exit_slot,
                    end_crossing=next_pass.crossing_index,
                    end_slot=next_pass.entry_slot,
                    start_pass_index=pass_index,
                    end_pass_index=next_pass_index,
                    label=label,
                    points=points,
                )
            )

    all_points = [crossing.center for crossing in crossings]
    all_points.extend(crossing.slot_points for crossing in crossings)
    all_points.extend(segment.points for segment in routed_segments)
    stacked = np.vstack(all_points).astype(float)
    padding = 0.9
    bounds = (
        float(stacked[:, 0].min() - padding),
        float(stacked[:, 0].max() + padding),
        float(stacked[:, 1].min() - padding),
        float(stacked[:, 1].max() + padding),
    )
    return DiagramLayout(
        crossings=crossings,
        passes=tuple(passes),
        strand_segments=tuple(routed_segments),
        component_pass_indices=tuple(component_pass_indices),
        bounds=bounds,
    )


def sample_crossing_pass(crossing: CrossingLayout, traversal: TraversalPass, samples: int = 18, gap_fraction: float = 0.18) -> tuple[np.ndarray, ...]:
    """Return one or two polylines for the local strand through a crossing."""

    entry = crossing.slot_points[traversal.entry_slot]
    center = crossing.center
    exit_ = crossing.slot_points[traversal.exit_slot]
    t = np.linspace(0.0, 1.0, max(10, samples), endpoint=True, dtype=float)[:, None]
    curve = ((1.0 - t) ** 2) * entry + 2.0 * (1.0 - t) * t * center + (t**2) * exit_
    if traversal.over:
        return (curve,)

    split = curve.shape[0] // 2
    gap = max(2, int(round(curve.shape[0] * gap_fraction * 0.5)))
    first = curve[: max(2, split - gap)]
    second = curve[min(curve.shape[0] - 2, split + gap) :]
    return (first, second)


def diagram_bounds(layout: DiagramLayout) -> tuple[float, float, float, float]:
    """Expose bounds without forcing callers to know the dataclass shape."""

    return layout.bounds
