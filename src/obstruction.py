"""Invariant-based lower bounds for unknotting number."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from src.hfk_engine import HFKResult
from src.invariants import InvariantReport


@dataclass(frozen=True)
class ObstructionReport:
    """Combined lower-bound summary."""

    signature_bound: int
    tau_bound: int
    lower_bound: int
    details: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert the report to a dictionary."""

        return asdict(self)


def compute_unknotting_obstruction(classical: InvariantReport, hfk: HFKResult | None) -> ObstructionReport:
    """Compute standard signature and tau lower bounds."""

    signature_bound = abs(classical.signature) // 2
    details = [f"|sigma| / 2 = {signature_bound}"]

    tau_bound = 0
    if hfk is not None and hfk.available and hfk.tau is not None:
        tau_bound = abs(hfk.tau)
        details.append(f"|tau| = {tau_bound}")
    else:
        details.append("|tau| unavailable")

    return ObstructionReport(
        signature_bound=signature_bound,
        tau_bound=tau_bound,
        lower_bound=max(signature_bound, tau_bound),
        details=details,
    )
