"""Classical invariant computations."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import snappy  # noqa: F401  # Required by Spherogram/SnapPy bridge.
import sympy as sp
from spherogram import Link

from src.utils import abs_dt_key, canonicalize_alexander_polynomial, polynomial_to_string, signature_from_symmetric, stable_float


@dataclass(frozen=True)
class FundamentalGroupSummary:
    """A JSON-friendly summary of a SnapPy fundamental group."""

    generators: list[str]
    relators: list[str]
    num_generators: int
    num_relators: int


@dataclass(frozen=True)
class InvariantReport:
    """Classical knot invariant summary."""

    crossing_number: int
    writhe: int
    num_components: int
    alexander_polynomial: str
    signature: int
    determinant: int
    hyperbolic_volume: float
    knot_id: str | None
    manifold_identifications: list[str]
    fundamental_group: FundamentalGroupSummary

    def to_dict(self) -> dict[str, Any]:
        """Convert the report to a serializable dictionary."""

        return asdict(self)


def _dt_name_lookup() -> dict[tuple[tuple[int, ...], ...], str]:
    """Return a small absolute-DT lookup table for low-crossing named examples."""

    lookup: dict[tuple[tuple[int, ...], ...], str] = {}
    for name in ("3_1", "4_1", "5_1", "5_2"):
        link = Link(name)
        lookup[abs_dt_key(link.DT_code())] = name
    return lookup


_KNOWN_DT_NAMES = _dt_name_lookup()


def _identify_name(link: Link, manifold: snappy.Manifold) -> tuple[str | None, list[str]]:
    """Infer a human-readable knot name from DT code or SnapPy identify()."""

    dt_key = abs_dt_key(link.DT_code())
    if dt_key in _KNOWN_DT_NAMES:
        try:
            manifold_idents = [str(item) for item in manifold.identify()]
        except Exception:
            manifold_idents = []
        return _KNOWN_DT_NAMES[dt_key], manifold_idents

    try:
        manifold_idents = [str(item) for item in manifold.identify()]
    except Exception:
        manifold_idents = []

    for item in manifold_idents:
        bare = item.split("(")[0]
        if "_" in bare or bare.startswith("K"):
            return bare, manifold_idents
    return None, manifold_idents


def _seifert_matrix(link: Link) -> sp.Matrix:
    """Return the Seifert matrix as a SymPy matrix."""

    matrix = link.seifert_matrix()
    return sp.Matrix(matrix)


def compute_classical_invariants(link: Link, manifold: snappy.Manifold) -> InvariantReport:
    """Compute classical invariants using Spherogram matrices and SnapPy geometry."""

    group = manifold.fundamental_group()
    if len(link.crossings) == 0:
        knot_id, manifold_idents = "0_1", [str(item) for item in manifold.identify()]
        return InvariantReport(
            crossing_number=0,
            writhe=0,
            num_components=1,
            alexander_polynomial="1",
            signature=0,
            determinant=1,
            hyperbolic_volume=0.0,
            knot_id=knot_id,
            manifold_identifications=manifold_idents,
            fundamental_group=FundamentalGroupSummary(
                generators=list(group.generators()),
                relators=list(group.relators()),
                num_generators=int(group.num_generators()),
                num_relators=int(group.num_relators()),
            ),
        )

    seifert = _seifert_matrix(link)
    t = sp.symbols("t")
    alex_expr = canonicalize_alexander_polynomial((seifert - t * seifert.T).det())
    determinant = abs(int(sp.expand(alex_expr).subs(t, -1)))
    signature = signature_from_symmetric(seifert + seifert.T)
    knot_id, manifold_idents = _identify_name(link, manifold)
    return InvariantReport(
        crossing_number=len(link.crossings),
        writhe=int(link.writhe()),
        num_components=len(link.link_components),
        alexander_polynomial=polynomial_to_string(alex_expr),
        signature=int(signature),
        determinant=int(determinant),
        hyperbolic_volume=stable_float(manifold.volume()),
        knot_id=knot_id,
        manifold_identifications=manifold_idents,
        fundamental_group=FundamentalGroupSummary(
            generators=list(group.generators()),
            relators=list(group.relators()),
            num_generators=int(group.num_generators()),
            num_relators=int(group.num_relators()),
        ),
    )


def quick_classical_invariants(link: Link, manifold: snappy.Manifold) -> dict[str, Any]:
    """Compute the subset of invariants used in filtering and tests."""

    report = compute_classical_invariants(link, manifold)
    return {
        "determinant": report.determinant,
        "alexander_polynomial": report.alexander_polynomial,
        "signature": report.signature,
        "hyperbolic_volume": report.hyperbolic_volume,
        "knot_id": report.knot_id,
    }
