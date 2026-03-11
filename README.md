# Knot Workbench

Knot Workbench is a native Python desktop application and CLI for topology-first knot analysis from 1-indexed planar diagram (PD) codes. The same shared engine powers both entry points, so the CLI and GUI agree on parsing, normalization, invariants, unknot recognition, and exports.

## Architecture

```text
CLI (main.py)                  Desktop GUI (gui_main.py)
        \                      /
         \                    /
          -> src/services/engine_facade.py
                    |
                    +-- src/pd_parser.py
                    +-- src/pd_conventions.py
                    +-- src/knot_builder.py
                    +-- src/invariants.py
                    +-- src/hfk_engine.py
                    +-- src/unknotting_search.py
                    +-- src/mesh_export.py
                    +-- src/viz_matplotlib.py
                    +-- src/viz_pyvista.py
```

The desktop layer is PySide6 widgets plus a docked workbench shell:

- `PySide6` for the native window, menus, docks, dialogs, and persistence.
- `pyvistaqt` / `pyvista` for the embedded 3D viewport in interactive mode.
- `matplotlib` for the 2D diagram tab and comparison view.
- `QThread` workers for analyze, unknot recognition, and mesh export jobs.

## Features

- Parse PD codes from JSON, Python literals, or files.
- Normalize blueprint conventions into buildable Spherogram inputs.
- Compute classical invariants, HFK-derived `tau` / `epsilon` / genus, and knot IDs when available.
- Decide whether `u(K)=0` using fast invariant obstructions plus direct unknot recognition checks.
- Inspect results in a desktop workbench with:
  - docked input, results, and log/progress panels
  - 2D diagram tab
  - 3D viewport tab
  - recognition-record table and detail panel
  - comparison tab
  - raw JSON tab
- Save and reload workbench sessions.
- Export analysis JSON, unknot-status JSON, recognition-record JSON, diagram PNG, viewport PNG, centerline CSV, and mesh bundles.

## Quick Start

CLI analyze:

```powershell
.\.venv\Scripts\python.exe main.py --pd-file examples\reference_11c.json --analyze --out out\reference
```

CLI unknot-status check:

```powershell
.\.venv\Scripts\python.exe main.py --pd-file examples\trefoil.json --unknotting-search --out out\trefoil
```

Desktop GUI:

```powershell
.\.venv\Scripts\python.exe gui_main.py
```

Makefile targets:

```powershell
make gui
make gui-offscreen
make test-gui
```

Windows-safe offscreen launch without `make`:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
$env:PYVISTA_OFF_SCREEN='true'
.\.venv\Scripts\python.exe gui_main.py
```

## Desktop Workflows

1. Analyze a knot
   Paste or load a PD code, click `Validate`, then `Analyze`.

2. Check whether `u(K)=0`
   Load `trefoil`, click `Check Unknot`, and inspect the recognition record.

3. Inspect the recognition trace
   Select the recognition row to inspect the evidence and populate the comparison tab.

4. Save and reload work
   Use `File -> Save Session` and `File -> Open Session`.

## Exports

The workbench and CLI share the same naming convention:

- `_analysis.json`
- `_unknotting.json`
- `_crossing_changes.json`
- `_diagram.png`
- `_3d.png`
- `_centerline.csv`
- mesh bundle: `.obj`, `.stl`, `.glb`

Example generated artifact paths:

- `out/trefoil_analysis.json`
- `out/trefoil_unknotting.json`
- `out/trefoil_diagram.png`
- `out/trefoil_3d.png`

## Screenshots

Generated output placeholders live in:

- `out/trefoil_diagram.png`
- `out/trefoil_3d.png`

## Testing

The full suite runs with `pytest -v`. GUI tests are headless and use:

- `QT_QPA_PLATFORM=offscreen`
- `PYVISTA_OFF_SCREEN=true`

Run everything:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Run only GUI-focused tests:

```powershell
powershell -Command "$env:QT_QPA_PLATFORM='offscreen'; $env:PYVISTA_OFF_SCREEN='true'; .\.venv\Scripts\python.exe -m pytest -v tests/test_main_window.py tests/test_gui_integration.py"
```

## Limitations

- The headless GUI test path uses a safe fallback 3D widget instead of a live VTK scene.
- Cancellation is cooperative; long-running topology calls may finish their current step before the UI fully settles.
- Regina and Sage-backed Spherogram helpers are not available in this environment.
- The blueprint cinquefoil sample is normalized through a documented override because the raw fixture is non-planar in this venv.

## License

MIT
