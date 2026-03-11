# Knot Engine

Knot Engine is a topology-first Python project for analyzing knots from 1-indexed planar diagram (PD) codes. The computation stack is centered on Spherogram, SnapPy, and `knot_floer_homology`; the visualization layer is a supporting window rather than the core deliverable.

## Architecture

```text
PD Input
  -> src/pd_parser.py
  -> src/pd_conventions.py
  -> src/knot_builder.py
  -> src/invariants.py + src/hfk_engine.py
  -> src/unknot_recognizer.py + src/unknotting_search.py
  -> src/viz_matplotlib.py + src/viz_pyvista.py + src/mesh_export.py
```

## Features

- Parse and validate 1-indexed PD codes from literals or files.
- Normalize blueprint PD conventions into buildable Spherogram inputs.
- Compute classical invariants from Seifert matrices and SnapPy geometry.
- Compute knot Floer homology data, including `tau`, `epsilon`, and genus.
- Run depth-1 unknotting searches by switching crossings on the normalized link.
- Export JSON reports, a 2D diagram preview, a 3D preview, a centerline CSV, and tube meshes.
- Solve the warm-up question directly with `warmup_solver.py`.

## Quick Start

Analyze the bundled reference knot:

```powershell
.\.venv\Scripts\python.exe main.py --pd-file examples\reference_11c.json --analyze --out out\reference
```

Run the trefoil unknotting search:

```powershell
.\.venv\Scripts\python.exe main.py --pd-file examples\trefoil.json --unknotting-search --out out\trefoil
```

Export meshes for the trefoil:

```powershell
.\.venv\Scripts\python.exe main.py --pd-file examples\trefoil.json --analyze --export-mesh --out out\trefoil_mesh
```

Solve the warm-up question directly:

```powershell
.\.venv\Scripts\python.exe warmup_solver.py "[[4,2,5,1],[10,6,11,5],[8,3,9,4],[2,9,3,10],[11,16,12,17],[7,15,8,14],[15,7,16,6],[13,20,14,21],[17,22,18,1],[21,18,22,19],[19,12,20,13]]"
```

## Algorithm Overview

1. Parse and validate the PD code.
2. Normalize the crossing convention to a Spherogram-buildable PD.
3. Build a `spherogram.Link` and its SnapPy exterior.
4. Compute Seifert-matrix-based classical invariants.
5. Compute HFK data with `knot_floer_homology.pd_to_hfk`.
6. For unknotting search, rotate crossings on the normalized link, rebuild, and filter candidates by determinant, Alexander polynomial, and HFK.
7. Recognize unknots by Spherogram simplification and, if needed, by the fundamental group of the complement.

## CLI Reference

| Flag | Meaning |
|---|---|
| `--pd` | PD code literal or JSON string |
| `--pd-file` | File containing a PD code |
| `--analyze` | Compute invariants and write analysis artifacts |
| `--unknotting-search` | Run the depth-1 unknotting search |
| `--export-mesh` | Export OBJ/STL/GLB meshes |
| `--out` | Output prefix |
| `-v`, `-vv` | Increase logging verbosity |

## Programmatic Usage

```python
from pathlib import Path
from main import run_pipeline

run_pipeline(Path("examples/trefoil.json"), Path("out/trefoil"), modes={"analyze", "unknotting_search"})
```

## Dependencies

The locked environment is recorded in `requirements.txt`. The core packages are:

- `snappy` and `spherogram` for topology objects and complements.
- `knot_floer_homology` for HFK, `tau`, `epsilon`, and genus.
- `sympy` for Alexander-polynomial algebra.
- `pyvista`, `trimesh`, and `matplotlib` for visualization and export.

## Testing

The repository includes a `tests/` tree that targets `pytest -v`, but the locked local venv available in this workspace does not currently include `pytest`, so the suite could not be executed without breaking the no-install constraint. The source tree was compile-checked and smoke-tested through the CLI.

## Limitations

- Regina is not available.
- SageMath is not available, so classical invariants come from Seifert matrices rather than Sage-backed Spherogram helpers.
- The blueprint cinquefoil PD is not planar in this venv and is normalized via a documented override.
- Unknot recognition is pragmatic rather than a certified normal-surface proof.

## Future Work

- Replace the pragmatic convention overrides with a fully general PD-convention translator.
- Add Regina-backed certified unknot recognition when available.
- Add a richer planar diagram renderer.
- Re-enable `pytest -v` once the locked environment actually includes `pytest`.

## License

MIT
