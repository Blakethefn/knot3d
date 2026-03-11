from __future__ import annotations

import math
import os
import time
from pathlib import Path

import numpy as np
import pytest
from PySide6 import QtCore, QtTest, QtWidgets

from src.config import PipelineConfig
from src.gui.controllers import AppController
import src.gui.main_window as main_window_module
from src.gui.main_window import MainWindow
from src.gui.settings import apply_default_preferences
from src.gui.state import SessionState
from src.pd_conventions import normalize_pd_code
from src.pd_parser import parse_pd_input
from src.services.compute_policy import ComputePreferences
from src.services import RecentFilesStore, SessionStore

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")


@pytest.fixture
def trefoil_pd() -> list[list[int]]:
    return [[1, 5, 2, 4], [3, 1, 4, 6], [5, 3, 6, 2]]


@pytest.fixture
def figure_eight_pd() -> list[list[int]]:
    return [[2, 8, 3, 7], [4, 2, 5, 1], [6, 3, 7, 4], [8, 5, 1, 6]]


@pytest.fixture
def cinquefoil_pd() -> list[list[int]]:
    return [[2, 10, 3, 9], [4, 2, 5, 1], [6, 4, 7, 3], [8, 6, 9, 5], [10, 8, 1, 7]]


@pytest.fixture
def reference_pd() -> list[list[int]]:
    return [[4, 2, 5, 1], [10, 6, 11, 5], [8, 3, 9, 4], [2, 9, 3, 10], [11, 16, 12, 17], [7, 15, 8, 14], [15, 7, 16, 6], [13, 20, 14, 21], [17, 22, 18, 1], [21, 18, 22, 19], [19, 12, 20, 13]]


@pytest.fixture
def unknot_pd() -> list[list[int]]:
    return []


@pytest.fixture
def default_config() -> PipelineConfig:
    return PipelineConfig()


@pytest.fixture
def tmp_output_prefix(tmp_path: Path) -> Path:
    return tmp_path / "sample"


@pytest.fixture
def qapp():
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    return app


@pytest.fixture
def qt_settings(tmp_path: Path):
    settings = QtCore.QSettings(str(tmp_path / "test_settings.ini"), QtCore.QSettings.Format.IniFormat)
    settings.clear()
    apply_default_preferences(settings)
    return settings


class FakeValidationResult:
    def __init__(self, pd_code: list[list[int]], normalized_pd: list[list[int]], detected_convention: str, notes: list[str]) -> None:
        self.valid = True
        self.message = f"Valid PD with {len(normalized_pd)} crossings."
        self.pd_code = pd_code
        self.normalized_pd = normalized_pd
        self.detected_convention = detected_convention
        self.notes = notes
        self.crossing_count = len(normalized_pd)

    def to_dict(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "message": self.message,
            "pd_code": self.pd_code,
            "normalized_pd": self.normalized_pd,
            "detected_convention": self.detected_convention,
            "notes": self.notes,
            "crossing_count": self.crossing_count,
        }


class FakeEngineFacade:
    def __init__(self, output_dir: Path, delay_seconds: float = 0.05) -> None:
        self.output_dir = output_dir
        self.delay_seconds = delay_seconds
        self.calls: list[str] = []
        self.fail_mode: str | None = None
        self.compute_preferences = ComputePreferences()
        logical_cpus = max(1, os.cpu_count() or 1)
        self.compute_runtime = {
            "requested_backend": "auto",
            "active_backend": "cpu",
            "cpu_max_usage_percent": 100,
            "cpu_thread_limit": logical_cpus,
            "logical_cpu_count": logical_cpus,
            "gpu_max_usage_percent": 100,
            "gpu_available": False,
            "notes": (),
        }

    def validate_pd(self, raw_text: str):
        self.calls.append("validate")
        parsed = parse_pd_input(raw_text)
        normalized = normalize_pd_code(parsed.to_list())
        return FakeValidationResult(
            parsed.to_list(),
            normalized.normalized_pd,
            normalized.detected_convention,
            normalized.notes,
        )

    def analyze(self, pd_code, output_prefix, progress_callback=None):
        return self._result("analyze", pd_code, output_prefix, progress_callback)

    def run_unknotting_search(self, pd_code, output_prefix, progress_callback=None):
        return self._result("unknotting_search", pd_code, output_prefix, progress_callback)

    def export_mesh(self, pd_code, output_prefix, progress_callback=None):
        self.calls.append("export_mesh")
        if progress_callback:
            progress_callback("Exporting mesh", 50)
        time.sleep(self.delay_seconds)
        prefix = Path(output_prefix)
        return {
            "mesh_outputs": {
                "obj": str(prefix.with_suffix(".obj")),
                "stl": str(prefix.with_suffix(".stl")),
                "glb": str(prefix.with_suffix(".glb")),
            },
            "output_files": {
                "analysis_json": str(prefix.with_name(prefix.name + "_analysis.json")),
                "unknotting_json": str(prefix.with_name(prefix.name + "_unknotting.json")),
                "crossing_changes_json": str(prefix.with_name(prefix.name + "_crossing_changes.json")),
            },
        }

    def build_crossing_candidate_preview(self, pd_code, crossing_idx):
        return {"crossing_index": crossing_idx, "modified_pd": pd_code}

    def get_engine_versions(self):
        return {"engine": "fake"}

    def update_compute_preferences(self, preferences: ComputePreferences):
        self.compute_preferences = preferences
        logical_cpus = max(1, os.cpu_count() or 1)
        thread_limit = max(1, math.ceil(logical_cpus * (preferences.cpu_max_usage_percent / 100.0)))
        notes: tuple[str, ...] = ()
        if preferences.backend == "gpu":
            notes = ("Fake engine runs CPU-only and ignores GPU requests.",)
        self.compute_runtime = {
            "requested_backend": preferences.backend,
            "active_backend": "cpu",
            "cpu_max_usage_percent": preferences.cpu_max_usage_percent,
            "cpu_thread_limit": thread_limit,
            "logical_cpu_count": logical_cpus,
            "gpu_max_usage_percent": preferences.gpu_max_usage_percent,
            "gpu_available": False,
            "notes": notes,
        }
        return self.compute_runtime

    def get_compute_runtime(self):
        return self.compute_runtime

    def _result(self, mode: str, pd_code, output_prefix, progress_callback=None):
        self.calls.append(mode)
        if self.fail_mode == mode:
            raise RuntimeError(f"{mode} failed")
        if progress_callback:
            progress_callback("Starting", 10)
        time.sleep(self.delay_seconds)
        if progress_callback:
            progress_callback("Finishing", 90)
        prefix = Path(output_prefix)
        analysis = {
            "knot_name": "3_1",
            "detected_convention": "direct",
            "convention_notes": [],
            "pd_code": pd_code,
            "invariants": {
                "crossing_number": len(pd_code),
                "determinant": 1,
                "signature": -2,
                "alexander_polynomial": "1",
            },
            "hfk": {"tau": 0, "epsilon": 0, "seifert_genus": 0},
            "computation_times": {"parse": 0.001},
        }
        candidates = [
            {
                "candidate_index": 0,
                "crossing_indices": [],
                "determinant": 3,
                "alexander_polynomial": "t^2 - t + 1",
                "tau": 0,
                "seifert_genus": 1,
                "full_check_status": "fast_filter",
                "is_unknot": False,
                "elapsed_time": 0.02,
                "recognition_method": "fast_filter",
                "notes": ["determinant = 3 != 1"],
                "modified_pd": pd_code,
            }
        ]
        unknotting = {
            "knot_name": "3_1",
            "total_candidates": 1,
            "obstruction_lower_bound": 1,
            "obstruction_details": ["determinant = 3 != 1"],
            "conclusion": "Rejected u(K)=0 by a nontrivial invariant.",
            "candidate_summaries": candidates,
            "filter_stats": {"rejected_by_invariants": 1, "proven_unknot": 0, "rejected_after_full_check": 0},
            "unknotting_changes": [],
            "upper_bound": None,
            "is_unknot": False,
            "recognition_method": "fast_filter",
        }
        return {
            "analysis": analysis,
            "unknotting": unknotting if mode == "unknotting_search" else None,
            "crossing_changes": {
                "candidates": candidates,
                "filter_stats": {"rejected_by_invariants": 1, "proven_unknot": 0, "rejected_after_full_check": 0},
            }
            if mode == "unknotting_search"
            else {"candidates": [], "filter_stats": {}},
            "centerline": [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
            "normalized_pd": pd_code,
            "output_files": {
                "analysis_json": str(prefix.with_name(prefix.name + "_analysis.json")),
                "unknotting_json": str(prefix.with_name(prefix.name + "_unknotting.json")),
                "crossing_changes_json": str(prefix.with_name(prefix.name + "_crossing_changes.json")),
                "diagram_png": str(prefix.with_name(prefix.name + "_diagram.png")),
                "preview_3d": str(prefix.with_name(prefix.name + "_3d.png")),
                "centerline_csv": str(prefix.with_name(prefix.name + "_centerline.csv")),
            },
        }


class FakePyVistaWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._centerline = np.zeros((0, 3), dtype=float)
        self._crossing_count = 0
        self._highlight_index = None
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Fake 3D View"))

    def load_centerline(self, centerline, crossing_count: int = 0) -> None:
        self._centerline = np.asarray(centerline, dtype=float)
        self._crossing_count = crossing_count

    def highlight_crossing(self, crossing_index: int | None) -> None:
        self._highlight_index = crossing_index

    def reset_camera(self) -> None:
        return None

    def set_camera_preset(self, preset: str) -> None:
        return None

    def export_screenshot(self, path: str | Path) -> Path:
        target = Path(path)
        target.write_bytes(b"fake-png")
        return target

    def camera_state(self) -> dict[str, list[float]]:
        return {"position": [0.0, 0.0, 1.0], "focal_point": [0.0, 0.0, 0.0], "viewup": [0.0, 1.0, 0.0]}

    def restore_camera_state(self, state: dict[str, list[float]] | None) -> None:
        return None

    def shutdown(self) -> None:
        return None


@pytest.fixture
def fake_engine(tmp_path: Path) -> FakeEngineFacade:
    return FakeEngineFacade(tmp_path)


@pytest.fixture
def default_session_state(tmp_path: Path) -> SessionState:
    return SessionState(output_dir=tmp_path)


@pytest.fixture
def wait_until(qapp):
    def _wait(predicate, timeout_ms: int = 5000, interval_ms: int = 20):
        deadline = time.time() + timeout_ms / 1000.0
        while time.time() < deadline:
            qapp.processEvents()
            if predicate():
                return
            QtTest.QTest.qWait(interval_ms)
        raise AssertionError("Condition not met before timeout.")

    return _wait


@pytest.fixture
def gui_window(qapp, qt_settings, tmp_path: Path, fake_engine: FakeEngineFacade, monkeypatch):
    recent = RecentFilesStore(settings=qt_settings)
    state = SessionState(output_dir=tmp_path)
    monkeypatch.setattr(main_window_module, "PyVistaViewWidget", FakePyVistaWidget)
    window = MainWindow()
    controller = AppController(
        window,
        qt_settings,
        state=state,
        engine=fake_engine,
        session_store=SessionStore(),
        recent_files=recent,
        use_threads=False,
    )
    window.controller = controller
    window.show()
    yield window
    window.deleteLater()


@pytest.fixture
def real_gui_window(qapp, qt_settings, tmp_path: Path):
    recent = RecentFilesStore(settings=qt_settings)
    state = SessionState(output_dir=tmp_path)
    window = MainWindow()
    controller = AppController(
        window,
        qt_settings,
        state=state,
        session_store=SessionStore(),
        recent_files=recent,
    )
    controller.engine.analyze([[1, 5, 2, 4], [3, 1, 4, 6], [5, 3, 6, 2]], tmp_path / "_warmup")
    controller.engine.clear_cache()
    window.controller = controller
    window.show()
    yield window
    window.pyvista_view.shutdown()
    window.deleteLater()
    qapp.processEvents()
