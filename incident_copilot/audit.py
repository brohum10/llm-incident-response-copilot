from __future__ import annotations

import json
import sqlite3
import weakref
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any


class AuditLog:
    def __init__(self, database_path: str | Path = ":memory:") -> None:
        self.database_path = str(database_path)
        self._lock = Lock()
        self._connection = sqlite3.connect(self.database_path, check_same_thread=False)
        self._finalizer = weakref.finalize(self, self._connection.close)
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

    def append(self, incident_id: str, event_type: str, payload: dict[str, Any]) -> None:
        with self._lock:
            self._connection.execute(
                "INSERT INTO audit_events (incident_id, event_type, payload, created_at) VALUES (?, ?, ?, ?)",
                (incident_id, event_type, json.dumps(payload, sort_keys=True), datetime.now(UTC).isoformat()),
            )
            self._connection.commit()

    def events_for(self, incident_id: str) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT event_type, payload, created_at FROM audit_events WHERE incident_id = ? ORDER BY id",
                (incident_id,),
            ).fetchall()
        return [
            {"event_type": event_type, "payload": json.loads(payload), "created_at": created_at}
            for event_type, payload, created_at in rows
        ]

    def close(self) -> None:
        """Close the database connection; calling this more than once is safe."""
        with self._lock:
            if self._finalizer.alive:
                self._finalizer()

    def __enter__(self) -> AuditLog:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
