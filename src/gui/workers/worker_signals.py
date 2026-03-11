"""Shared worker signals."""

from __future__ import annotations

from PySide6 import QtCore


class WorkerSignals(QtCore.QObject):
    """Common signals emitted by background workers."""

    started = QtCore.Signal(str)
    progress = QtCore.Signal(str, int)
    result = QtCore.Signal(str, object)
    error = QtCore.Signal(str, str)
    finished = QtCore.Signal(str)
    cancelled = QtCore.Signal(str)
