import pytest

from hybrid_ir.evaluation.demographics_scoring import GoldLabel, score_extraction
from hybrid_ir.queries.demographics import PatientDemographics

GOLD = {
    "q1": GoldLabel(age_years=45.0, sex="Male"),
    "q2": GoldLabel(age_years=7.0, sex="Female"),
    "q3": GoldLabel(age_years=60.0, sex="Female"),
    "q4": GoldLabel(age_years=3.0, sex="Male"),
}


def test_a_perfect_extraction_scores_one_everywhere():
    predictions = {key: PatientDemographics(label.age_years, label.sex) for key, label in GOLD.items()}

    score = score_extraction(predictions, GOLD)

    assert score.n_queries == 4
    assert score.age.correct == 4 and score.age.wrong == 0 and score.age.abstained == 0
    assert score.sex.correct == 4 and score.sex.wrong == 0 and score.sex.abstained == 0
    assert score.errors == []


def test_a_wrong_value_and_an_abstention_are_counted_separately():
    predictions = {
        "q1": PatientDemographics(45.0, "Male"),
        "q2": PatientDemographics(17.0, None),   # âge faux, sexe non trouvé
        "q3": PatientDemographics(60.0, "Male"),  # sexe faux
        "q4": PatientDemographics(None, "Male"),  # âge non trouvé
    }

    score = score_extraction(predictions, GOLD)

    assert (score.age.correct, score.age.wrong, score.age.abstained) == (2, 1, 1)
    assert (score.sex.correct, score.sex.wrong, score.sex.abstained) == (2, 1, 1)
    assert sorted(error.query_key for error in score.errors) == ["q2", "q3"]


def test_rates_are_derived_from_the_counts():
    predictions = {
        "q1": PatientDemographics(45.0, "Male"),
        "q2": PatientDemographics(17.0, None),
        "q3": PatientDemographics(None, None),
        "q4": PatientDemographics(3.0, "Male"),
    }

    score = score_extraction(predictions, GOLD)

    assert score.age.found_rate == pytest.approx(3 / 4)
    assert score.age.precision == pytest.approx(2 / 3)
    assert score.sex.found_rate == pytest.approx(2 / 4)
    assert score.sex.precision == pytest.approx(1.0)


def test_ages_equal_up_to_rounding_are_the_same():
    predictions = {key: PatientDemographics(label.age_years + 1e-9, label.sex) for key, label in GOLD.items()}

    assert score_extraction(predictions, GOLD).age.correct == 4


def test_every_gold_query_needs_a_prediction():
    with pytest.raises(KeyError):
        score_extraction({"q1": PatientDemographics(45.0, "Male")}, GOLD)
