"""Crossing-candidate table using Qt model/view."""

from __future__ import annotations

from typing import Any

from PySide6 import QtCore, QtGui, QtWidgets


class CrossingCandidateTableModel(QtCore.QAbstractTableModel):
    """Table model for crossing-change candidate metadata."""

    COLUMNS = [
        ("candidate_index", "Candidate"),
        ("crossing_indices", "Crossings"),
        ("determinant", "Det"),
        ("alexander_polynomial", "Alexander"),
        ("tau", "Tau"),
        ("full_check_status", "Status"),
        ("is_unknot", "Is Unknot"),
        ("elapsed_time", "Elapsed"),
    ]

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self._rows: list[dict[str, Any]] = []

    def rowCount(self, parent: QtCore.QModelIndex | None = None) -> int:
        return 0 if parent and parent.isValid() else len(self._rows)

    def columnCount(self, parent: QtCore.QModelIndex | None = None) -> int:
        return 0 if parent and parent.isValid() else len(self.COLUMNS)

    def data(self, index: QtCore.QModelIndex, role: int = QtCore.Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        key = self.COLUMNS[index.column()][0]
        value = row.get(key)
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if key == "crossing_indices":
                return ", ".join(str(item) for item in value or [])
            if key == "elapsed_time" and value is not None:
                return f"{float(value):.3f}s"
            if isinstance(value, bool):
                return "yes" if value else "no"
            return "" if value is None else str(value)
        if role == QtCore.Qt.ItemDataRole.UserRole:
            return row
        if role == QtCore.Qt.ItemDataRole.TextAlignmentRole and key in {"determinant", "tau", "elapsed_time"}:
            return int(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        if role == QtCore.Qt.ItemDataRole.ForegroundRole and key == "full_check_status":
            status = str(value or "")
            if status == "full_check":
                return QtGui.QColor("#176087")
            if status.startswith("filtered"):
                return QtGui.QColor("#a63d40")
        return None

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = QtCore.Qt.ItemDataRole.DisplayRole) -> Any:
        if role != QtCore.Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == QtCore.Qt.Orientation.Horizontal:
            return self.COLUMNS[section][1]
        return str(section + 1)

    def sort(self, column: int, order: QtCore.Qt.SortOrder = QtCore.Qt.SortOrder.AscendingOrder) -> None:
        key = self.COLUMNS[column][0]
        reverse = order == QtCore.Qt.SortOrder.DescendingOrder
        self.layoutAboutToBeChanged.emit()
        self._rows.sort(key=lambda row: self._sort_key(row.get(key)), reverse=reverse)
        self.layoutChanged.emit()

    def set_candidates(self, rows: list[dict[str, Any]]) -> None:
        self.beginResetModel()
        self._rows = list(rows)
        self.endResetModel()

    def candidate_at(self, row_index: int) -> dict[str, Any] | None:
        if row_index < 0 or row_index >= len(self._rows):
            return None
        return self._rows[row_index]

    def _sort_key(self, value: Any) -> Any:
        if isinstance(value, list):
            return tuple(value)
        if value is None:
            return (1, "")
        return (0, value)


class CandidateFilterProxyModel(QtCore.QSortFilterProxyModel):
    """Filter candidates by success/full-check mode."""

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self._mode = "all"

    def set_mode(self, mode: str) -> None:
        if hasattr(self, "beginFilterChange") and hasattr(self, "endFilterChange"):
            self.beginFilterChange()
            self._mode = mode
            self.endFilterChange()
            return
        self._mode = mode
        self.invalidate()

    def filterAcceptsRow(self, source_row: int, source_parent: QtCore.QModelIndex) -> bool:
        model = self.sourceModel()
        if model is None:
            return True
        index = model.index(source_row, 0, source_parent)
        row = model.data(index, QtCore.Qt.ItemDataRole.UserRole) or {}
        if self._mode == "success":
            return bool(row.get("is_unknot"))
        if self._mode == "full_check":
            return row.get("full_check_status") == "full_check"
        return True


class CrossingTableWidget(QtWidgets.QWidget):
    """Crossing-change table with sorting, filtering, and row selection."""

    candidate_selected = QtCore.Signal(dict)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.model = CrossingCandidateTableModel(self)
        self.proxy_model = CandidateFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        filter_row = QtWidgets.QHBoxLayout()
        self.filter_combo = QtWidgets.QComboBox()
        self.filter_combo.addItem("All Candidates", "all")
        self.filter_combo.addItem("Only Successful", "success")
        self.filter_combo.addItem("Only Full-Check", "full_check")
        filter_row.addWidget(QtWidgets.QLabel("Filter"))
        filter_row.addWidget(self.filter_combo, 1)

        self.table = QtWidgets.QTableView()
        self.table.setModel(self.proxy_model)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)

        layout.addLayout(filter_row)
        layout.addWidget(self.table, 1)

        self.filter_combo.currentIndexChanged.connect(self._apply_filter)
        self.table.selectionModel().selectionChanged.connect(self._emit_selection)

    def _apply_filter(self) -> None:
        self.proxy_model.set_mode(self.filter_combo.currentData())

    def _emit_selection(self) -> None:
        index = self.table.currentIndex()
        if not index.isValid():
            return
        source_index = self.proxy_model.mapToSource(index)
        candidate = self.model.candidate_at(source_index.row())
        if candidate is not None:
            self.candidate_selected.emit(candidate)

    def set_candidates(self, rows: list[dict[str, Any]]) -> None:
        """Populate the table with a new candidate list."""

        self.model.set_candidates(rows)
        self.table.resizeColumnsToContents()
        if rows:
            self.select_row(0)

    def select_row(self, source_row: int) -> None:
        """Programmatically select a source-model row."""

        source_index = self.model.index(source_row, 0)
        proxy_index = self.proxy_model.mapFromSource(source_index)
        if proxy_index.isValid():
            self.table.selectRow(proxy_index.row())

    def visible_row_count(self) -> int:
        """Return the current proxy-model row count."""

        return self.proxy_model.rowCount()
