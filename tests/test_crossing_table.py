from __future__ import annotations

from PySide6 import QtCore

from src.gui.widgets.crossing_detail import CrossingDetailWidget
from src.gui.widgets.crossing_table import CrossingTableWidget


def _rows():
    return [
        {
            "candidate_index": 1,
            "crossing_indices": [1],
            "determinant": 3,
            "alexander_polynomial": "t - 1",
            "tau": 1,
            "full_check_status": "filtered_tau",
            "is_unknot": False,
            "elapsed_time": 0.2,
            "notes": ["not unknot"],
        },
        {
            "candidate_index": 0,
            "crossing_indices": [0],
            "determinant": 1,
            "alexander_polynomial": "1",
            "tau": 0,
            "full_check_status": "full_check",
            "is_unknot": True,
            "elapsed_time": 0.1,
            "notes": ["unknot"],
        },
    ]


def test_table_populates(qapp):
    widget = CrossingTableWidget()
    widget.set_candidates(_rows())
    assert widget.model.rowCount() == 2


def test_sorting(qapp):
    widget = CrossingTableWidget()
    widget.set_candidates(_rows())
    widget.table.sortByColumn(2, QtCore.Qt.SortOrder.AscendingOrder)
    qapp.processEvents()
    first = widget.proxy_model.index(0, 2)
    assert widget.proxy_model.data(first) == "1"


def test_row_selection_signal(qapp):
    widget = CrossingTableWidget()
    seen = []
    widget.candidate_selected.connect(seen.append)
    widget.set_candidates(_rows())
    widget.select_row(0)
    qapp.processEvents()
    assert seen


def test_success_filter(qapp):
    widget = CrossingTableWidget()
    widget.set_candidates(_rows())
    widget.filter_combo.setCurrentIndex(1)
    qapp.processEvents()
    assert widget.visible_row_count() == 1


def test_candidate_metadata_shown(qapp):
    detail = CrossingDetailWidget()
    detail.set_candidate(_rows()[0])
    assert "Crossings" in detail.summary_label.text()
