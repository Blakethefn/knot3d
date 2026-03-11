"""Crossing-change enumeration and application."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations
from typing import Any

import snappy  # noqa: F401  # Needed by Spherogram rebuild/exterior paths.
from spherogram import Link


@dataclass(frozen=True)
class CrossingChangeCandidate:
    """A PD code produced by changing one or more crossings."""

    crossing_indices: tuple[int, ...]
    pd_code: list[list[int]]

    def to_dict(self) -> dict[str, Any]:
        """Convert the candidate to a dictionary."""

        return asdict(self)


def _labeled_copy(pd_code: list[list[int]]) -> Link:
    """Build a copyable link whose crossings carry stable integer labels."""

    link = Link(pd_code)
    for index, crossing in enumerate(link.crossings):
        crossing.label = index
    return link


def apply_crossing_changes(pd_code: list[list[int]], crossing_indices: tuple[int, ...]) -> list[list[int]]:
    """Apply crossing changes to the selected crossings and return a rebuilt PD code."""

    link = _labeled_copy(pd_code).copy()
    label_to_crossing = {int(crossing.label): crossing for crossing in link.crossings}

    for index in crossing_indices:
        label_to_crossing[index].rotate_by_90()
        link._rebuild()
        label_to_crossing = {int(crossing.label): crossing for crossing in link.crossings}

    return [list(crossing) for crossing in link.PD_code(min_strand_index=1)]


def enumerate_single_crossing_changes(pd_code: list[list[int]]) -> list[CrossingChangeCandidate]:
    """Enumerate all single crossing changes."""

    return [
        CrossingChangeCandidate((index,), apply_crossing_changes(pd_code, (index,)))
        for index in range(len(pd_code))
    ]


def enumerate_double_crossing_changes(pd_code: list[list[int]]) -> list[CrossingChangeCandidate]:
    """Enumerate all double crossing changes."""

    return [
        CrossingChangeCandidate(pair, apply_crossing_changes(pd_code, pair))
        for pair in combinations(range(len(pd_code)), 2)
    ]


def verify_crossing_change_operator() -> bool:
    """Verify that a single crossing change can unknot the native trefoil."""

    native_trefoil = [[6, 3, 1, 4], [4, 1, 5, 2], [2, 5, 3, 6]]
    for candidate in enumerate_single_crossing_changes(native_trefoil):
        link = Link(candidate.pd_code)
        if link.simplify() and len(link.crossings) == 0:
            return True
    return False
