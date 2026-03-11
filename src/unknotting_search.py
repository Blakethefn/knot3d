"""Depth-limited unknotting search."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from time import perf_counter
from typing import Any

from src.config import PipelineConfig
from src.crossing_change import enumerate_single_crossing_changes
from src.hfk_engine import HFKResult, compute_hfk
from src.invariants import InvariantReport, compute_classical_invariants
from src.knot_builder import build_all
from src.obstruction import compute_unknotting_obstruction
from src.unknot_recognizer import recognize_unknot


@dataclass(frozen=True)
class FilterStats:
    """How many candidates were rejected at each search stage."""

    filtered_by_determinant: int = 0
    filtered_by_alexander: int = 0
    filtered_by_tau: int = 0
    reached_full_check: int = 0
    identified_as_unknot: int = 0


@dataclass(frozen=True)
class CrossingChangeOutcome:
    """Recognition summary for one candidate."""

    crossing_indices: list[int]
    is_unknot: bool
    confidence: str
    recognition_method: str
    computation_time: float
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CandidateSummary:
    """Detailed candidate metadata for GUI inspection and export."""

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
    """Full depth-1 unknotting search report."""

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
    conclusion: str
    total_time: float

    def to_dict(self) -> dict[str, Any]:
        """Convert the report to a dictionary."""

        return asdict(self)


def _increment(stats: FilterStats, **updates: int) -> FilterStats:
    values = asdict(stats)
    for key, value in updates.items():
        values[key] += value
    return FilterStats(**values)


def search_unknotting_number_one(
    normalized_pd: list[list[int]],
    classical: InvariantReport,
    hfk: HFKResult | None,
    config: PipelineConfig | None = None,
) -> UnknottingReport:
    """Search all single crossing changes for an unknotting move."""

    pipeline = config or PipelineConfig()
    start = perf_counter()
    obstruction = compute_unknotting_obstruction(classical, hfk)

    if classical.crossing_number == 0:
        return UnknottingReport(
            knot_name=classical.knot_id,
            original_crossing_number=0,
            obstruction_lower_bound=0,
            obstruction_details=["Already the unknot."],
            search_depth=0,
            total_candidates=0,
            filter_stats=asdict(FilterStats()),
            candidate_summaries=[],
            unknotting_changes=[],
            upper_bound=0,
            conclusion="Unknotting number = 0.",
            total_time=perf_counter() - start,
        )

    if obstruction.lower_bound > pipeline.search.max_depth:
        return UnknottingReport(
            knot_name=classical.knot_id,
            original_crossing_number=classical.crossing_number,
            obstruction_lower_bound=obstruction.lower_bound,
            obstruction_details=obstruction.details,
            search_depth=pipeline.search.max_depth,
            total_candidates=0,
            filter_stats=asdict(FilterStats()),
            candidate_summaries=[],
            unknotting_changes=[],
            upper_bound=None,
            conclusion=f"Unknotting number is at least {obstruction.lower_bound}; depth-1 search skipped.",
            total_time=perf_counter() - start,
        )

    candidates = enumerate_single_crossing_changes(normalized_pd)
    stats = FilterStats()
    outcomes: list[CrossingChangeOutcome] = []
    candidate_summaries: list[CandidateSummary] = []

    for candidate_index, candidate in enumerate(candidates):
        candidate_start = perf_counter()
        artifacts = build_all(candidate.pd_code, pipeline)
        candidate_classical = compute_classical_invariants(artifacts.link, artifacts.manifold)
        elapsed = perf_counter() - candidate_start
        summary = CandidateSummary(
            candidate_index=candidate_index,
            crossing_indices=list(candidate.crossing_indices),
            determinant=candidate_classical.determinant,
            alexander_polynomial=candidate_classical.alexander_polynomial,
            tau=None,
            seifert_genus=None,
            full_check_status="pending",
            is_unknot=None,
            elapsed_time=elapsed,
            knot_name=candidate_classical.knot_id,
            modified_pd=artifacts.normalization.normalized_pd,
        )

        if candidate_classical.determinant != 1:
            stats = _increment(stats, filtered_by_determinant=1)
            candidate_summaries.append(
                CandidateSummary(
                    **{
                        **asdict(summary),
                        "full_check_status": "filtered_determinant",
                        "is_unknot": False,
                        "notes": [f"determinant = {candidate_classical.determinant} != 1"],
                    }
                )
            )
            continue
        if candidate_classical.alexander_polynomial != "1":
            stats = _increment(stats, filtered_by_alexander=1)
            candidate_summaries.append(
                CandidateSummary(
                    **{
                        **asdict(summary),
                        "full_check_status": "filtered_alexander",
                        "is_unknot": False,
                        "notes": [f"Alexander polynomial = {candidate_classical.alexander_polynomial} != 1"],
                    }
                )
            )
            continue

        candidate_hfk = compute_hfk(candidate.pd_code, timeout=pipeline.invariants.hfk_timeout)
        elapsed = perf_counter() - candidate_start
        if candidate_hfk.available and (
            candidate_hfk.tau not in (None, 0) or candidate_hfk.seifert_genus not in (None, 0)
        ):
            stats = _increment(stats, filtered_by_tau=1)
            candidate_summaries.append(
                CandidateSummary(
                    **{
                        **asdict(summary),
                        "tau": candidate_hfk.tau,
                        "seifert_genus": candidate_hfk.seifert_genus,
                        "elapsed_time": elapsed,
                        "full_check_status": "filtered_tau",
                        "is_unknot": False,
                        "notes": [f"tau={candidate_hfk.tau}, genus={candidate_hfk.seifert_genus}"],
                    }
                )
            )
            continue

        stats = _increment(stats, reached_full_check=1)
        recognition = recognize_unknot(candidate.pd_code, candidate_classical, candidate_hfk, pipeline.search)
        summary_kwargs = {
            **asdict(summary),
            "tau": candidate_hfk.tau,
            "seifert_genus": candidate_hfk.seifert_genus,
            "elapsed_time": perf_counter() - candidate_start,
            "full_check_status": "full_check",
            "is_unknot": recognition.is_unknot,
            "recognition_method": recognition.method,
            "notes": recognition.reasons,
        }
        if recognition.is_unknot:
            stats = _increment(stats, identified_as_unknot=1)
            outcomes.append(
                CrossingChangeOutcome(
                    crossing_indices=list(candidate.crossing_indices),
                    is_unknot=True,
                    confidence=recognition.confidence,
                    recognition_method=recognition.method,
                    computation_time=perf_counter() - candidate_start,
                    notes=recognition.reasons,
                )
            )
            candidate_summaries.append(CandidateSummary(**summary_kwargs))
            continue

        candidate_summaries.append(CandidateSummary(**summary_kwargs))

    if outcomes:
        conclusion = f"Unknotting number = 1. Crossing {outcomes[0].crossing_indices[0]} unknots the diagram."
        upper_bound: int | None = 1
    else:
        conclusion = "No depth-1 unknotting crossing was found."
        upper_bound = None

    return UnknottingReport(
        knot_name=classical.knot_id,
        original_crossing_number=classical.crossing_number,
        obstruction_lower_bound=obstruction.lower_bound,
        obstruction_details=obstruction.details,
        search_depth=1,
        total_candidates=len(candidates),
        filter_stats=asdict(stats),
        candidate_summaries=[asdict(summary) for summary in candidate_summaries],
        unknotting_changes=[asdict(outcome) for outcome in outcomes],
        upper_bound=upper_bound,
        conclusion=conclusion,
        total_time=perf_counter() - start,
    )
