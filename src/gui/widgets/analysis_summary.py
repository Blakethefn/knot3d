"""High-level analysis and unknot-status summary panel."""

from __future__ import annotations

from PySide6 import QtWidgets


class AnalysisSummaryWidget(QtWidgets.QGroupBox):
    """Show knot identity, convention information, and run conclusions."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Summary", parent)
        layout = QtWidgets.QVBoxLayout(self)
        self.knot_name_label = QtWidgets.QLabel("Knot: --")
        self.convention_label = QtWidgets.QLabel("Convention: --")
        self.conclusion_label = QtWidgets.QLabel("Conclusion: --")
        self.metadata = QtWidgets.QPlainTextEdit()
        self.metadata.setReadOnly(True)
        self.metadata.setMaximumBlockCount(200)
        layout.addWidget(self.knot_name_label)
        layout.addWidget(self.convention_label)
        layout.addWidget(self.conclusion_label)
        layout.addWidget(self.metadata, 1)

    def clear(self) -> None:
        """Reset the summary content."""

        self.knot_name_label.setText("Knot: --")
        self.convention_label.setText("Convention: --")
        self.conclusion_label.setText("Conclusion: --")
        self.metadata.setPlainText("")

    def set_results(self, analysis: dict | None, unknotting: dict | None = None) -> None:
        """Populate summary data from the latest results."""

        self.clear()
        if not analysis:
            return

        self.knot_name_label.setText(f"Knot: {analysis.get('knot_name') or 'unknown'}")
        self.convention_label.setText(f"Convention: {analysis.get('detected_convention') or 'unknown'}")
        conclusion = unknotting.get("conclusion") if unknotting else "Analysis complete."
        self.conclusion_label.setText(f"Conclusion: {conclusion}")

        lines = [
            f"Notes: {', '.join(analysis.get('convention_notes', [])) or 'none'}",
            f"Computation stages: {', '.join(sorted((analysis.get('computation_times') or {}).keys())) or 'none'}",
        ]
        if unknotting:
            lines.append(f"Recognition method: {unknotting.get('recognition_method', 'unknown')}")
            lines.append(f"u(K)=0 proven: {'yes' if unknotting.get('is_unknot') else 'no'}")
            details = unknotting.get("obstruction_details") or []
            lines.append(f"Evidence: {details[0] if details else 'none'}")
        self.metadata.setPlainText("\n".join(lines))
