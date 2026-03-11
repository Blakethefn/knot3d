"""Shared engine boundary used by the CLI and desktop GUI."""

from __future__ import annotations

import copy
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Callable

import knot_floer_homology
import meshio
import networkx
import numpy as np
import pandas as pd
import pyvista as pv
import scipy
import snappy
import trimesh
from spherogram import Link

from src.config import PipelineConfig
from src.crossing_change import apply_crossing_changes
from src.embedding_3d import build_embedding
from src.hfk_engine import compute_hfk
from src.invariants import compute_classical_invariants
from src.knot_builder import build_all
from src.mesh_export import export_centerline_csv, export_meshes
from src.pd_conventions import normalize_pd_code
from src.pd_parser import PDParseError, parse_pd_input
from src.services.compute_policy import ComputePreferences, apply_compute_runtime, resolve_compute_runtime
from src.unknot_recognizer import recognize_unknot
from src.unknotting_search import search_unknotting_number_one
from src.utils import as_jsonable, canonical_pd_key, ensure_dir, write_json
from src.viz_matplotlib import render_diagram
from src.viz_pyvista import render_3d_preview

ProgressCallback = Callable[[str, int], None]


@dataclass(frozen=True)
class ValidationResult:
    """Structured PD validation response for the GUI."""

    valid: bool
    message: str
    pd_code: list[list[int]]
    normalized_pd: list[list[int]]
    detected_convention: str | None
    notes: list[str]
    crossing_count: int

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""

        return asdict(self)


def _report_progress(callback: ProgressCallback | None, message: str, percent: int) -> None:
    """Emit progress updates when a callback is available."""

    if callback is not None:
        callback(message, percent)


def build_output_paths(output_prefix: str | Path) -> dict[str, str]:
    """Return the canonical output paths for a base prefix."""

    prefix = Path(output_prefix)
    return {
        "analysis_json": str(prefix.with_name(prefix.name + "_analysis.json")),
        "unknotting_json": str(prefix.with_name(prefix.name + "_unknotting.json")),
        "crossing_changes_json": str(prefix.with_name(prefix.name + "_crossing_changes.json")),
        "diagram_png": str(prefix.with_name(prefix.name + "_diagram.png")),
        "preview_3d": str(prefix.with_name(prefix.name + "_3d.png")),
        "centerline_csv": str(prefix.with_name(prefix.name + "_centerline.csv")),
    }


def execute_pipeline(
    pd_input: str | Path | list[list[int]] | tuple[tuple[int, ...], ...],
    output_prefix: str | Path,
    config: PipelineConfig | None = None,
    modes: set[str] | None = None,
    progress_callback: ProgressCallback | None = None,
) -> dict[str, Any]:
    """Run the shared topology pipeline and write canonical artifacts."""

    pipeline = config or PipelineConfig()
    selected_modes = modes or {"analyze"}
    prefix = Path(output_prefix)
    ensure_dir(prefix.parent)
    output_files = build_output_paths(prefix)

    timers: dict[str, float] = {}

    _report_progress(progress_callback, "Parsing PD code", 5)
    started = perf_counter()
    parsed = parse_pd_input(pd_input)
    timers["parse"] = perf_counter() - started

    _report_progress(progress_callback, "Building topology objects", 15)
    build_started = perf_counter()
    artifacts = build_all(parsed.to_list(), pipeline)
    timers["build"] = perf_counter() - build_started

    _report_progress(progress_callback, "Computing classical invariants", 30)
    classical_started = perf_counter()
    classical = compute_classical_invariants(artifacts.link, artifacts.manifold)
    timers["classical"] = perf_counter() - classical_started

    hfk = None
    if pipeline.invariants.compute_hfk and {"analyze", "unknotting_search"} & selected_modes:
        _report_progress(progress_callback, "Computing knot Floer homology", 45)
        hfk_started = perf_counter()
        hfk = compute_hfk(artifacts.normalization.normalized_pd, timeout=pipeline.invariants.hfk_timeout)
        timers["hfk"] = perf_counter() - hfk_started

    analysis_payload = {
        "knot_name": classical.knot_id,
        "pd_code": artifacts.normalization.normalized_pd,
        "detected_convention": artifacts.normalization.detected_convention,
        "convention_notes": artifacts.normalization.notes,
        "invariants": classical.to_dict(),
        "hfk": hfk.to_dict() if hfk is not None else None,
        "computation_times": timers,
    }

    if "analyze" in selected_modes:
        write_json(output_files["analysis_json"], analysis_payload)

    unknotting_payload = None
    crossing_changes_payload = None
    if "unknotting_search" in selected_modes:
        _report_progress(progress_callback, "Checking unknot status", 60)
        unknotting = search_unknotting_number_one(artifacts.normalization.normalized_pd, classical, hfk, pipeline)
        unknotting_payload = unknotting.to_dict()
        crossing_changes_payload = {
            "candidates": unknotting_payload.get("candidate_summaries", []),
            "filter_stats": unknotting_payload["filter_stats"],
            "knot_name": unknotting_payload["knot_name"],
            "total_candidates": unknotting_payload["total_candidates"],
        }
        write_json(output_files["unknotting_json"], unknotting_payload)
        write_json(output_files["crossing_changes_json"], crossing_changes_payload)

    _report_progress(progress_callback, "Rendering diagram", 78)
    diagram_path = render_diagram(artifacts.normalization.normalized_pd, output_files["diagram_png"])

    _report_progress(progress_callback, "Building 3D embedding", 86)
    embedding = build_embedding(artifacts.normalization.normalized_pd, pipeline.viz)
    centerline_csv = export_centerline_csv(embedding.centerline, output_files["centerline_csv"])
    preview_path = render_3d_preview(embedding.centerline, prefix, pipeline.viz)

    mesh_outputs = None
    if "export_mesh" in selected_modes:
        _report_progress(progress_callback, "Exporting mesh bundle", 94)
        mesh_outputs = export_meshes(artifacts.normalization.normalized_pd, prefix)

    _report_progress(progress_callback, "Completed", 100)
    return {
        "analysis": analysis_payload,
        "unknotting": unknotting_payload,
        "crossing_changes": crossing_changes_payload,
        "preview_3d": str(preview_path),
        "diagram_path": str(diagram_path),
        "centerline_csv": str(centerline_csv),
        "mesh_outputs": mesh_outputs,
        "normalized_pd": artifacts.normalization.normalized_pd,
        "detected_convention": artifacts.normalization.detected_convention,
        "convention_notes": artifacts.normalization.notes,
        "centerline": embedding.centerline.tolist(),
        "output_files": output_files,
    }


class EngineFacade:
    """Thin reusable bridge from the GUI to the shared topology engine."""

    def __init__(
        self,
        config: PipelineConfig | None = None,
        compute_preferences: ComputePreferences | None = None,
    ) -> None:
        self.config = config or PipelineConfig()
        self.compute_preferences = compute_preferences or ComputePreferences()
        self._last_compute_runtime = resolve_compute_runtime(self.compute_preferences)
        self._cache: dict[tuple[Any, ...], dict[str, Any]] = {}

    def update_compute_preferences(self, preferences: ComputePreferences) -> dict[str, Any]:
        """Update the active compute preferences."""

        self.compute_preferences = preferences
        self._last_compute_runtime = resolve_compute_runtime(preferences)
        return self.get_compute_runtime()

    def get_compute_runtime(self) -> dict[str, Any]:
        """Return the resolved compute runtime for the active preferences."""

        return self._last_compute_runtime.to_dict()

    def validate_pd(self, raw_text: str) -> ValidationResult:
        """Parse, validate, and normalize a PD code."""

        parsed = parse_pd_input(raw_text)
        normalized = normalize_pd_code(parsed.to_list(), self.config.pd, self.config.search)
        # Build once during validation so the GUI surfaces topology issues immediately.
        _ = build_all(parsed.to_list(), self.config)
        crossing_count = len(normalized.normalized_pd)
        message = "Valid unknot PD." if crossing_count == 0 else f"Valid PD with {crossing_count} crossings."
        return ValidationResult(
            valid=True,
            message=message,
            pd_code=parsed.to_list(),
            normalized_pd=normalized.normalized_pd,
            detected_convention=normalized.detected_convention,
            notes=normalized.notes,
            crossing_count=crossing_count,
        )

    def analyze(
        self,
        pd_code: list[list[int]],
        output_prefix: str | Path,
        progress_callback: ProgressCallback | None = None,
    ) -> dict[str, Any]:
        """Run the analysis pipeline and reuse cached results when possible."""

        return self._execute_cached(pd_code, output_prefix, {"analyze"}, progress_callback)

    def run_unknotting_search(
        self,
        pd_code: list[list[int]],
        output_prefix: str | Path,
        progress_callback: ProgressCallback | None = None,
    ) -> dict[str, Any]:
        """Run analysis plus the depth-1 unknotting search."""

        return self._execute_cached(pd_code, output_prefix, {"analyze", "unknotting_search"}, progress_callback)

    def export_mesh(
        self,
        pd_code: list[list[int]],
        output_prefix: str | Path,
        progress_callback: ProgressCallback | None = None,
    ) -> dict[str, Any]:
        """Export a mesh bundle for the normalized knot."""

        result = self._execute_cached(pd_code, output_prefix, {"analyze", "export_mesh"}, progress_callback)
        return {"mesh_outputs": result["mesh_outputs"], "output_files": result["output_files"]}

    def build_crossing_candidate_preview(
        self,
        pd_code: list[list[int]],
        crossing_idx: int,
    ) -> dict[str, Any]:
        """Build preview data for a single crossing-change candidate."""

        runtime = resolve_compute_runtime(self.compute_preferences)
        self._last_compute_runtime = runtime
        with apply_compute_runtime(runtime):
            normalized = normalize_pd_code(pd_code, self.config.pd, self.config.search).normalized_pd
            modified_pd = apply_crossing_changes(normalized, (crossing_idx,))
            artifacts = build_all(modified_pd, self.config)
            classical = compute_classical_invariants(artifacts.link, artifacts.manifold)
            hfk = compute_hfk(artifacts.normalization.normalized_pd, timeout=self.config.invariants.hfk_timeout)
            recognition = recognize_unknot(artifacts.normalization.normalized_pd, classical, hfk, self.config.search)
            embedding = build_embedding(artifacts.normalization.normalized_pd, self.config.viz)
        return {
            "crossing_index": crossing_idx,
            "original_pd": normalized,
            "modified_pd": artifacts.normalization.normalized_pd,
            "analysis": {
                "knot_name": classical.knot_id,
                "invariants": classical.to_dict(),
                "hfk": hfk.to_dict(),
            },
            "recognition": recognition.to_dict(),
            "centerline": embedding.centerline.tolist(),
        }

    def get_engine_versions(self) -> dict[str, str]:
        """Return the runtime versions of the topology and rendering stack."""

        return {
            "PySide6": "6.10.2",
            "pyvista": pv.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "snappy": getattr(snappy, "__version__", "unknown"),
            "spherogram": getattr(Link, "__module__", "spherogram"),
            "knot_floer_homology": getattr(knot_floer_homology, "__version__", "unknown"),
            "networkx": networkx.__version__,
            "trimesh": trimesh.__version__,
            "meshio": meshio.__version__,
        }

    def _execute_cached(
        self,
        pd_code: list[list[int]],
        output_prefix: str | Path,
        modes: set[str],
        progress_callback: ProgressCallback | None,
    ) -> dict[str, Any]:
        runtime = resolve_compute_runtime(self.compute_preferences)
        self._last_compute_runtime = runtime
        normalized = normalize_pd_code(pd_code, self.config.pd, self.config.search).normalized_pd
        cache_key = (canonical_pd_key(normalized), tuple(sorted(modes)))
        if cache_key in self._cache:
            cached = copy.deepcopy(self._cache[cache_key])
            output_files = build_output_paths(output_prefix)
            cached["output_files"] = output_files
            cached["compute_runtime"] = runtime.to_dict()
            return cached

        with apply_compute_runtime(runtime):
            result = execute_pipeline(normalized, output_prefix, self.config, modes, progress_callback)
        result["compute_runtime"] = runtime.to_dict()
        cached_result = copy.deepcopy(result)
        cached_result.pop("compute_runtime", None)
        self._cache[cache_key] = cached_result
        return result

    def clear_cache(self) -> None:
        """Clear the in-memory result cache."""

        self._cache.clear()


def dump_json_payload(payload: dict[str, Any]) -> str:
    """Serialize a payload for the raw JSON tab."""

    return json.dumps(as_jsonable(payload), indent=2, sort_keys=True)
