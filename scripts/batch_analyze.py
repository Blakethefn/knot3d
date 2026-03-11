"""Batch-analyze all example JSON files."""

from __future__ import annotations

from pathlib import Path

from main import run_pipeline


def main() -> int:
    for example in sorted(Path("examples").glob("*.json")):
        if example.name == "notebook_demo.ipynb":
            continue
        output_prefix = Path("out") / example.stem
        run_pipeline(example, output_prefix, modes={"analyze"})
        print(f"processed {example}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
