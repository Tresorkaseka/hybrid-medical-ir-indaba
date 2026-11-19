from hybrid_ir.evaluation.filter_risk import FilterRisk, measure_filter_risk

NOT_RELEVANT, EXCLUDED, ELIGIBLE = 0, 1, 2


def test_counts_kept_and_removed_trials_at_each_judgment_level():
    judgments = {"a": ELIGIBLE, "b": ELIGIBLE, "c": EXCLUDED, "d": NOT_RELEVANT, "e": NOT_RELEVANT, "f": NOT_RELEVANT}

    risk = measure_filter_risk(kept_ids={"a", "c", "d"}, judgments=judgments)

    assert risk == FilterRisk(
        eligible_total=2, eligible_removed=1,
        excluded_total=1, excluded_removed=0,
        not_relevant_total=3, not_relevant_removed=2,
    )


def test_a_kept_trial_without_judgment_is_ignored():
    risk = measure_filter_risk(kept_ids={"zzz"}, judgments={"a": ELIGIBLE})

    assert risk.eligible_total == 1 and risk.eligible_removed == 1


def test_an_unknown_judgment_level_is_an_error():
    import pytest

    with pytest.raises(ValueError, match="niveau"):
        measure_filter_risk(kept_ids=set(), judgments={"a": 7})
