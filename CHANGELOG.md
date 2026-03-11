# Changelog

## v0.2.0 - 2026-03-11

- Added the native PySide6 desktop workbench entry point in `gui_main.py`.
- Added docked input/results/log panels, a 2D diagram tab, a 3D viewport tab, a comparison tab, and a raw JSON tab.
- Added shared services for engine reuse, session persistence, recent files, and export orchestration.
- Added QThread-backed GUI workers plus controller/state layers for validation, analysis, unknot recognition, exports, and session round-tripping.
- Simplified the unknot pipeline to answer only whether `u(K)=0`, with fast invariant rejection and direct recognition evidence instead of depth-1 unknotting-number search.
- Added persisted compute preferences for backend selection plus CPU/GPU usage caps, with real CPU thread limiting and safe GPU fallback.
- Added headless GUI tests plus full end-to-end GUI integration coverage.

## v0.1.0 - 2026-03-11

- Built the initial topology-first knot-analysis pipeline.
- Added PD parsing, convention normalization, invariant computation, HFK integration, unknot recognition, and the original depth-1 unknotting search.
- Added 2D and 3D previews, tube-mesh export, bundled examples, and a dedicated warm-up solver.
- Added a calibrated test suite and runtime API discovery scripts.
