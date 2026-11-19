"""Métriques de classement TREC, vérifiées sur un exemple calculé à la main.

Jugements : a=2 (éligible), b=0, c=1 (exclu), d=2, e=2 (éligible mais jamais retrouvé), « z » non jugé.
"""
import math

import pytest
from hybrid_ir.evaluation.ranking_metrics import judged_at_k, ndcg_at_k, precision_at_k, r_precision, reciprocal_rank

JUDGMENTS = {"a": 2, "b": 0, "c": 1, "d": 2, "e": 2}
RANKING = ["a", "b", "c", "d"]


def test_ndcg_uses_the_level_as_gain_and_a_log2_discount():
    dcg = 2 / math.log2(2) + 0 / math.log2(3) + 1 / math.log2(4) + 2 / math.log2(5)
    ideal = 2 / math.log2(2) + 2 / math.log2(3) + 2 / math.log2(4) + 1 / math.log2(5)

    assert ndcg_at_k(RANKING, JUDGMENTS, k=10) == pytest.approx(dcg / ideal)


def test_ndcg_is_one_for_the_ideal_ranking_and_zero_without_any_relevant_trial():
    assert ndcg_at_k(["a", "d", "e", "c", "b"], JUDGMENTS, k=10) == pytest.approx(1.0)
    assert ndcg_at_k(["a"], {"a": 0, "b": 0}, k=10) == 0.0


def test_ndcg_only_looks_at_the_first_k_results():
    assert ndcg_at_k(["b", "c", "a"], JUDGMENTS, k=2) == pytest.approx(
        (1 / math.log2(3)) / (2 / math.log2(2) + 2 / math.log2(3))
    )


def test_precision_counts_eligible_trials_only_and_divides_by_k():
    assert precision_at_k(RANKING, JUDGMENTS, k=10) == pytest.approx(2 / 10)  # a et d ; c (exclu) ne compte pas


def test_r_precision_uses_the_number_of_eligible_trials_as_cutoff():
    assert r_precision(RANKING, JUDGMENTS) == pytest.approx(1 / 3)  # R = 3 (a, d, e) ; a, b, c -> 1 éligible
    assert r_precision(["a"], {"a": 0}) == 0.0


def test_reciprocal_rank_is_one_over_the_rank_of_the_first_eligible_trial():
    assert reciprocal_rank(RANKING, JUDGMENTS) == 1.0
    assert reciprocal_rank(["b", "c", "d"], JUDGMENTS) == pytest.approx(1 / 3)
    assert reciprocal_rank(["b", "c"], JUDGMENTS) == 0.0


def test_judged_at_k_is_the_share_of_returned_results_that_have_a_judgment():
    assert judged_at_k(["a", "z", "b"], JUDGMENTS, k=10) == pytest.approx(2 / 3)  # 3 résultats renvoyés, 2 jugés
    assert judged_at_k(["a", "z", "b", "d"], JUDGMENTS, k=2) == pytest.approx(1 / 2)  # seuls les 2 premiers comptent
    assert judged_at_k([], JUDGMENTS, k=10) == 0.0


def test_recall_is_the_share_of_all_eligible_trials_found_in_the_first_k():
    from hybrid_ir.evaluation.ranking_metrics import recall_at_k

    assert recall_at_k(RANKING, JUDGMENTS, k=10) == pytest.approx(2 / 3)  # a et d trouvés, e manque
    assert recall_at_k(RANKING, JUDGMENTS, k=1) == pytest.approx(1 / 3)
    assert recall_at_k(["a"], {"a": 0}, k=10) == 0.0  # aucun essai éligible : 0 par convention
