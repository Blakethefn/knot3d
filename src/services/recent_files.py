"""Recent-file persistence backed by QSettings."""

from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore


class RecentFilesStore:
    """Track recently opened session and PD files."""

    def __init__(
        self,
        key_prefix: str = "recent_files",
        max_entries: int = 10,
        settings: QtCore.QSettings | None = None,
    ) -> None:
        self.key_prefix = key_prefix
        self.max_entries = max_entries
        self.settings = settings or QtCore.QSettings()

    def list_recent_files(self, kind: str) -> list[Path]:
        """Return existing recent files for the given kind."""

        values = self.settings.value(f"{self.key_prefix}/{kind}", [], list)
        paths = [Path(value) for value in values]
        return [path for path in paths if path.exists()]

    def add_recent_file(self, kind: str, path: str | Path) -> None:
        """Push a new path to the top of the recent-files list."""

        candidate = str(Path(path))
        values = [entry for entry in self.settings.value(f"{self.key_prefix}/{kind}", [], list) if entry != candidate]
        values.insert(0, candidate)
        self.settings.setValue(f"{self.key_prefix}/{kind}", values[: self.max_entries])

    def clear(self, kind: str) -> None:
        """Clear the given recent-file list."""

        self.settings.remove(f"{self.key_prefix}/{kind}")
