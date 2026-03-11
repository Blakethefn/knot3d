"""Shared utility helpers."""

from __future__ import annotations

import json
import math
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Iterable

import numpy as np
import sympy as sp


def ensure_parent_dir(path: str | Path) -> Path:
    """Create the parent directory for a file path if needed."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def ensure_dir(path: str | Path) -> Path:
    """Create a directory if it does not already exist."""

    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    return target


def canonical_pd_key(pd_code: Iterable[Iterable[int]]) -> tuple[tuple[int, ...], ...]:
    """Return a hashable key for a PD code."""

    return tuple(tuple(int(v) for v in crossing) for crossing in pd_code)


def abs_dt_key(dt_code: Iterable[Iterable[int]]) -> tuple[tuple[int, ...], ...]:
    """Normalize a DT code by discarding signs."""

    return tuple(tuple(abs(int(v)) for v in component) for component in dt_code)


def canonicalize_alexander_polynomial(poly: sp.Expr | int) -> sp.Expr:
    """Normalize an Alexander polynomial up to multiplication by ±t^k."""

    t = sp.symbols("t")
    expr = sp.expand(sp.sympify(poly))
    if expr == 0:
        return sp.Integer(0)
    if expr.is_number:
        return sp.Integer(1 if int(expr) >= 0 else -1)

    poly_obj = sp.Poly(expr, t)
    degrees = [monomial[0] for monomial in poly_obj.monoms()]
    min_degree = min(degrees) if degrees else 0
    normalized = sp.expand(expr / (t**min_degree))
    lead_coeff = sp.Poly(normalized, t).LC()
    if lead_coeff < 0:
        normalized = -normalized
    return sp.expand(normalized)


def polynomial_to_string(poly: sp.Expr | int) -> str:
    """Serialize a polynomial expression to a stable string."""

    return str(sp.expand(sp.sympify(poly)))


def signature_from_symmetric(matrix: sp.Matrix | list[list[int]]) -> int:
    """Compute the signature of a symmetric matrix numerically."""

    if isinstance(matrix, sp.MatrixBase):
        array = np.asarray(matrix.tolist(), dtype=np.float64)
    else:
        array = np.asarray(matrix, dtype=np.float64)
    if array.size == 0:
        return 0
    eigenvalues = np.linalg.eigvalsh(array)
    tol = 1e-8
    positives = int(np.sum(eigenvalues > tol))
    negatives = int(np.sum(eigenvalues < -tol))
    return positives - negatives


def stable_float(value: Any, tol: float = 1e-9) -> float:
    """Convert an object to float and clamp near-zero noise."""

    numeric = float(value)
    if abs(numeric) < tol:
        return 0.0
    return numeric


def as_jsonable(value: Any) -> Any:
    """Convert rich objects to JSON-friendly values."""

    if isinstance(value, Path):
        return str(value)
    if isinstance(value, tuple):
        return [as_jsonable(v) for v in value]
    if isinstance(value, list):
        return [as_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    return value


def write_json(path: str | Path, payload: Any) -> None:
    """Write JSON with stable formatting."""

    target = ensure_parent_dir(path)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(as_jsonable(payload), handle, indent=2, sort_keys=True)
        handle.write("\n")


@contextmanager
def timer() -> Generator[dict[str, float], None, None]:
    """Measure wall-clock duration with a mutable result dictionary."""

    payload: dict[str, float] = {"seconds": 0.0}
    start = time.perf_counter()
    try:
        yield payload
    finally:
        payload["seconds"] = time.perf_counter() - start


def gcd_pair(a: int, b: int) -> int:
    """Return the gcd of two integers."""

    return math.gcd(a, b)
