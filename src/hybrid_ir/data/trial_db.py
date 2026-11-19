import sqlite3
from collections.abc import Iterable
from contextlib import closing
from pathlib import Path

from hybrid_ir.data.trial_corpus import iter_trial_records
from hybrid_ir.data.trial_xml import TrialRecord

_SCHEMA = """
CREATE TABLE trials (
    nct_id                      TEXT PRIMARY KEY,
    gender                      TEXT CHECK (gender IN ('All', 'Male', 'Female')),
    min_age_years               REAL,
    max_age_years               REAL,
    accepts_healthy_volunteers  INTEGER CHECK (accepts_healthy_volunteers IN (0, 1)),
    phase                       TEXT
)
"""
_INSERT = "INSERT INTO trials VALUES (?, ?, ?, ?, ?, ?)"


def create_schema(conn: sqlite3.Connection) -> None:
    conn.execute(_SCHEMA)


def insert_trials(conn: sqlite3.Connection, records: Iterable[TrialRecord]) -> None:
    with conn:
        conn.executemany(_INSERT, (_to_row(record) for record in records))


def count_trials(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM trials").fetchone()[0]


def build_trial_database(archive_paths: Iterable[Path], db_path: Path) -> int:
    """Reconstruit la base depuis zéro à partir des archives TREC et renvoie le nombre d'essais."""
    Path(db_path).unlink(missing_ok=True)
    with closing(sqlite3.connect(db_path)) as conn:
        create_schema(conn)
        for archive_path in archive_paths:
            insert_trials(conn, iter_trial_records(archive_path))
        total = count_trials(conn)
    return total


def _to_row(record: TrialRecord) -> tuple:
    return (
        record.nct_id,
        record.gender,
        record.min_age_years,
        record.max_age_years,
        _bool_to_int(record.accepts_healthy_volunteers),
        record.phase,
    )


def _bool_to_int(value: bool | None) -> int | None:
    return None if value is None else int(value)
