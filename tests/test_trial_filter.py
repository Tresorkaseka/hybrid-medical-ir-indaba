"""Filtre SQL âge/sexe. Règle : une information absente dans l'essai n'écarte jamais l'essai."""
import sqlite3

import pytest
from hybrid_ir.data.trial_db import create_schema, insert_trials
from hybrid_ir.data.trial_xml import TrialRecord
from hybrid_ir.retrieval.trial_filter import eligible_trial_ids


def trial(nct_id, gender="All", min_age=None, max_age=None):
    return TrialRecord(nct_id, gender, min_age, max_age, None, None)


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    create_schema(connection)
    yield connection
    connection.close()


def ids(conn, trials, age_years, sex):
    insert_trials(conn, trials)
    return eligible_trial_ids(conn, age_years=age_years, sex=sex)


def test_keeps_trials_whose_age_range_contains_the_patient(conn):
    trials = [trial("in", min_age=18, max_age=65), trial("young", min_age=2, max_age=17), trial("old", min_age=70, max_age=90)]

    assert ids(conn, trials, 40.0, "Male") == {"in"}


def test_age_bounds_are_inclusive(conn):
    trials = [trial("lower", min_age=18, max_age=65), trial("upper", min_age=10, max_age=18)]

    assert ids(conn, trials, 18.0, "Male") == {"lower", "upper"}


def test_a_missing_age_bound_means_no_constraint(conn):
    trials = [trial("no_min", max_age=65), trial("no_max", min_age=18), trial("no_bounds"), trial("too_old", max_age=30)]

    assert ids(conn, trials, 50.0, "Female") == {"no_min", "no_max", "no_bounds"}


def test_all_gender_trials_accept_either_sex_and_others_only_their_own(conn):
    trials = [trial("all", "All"), trial("men", "Male"), trial("women", "Female")]

    assert ids(conn, trials, 40.0, "Female") == {"all", "women"}


def test_a_missing_gender_means_no_constraint(conn):
    trials = [trial("unknown", gender=None), trial("men", "Male")]

    assert ids(conn, trials, 40.0, "Female") == {"unknown"}


def test_a_patient_without_age_or_sex_gets_no_filter_on_that_field(conn):
    trials = [trial("old_men", "Male", 70, 90), trial("young_women", "Female", 2, 17)]
    insert_trials(conn, trials)

    assert eligible_trial_ids(conn, age_years=None, sex="Male") == {"old_men"}
    assert eligible_trial_ids(conn, age_years=5.0, sex=None) == {"young_women"}
    assert eligible_trial_ids(conn, age_years=None, sex=None) == {"old_men", "young_women"}


def test_an_unknown_sex_value_is_an_error(conn):
    with pytest.raises(ValueError, match="sexe"):
        eligible_trial_ids(conn, age_years=40.0, sex="M")
