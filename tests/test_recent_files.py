from __future__ import annotations

from PySide6 import QtCore

from src.services.recent_files import RecentFilesStore


def test_add_and_list_recent_files(tmp_path):
    settings = QtCore.QSettings(str(tmp_path / "recent.ini"), QtCore.QSettings.Format.IniFormat)
    store = RecentFilesStore(settings=settings)
    first = tmp_path / "a.json"
    first.write_text("{}", encoding="utf-8")
    store.add_recent_file("session", first)
    assert store.list_recent_files("session") == [first]


def test_recency_order(tmp_path):
    settings = QtCore.QSettings(str(tmp_path / "recent.ini"), QtCore.QSettings.Format.IniFormat)
    store = RecentFilesStore(settings=settings)
    first = tmp_path / "a.json"
    second = tmp_path / "b.json"
    first.write_text("{}", encoding="utf-8")
    second.write_text("{}", encoding="utf-8")
    store.add_recent_file("session", first)
    store.add_recent_file("session", second)
    assert store.list_recent_files("session")[0] == second


def test_clear_recent_files(tmp_path):
    settings = QtCore.QSettings(str(tmp_path / "recent.ini"), QtCore.QSettings.Format.IniFormat)
    store = RecentFilesStore(settings=settings)
    first = tmp_path / "a.json"
    first.write_text("{}", encoding="utf-8")
    store.add_recent_file("session", first)
    store.clear("session")
    assert store.list_recent_files("session") == []
