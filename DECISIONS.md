# Decisions

## Runtime API discovery

- `spherogram.Link` must be constructed as `Link(pd)` in this venv. The `pd_code=` keyword does not work here.
- `Link.exterior()` only works after SnapPy has been imported.
- `knot_floer_homology` exposes `pd_to_hfk(pd_code)` and `pd_to_morse(pd)`.
- `Link.knot_floer_homology()` also works on buildable Spherogram links.

## Classical invariants

- Sage-backed Spherogram helpers for Alexander polynomial, determinant, signature, and Goeritz matrices are unavailable.
- Classical invariants are therefore computed from `Link.seifert_matrix()` using SymPy and NumPy.
- Signature is taken from the symmetric matrix `V + V^T`.
- The Alexander polynomial is normalized up to multiplication by `± t^k`.
- Threaded GUI runs use the DT-code lookup first and treat `manifold.identify()` as optional because the SnapPy manifold database is not thread-safe in this Windows worker-thread path.

## PD conventions

- The blueprint trefoil and 11-crossing reference PDs build directly in Spherogram.
- The blueprint figure-eight PD requires an empirically verified adapter that swaps entries 1 and 3 on the middle two crossings.
- The blueprint cinquefoil PD is non-planar in this venv under all tested local rewrites, so that sample is normalized to Spherogram's native `5_1` PD.

## Crossing changes

- A crossing change is implemented on the normalized link object, not by tuple rewriting.
- The correct workflow is `crossing.rotate_by_90()` followed by `link._rebuild()`.
- The unknotting search now records metadata for every candidate so the GUI can drive the crossing table, filters, and comparison tab from shared engine output.

## Unknot recognition

- The first stage is a fast obstruction filter using determinant, Alexander polynomial, `tau`, and HFK genus.
- If the obstructions vanish, the project simplifies the diagram with Spherogram and checks whether it reduces to zero crossings.
- If simplification is inconclusive, the complement group is used: a single generator and zero relators with homology `Z` is accepted as the unknot.

## Desktop architecture pattern

- The desktop layer uses a classic Qt widgets architecture:
  - `QMainWindow` as the shell
  - dock widgets for input, results, and progress/logs
  - typed `SessionState` dataclasses as shared state
  - controllers for orchestration
  - services for engine, session, export, and recent-file persistence
- Widgets stay presentation-focused; filesystem writes and engine calls live in services/controllers.

## Worker and threading model

- The production GUI uses `QObject` workers moved onto `QThread` instances.
- Analyze, unknotting search, and mesh export all run off the UI thread.
- Cancellation is cooperative: the controller marks cancellation and ignores late results when the worker finishes.
- Unit tests use a synchronous controller mode with a fake engine to avoid unstable VTK teardown paths while preserving the threaded production path.

## Qt state synchronization strategy

- `SessionState` is the source of truth for PD text, normalized PD, result payloads, selection state, and session metadata.
- Controllers update `SessionState` first, then refresh widgets from that state.
- The crossing table drives selected-crossing state, and that state fans out to the 2D diagram, 3D view, detail pane, status bar, and comparison tab.

## 3D viewport integration details

- Interactive desktop mode embeds `pyvistaqt.QtInteractor` directly in the main window.
- Headless test mode intentionally falls back to a safe placeholder viewport because QtInteractor/VTK is not reliable enough in this Windows offscreen environment.
- Crossing highlights are represented by sampling deterministic centerline points by crossing index.

## Session file format

- Sessions are stored as JSON with version `1`.
- The file includes:
  - PD text and parsed PD
  - normalized PD
  - inline analysis / unknotting / crossing-change payloads
  - optional artifact paths
  - selected example
  - selected crossing
  - camera state
  - serialized UI layout metadata
- Inline payloads are kept even when artifact paths exist so sessions remain portable.

## Export behavior

- Export naming follows the blueprint suffix convention from a chosen base path.
- Export code is centralized in `src/services/export_service.py`; widgets do not write files directly.
- The GUI export bundle reuses the currently rendered diagram and viewport state instead of reconstructing separate GUI-only output paths.

## Environment findings

- `pytest`, `PySide6`, `pyvistaqt`, `pyvista`, SnapPy, Spherogram, and the other locked dependencies are available in the current `.venv`.
- The full `pytest -v` suite now runs in this workspace, including headless GUI coverage.
