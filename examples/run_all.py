"""Run the full pipeline for every bundled example."""

from __future__ import annotations

from pathlib import Path

from main import run_pipeline


def main() -> int:
    for example in sorted(Path("examples").glob("*.json")):
        output = Path("out") / example.stem
        run_pipeline(example, output, modes={"analyze", "unknotting_search"})
        print(f"completed {example.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
