"""Persistent run state tracking and idempotent stage retries."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Iterator, List, Optional
from uuid import uuid4

from core.config import RUN_STAGE_MAX_ATTEMPTS, RUN_STATE_DATABASE_URL, RUN_STATE_SQLITE_PATH

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover - handled by runtime dependency
    psycopg = None
    dict_row = None


class StageRetryLimitExceededError(RuntimeError):
    """Raised when a stage exceeds its configured retry budget."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _json_loads(value: Optional[str]) -> Any:
    if not value:
        return None
    return json.loads(value)


def _input_hash(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(_json_dumps(payload).encode("utf-8")).hexdigest()


class _Session:
    def __init__(self, connection: Any, backend: str) -> None:
        self.connection = connection
        self.backend = backend

    def _query(self, query: str) -> str:
        if self.backend == "postgres":
            return query.replace("?", "%s")
        return query

    def _cursor(self) -> Any:
        return self.connection.cursor()

    def execute(self, query: str, params: Optional[List[Any]] = None) -> None:
        cursor = self._cursor()
        try:
            cursor.execute(self._query(query), params or [])
        finally:
            cursor.close()

    def fetchone(self, query: str, params: Optional[List[Any]] = None) -> Optional[Dict[str, Any]]:
        cursor = self._cursor()
        try:
            cursor.execute(self._query(query), params or [])
            row = cursor.fetchone()
        finally:
            cursor.close()
        if row is None:
            return None
        if self.backend == "sqlite":
            return dict(row)
        return row

    def fetchall(self, query: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        cursor = self._cursor()
        try:
            cursor.execute(self._query(query), params or [])
            rows = cursor.fetchall()
        finally:
            cursor.close()
        if self.backend == "sqlite":
            return [dict(row) for row in rows]
        return rows


class _DatabaseStore:
    def __init__(self) -> None:
        self.backend = "postgres" if RUN_STATE_DATABASE_URL else "sqlite"
        self._lock = RLock()
        self._initialized = False

    def _connect(self) -> Any:
        if self.backend == "postgres":
            if psycopg is None:
                raise RuntimeError("psycopg is required when RUN_STATE_DATABASE_URL is configured")
            return psycopg.connect(RUN_STATE_DATABASE_URL, row_factory=dict_row)

        sqlite_path = Path(RUN_STATE_SQLITE_PATH)
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(sqlite_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self._lock:
            if self._initialized:
                return

            statements = [
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    current_stage TEXT,
                    last_error TEXT
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS stage_attempts (
                    attempt_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    attempt_number INTEGER NOT NULL,
                    input_hash TEXT NOT NULL,
                    status TEXT NOT NULL,
                    input_payload TEXT,
                    output_payload TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(run_id, stage, attempt_number)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS run_events (
                    event_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    attempt_number INTEGER,
                    status TEXT NOT NULL,
                    error TEXT,
                    created_at TEXT NOT NULL
                )
                """,
                "CREATE INDEX IF NOT EXISTS idx_runs_updated_at ON runs (updated_at)",
                "CREATE INDEX IF NOT EXISTS idx_stage_attempts_lookup ON stage_attempts (run_id, stage, updated_at)",
                "CREATE INDEX IF NOT EXISTS idx_stage_attempts_hash ON stage_attempts (run_id, stage, input_hash, status)",
                "CREATE INDEX IF NOT EXISTS idx_run_events_lookup ON run_events (run_id, created_at)",
            ]

            connection = self._connect()
            try:
                session = _Session(connection, self.backend)
                for statement in statements:
                    session.execute(statement)
                connection.commit()
            finally:
                connection.close()

            self._initialized = True

    @contextmanager
    def session(self) -> Iterator[_Session]:
        self.initialize()
        connection = self._connect()
        try:
            session = _Session(connection, self.backend)
            yield session
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()


_STORE = _DatabaseStore()


def ensure_run(run_id: Optional[str] = None) -> str:
    """Create a run if it does not exist and return its id."""
    resolved_run_id = (run_id or "").strip() or str(uuid4())
    now = _now_iso()

    with _STORE._lock, _STORE.session() as session:
        existing = session.fetchone(
            "SELECT run_id FROM runs WHERE run_id = ?",
            [resolved_run_id],
        )
        if existing is None:
            session.execute(
                """
                INSERT INTO runs (run_id, status, created_at, updated_at, current_stage, last_error)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [resolved_run_id, "created", now, now, None, None],
            )

    return resolved_run_id


def start_stage(run_id: Optional[str], stage: str, input_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Start a stage attempt or return a cached successful result."""
    resolved_run_id = ensure_run(run_id)
    now = _now_iso()
    serialized_input = _json_dumps(input_payload)
    serialized_hash = _input_hash(input_payload)

    with _STORE._lock, _STORE.session() as session:
        cached = session.fetchone(
            """
            SELECT attempt_id, attempt_number, output_payload
            FROM stage_attempts
            WHERE run_id = ? AND stage = ? AND input_hash = ? AND status = ?
            ORDER BY attempt_number DESC
            LIMIT 1
            """,
            [resolved_run_id, stage, serialized_hash, "success"],
        )
        if cached and cached.get("output_payload"):
            session.execute(
                """
                INSERT INTO run_events (event_id, run_id, stage, attempt_number, status, error, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [str(uuid4()), resolved_run_id, stage, cached["attempt_number"], "cached", None, now],
            )
            session.execute(
                "UPDATE runs SET updated_at = ?, current_stage = ? WHERE run_id = ?",
                [now, stage, resolved_run_id],
            )
            return {
                "run_id": resolved_run_id,
                "cached": True,
                "attempt_id": cached["attempt_id"],
                "attempt_number": cached["attempt_number"],
                "output_payload": _json_loads(cached["output_payload"]),
            }

        last_attempt = session.fetchone(
            """
            SELECT COALESCE(MAX(attempt_number), 0) AS max_attempt
            FROM stage_attempts
            WHERE run_id = ? AND stage = ?
            """,
            [resolved_run_id, stage],
        )
        next_attempt = int((last_attempt or {}).get("max_attempt", 0)) + 1
        if next_attempt > RUN_STAGE_MAX_ATTEMPTS:
            raise StageRetryLimitExceededError(
                f"Stage '{stage}' exceeded max attempts ({RUN_STAGE_MAX_ATTEMPTS}) for run_id={resolved_run_id}"
            )

        attempt_id = str(uuid4())
        session.execute(
            """
            INSERT INTO stage_attempts (
                attempt_id, run_id, stage, attempt_number, input_hash, status,
                input_payload, output_payload, error, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                attempt_id,
                resolved_run_id,
                stage,
                next_attempt,
                serialized_hash,
                "running",
                serialized_input,
                None,
                None,
                now,
                now,
            ],
        )
        session.execute(
            """
            INSERT INTO run_events (event_id, run_id, stage, attempt_number, status, error, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [str(uuid4()), resolved_run_id, stage, next_attempt, "running", None, now],
        )
        session.execute(
            "UPDATE runs SET status = ?, updated_at = ?, current_stage = ?, last_error = ? WHERE run_id = ?",
            ["running", now, stage, None, resolved_run_id],
        )

        return {
            "run_id": resolved_run_id,
            "cached": False,
            "attempt_id": attempt_id,
            "attempt_number": next_attempt,
        }


def finish_stage_success(run_id: str, stage: str, attempt_id: str, output_payload: Dict[str, Any]) -> None:
    """Complete a stage attempt successfully."""
    now = _now_iso()
    serialized_output = _json_dumps(output_payload)

    with _STORE._lock, _STORE.session() as session:
        attempt = session.fetchone(
            "SELECT attempt_number FROM stage_attempts WHERE attempt_id = ?",
            [attempt_id],
        )
        if attempt is None:
            raise RuntimeError(f"Unknown attempt_id: {attempt_id}")

        session.execute(
            """
            UPDATE stage_attempts
            SET status = ?, output_payload = ?, error = ?, updated_at = ?
            WHERE attempt_id = ?
            """,
            ["success", serialized_output, None, now, attempt_id],
        )
        session.execute(
            """
            INSERT INTO run_events (event_id, run_id, stage, attempt_number, status, error, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [str(uuid4()), run_id, stage, attempt["attempt_number"], "success", None, now],
        )

        run_status = "completed" if stage == "deployer" else "running"
        session.execute(
            "UPDATE runs SET status = ?, updated_at = ?, current_stage = ?, last_error = ? WHERE run_id = ?",
            [run_status, now, stage, None, run_id],
        )


def finish_stage_error(run_id: str, stage: str, attempt_id: str, error: str) -> None:
    """Complete a stage attempt with error."""
    now = _now_iso()

    with _STORE._lock, _STORE.session() as session:
        attempt = session.fetchone(
            "SELECT attempt_number FROM stage_attempts WHERE attempt_id = ?",
            [attempt_id],
        )
        if attempt is None:
            raise RuntimeError(f"Unknown attempt_id: {attempt_id}")

        session.execute(
            """
            UPDATE stage_attempts
            SET status = ?, error = ?, updated_at = ?
            WHERE attempt_id = ?
            """,
            ["error", error, now, attempt_id],
        )
        session.execute(
            """
            INSERT INTO run_events (event_id, run_id, stage, attempt_number, status, error, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [str(uuid4()), run_id, stage, attempt["attempt_number"], "error", error, now],
        )
        session.execute(
            "UPDATE runs SET status = ?, updated_at = ?, current_stage = ?, last_error = ? WHERE run_id = ?",
            ["error", now, stage, error, run_id],
        )


def set_run_status(run_id: str, status: str, current_stage: Optional[str] = None, error: Optional[str] = None) -> None:
    """Override the run status for terminal business outcomes."""
    now = _now_iso()
    with _STORE._lock, _STORE.session() as session:
        session.execute(
            "UPDATE runs SET status = ?, updated_at = ?, current_stage = ?, last_error = ? WHERE run_id = ?",
            [status, now, current_stage, error, run_id],
        )


def get_run(run_id: str) -> Optional[Dict[str, Any]]:
    """Return one persistent run snapshot."""
    with _STORE.session() as session:
        run = session.fetchone(
            "SELECT run_id, status, created_at, updated_at, current_stage, last_error FROM runs WHERE run_id = ?",
            [run_id],
        )
        if run is None:
            return None

        attempts = session.fetchall(
            """
            SELECT stage, attempt_number, status, input_payload, output_payload, error, updated_at
            FROM stage_attempts
            WHERE run_id = ?
            ORDER BY stage ASC, attempt_number DESC
            """,
            [run_id],
        )
        events = session.fetchall(
            """
            SELECT stage, attempt_number, status, error, created_at
            FROM run_events
            WHERE run_id = ?
            ORDER BY created_at ASC
            """,
            [run_id],
        )

    stage_attempt_counts: Dict[str, int] = {}
    for attempt in attempts:
        stage_name = attempt["stage"]
        stage_attempt_counts[stage_name] = stage_attempt_counts.get(stage_name, 0) + 1

    stage_summaries: Dict[str, Dict[str, Any]] = {}
    for attempt in attempts:
        stage_name = attempt["stage"]
        if stage_name in stage_summaries:
            continue

        stage_summaries[stage_name] = {
            "status": attempt["status"],
            "updated_at": attempt["updated_at"],
            "attempt_number": attempt["attempt_number"],
            "attempts": stage_attempt_counts[stage_name],
            "input": _json_loads(attempt["input_payload"]),
            "output": _json_loads(attempt["output_payload"]),
            "error": attempt["error"],
        }

    normalized_events = [
        {
            "at": event["created_at"],
            "stage": event["stage"],
            "attempt_number": event["attempt_number"],
            "status": event["status"],
            "error": event["error"],
        }
        for event in events
    ]

    return {
        "run_id": run["run_id"],
        "status": run["status"],
        "created_at": run["created_at"],
        "updated_at": run["updated_at"],
        "current_stage": run["current_stage"],
        "last_error": run["last_error"],
        "stages": stage_summaries,
        "events": normalized_events,
    }


def list_runs(limit: int = 20) -> List[Dict[str, Any]]:
    """Return latest runs sorted by update timestamp desc."""
    safe_limit = max(1, min(limit, 200))
    with _STORE.session() as session:
        items = session.fetchall(
            """
            SELECT run_id, status, created_at, updated_at, current_stage, last_error
            FROM runs
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            [safe_limit],
        )

    return [
        {
            "run_id": item["run_id"],
            "status": item["status"],
            "created_at": item["created_at"],
            "updated_at": item["updated_at"],
            "current_stage": item["current_stage"],
            "last_error": item["last_error"],
        }
        for item in items
    ]
