"""CLI entry point for the knot engine."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from time import perf_counter

from src.config import PipelineConfig
from src.embedding_3d import build_embedding
from src.hfk_engine import compute_hfk
from src.invariants import compute_classical_invariants
from src.knot_builder import build_all
from src.logging_setup import configure_logging
from src.mesh_export import export_centerline_csv, export_meshes
from src.pd_parser import parse_pd_input
from src.unknotting_search import search_unknotting_number_one
from src.utils import ensure_dir, write_json
from src.viz_matplotlib import render_diagram
from src.viz_pyvista import render_3d_preview

LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI parser."""

    parser = argparse.ArgumentParser(description="Topology-first knot analysis engine")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pd", help="PD code literal or JSON string")
    group.add_argument("--pd-file", help="Path to a JSON or text file containing a PD code")
    parser.add_argument("--analyze", action="store_true", help="Run the analysis pipeline")
    parser.add_argument("--unknotting-search", action="store_true", help="Run depth-1 unknotting search")
    parser.add_argument("--export-mesh", action="store_true", help="Export mesh artifacts")
    parser.add_argument("--out", required=True, help="Output prefix, for example out/trefoil")
    parser.add_argument("-v", action="count", default=0, help="Increase logging verbosity")
    return parser


def run_pipeline(
    pd_input: str | Path,
    output_prefix: str | Path,
    config: PipelineConfig | None = None,
    modes: set[str] | None = None,
) -> dict[str, object]:
    """Run the analysis pipeline and return a serializable summary."""

    pipeline = config or PipelineConfig()
    selected_modes = modes or {"analyze"}
    prefix = Path(output_prefix)
    ensure_dir(prefix.parent)

    timers: dict[str, float] = {}
    started = perf_counter()
    parsed = parse_pd_input(pd_input)
    timers["parse"] = perf_counter() - started

    build_started = perf_counter()
    artifacts = build_all(parsed.to_list(), pipeline)
    timers["build"] = perf_counter() - build_started

    classical_started = perf_counter()
    classical = compute_classical_invariants(artifacts.link, artifacts.manifold)
    timers["classical"] = perf_counter() - classical_started

    hfk = None
    if pipeline.invariants.compute_hfk and ("analyze" in selected_modes or "unknotting_search" in selected_modes):
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
        write_json(prefix.with_name(prefix.name + "_analysis.json"), analysis_payload)

    unknotting_payload = None
    if "unknotting_search" in selected_modes:
        unknotting = search_unknotting_number_one(artifacts.normalization.normalized_pd, classical, hfk, pipeline)
        unknotting_payload = unknotting.to_dict()
        write_json(prefix.with_name(prefix.name + "_unknotting.json"), unknotting_payload)
        write_json(
            prefix.with_name(prefix.name + "_crossing_changes.json"),
            {"candidates": unknotting_payload["unknotting_changes"], "filter_stats": unknotting_payload["filter_stats"]},
        )

    render_diagram(artifacts.normalization.normalized_pd, prefix.with_name(prefix.name + "_diagram.png"))
    embedding = build_embedding(artifacts.normalization.normalized_pd, pipeline.viz)
    export_centerline_csv(embedding.centerline, prefix.with_name(prefix.name + "_centerline.csv"))
    preview_path = render_3d_preview(embedding.centerline, prefix, pipeline.viz)

    mesh_outputs = None
    if "export_mesh" in selected_modes:
        mesh_outputs = export_meshes(artifacts.normalization.normalized_pd, prefix)

    return {
        "analysis": analysis_payload,
        "unknotting": unknotting_payload,
        "preview_3d": str(preview_path),
        "mesh_outputs": mesh_outputs,
    }


def main() -> int:
    """Parse CLI arguments and execute the pipeline."""

    parser = build_parser()
    args = parser.parse_args()
    configure_logging(args.v or 0)
    modes: set[str] = set()
    if args.analyze or (not args.unknotting_search and not args.export_mesh):
        modes.add("analyze")
    if args.unknotting_search:
        modes.add("unknotting_search")
    if args.export_mesh:
        modes.add("export_mesh")

    pd_input: str | Path = args.pd if args.pd is not None else Path(args.pd_file)
    LOGGER.info("Running pipeline with modes=%s", sorted(modes))
    run_pipeline(pd_input, args.out, PipelineConfig(), modes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
