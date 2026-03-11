"""Shared Qt signal objects for cross-controller coordination."""

from __future__ import annotations

from PySide6 import QtCore


class AppSignals(QtCore.QObject):
    """Application-wide signal bus."""

    log_message = QtCore.Signal(str)
    status_message = QtCore.Signal(str)
    busy_changed = QtCore.Signal(bool)
    candidate_selected = QtCore.Signal(int)
