"""Application entry point for the knot workbench and CLI pipeline."""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

LOGGER = logging.getLogger(__name__)


def _repo_python() -> Path | None:
    root = Path(__file__).resolve().parent
    candidates = (
        root / ".venv" / "Scripts" / "python.exe",
        root / ".venv" / "bin" / "python",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _bootstrap_repo_environment() -> None:
    if os.environ.get("KNOT3D_BOOTSTRAPPED") == "1":
        return
    try:
        import PySide6  # noqa: F401
        import spherogram  # noqa: F401
    except ImportError:
        repo_python = _repo_python()
        if repo_python is None:
            return
        if Path(sys.executable).resolve() == repo_python.resolve():
            return
        env = os.environ.copy()
        env["KNOT3D_BOOTSTRAPPED"] = "1"
        raise SystemExit(subprocess.call([str(repo_python), __file__, *sys.argv[1:]], env=env))


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
    config=None,
    modes: set[str] | None = None,
) -> dict[str, object]:
    """Run the analysis pipeline and return a serializable summary."""

    from src.config import PipelineConfig
    from src.services.engine_facade import execute_pipeline

    return execute_pipeline(pd_input, output_prefix, config or PipelineConfig(), modes)


def _run_cli(argv: list[str]) -> int:
    from src.config import PipelineConfig
    from src.logging_setup import configure_logging

    parser = build_parser()
    args = parser.parse_args(argv)
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


def _run_gui() -> int:
    from src.gui.app import run

    return run()


def main(argv: list[str] | None = None) -> int:
    """Launch the GUI by default, or the CLI when pipeline flags are present."""

    _bootstrap_repo_environment()
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        return _run_gui()
    return _run_cli(argv)


if __name__ == "__main__":
    raise SystemExit(main())
