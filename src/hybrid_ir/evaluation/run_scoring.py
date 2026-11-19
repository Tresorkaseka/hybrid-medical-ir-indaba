"""Les cinq métriques, requête par requête, pour les classements d'un système."""
from collections.abc import Mapping, Sequence

from hybrid_ir.evaluation.ranking_metrics import (
    judged_at_k, ndcg_at_k, precision_at_k, r_precision, recall_at_k, reciprocal_rank,
)

_METRICS = {
    **{f"P@{k}": (lambda k: lambda ranking, judgments: precision_at_k(ranking, judgments, k))(k) for k in (5, 10, 20)},
    **{f"R@{k}": (lambda k: lambda ranking, judgments: recall_at_k(ranking, judgments, k))(k) for k in (5, 10, 20)},
    "RPrec": r_precision,
    "MRR": reciprocal_rank,
    "nDCG@10": lambda ranking, judgments: ndcg_at_k(ranking, judgments, 10),
    "Judged@10": lambda ranking, judgments: judged_at_k(ranking, judgments, 10),
}
METRIC_NAMES = tuple(_METRICS)


def score_run(
    rankings: Mapping[str, Sequence[str]], judgments: Mapping[str, Mapping[str, int]]
) -> dict[str, dict[str, float]]:
    """`{métrique: {requête: valeur}}` pour chaque requête jugée ; sans classement, liste de résultats vide."""
    return {
        name: {query_id: metric(rankings.get(query_id, []), levels) for query_id, levels in judgments.items()}
        for name, metric in _METRICS.items()
    }
