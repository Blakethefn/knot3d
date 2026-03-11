"""Warm-up solver: return True iff the given PD code is the unknot."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

from src.hfk_engine import compute_hfk
from src.invariants import compute_classical_invariants
from src.knot_builder import build_all
from src.unknot_recognizer import recognize_unknot
from src.pd_parser import parse_pd_input


def is_unknot_pd(pd_input: str | Path | list[list[int]]) -> bool:
    """Return True iff the input PD code represents the unknot."""

    parsed = parse_pd_input(pd_input)
    artifacts = build_all(parsed.to_list())
    classical = compute_classical_invariants(artifacts.link, artifacts.manifold)
    hfk = compute_hfk(artifacts.normalization.normalized_pd, timeout=30.0)
    result = recognize_unknot(artifacts.normalization.normalized_pd, classical, hfk)
    return result.is_unknot


def main() -> int:
    """Parse a PD code and print whether it is the unknot."""

    parser = argparse.ArgumentParser(description="Return True iff a PD code is the unknot")
    parser.add_argument("pd", help="PD code literal or file path")
    args = parser.parse_args()
    answer = is_unknot_pd(args.pd)
    print("True" if answer else "False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
