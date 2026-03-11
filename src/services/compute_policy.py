"""Compute backend preferences and runtime limits."""

from __future__ import annotations

import math
import os
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from typing import Any, Iterator, Literal

from threadpoolctl import threadpool_limits

BackendPreference = Literal["auto", "cpu", "gpu"]
ResolvedBackend = Literal["cpu", "gpu"]

_THREAD_ENV_KEYS = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "BLIS_NUM_THREADS",
)


def _clamp_usage(value: int) -> int:
    return max(1, min(100, int(value)))


@dataclass(frozen=True)
class ComputePreferences:
    """User-selected compute preferences."""

    backend: BackendPreference = "auto"
    cpu_max_usage_percent: int = 100
    gpu_max_usage_percent: int = 100

    @classmethod
    def from_values(
        cls,
        *,
        backend: str = "auto",
        cpu_max_usage_percent: int = 100,
        gpu_max_usage_percent: int = 100,
    ) -> "ComputePreferences":
        normalized_backend = backend if backend in {"auto", "cpu", "gpu"} else "auto"
        return cls(
            backend=normalized_backend,
            cpu_max_usage_percent=_clamp_usage(cpu_max_usage_percent),
            gpu_max_usage_percent=_clamp_usage(gpu_max_usage_percent),
        )


@dataclass(frozen=True)
class ComputeRuntime:
    """Resolved runtime policy derived from user preferences."""

    requested_backend: BackendPreference
    active_backend: ResolvedBackend
    cpu_max_usage_percent: int
    cpu_thread_limit: int
    logical_cpu_count: int
    gpu_max_usage_percent: int
    gpu_available: bool
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""

        return asdict(self)

    def summary(self) -> str:
        """Return a compact human-readable description."""

        base = (
            f"{self.active_backend.upper()} | "
            f"CPU {self.cpu_max_usage_percent}% ({self.cpu_thread_limit}/{self.logical_cpu_count} threads)"
        )
        if self.requested_backend == "gpu" and not self.gpu_available:
            return f"{base} | GPU requested, using CPU fallback"
        if self.active_backend == "gpu":
            return f"{base} | GPU {self.gpu_max_usage_percent}%"
        return base


def resolve_compute_runtime(preferences: ComputePreferences) -> ComputeRuntime:
    """Resolve a concrete runtime policy from persisted preferences."""

    logical_cpu_count = max(1, os.cpu_count() or 1)
    cpu_thread_limit = max(1, math.ceil(logical_cpu_count * (preferences.cpu_max_usage_percent / 100.0)))
    gpu_available = False
    notes: list[str] = []

    active_backend: ResolvedBackend = "cpu"
    if preferences.backend == "gpu":
        notes.append(
            "GPU compute was requested, but the current engine stack is CPU-only. "
            "Runs will execute on the CPU."
        )
    elif preferences.backend == "auto":
        notes.append("Auto backend resolved to CPU for the current engine stack.")

    if preferences.cpu_max_usage_percent < 100:
        notes.append(
            f"CPU usage is capped to {cpu_thread_limit} logical thread(s) out of {logical_cpu_count}."
        )

    return ComputeRuntime(
        requested_backend=preferences.backend,
        active_backend=active_backend,
        cpu_max_usage_percent=preferences.cpu_max_usage_percent,
        cpu_thread_limit=cpu_thread_limit,
        logical_cpu_count=logical_cpu_count,
        gpu_max_usage_percent=preferences.gpu_max_usage_percent,
        gpu_available=gpu_available,
        notes=tuple(notes),
    )


@contextmanager
def apply_compute_runtime(runtime: ComputeRuntime) -> Iterator[None]:
    """Apply the resolved runtime policy for the duration of a compute task."""

    previous_values = {key: os.environ.get(key) for key in _THREAD_ENV_KEYS}
    limit = str(runtime.cpu_thread_limit)
    for key in _THREAD_ENV_KEYS:
        os.environ[key] = limit
    try:
        with threadpool_limits(limits=runtime.cpu_thread_limit):
            yield
    finally:
        for key, value in previous_values.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
