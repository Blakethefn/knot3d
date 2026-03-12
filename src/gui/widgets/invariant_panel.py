"""Invariant summary cards."""

from __future__ import annotations

from PySide6 import QtCore, QtWidgets


class InvariantPanelWidget(QtWidgets.QGroupBox):
    """Display the primary invariant values as compact form rows."""

    FIELDS = [
        ("crossing_number", "Crossings"),
        ("determinant", "Determinant"),
        ("signature", "Signature"),
        ("alexander_polynomial", "Alexander"),
        ("tau", "Tau"),
        ("epsilon", "Epsilon"),
        ("seifert_genus", "Genus"),
    ]

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Invariants", parent)
        self._labels: dict[str, QtWidgets.QLabel] = {}
        layout = QtWidgets.QFormLayout(self)
        for key, title in self.FIELDS:
            label = QtWidgets.QLabel("--")
            label.setWordWrap(True)
            label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
            label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
            self._labels[key] = label
            layout.addRow(title, label)

    def clear(self) -> None:
        """Reset all values."""

        for label in self._labels.values():
            label.setText("--")

    def set_payload(self, analysis_result: dict | None) -> None:
        """Populate values from an analysis payload."""

        self.clear()
        if not analysis_result:
            return
        invariants = analysis_result.get("invariants", {})
        hfk = analysis_result.get("hfk") or {}
        values = {
            "crossing_number": invariants.get("crossing_number", "--"),
            "determinant": invariants.get("determinant", "--"),
            "signature": invariants.get("signature", "--"),
            "alexander_polynomial": invariants.get("alexander_polynomial", "--"),
            "tau": hfk.get("tau", "--"),
            "epsilon": hfk.get("epsilon", "--"),
            "seifert_genus": hfk.get("seifert_genus", "--"),
        }
        for key, value in values.items():
            self._labels[key].setText(str(value))
