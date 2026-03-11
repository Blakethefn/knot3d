"""Runtime API discovery helpers for the installed knot packages."""

from __future__ import annotations

import inspect
from dataclasses import dataclass

import knot_floer_homology
import pyvista as pv
import snappy
from spherogram import Link


@dataclass(frozen=True)
class DiscoveryReport:
    """A markdown-friendly summary of the runtime APIs."""

    markdown: str


def build_discovery_markdown() -> DiscoveryReport:
    """Discover the runtime API surfaces needed by the project."""

    trefoil = [[1, 5, 2, 4], [3, 1, 4, 6], [5, 3, 6, 2]]
    link = Link(trefoil)
    manifold = link.exterior()
    public_hfk = [name for name in dir(knot_floer_homology) if not name.startswith("_")]
    plotter = pv.Plotter(off_screen=True)
    export_methods = [name for name in dir(plotter) if "export" in name.lower() or "html" in name.lower()]
    plotter.close()

    lines = [
        "# Runtime API Discovery",
        "",
        f"- SnapPy version: `{snappy.version()}`",
        f"- `spherogram.Link` signature: `{inspect.signature(Link)}`",
        "- `Link(pd_code=...)` does not work in this venv; use `Link(pd)`.",
        f"- Trefoil DT code: `{link.DT_code()}`",
        f"- Trefoil writhe: `{link.writhe()}`",
        f"- Trefoil HFK via `Link.knot_floer_homology()`: `{link.knot_floer_homology()}`",
        f"- Manifold volume: `{manifold.volume()}`",
        f"- Manifold identify: `{manifold.identify()}`",
        f"- HFK public names: `{public_hfk}`",
        f"- PyVista export/html methods: `{export_methods}`",
    ]
    return DiscoveryReport(markdown="\n".join(lines))
