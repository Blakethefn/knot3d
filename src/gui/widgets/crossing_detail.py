"""Detail panel for the selected recognition record."""

from __future__ import annotations

from PySide6 import QtCore, QtWidgets


class CrossingDetailWidget(QtWidgets.QGroupBox):
    """Show selected record metadata and notes."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Recognition Detail", parent)
        layout = QtWidgets.QVBoxLayout(self)
        self.summary_label = QtWidgets.QLabel("No record selected.")
        self.summary_label.setWordWrap(True)
        self.notes = QtWidgets.QPlainTextEdit()
        self.notes.setReadOnly(True)
        self.notes.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.notes.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.notes.setMaximumBlockCount(200)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.notes, 1)

    def set_candidate(self, candidate: dict | None) -> None:
        """Render the selected record metadata."""

        if not candidate:
            self.summary_label.setText("No record selected.")
            self.notes.setPlainText("")
            return

        crossing_indices = candidate.get("crossing_indices") or []
        label = ", ".join(str(item) for item in crossing_indices) if crossing_indices else "current diagram"
        self.summary_label.setText(
            "Crossings: {crossings} | Status: {status} | Unknot: {unknot}".format(
                crossings=label,
                status=candidate.get("full_check_status", "--"),
                unknot=candidate.get("is_unknot", "--"),
            )
        )
        lines = [
            f"Knot name: {candidate.get('knot_name', '--')}",
            f"Determinant: {candidate.get('determinant', '--')}",
            f"Alexander: {candidate.get('alexander_polynomial', '--')}",
            f"Tau: {candidate.get('tau', '--')}",
            f"Recognition: {candidate.get('recognition_method', '--')}",
            "",
            *candidate.get("notes", []),
        ]
        self.notes.setPlainText("\n".join(str(line) for line in lines))
