"""Built-in example selector."""

from __future__ import annotations

import json
from pathlib import Path

from PySide6 import QtCore, QtWidgets


class ExamplePickerWidget(QtWidgets.QWidget):
    """Load canonical examples from the repository."""

    example_loaded = QtCore.Signal(str, str)

    def __init__(self, examples_dir: Path | None = None, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.examples_dir = examples_dir or Path(__file__).resolve().parents[3] / "examples"
        self._example_paths: dict[str, Path] = {}
        self._build_ui()
        self._load_examples()

    def _build_ui(self) -> None:
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.combo = QtWidgets.QComboBox()
        self.load_button = QtWidgets.QPushButton("Load Example")
        layout.addWidget(QtWidgets.QLabel("Examples"))
        layout.addWidget(self.combo, 1)
        layout.addWidget(self.load_button)
        self.load_button.clicked.connect(self.load_current)

    def _load_examples(self) -> None:
        preferred_order = ["trefoil", "figure_eight", "cinquefoil", "reference_11c", "hundred_crossing", "unknot"]
        for name in preferred_order:
            candidate = self.examples_dir / f"{name}.json"
            if candidate.exists():
                self._example_paths[name] = candidate
                self.combo.addItem(name, candidate)

    def load_current(self) -> None:
        """Emit the currently selected example payload."""

        name = self.combo.currentText()
        if not name:
            return
        path = self._example_paths[name]
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        pd_code = payload.get("pd_code", payload)
        self.example_loaded.emit(name, json.dumps(pd_code))

    def select_example(self, name: str) -> None:
        """Select and load an example by name."""

        index = self.combo.findText(name)
        if index >= 0:
            self.combo.setCurrentIndex(index)
            self.load_current()
