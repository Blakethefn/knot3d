"""PD code parsing and validation."""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


class PDParseError(ValueError):
    """Raised when a PD code cannot be parsed or validated."""


@dataclass(frozen=True)
class PDCode:
    """Structured PD code container."""

    crossings: list[list[int]]

    @property
    def crossing_count(self) -> int:
        """Return the number of crossings."""

        return len(self.crossings)

    @property
    def labels(self) -> list[int]:
        """Return the flattened strand labels."""

        return [label for crossing in self.crossings for label in crossing]

    @property
    def edge_count(self) -> int:
        """Return the number of strand labels on the diagram."""

        return 0 if not self.crossings else max(self.labels)

    def to_list(self) -> list[list[int]]:
        """Return a mutable copy."""

        return [list(crossing) for crossing in self.crossings]


def _coerce_crossings(payload: Any) -> list[list[int]]:
    """Convert a parsed payload into a normalized list-of-lists."""

    if payload == []:
        return []
    if not isinstance(payload, (list, tuple)):
        raise PDParseError("PD code must be a list of crossings")
    crossings: list[list[int]] = []
    for crossing in payload:
        if not isinstance(crossing, (list, tuple)):
            raise PDParseError("Each crossing must be a list or tuple")
        if len(crossing) != 4:
            raise PDParseError("Each crossing must have exactly four labels")
        try:
            values = [int(value) for value in crossing]
        except (TypeError, ValueError) as exc:
            raise PDParseError("Crossing labels must be integers") from exc
        crossings.append(values)
    return crossings


def validate_pd_code(crossings: Iterable[Iterable[int]]) -> list[list[int]]:
    """Validate a PD code and return it as a list of integer crossings."""

    pd_code = _coerce_crossings(list(crossings))
    if not pd_code:
        return []

    counts: dict[int, int] = {}
    for crossing in pd_code:
        if any(value <= 0 for value in crossing):
            raise PDParseError("PD labels must be positive integers")
        if len(set(crossing)) != 4:
            raise PDParseError("A crossing may not repeat a strand label")
        for value in crossing:
            counts[value] = counts.get(value, 0) + 1

    expected = set(range(1, max(counts) + 1))
    missing = sorted(expected - set(counts))
    if missing:
        raise PDParseError(f"Missing strand labels: {missing}")

    bad_counts = {label: count for label, count in counts.items() if count != 2}
    if bad_counts:
        raise PDParseError(f"Every strand label must appear exactly twice: {bad_counts}")

    return pd_code


def parse_pd_input(value: str | Path | list[list[int]] | tuple[tuple[int, ...], ...]) -> PDCode:
    """Parse a PD code from a string, path, or already-materialized list."""

    if isinstance(value, Path):
        payload = _read_path(value)
        return PDCode(validate_pd_code(payload))
    if isinstance(value, list):
        return PDCode(validate_pd_code(value))
    if isinstance(value, tuple):
        return PDCode(validate_pd_code([list(crossing) for crossing in value]))
    if not isinstance(value, str):
        raise PDParseError(f"Unsupported PD input type: {type(value)!r}")

    text = value.strip()
    candidate_path = Path(text)
    if candidate_path.exists():
        payload = _read_path(candidate_path)
        return PDCode(validate_pd_code(payload))

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        try:
            payload = ast.literal_eval(text)
        except (ValueError, SyntaxError) as exc:
            raise PDParseError("Could not parse PD code from string input") from exc
    return PDCode(validate_pd_code(payload))


def _read_path(path: Path) -> Any:
    """Read a PD payload from a text or JSON file."""

    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        payload = json.loads(text)
        if isinstance(payload, dict) and "pd_code" in payload:
            return payload["pd_code"]
        return payload
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return ast.literal_eval(text)
