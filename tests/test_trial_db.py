import sqlite3
import zipfile

import pytest
from helpers import make_trial_xml
from hybrid_ir.data.trial_db import build_trial_database, count_trials, create_schema, insert_trials
from hybrid_ir.data.trial_xml import TrialRecord


def record(nct_id="NCT00000001", **overrides):
    fields = {
        "nct_id": nct_id,
        "gender": "All",
        "min_age_years": 18.0,
        "max_age_years": 65.0,
        "accepts_healthy_volunteers": False,
        "phase": "Phase 2",
    }
    return TrialRecord(**{**fields, **overrides})


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    create_schema(connection)
    yield connection
    connection.close()


def test_schema_has_the_filter_columns(conn):
    columns = [row[1] for row in conn.execute("PRAGMA table_info(trials)")]

    assert columns == [
        "nct_id",
        "gender",
        "min_age_years",
        "max_age_years",
        "accepts_healthy_volunteers",
        "phase",
    ]


def test_inserted_records_are_read_back_with_nulls_and_booleans(conn):
    insert_trials(
        conn,
        [
            record("NCT00000001", accepts_healthy_volunteers=True),
            record("NCT00000002", gender=None, min_age_years=None, max_age_years=None,
                   accepts_healthy_volunteers=None, phase=None),
        ],
    )

    rows = conn.execute("SELECT * FROM trials ORDER BY nct_id").fetchall()
    assert rows == [
        ("NCT00000001", "All", 18.0, 65.0, 1, "Phase 2"),
        ("NCT00000002", None, None, None, None, None),
    ]
    assert count_trials(conn) == 2


def test_duplicate_trial_id_is_rejected_not_overwritten(conn):
    insert_trials(conn, [record("NCT00000001")])

    with pytest.raises(sqlite3.IntegrityError):
        insert_trials(conn, [record("NCT00000001", gender="Male")])


def test_database_itself_rejects_an_invalid_gender(conn):
    with pytest.raises(sqlite3.IntegrityError):
        insert_trials(conn, [record(gender="Other")])


def test_build_database_from_archives(tmp_path):
    archive = tmp_path / "part.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("p/NCT00000001.xml", make_trial_xml(nct_id="NCT00000001"))
        z.writestr("p/NCT00000002.xml", make_trial_xml(nct_id="NCT00000002"))
    db_path = tmp_path / "trials.sqlite"

    total = build_trial_database([archive], db_path)

    assert total == 2
    with sqlite3.connect(db_path) as check:
        assert count_trials(check) == 2


def test_build_database_starts_from_scratch_when_the_file_exists(tmp_path):
    archive = tmp_path / "part.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("p/NCT00000001.xml", make_trial_xml(nct_id="NCT00000001"))
    db_path = tmp_path / "trials.sqlite"

    build_trial_database([archive], db_path)
    total = build_trial_database([archive], db_path)

    assert total == 1
