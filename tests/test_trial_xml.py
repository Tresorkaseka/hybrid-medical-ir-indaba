import pytest

from helpers import make_trial_xml
from hybrid_ir.data.trial_xml import TrialRecord, parse_trial_xml


def test_reads_all_structured_fields():
    record = parse_trial_xml(
        make_trial_xml(
            nct_id="NCT00000102",
            gender="Female",
            minimum_age="6 Months",
            maximum_age="65 Years",
            healthy_volunteers="Accepts Healthy Volunteers",
            phase="Phase 1/Phase 2",
        )
    )

    assert record == TrialRecord(
        nct_id="NCT00000102",
        gender="Female",
        min_age_years=0.5,
        max_age_years=65.0,
        accepts_healthy_volunteers=True,
        phase="Phase 1/Phase 2",
    )


def test_healthy_volunteers_no_means_false():
    record = parse_trial_xml(make_trial_xml(healthy_volunteers="No"))
    assert record.accepts_healthy_volunteers is False


def test_fields_missing_from_the_file_become_none():
    record = parse_trial_xml(
        make_trial_xml(gender=None, minimum_age=None, maximum_age=None, healthy_volunteers=None, phase=None)
    )

    assert record.gender is None
    assert record.min_age_years is None
    assert record.max_age_years is None
    assert record.accepts_healthy_volunteers is None
    assert record.phase is None


def test_not_applicable_age_bounds_become_none():
    record = parse_trial_xml(make_trial_xml(minimum_age="N/A", maximum_age="N/A"))

    assert record.min_age_years is None
    assert record.max_age_years is None


def test_unknown_gender_fails_loudly():
    with pytest.raises(ValueError, match="gender"):
        parse_trial_xml(make_trial_xml(gender="Other"))


def test_unknown_healthy_volunteers_value_fails_loudly():
    with pytest.raises(ValueError, match="healthy_volunteers"):
        parse_trial_xml(make_trial_xml(healthy_volunteers="Maybe"))


def test_record_without_nct_id_fails_loudly():
    xml = b"<clinical_study><eligibility><gender>All</gender></eligibility></clinical_study>"
    with pytest.raises(ValueError, match="nct_id"):
        parse_trial_xml(xml)
