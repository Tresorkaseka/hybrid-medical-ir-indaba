#!/usr/bin/env python3
"""Expérience 1, étape 2 : construit la base SQLite des champs structurés des essais.

Entrée  : data/raw/ir_datasets/clinicaltrials/docs_2021_*.zip (étape 0)
Sorties : data/processed/trials.sqlite (hors dépôt), results/exp1_trial_db_summary.json
"""
import json
import sqlite3
from contextlib import closing
from pathlib import Path

from hybrid_ir.data.trial_db import build_trial_database

ROOT = Path(__file__).resolve().parents[2]
ARCHIVES = sorted((ROOT / "data/raw/ir_datasets/clinicaltrials").glob("docs_2021_*.zip"))
DB_PATH = ROOT / "data/processed/trials.sqlite"
SUMMARY_PATH = ROOT / "results/exp1_trial_db_summary.json"


def distribution(conn: sqlite3.Connection, column: str) -> dict[str, int]:
    rows = conn.execute(f"SELECT {column}, COUNT(*) FROM trials GROUP BY {column}").fetchall()
    return {str(value): count for value, count in rows}


def count_missing(conn: sqlite3.Connection, column: str) -> int:
    return conn.execute(f"SELECT COUNT(*) FROM trials WHERE {column} IS NULL").fetchone()[0]


def summarize(db_path: Path) -> dict:
    with closing(sqlite3.connect(db_path)) as conn:
        return {
            "n_trials": conn.execute("SELECT COUNT(*) FROM trials").fetchone()[0],
            "gender": distribution(conn, "gender"),
            "accepts_healthy_volunteers": distribution(conn, "accepts_healthy_volunteers"),
            "phase": distribution(conn, "phase"),
            "missing_min_age": count_missing(conn, "min_age_years"),
            "missing_max_age": count_missing(conn, "max_age_years"),
        }


def main() -> None:
    if not ARCHIVES:
        raise SystemExit("Archives TREC absentes : lancer d'abord 00_download_and_check.py")
    total = build_trial_database(ARCHIVES, DB_PATH)
    print(f"{total} essais écrits dans {DB_PATH}")
    SUMMARY_PATH.write_text(json.dumps(summarize(DB_PATH), indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
