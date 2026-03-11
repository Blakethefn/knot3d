"""Main application window for the knot workbench."""

from __future__ import annotations

import json

from PySide6 import QtCore, QtGui, QtWidgets

from src.gui.widgets import (
    AnalysisSummaryWidget,
    ComparisonViewWidget,
    CrossingDetailWidget,
    CrossingTableWidget,
    DiagramCanvasWidget,
    ExamplePickerWidget,
    InvariantPanelWidget,
    LogConsoleWidget,
    PDEditorWidget,
    ProgressPanelWidget,
    PyVistaViewWidget,
    RunPanelWidget,
    StatusBarWidget,
)
from src.utils import as_jsonable


class MainWindow(QtWidgets.QMainWindow):
    """Dockable scientific workbench shell."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.session_state = None
        self.on_save_before_close = None
        self._raw_payloads: dict[str, dict | None] = {}
        self.setWindowTitle("Knot Workbench")
        self.resize(1600, 980)
        self._build_actions()
        self._build_ui()

    def _build_actions(self) -> None:
        self.action_new_session = QtGui.QAction("New Session", self)
        self.action_open_pd = QtGui.QAction("Open PD File", self)
        self.action_open_session = QtGui.QAction("Open Session", self)
        self.action_save_session = QtGui.QAction("Save Session", self)
        self.action_export_results = QtGui.QAction("Export Results", self)
        self.action_export_screenshot = QtGui.QAction("Export Screenshot", self)
        self.action_export_diagram = QtGui.QAction("Export Diagram", self)
        self.action_exit = QtGui.QAction("Exit", self)

        self.action_validate = QtGui.QAction("Validate", self)
        self.action_analyze = QtGui.QAction("Analyze", self)
        self.action_unknot = QtGui.QAction("Unknotting Search", self)
        self.action_export_mesh = QtGui.QAction("Export Mesh", self)
        self.action_cancel = QtGui.QAction("Cancel Active Job", self)
        self.action_cancel.setEnabled(False)

        self.action_reset_layout = QtGui.QAction("Reset Layout", self)
        self.action_reset_camera = QtGui.QAction("Reset Camera", self)
        self.action_camera_top = QtGui.QAction("Top", self)
        self.action_camera_front = QtGui.QAction("Front", self)
        self.action_camera_iso = QtGui.QAction("Isometric", self)
        self.action_preferences = QtGui.QAction("Preferences", self)
        self.action_session_info = QtGui.QAction("Session Info", self)
        self.action_about = QtGui.QAction("About", self)

        self.example_actions = {
            "trefoil": QtGui.QAction("Trefoil", self),
            "figure_eight": QtGui.QAction("Figure-Eight", self),
            "cinquefoil": QtGui.QAction("Cinquefoil", self),
            "reference_11c": QtGui.QAction("Reference 11-Crossing", self),
            "unknot": QtGui.QAction("Unknot", self),
        }
        self.action_exit.triggered.connect(self.close)

    def _build_ui(self) -> None:
        self._build_menu_bar()
        self._build_toolbar()
        self._build_central_workspace()
        self._build_input_dock()
        self._build_results_dock()
        self._build_bottom_dock()
        self._build_status_bar()
        self.reset_layout()

    def _build_menu_bar(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        for action in (
            self.action_new_session,
            self.action_open_pd,
            self.action_open_session,
            self.action_save_session,
            self.action_export_results,
            self.action_export_screenshot,
            self.action_exit,
        ):
            file_menu.addAction(action)

        run_menu = self.menuBar().addMenu("Run")
        for action in (
            self.action_validate,
            self.action_analyze,
            self.action_unknot,
            self.action_export_mesh,
            self.action_cancel,
        ):
            run_menu.addAction(action)

        view_menu = self.menuBar().addMenu("View")
        for action in (
            self.action_reset_layout,
            self.action_reset_camera,
            self.action_camera_top,
            self.action_camera_front,
            self.action_camera_iso,
            self.action_preferences,
            self.action_session_info,
        ):
            view_menu.addAction(action)

        examples_menu = self.menuBar().addMenu("Examples")
        for action in self.example_actions.values():
            examples_menu.addAction(action)

        help_menu = self.menuBar().addMenu("Help")
        help_menu.addAction(self.action_about)

    def _build_toolbar(self) -> None:
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        for action in (
            self.action_validate,
            self.action_analyze,
            self.action_unknot,
            self.action_export_mesh,
            self.action_cancel,
        ):
            toolbar.addAction(action)

    def _build_central_workspace(self) -> None:
        self.workspace_tabs = QtWidgets.QTabWidget()
        self.pyvista_view = PyVistaViewWidget(self)
        self.diagram_canvas = DiagramCanvasWidget(self)
        self.comparison_view = ComparisonViewWidget(self)

        self.raw_json_combo = QtWidgets.QComboBox()
        self.raw_json_combo.addItem("Analysis", "analysis")
        self.raw_json_combo.addItem("Unknotting", "unknotting")
        self.raw_json_combo.addItem("Crossing Changes", "crossing_changes")
        self.raw_json_view = QtWidgets.QPlainTextEdit()
        self.raw_json_view.setReadOnly(True)
        raw_json_container = QtWidgets.QWidget()
        raw_json_layout = QtWidgets.QVBoxLayout(raw_json_container)
        raw_json_layout.setContentsMargins(0, 0, 0, 0)
        raw_json_layout.addWidget(self.raw_json_combo)
        raw_json_layout.addWidget(self.raw_json_view, 1)
        self.raw_json_combo.currentIndexChanged.connect(self._refresh_raw_json_view)

        self.workspace_tabs.addTab(self.pyvista_view, "3D View")
        self.workspace_tabs.addTab(self.diagram_canvas, "2D Diagram")
        self.workspace_tabs.addTab(self.comparison_view, "Comparison")
        self.workspace_tabs.addTab(raw_json_container, "Raw JSON")
        self.setCentralWidget(self.workspace_tabs)

    def _build_input_dock(self) -> None:
        self.example_picker = ExamplePickerWidget(parent=self)
        self.pd_editor = PDEditorWidget(self)
        self.run_panel = RunPanelWidget(self)

        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.addWidget(self.example_picker)
        layout.addWidget(self.pd_editor, 1)
        layout.addWidget(self.run_panel)

        self.input_dock = QtWidgets.QDockWidget("Input", self)
        self.input_dock.setObjectName("inputDock")
        self.input_dock.setWidget(container)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self.input_dock)

    def _build_results_dock(self) -> None:
        self.invariant_panel = InvariantPanelWidget(self)
        self.analysis_summary = AnalysisSummaryWidget(self)
        self.crossing_table = CrossingTableWidget(self)
        self.crossing_detail = CrossingDetailWidget(self)

        export_box = QtWidgets.QGroupBox("Export Shortcuts", self)
        export_layout = QtWidgets.QVBoxLayout(export_box)
        self.export_results_button = QtWidgets.QPushButton("Export Results")
        self.export_screenshot_button = QtWidgets.QPushButton("Export Screenshot")
        self.export_session_button = QtWidgets.QPushButton("Save Session")
        export_layout.addWidget(self.export_results_button)
        export_layout.addWidget(self.export_screenshot_button)
        export_layout.addWidget(self.export_session_button)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        splitter.addWidget(self.crossing_table)
        splitter.addWidget(self.crossing_detail)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.addWidget(self.invariant_panel)
        layout.addWidget(self.analysis_summary)
        layout.addWidget(splitter, 1)
        layout.addWidget(export_box)

        self.results_dock = QtWidgets.QDockWidget("Results", self)
        self.results_dock.setObjectName("resultsDock")
        self.results_dock.setWidget(container)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.results_dock)

    def _build_bottom_dock(self) -> None:
        self.progress_panel = ProgressPanelWidget(self)
        self.log_console = LogConsoleWidget(self)

        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.addWidget(self.progress_panel)
        layout.addWidget(self.log_console, 1)

        self.bottom_dock = QtWidgets.QDockWidget("Progress / Logs", self)
        self.bottom_dock.setObjectName("bottomDock")
        self.bottom_dock.setWidget(container)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.BottomDockWidgetArea, self.bottom_dock)

    def _build_status_bar(self) -> None:
        self.status_widget = StatusBarWidget(self)
        self.statusBar().addPermanentWidget(self.status_widget, 1)

    def set_busy(self, busy: bool, job_name: str = "") -> None:
        """Update busy state across the shared UI controls."""

        self.run_panel.set_busy(busy)
        self.progress_panel.set_busy(busy, job_name)
        self.action_cancel.setEnabled(busy)

    def set_raw_json_payloads(self, payloads: dict[str, dict | None]) -> None:
        """Update the raw JSON tab payloads."""

        self._raw_payloads = payloads
        self._refresh_raw_json_view()

    def _refresh_raw_json_view(self) -> None:
        key = self.raw_json_combo.currentData()
        payload = self._raw_payloads.get(key)
        if payload is None:
            self.raw_json_view.setPlainText("")
            return
        self.raw_json_view.setPlainText(json.dumps(as_jsonable(payload), indent=2, sort_keys=True))

    def serialized_ui_state(self) -> dict[str, str]:
        """Return a JSON-safe snapshot of active tab and window layout."""

        return {
            "active_tab": str(self.workspace_tabs.currentIndex()),
            "window_geometry": bytes(self.saveGeometry().toBase64()).decode("ascii"),
            "dock_state": bytes(self.saveState().toBase64()).decode("ascii"),
        }

    def restore_ui_state(self, ui_state: dict[str, str]) -> None:
        """Restore a serialized window layout snapshot."""

        geometry = ui_state.get("window_geometry")
        dock_state = ui_state.get("dock_state")
        active_tab = ui_state.get("active_tab")
        if geometry:
            self.restoreGeometry(QtCore.QByteArray.fromBase64(geometry.encode("ascii")))
        if dock_state:
            self.restoreState(QtCore.QByteArray.fromBase64(dock_state.encode("ascii")))
        if active_tab is not None:
            self.workspace_tabs.setCurrentIndex(int(active_tab))

    def reset_layout(self) -> None:
        """Restore the default dock arrangement."""

        self.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self.input_dock)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.results_dock)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.BottomDockWidgetArea, self.bottom_dock)
        self.workspace_tabs.setCurrentIndex(0)

    def reset_for_new_session(self) -> None:
        """Clear all widget state for a fresh session."""

        self.pd_editor.set_text("")
        self.pd_editor.clear_validation_message()
        self.run_panel.set_validation_message("No validation run yet.")
        self.invariant_panel.clear()
        self.analysis_summary.clear()
        self.crossing_table.set_candidates([])
        self.crossing_detail.set_candidate(None)
        self.comparison_view.clear_view()
        self.diagram_canvas.set_diagram([])
        self.pyvista_view.load_centerline([], 0)
        self.set_raw_json_payloads({})
        self.status_widget.set_session(None)
        self.status_widget.set_selected_crossing(None)
        self.status_widget.set_engine_state("idle")
        self.status_widget.set_progress("Ready")

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Prompt about unsaved changes before closing."""

        state = self.session_state
        if state is not None and state.dirty:
            choice = QtWidgets.QMessageBox.question(
                self,
                "Unsaved Session",
                "Save changes to the current session before closing?",
                QtWidgets.QMessageBox.StandardButton.Save
                | QtWidgets.QMessageBox.StandardButton.Discard
                | QtWidgets.QMessageBox.StandardButton.Cancel,
            )
            if choice == QtWidgets.QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            if choice == QtWidgets.QMessageBox.StandardButton.Save and self.on_save_before_close is not None:
                self.on_save_before_close()
        self.pyvista_view.shutdown()
        event.accept()
