"""Recoupe nos métriques, requête par requête, avec `ir_measures` (qui s'appuie sur `trec_eval`)."""
from collections.abc import Mapping, Sequence

import ir_measures

IR_MEASURES_NAMES = {
    **{f"P@{k}": f"P(rel=2)@{k}" for k in (5, 10, 20)}, **{f"R@{k}": f"R(rel=2)@{k}" for k in (5, 10, 20)},
    "RPrec": "Rprec(rel=2)", "MRR": "RR(rel=2)", "nDCG@10": "nDCG@10", "Judged@10": "Judged@10",
}


class MismatchError(AssertionError):
    pass


def crosscheck_with_ir_measures(
    rankings: Mapping[str, Sequence[str]], judgments: Mapping[str, Mapping[str, int]], scores: Mapping[str, Mapping[str, float]]
) -> int:
    """Lève `MismatchError` au premier écart ; renvoie le nombre de valeurs comparées."""
    qrels = [ir_measures.Qrel(q, t, level) for q, levels in judgments.items() for t, level in levels.items()]
    run = [ir_measures.ScoredDoc(q, t, float(len(r) - rank)) for q, r in rankings.items() for rank, t in enumerate(r)]
    compared = 0
    for name, reference_name in IR_MEASURES_NAMES.items():
        for result in ir_measures.iter_calc([ir_measures.parse_measure(reference_name)], qrels, run):
            ours = scores[name][result.query_id]
            if abs(ours - result.value) > 1e-9:
                raise MismatchError(f"{name}, requête {result.query_id} : {ours} contre {result.value} (ir_measures)")
            compared += 1
    return compared
