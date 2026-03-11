"""Knot Floer homology wrapper with timeout support."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import asdict, dataclass
from typing import Any

import knot_floer_homology


@dataclass(frozen=True)
class HFKResult:
    """Structured result of a knot Floer homology computation."""

    available: bool
    tau: int | None
    epsilon: int | None
    seifert_genus: int | None
    total_rank: int | None
    ranks: dict[str, int]
    timed_out: bool = False
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert the result to a serializable dictionary."""

        return asdict(self)


def _normalize_ranks(ranks: dict[tuple[int, int], int] | None) -> dict[str, int]:
    """Stringify the bigrading keys."""

    if not ranks:
        return {}
    return {f"{key[0]},{key[1]}": int(value) for key, value in ranks.items()}


def discover_hfk_api() -> dict[str, list[str]]:
    """Expose the runtime HFK module surface."""

    public_names = [name for name in dir(knot_floer_homology) if not name.startswith("_")]
    return {
        "public_names": public_names,
        "callables": [name for name in public_names if callable(getattr(knot_floer_homology, name))],
    }


def compute_hfk(pd_code: list[list[int]], timeout: float = 60.0) -> HFKResult:
    """Compute HFK data from a PD code using the runtime-discovered API."""

    if not pd_code:
        return HFKResult(
            available=True,
            tau=0,
            epsilon=0,
            seifert_genus=0,
            total_rank=1,
            ranks={"0,0": 1},
        )

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(knot_floer_homology.pd_to_hfk, pd_code)
        try:
            result = future.result(timeout=timeout)
        except FutureTimeoutError:
            future.cancel()
            return HFKResult(
                available=False,
                tau=None,
                epsilon=None,
                seifert_genus=None,
                total_rank=None,
                ranks={},
                timed_out=True,
                error=f"HFK computation exceeded {timeout:.1f} seconds",
            )
        except Exception as exc:
            return HFKResult(
                available=False,
                tau=None,
                epsilon=None,
                seifert_genus=None,
                total_rank=None,
                ranks={},
                error=str(exc),
            )

    return HFKResult(
        available=True,
        tau=result.get("tau"),
        epsilon=result.get("epsilon"),
        seifert_genus=result.get("seifert_genus"),
        total_rank=result.get("total_rank"),
        ranks=_normalize_ranks(result.get("ranks")),
    )
