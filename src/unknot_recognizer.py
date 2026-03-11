"""Pragmatic unknot recognition using invariants, simplification, and SnapPy groups."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from src.config import SearchConfig
from src.hfk_engine import HFKResult
from src.invariants import InvariantReport
from src.knot_builder import build_all


@dataclass(frozen=True)
class RecognitionResult:
    """Outcome of an unknot recognition attempt."""

    is_unknot: bool
    confidence: str
    method: str
    reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert the result to a dictionary."""

        return asdict(self)


def quick_filter(classical: InvariantReport, hfk: HFKResult | None) -> RecognitionResult:
    """Cheap necessary conditions for the unknot."""

    reasons: list[str] = []
    if classical.determinant != 1:
        reasons.append(f"determinant = {classical.determinant} != 1")
    if classical.alexander_polynomial != "1":
        reasons.append(f"Alexander polynomial = {classical.alexander_polynomial} != 1")
    if classical.signature != 0:
        reasons.append(f"signature = {classical.signature} != 0")
    if hfk is not None and hfk.available:
        if hfk.tau not in (None, 0):
            reasons.append(f"tau = {hfk.tau} != 0")
        if hfk.epsilon not in (None, 0):
            reasons.append(f"epsilon = {hfk.epsilon} != 0")
        if hfk.seifert_genus not in (None, 0):
            reasons.append(f"Seifert genus = {hfk.seifert_genus} != 0")
        if hfk.total_rank not in (None, 1):
            reasons.append(f"HFK total rank = {hfk.total_rank} != 1")
        normalized_ranks = hfk.ranks or {}
        if normalized_ranks and normalized_ranks != {"0,0": 1}:
            reasons.append(f"HFK ranks = {normalized_ranks} != {{'0,0': 1}}")

    if reasons:
        return RecognitionResult(
            is_unknot=False,
            confidence="high",
            method="fast_filter",
            reasons=reasons,
        )
    return RecognitionResult(
        is_unknot=False,
        confidence="undetermined",
        method="fast_filter_pass",
        reasons=["All fast obstructions vanished."],
    )


def recognize_unknot(
    pd_code: list[list[int]],
    classical: InvariantReport | None = None,
    hfk: HFKResult | None = None,
    search_config: SearchConfig | None = None,
) -> RecognitionResult:
    """Recognize the unknot using simplification and fundamental-group data."""

    if not pd_code:
        return RecognitionResult(
            is_unknot=True,
            confidence="high",
            method="empty_pd",
            reasons=["The empty PD code is the unknot."],
        )

    if classical is not None:
        filtered = quick_filter(classical, hfk)
        if filtered.method == "fast_filter" and not filtered.is_unknot:
            return filtered

    artifacts = build_all(pd_code)
    link = artifacts.link.copy()
    settings = search_config or SearchConfig()

    for _ in range(settings.simplify_rounds):
        changed = link.simplify()
        if len(link.crossings) == 0:
            return RecognitionResult(
                is_unknot=True,
                confidence="high",
                method="simplify_to_empty",
                reasons=["Spherogram simplification reduced the diagram to zero crossings."],
            )
        if not changed:
            break

    manifold = link.exterior()
    group = manifold.fundamental_group()
    if str(manifold.homology()) == "Z" and int(group.num_generators()) == 1 and int(group.num_relators()) == 0:
        return RecognitionResult(
            is_unknot=True,
            confidence="high",
            method="fundamental_group_Z",
            reasons=["The complement group is infinite cyclic and homology is Z."],
        )

    return RecognitionResult(
        is_unknot=False,
        confidence="high",
        method="group_nontrivial",
        reasons=[
            f"Group generators: {list(group.generators())}",
            f"Group relators: {list(group.relators())}",
        ],
    )
