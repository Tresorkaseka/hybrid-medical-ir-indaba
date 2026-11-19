import pytest
from hybrid_ir.evaluation.run_scoring import score_run

ir_measures = pytest.importorskip("ir_measures")
from hybrid_ir.evaluation.trec_eval_check import MismatchError, crosscheck_with_ir_measures  # noqa: E402

JUDGMENTS = {"1": {"a": 2, "b": 0, "c": 1}, "2": {"d": 2}}
RANKINGS = {"1": ["b", "a", "z"], "2": ["d"]}


def test_correct_scores_pass_and_return_the_number_of_values_compared():
    assert crosscheck_with_ir_measures(RANKINGS, JUDGMENTS, score_run(RANKINGS, JUDGMENTS)) > 0


def test_a_wrong_value_is_detected():
    scores = score_run(RANKINGS, JUDGMENTS)
    scores["nDCG@10"]["1"] += 0.01

    with pytest.raises(MismatchError, match="nDCG@10"):
        crosscheck_with_ir_measures(RANKINGS, JUDGMENTS, scores)
