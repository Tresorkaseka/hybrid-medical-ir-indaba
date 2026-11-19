import pytest
from hybrid_ir.evaluation.run_scoring import METRIC_NAMES, score_run

JUDGMENTS = {"q1": {"a": 2}, "q2": {"b": 0, "c": 2}, "q3": {"d": 2}}


def test_score_run_gives_every_metric_for_every_judged_query():
    scores = score_run({"q1": ["a"], "q2": ["b"], "q3": ["d"]}, JUDGMENTS)

    assert set(scores) == set(METRIC_NAMES)
    assert all(set(per_query) == {"q1", "q2", "q3"} for per_query in scores.values())


def test_score_run_values_on_a_hand_checked_example():
    scores = score_run({"q1": ["a"], "q2": ["b"], "q3": ["d"]}, JUDGMENTS)

    assert scores["nDCG@10"]["q1"] == pytest.approx(1.0)
    assert scores["P@10"]["q1"] == pytest.approx(0.1)
    assert scores["RPrec"]["q1"] == pytest.approx(1.0)
    assert scores["MRR"]["q1"] == pytest.approx(1.0)
    assert scores["Judged@10"]["q1"] == pytest.approx(1.0)
    assert [scores[name]["q2"] for name in ("nDCG@10", "P@10", "RPrec", "MRR")] == [0.0, 0.0, 0.0, 0.0]
    assert scores["Judged@10"]["q2"] == pytest.approx(1.0)  # b est jugé (non pertinent)


def test_a_query_without_a_ranking_is_scored_as_an_empty_result_list():
    scores = score_run({"q1": ["a"], "q2": ["b"]}, JUDGMENTS)

    assert scores["nDCG@10"]["q3"] == 0.0 and scores["Judged@10"]["q3"] == 0.0


def test_the_reported_metrics_are_those_announced_in_the_paper():
    assert METRIC_NAMES == ("P@5", "P@10", "P@20", "R@5", "R@10", "R@20", "RPrec", "MRR", "nDCG@10", "Judged@10")
