"""Compare plusieurs systèmes évalués sur les mêmes requêtes.

Pour chaque système et chaque métrique : moyenne et intervalle à 95 % (bootstrap sur les requêtes).
Pour chaque paire (A, B) : différence A − B requête par requête avec son intervalle, test de Wilcoxon
apparié, et valeur p corrigée par Holm sur toute la famille (toutes les paires × les métriques de `family`).
Une métrique hors famille (par ex. Judged@10) est testée mais pas corrigée.
"""
from collections.abc import Mapping, Sequence

from hybrid_ir.evaluation.bootstrap import bootstrap_ci, paired_bootstrap_ci
from hybrid_ir.evaluation.significance import holm_adjust, wilcoxon_p_value

Scores = Mapping[str, Mapping[str, Mapping[str, float]]]  # système -> métrique -> requête -> valeur


def compare_systems(scores: Scores, query_ids: Sequence[str], pairs: Sequence[tuple[str, str]], family: Sequence[str]) -> dict:
    values = lambda system, metric: [scores[system][metric][q] for q in query_ids]
    systems = {s: {m: vars(bootstrap_ci(values(s, m))) for m in metrics} for s, metrics in scores.items()}
    report_pairs = {}
    for a, b in pairs:
        report_pairs[f"{a} − {b}"] = {
            m: {"difference": vars(paired_bootstrap_ci(values(a, m), values(b, m))), "p": wilcoxon_p_value(values(a, m), values(b, m)), "p_holm": None}
            for m in scores[a]
        }
    tested = [(f"{a} − {b}", m) for a, b in pairs for m in family]
    for (pair, metric), adjusted in zip(tested, holm_adjust([report_pairs[p][m]["p"] for p, m in tested])):
        report_pairs[pair][metric]["p_holm"] = adjusted
    return {"systems": systems, "pairs": report_pairs}
