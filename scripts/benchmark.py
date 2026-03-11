"""Simple benchmark runner for the bundled examples."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter

from main import run_pipeline


EXAMPLES = [
    Path("examples/trefoil.json"),
    Path("examples/figure_eight.json"),
    Path("examples/cinquefoil.json"),
    Path("examples/reference_11c.json"),
]


def main() -> int:
    for example in EXAMPLES:
        started = perf_counter()
        run_pipeline(example, Path("out") / example.stem, modes={"analyze"})
        elapsed = perf_counter() - started
        print(f"{example.name}: {elapsed:.3f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
