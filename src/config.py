\\\Configuration dataclasses for the knot pipeline.\\\

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class PDConfig:
 \\\PD code parsing and convention configuration.\\\

 index_base: int = 1
 validate_strict: bool = True
 input_convention: Literal[\knotinfo\, \spherogram\, \auto\] = \auto\


@dataclass(frozen=True)
class InvariantConfig:
 \\\Invariant computation toggles and limits.\\\

 compute_alexander: bool = True
 compute_signature: bool = True
 compute_determinant: bool = True
 compute_crossing_number: bool = True
 compute_writhe: bool = True
 compute_hyperbolic_volume: bool = True
 compute_fundamental_group: bool = True
 compute_hfk: bool = True
 compute_tau: bool = True
 compute_epsilon: bool = True
 compute_seifert_genus: bool = True
 hfk_timeout: float = 60.0


@dataclass(frozen=True)
class SearchConfig:
 \\\Unknotting search configuration.\\\

 max_depth: int = 1
 max_swap_search_crossings: int = 8
 simplify_rounds: int = 8


@dataclass(frozen=True)
class VizConfig:
 \\\Visualization and mesh generation parameters.\\\

 diagram_dpi: int = 180
 centerline_samples_per_crossing: int = 36
 centerline_base_samples: int = 160
 tube_radius: float = 0.08
 tube_sides: int = 16
 pyvista_off_screen: bool = True


@dataclass(frozen=True)
class OutputConfig:
 \\\Output control flags.\\\

 write_json: bool = True
 write_diagram: bool = True
 write_preview_3d: bool = True
 write_centerline: bool = True


@dataclass(frozen=True)
class PipelineConfig:
 \\\Top-level pipeline configuration.\\\

 pd: PDConfig = field(default_factory=PDConfig)
 invariants: InvariantConfig = field(default_factory=InvariantConfig)
 search: SearchConfig = field(default_factory=SearchConfig)
 viz: VizConfig = field(default_factory=VizConfig)
 output: OutputConfig = field(default_factory=OutputConfig)
