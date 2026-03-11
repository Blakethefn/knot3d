from __future__ import annotations

import subprocess

import pytest

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
    assert result["unknotting"]["upper_bound"] == 1


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
