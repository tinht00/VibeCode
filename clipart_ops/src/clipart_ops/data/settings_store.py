"""Lưu settings đơn giản bằng SQLite."""

from __future__ import annotations

import sqlite3
from pathlib import Path


class SettingsStore:
    """Store SQLite cho workspace gần đây và operation log."""

    def __init__(self, state_dir: Path) -> None:
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.state_dir / "settings.sqlite3"
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                create table if not exists settings (
                    key text primary key,
                    value text not null
                )
                """
            )
            conn.execute(
                """
                create table if not exists recent_workspaces (
                    path text primary key,
                    opened_at text not null
                )
                """
            )
            conn.commit()

    def set_value(self, key: str, value: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "insert into settings(key, value) values(?, ?) "
                "on conflict(key) do update set value = excluded.value",
                (key, value),
            )
            conn.commit()

    def get_value(self, key: str, default: str = "") -> str:
        with self._connect() as conn:
            row = conn.execute(
                "select value from settings where key = ?",
                (key,),
            ).fetchone()
        return row[0] if row else default

    def add_recent_workspace(self, path: Path) -> None:
        with self._connect() as conn:
            conn.execute(
                "insert into recent_workspaces(path, opened_at) values(?, datetime('now')) "
                "on conflict(path) do update set opened_at = datetime('now')",
                (str(path),),
            )
            conn.commit()

    def list_recent_workspaces(self) -> list[Path]:
        with self._connect() as conn:
            rows = conn.execute(
                "select path from recent_workspaces order by opened_at desc limit 10"
            ).fetchall()
        return [Path(row[0]) for row in rows]
