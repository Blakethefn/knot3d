"""Unknot-status recognition reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from time import perf_counter
from typing import Any

from src.config import PipelineConfig
from src.hfk_engine import HFKResult
from src.invariants import InvariantReport
from src.unknot_recognizer import RecognitionResult, quick_filter, recognize_unknot


@dataclass(frozen=True)
class FilterStats:
    """How the unknot-status decision was reached."""

    rejected_by_invariants: int = 0
    proven_unknot: int = 0
    rejected_after_full_check: int = 0


@dataclass(frozen=True)
class CandidateSummary:
    """Single recognition record shown in the GUI inspection table."""

    candidate_index: int
    crossing_indices: list[int]
    determinant: int | None
    alexander_polynomial: str | None
    tau: int | None
    seifert_genus: int | None
    full_check_status: str
    is_unknot: bool | None
    elapsed_time: float
    knot_name: str | None = None
    recognition_method: str | None = None
    notes: list[str] = field(default_factory=list)
    modified_pd: list[list[int]] = field(default_factory=list)


@dataclass(frozen=True)
class UnknottingReport:
    """Summary of whether the input diagram is the unknot."""

    knot_name: str | None
    original_crossing_number: int
    obstruction_lower_bound: int
    obstruction_details: list[str]
    search_depth: int
    total_candidates: int
    filter_stats: dict[str, int]
    candidate_summaries: list[dict[str, Any]]
    unknotting_changes: list[dict[str, Any]]
    upper_bound: int | None
    is_unknot: bool
    recognition_method: str
    conclusion: str
    total_time: float

    def to_dict(self) -> dict[str, Any]:
        """Convert the report to a dictionary."""

        return asdict(self)


def _candidate_summary(
    normalized_pd: list[list[int]],
    classical: InvariantReport,
    hfk: HFKResult | None,
    recognition: RecognitionResult,
    elapsed: float,
) -> CandidateSummary:
    return CandidateSummary(
        candidate_index=0,
        crossing_indices=[],
        determinant=classical.determinant,
        alexander_polynomial=classical.alexander_polynomial,
        tau=None if hfk is None else hfk.tau,
        seifert_genus=None if hfk is None else hfk.seifert_genus,
        full_check_status=recognition.method,
        is_unknot=recognition.is_unknot,
        elapsed_time=elapsed,
        knot_name=classical.knot_id,
        recognition_method=recognition.method,
        notes=list(recognition.reasons),
        modified_pd=normalized_pd,
    )


def search_unknotting_number_one(
    normalized_pd: list[list[int]],
    classical: InvariantReport,
    hfk: HFKResult | None,
    config: PipelineConfig | None = None,
) -> UnknottingReport:
    """Decide whether the current diagram is the unknot."""

    pipeline = config or PipelineConfig()
    start = perf_counter()

    if classical.crossing_number == 0:
        recognition = RecognitionResult(
            is_unknot=True,
            confidence="high",
            method="empty_pd",
            reasons=["The empty PD code is the unknot."],
        )
        elapsed = perf_counter() - start
        return UnknottingReport(
            knot_name=classical.knot_id,
            original_crossing_number=0,
            obstruction_lower_bound=0,
            obstruction_details=[],
            search_depth=0,
            total_candidates=1,
            filter_stats=asdict(FilterStats(proven_unknot=1)),
            candidate_summaries=[asdict(_candidate_summary(normalized_pd, classical, hfk, recognition, elapsed))],
            unknotting_changes=[],
            upper_bound=0,
            is_unknot=True,
            recognition_method=recognition.method,
            conclusion="Recognized as the unknot; u(K)=0.",
            total_time=elapsed,
        )

    filtered = quick_filter(classical, hfk)
    if filtered.method == "fast_filter":
        elapsed = perf_counter() - start
        return UnknottingReport(
            knot_name=classical.knot_id,
            original_crossing_number=classical.crossing_number,
            obstruction_lower_bound=1,
            obstruction_details=list(filtered.reasons),
            search_depth=0,
            total_candidates=1,
            filter_stats=asdict(FilterStats(rejected_by_invariants=1)),
            candidate_summaries=[asdict(_candidate_summary(normalized_pd, classical, hfk, filtered, elapsed))],
            unknotting_changes=[],
            upper_bound=None,
            is_unknot=False,
            recognition_method=filtered.method,
            conclusion="Rejected u(K)=0 by a nontrivial invariant.",
            total_time=elapsed,
        )

    recognition = recognize_unknot(normalized_pd, classical, hfk, pipeline.search)
    elapsed = perf_counter() - start
    if recognition.is_unknot:
        stats = FilterStats(proven_unknot=1)
        obstruction_lower_bound = 0
        obstruction_details: list[str] = []
        upper_bound: int | None = 0
        conclusion = "Recognized as the unknot; u(K)=0."
    else:
        stats = FilterStats(rejected_after_full_check=1)
        obstruction_lower_bound = 1
        obstruction_details = list(recognition.reasons)
        upper_bound = None
        conclusion = "Rejected u(K)=0 after full unknot recognition checks."

    return UnknottingReport(
        knot_name=classical.knot_id,
        original_crossing_number=classical.crossing_number,
        obstruction_lower_bound=obstruction_lower_bound,
        obstruction_details=obstruction_details,
        search_depth=0,
        total_candidates=1,
        filter_stats=asdict(stats),
        candidate_summaries=[asdict(_candidate_summary(normalized_pd, classical, hfk, recognition, elapsed))],
        unknotting_changes=[],
        upper_bound=upper_bound,
        is_unknot=recognition.is_unknot,
        recognition_method=recognition.method,
        conclusion=conclusion,
        total_time=elapsed,
    )
