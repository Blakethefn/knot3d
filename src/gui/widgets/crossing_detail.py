"""Detail panel for the selected crossing-change candidate."""

from __future__ import annotations

from PySide6 import QtWidgets


class CrossingDetailWidget(QtWidgets.QGroupBox):
    """Show candidate metadata and notes."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Candidate Detail", parent)
        layout = QtWidgets.QVBoxLayout(self)
        self.summary_label = QtWidgets.QLabel("No candidate selected.")
        self.summary_label.setWordWrap(True)
        self.notes = QtWidgets.QPlainTextEdit()
        self.notes.setReadOnly(True)
        self.notes.setMaximumBlockCount(200)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.notes, 1)

    def set_candidate(self, candidate: dict | None) -> None:
        """Render the selected candidate metadata."""

        if not candidate:
            self.summary_label.setText("No candidate selected.")
            self.notes.setPlainText("")
            return
        self.summary_label.setText(
            "Crossings: {crossings} | Status: {status} | Unknot: {unknot}".format(
                crossings=", ".join(str(item) for item in candidate.get("crossing_indices", [])),
                status=candidate.get("full_check_status", "—"),
                unknot=candidate.get("is_unknot", "—"),
            )
        )
        lines = [
            f"Knot name: {candidate.get('knot_name', '—')}",
            f"Determinant: {candidate.get('determinant', '—')}",
            f"Alexander: {candidate.get('alexander_polynomial', '—')}",
            f"Tau: {candidate.get('tau', '—')}",
            f"Recognition: {candidate.get('recognition_method', '—')}",
            "",
            *candidate.get("notes", []),
        ]
        self.notes.setPlainText("\n".join(str(line) for line in lines))
