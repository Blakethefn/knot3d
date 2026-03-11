"""Build Spherogram and SnapPy objects from normalized PD codes."""

from __future__ import annotations

from dataclasses import dataclass

import snappy  # noqa: F401  # Required by Spherogram's exterior() bridge.
from spherogram import Link

from src.config import PipelineConfig
from src.pd_conventions import PDNormalizationResult, normalize_pd_code


class KnotBuildError(RuntimeError):
    """Raised when a knot object cannot be built."""


@dataclass(frozen=True)
class BuildArtifacts:
    """Built knot objects and metadata."""

    normalization: PDNormalizationResult
    link: Link
    manifold: snappy.Manifold


def build_link(pd_code: list[list[int]]) -> Link:
    """Build a Spherogram link from a normalized PD code."""

    try:
        return Link(pd_code)
    except Exception as exc:
        raise KnotBuildError(f"Could not build Link from PD code: {exc}") from exc


def build_all(pd_code: list[list[int]], config: PipelineConfig | None = None) -> BuildArtifacts:
    """Normalize a PD code, then build the Spherogram link and its exterior."""

    pipeline = config or PipelineConfig()
    normalization = normalize_pd_code(pd_code, pipeline.pd, pipeline.search)
    link = build_link(normalization.normalized_pd)
    if len(link.link_components) != 1:
        raise KnotBuildError("Only single-component knots are supported")

    try:
        manifold = link.exterior()
    except Exception as exc:
        raise KnotBuildError(f"Could not build knot exterior: {exc}") from exc

    return BuildArtifacts(normalization=normalization, link=link, manifold=manifold)
