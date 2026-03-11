"""CLI entry point for the knot engine."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.config import PipelineConfig
from src.logging_setup import configure_logging
from src.services.engine_facade import execute_pipeline

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

    return execute_pipeline(pd_input, output_prefix, config or PipelineConfig(), modes)


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
