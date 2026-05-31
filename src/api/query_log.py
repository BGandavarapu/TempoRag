import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from src.api.schemas import ConflictEntry, QueryEntry

_DB_PATH = Path("data/query_log.db")


@contextmanager
def _conn():
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(_DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def _ensure_tables() -> None:
    with _conn() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS query_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                recommended_action TEXT NOT NULL,
                freshness_score REAL NOT NULL,
                source_count INTEGER NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS conflict_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chunk_a_id TEXT NOT NULL,
                chunk_b_id TEXT NOT NULL,
                conflict_type TEXT NOT NULL,
                source_a TEXT NOT NULL,
                source_b TEXT NOT NULL,
                date_a TEXT NOT NULL,
                date_b TEXT NOT NULL,
                date_delta_days INTEGER NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)


_ensure_tables()


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()


def log_query(
    query: str,
    recommended_action: str,
    freshness_score: float,
    source_count: int,
) -> None:
    with _conn() as con:
        con.execute(
            "INSERT INTO query_log (query, recommended_action, freshness_score, source_count, timestamp) "
            "VALUES (?, ?, ?, ?, ?)",
            (query, recommended_action, freshness_score, source_count, _utcnow()),
        )


def log_conflict(
    chunk_a_id: str,
    chunk_b_id: str,
    conflict_type: str,
    source_a: str,
    source_b: str,
    date_a: str,
    date_b: str,
    date_delta_days: int,
) -> None:
    with _conn() as con:
        con.execute(
            "INSERT INTO conflict_log "
            "(chunk_a_id, chunk_b_id, conflict_type, source_a, source_b, date_a, date_b, date_delta_days, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (chunk_a_id, chunk_b_id, conflict_type, source_a, source_b, date_a, date_b, date_delta_days, _utcnow()),
        )


def get_recent_queries(limit: int = 10) -> list[QueryEntry]:
    with _conn() as con:
        rows = con.execute(
            "SELECT query, recommended_action, freshness_score, source_count, timestamp "
            "FROM query_log ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [QueryEntry(**dict(row)) for row in rows]


def get_recent_conflicts(limit: int = 20) -> list[ConflictEntry]:
    with _conn() as con:
        rows = con.execute(
            "SELECT chunk_a_id, chunk_b_id, conflict_type, source_a, source_b, "
            "date_a, date_b, date_delta_days "
            "FROM conflict_log ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [ConflictEntry(**dict(row)) for row in rows]
