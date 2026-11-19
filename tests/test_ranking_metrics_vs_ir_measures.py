"""Recoupement de nos métriques avec `ir_measures` (qui enveloppe `trec_eval`, l'outil officiel de TREC).

300 requêtes aléatoires (graine fixée) : jugements sur 0 à 40 essais, classements de 0 à 30 essais
dont certains non jugés. Chaque métrique doit coïncider, requête par requête.
"""
import random

import pytest
from hybrid_ir.evaluation.ranking_metrics import judged_at_k, ndcg_at_k, precision_at_k, r_precision, recall_at_k, reciprocal_rank

ir_measures = pytest.importorskip("ir_measures")

OURS = {
    "nDCG@10": lambda r, j: ndcg_at_k(r, j, 10),
    "P(rel=2)@5": lambda r, j: precision_at_k(r, j, 5),
    "P(rel=2)@10": lambda r, j: precision_at_k(r, j, 10),
    "P(rel=2)@20": lambda r, j: precision_at_k(r, j, 20),
    "R(rel=2)@5": lambda r, j: recall_at_k(r, j, 5),
    "R(rel=2)@10": lambda r, j: recall_at_k(r, j, 10),
    "R(rel=2)@20": lambda r, j: recall_at_k(r, j, 20),
    "Rprec(rel=2)": r_precision,
    "RR(rel=2)": reciprocal_rank,
    "Judged@10": lambda r, j: judged_at_k(r, j, 10),
}


def random_queries(seed=11, n_queries=300):
    rng = random.Random(seed)
    pool = [f"NCT{i:05d}" for i in range(80)]
    for query_id in range(n_queries):
        judged = rng.sample(pool, rng.randint(1, 40))
        judgments = {trial: rng.choice([0, 0, 1, 2]) for trial in judged}
        ranking = rng.sample(pool, rng.randint(1, 30))
        yield str(query_id), ranking, judgments


@pytest.mark.parametrize("measure", OURS)
def test_metric_matches_ir_measures_on_random_queries(measure):
    queries = list(random_queries())
    qrels = [ir_measures.Qrel(q, t, level) for q, _, j in queries for t, level in j.items()]
    run = [ir_measures.ScoredDoc(q, t, float(len(r) - rank)) for q, r, _ in queries for rank, t in enumerate(r)]
    reference = {m.query_id: m.value for m in ir_measures.iter_calc([ir_measures.parse_measure(measure)], qrels, run)}

    for query_id, ranking, judgments in queries:
        if query_id in reference:
            assert OURS[measure](ranking, judgments) == pytest.approx(reference[query_id]), f"{measure}, requête {query_id}"
