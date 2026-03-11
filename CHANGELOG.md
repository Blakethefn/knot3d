# Changelog

## v0.2.0 - 2026-03-11

- Added the native PySide6 desktop workbench entry point in `gui_main.py`.
- Added docked input/results/log panels, a 2D diagram tab, a 3D viewport tab, a comparison tab, and a raw JSON tab.
- Added shared services for engine reuse, session persistence, recent files, and export orchestration.
- Added QThread-backed GUI workers plus controller/state layers for validation, analysis, unknotting, exports, and session round-tripping.
- Extended unknotting outputs with per-candidate metadata for the crossing table and GUI comparison workflows.
- Added headless GUI tests plus full end-to-end GUI integration coverage.

## v0.1.0 - 2026-03-11

- Built the initial topology-first knot-analysis pipeline.
- Added PD parsing, convention normalization, invariant computation, HFK integration, unknot recognition, and depth-1 unknotting search.
- Added 2D and 3D previews, tube-mesh export, bundled examples, and a dedicated warm-up solver.
- Added a calibrated test suite and runtime API discovery scripts.
