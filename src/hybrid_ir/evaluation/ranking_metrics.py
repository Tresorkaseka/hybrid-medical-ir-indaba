"""Métriques de classement de TREC Clinical Trials.

`ranking` : identifiants d'essais, du meilleur au moins bon. `judgments` : niveau par essai jugé
(0 non pertinent, 1 exclu, 2 éligible). Un essai absent de `judgments` n'est pas jugé.

- nDCG : le gain d'un essai est son niveau (0, 1 ou 2), escompté par 1 / log2(rang + 1).
- P@k, R@k, R-précision, rang réciproque : seuls les essais éligibles (niveau 2) comptent comme pertinents.
- P@k divise par k même si le classement est plus court (convention de trec_eval).
- Judged@k est la part des résultats renvoyés parmi les k premiers qui ont un jugement : il divise par
  le nombre de résultats renvoyés (au plus k), comme `ir_measures` ; classement vide : 0.
"""
import math
from collections.abc import Mapping, Sequence

from hybrid_ir.evaluation.judgment_levels import ELIGIBLE


def ndcg_at_k(ranking: Sequence[str], judgments: Mapping[str, int], k: int) -> float:
    gains = [judgments.get(trial_id, 0) for trial_id in ranking[:k]]
    ideal_gains = sorted(judgments.values(), reverse=True)[:k]
    ideal = _discounted_sum(ideal_gains)
    return _discounted_sum(gains) / ideal if ideal else 0.0


def precision_at_k(ranking: Sequence[str], judgments: Mapping[str, int], k: int) -> float:
    return _eligible_count(ranking[:k], judgments) / k


def recall_at_k(ranking: Sequence[str], judgments: Mapping[str, int], k: int) -> float:
    """Part des essais éligibles jugés retrouvés parmi les k premiers ; 0 s'il n'y en a aucun."""
    n_eligible = sum(level == ELIGIBLE for level in judgments.values())
    return _eligible_count(ranking[:k], judgments) / n_eligible if n_eligible else 0.0


def r_precision(ranking: Sequence[str], judgments: Mapping[str, int]) -> float:
    n_eligible = sum(level == ELIGIBLE for level in judgments.values())
    return _eligible_count(ranking[:n_eligible], judgments) / n_eligible if n_eligible else 0.0


def reciprocal_rank(ranking: Sequence[str], judgments: Mapping[str, int]) -> float:
    for rank, trial_id in enumerate(ranking, start=1):
        if judgments.get(trial_id) == ELIGIBLE:
            return 1 / rank
    return 0.0


def judged_at_k(ranking: Sequence[str], judgments: Mapping[str, int], k: int) -> float:
    top = ranking[:k]
    return sum(trial_id in judgments for trial_id in top) / len(top) if top else 0.0


def _discounted_sum(gains: Sequence[int]) -> float:
    return sum(gain / math.log2(rank + 1) for rank, gain in enumerate(gains, start=1))


def _eligible_count(trial_ids: Sequence[str], judgments: Mapping[str, int]) -> int:
    return sum(judgments.get(trial_id) == ELIGIBLE for trial_id in trial_ids)
