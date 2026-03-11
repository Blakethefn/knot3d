from __future__ import annotations

from src.embedding_3d import compute_centerline
from src.gui.widgets.pyvista_view import PyVistaViewWidget


def test_widget_constructs_offscreen(qapp):
    widget = PyVistaViewWidget()
    assert widget is not None


def test_scene_loads_centerline(qapp, trefoil_pd):
    widget = PyVistaViewWidget()
    widget.load_centerline(compute_centerline(trefoil_pd), crossing_count=len(trefoil_pd))
    assert widget._tube_actor is not None


def test_reset_camera(qapp, trefoil_pd):
    widget = PyVistaViewWidget()
    widget.load_centerline(compute_centerline(trefoil_pd), crossing_count=len(trefoil_pd))
    widget.set_camera_preset("top")
    widget.reset_camera()
    assert "position" in widget.camera_state()


def test_highlight_crossing(qapp, trefoil_pd):
    widget = PyVistaViewWidget()
    widget.load_centerline(compute_centerline(trefoil_pd), crossing_count=len(trefoil_pd))
    widget.highlight_crossing(1)
    assert widget._highlight_actor is not None


def test_screenshot_export(qapp, trefoil_pd, tmp_path):
    widget = PyVistaViewWidget()
    widget.load_centerline(compute_centerline(trefoil_pd), crossing_count=len(trefoil_pd))
    target = widget.export_screenshot(tmp_path / "shot.png")
    assert target.exists()
