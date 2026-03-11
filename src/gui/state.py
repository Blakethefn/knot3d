"""Typed GUI state models."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SessionState:
    """Serializable workbench session state."""

    pd_text: str = ""
    pd_code: list[list[int]] = field(default_factory=list)
    normalized_pd: list[list[int]] = field(default_factory=list)
    validation_result: dict[str, Any] | None = None
    analysis_result: dict[str, Any] | None = None
    unknotting_result: dict[str, Any] | None = None
    crossing_changes_result: dict[str, Any] | None = None
    selected_crossing_index: int | None = None
    output_dir: Path | None = None
    session_path: Path | None = None
    analysis_result_path: Path | None = None
    unknotting_result_path: Path | None = None
    crossing_changes_result_path: Path | None = None
    selected_example: str | None = None
    camera_state: dict[str, list[float]] | None = None
    ui_state: dict[str, Any] = field(default_factory=dict)
    export_history: list[dict[str, Any]] = field(default_factory=list)
    dirty: bool = False

    def mark_clean(self, session_path: Path | None = None) -> None:
        """Reset the dirty flag after a save or load."""

        self.session_path = session_path or self.session_path
        self.dirty = False

    def mark_dirty(self) -> None:
        """Mark the session as modified."""

        self.dirty = True

    @property
    def has_results(self) -> bool:
        """Return whether any analysis payload is present."""

        return self.analysis_result is not None or self.unknotting_result is not None


@dataclass(frozen=True)
class RunRequest:
    """Typed job request passed to background workers."""

    mode: str
    pd_code: list[list[int]]
    output_prefix: str
    export_mesh: bool = False


@dataclass
class CandidateSelection:
    """Structured crossing-candidate selection state."""

    row_index: int | None = None
    crossing_indices: tuple[int, ...] = ()
    is_unknot: bool | None = None
