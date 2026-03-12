from __future__ import annotations

import math
import os
import subprocess

import pytest

from src.services.compute_policy import ComputePreferences
from src.services.engine_facade import EngineFacade


def test_validate_trefoil(trefoil_pd):
    facade = EngineFacade()
    result = facade.validate_pd(str(trefoil_pd))
    assert result.valid is True
    assert result.crossing_count == 3


def test_analyze_returns_dict(trefoil_pd, tmp_path):
    facade = EngineFacade()
    result = facade.analyze(trefoil_pd, tmp_path / "trefoil")
    assert isinstance(result, dict)
    assert "analysis" in result


def test_unknotting_returns_dict(trefoil_pd, tmp_path):
    facade = EngineFacade()
    result = facade.run_unknotting_search(trefoil_pd, tmp_path / "trefoil_u")
    assert isinstance(result, dict)
    assert result["unknotting"]["is_unknot"] is False
    assert result["unknotting"]["recognition_method"] == "fast_filter"


def test_export_mesh_returns_paths(trefoil_pd, tmp_path):
    facade = EngineFacade()
    result = facade.export_mesh(trefoil_pd, tmp_path / "trefoil_mesh")
    assert set(result["mesh_outputs"]) >= {"obj", "stl", "glb", "csv"}


def test_invalid_pd_raises(tmp_path):
    facade = EngineFacade()
    with pytest.raises(Exception):
        facade.analyze([[1, 2, 3]], tmp_path / "bad")


def test_facade_reuses_engine_modules(monkeypatch, trefoil_pd, tmp_path):
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no shell")))
    facade = EngineFacade()
    result = facade.analyze(trefoil_pd, tmp_path / "trefoil")
    assert result["analysis"]["knot_name"] == "3_1"


def test_compute_preferences_resolve_gpu_request(trefoil_pd, tmp_path):
    facade = EngineFacade()
    runtime = facade.update_compute_preferences(
        ComputePreferences.from_values(backend="gpu", cpu_max_usage_percent=40, gpu_max_usage_percent=60)
    )
    expected_threads = max(1, math.ceil((os.cpu_count() or 1) * 0.4))
    assert runtime["requested_backend"] == "gpu"
    # active_backend depends on whether GPUs are detected on this machine
    if runtime["gpu_available"]:
        assert runtime["active_backend"] == "gpu"
    else:
        assert runtime["active_backend"] == "cpu"
    assert runtime["cpu_thread_limit"] == expected_threads

    result = facade.analyze(trefoil_pd, tmp_path / "trefoil_gpu_pref")
    assert result["compute_runtime"]["cpu_thread_limit"] == expected_threads
