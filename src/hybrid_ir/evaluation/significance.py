"""Tests de différence entre deux configurations, requête par requête.

- Wilcoxon des rangs signés, apparié, bilatéral (`scipy.stats.wilcoxon`, méthode « wilcox » : les
  requêtes à écart nul sont écartées). Si toutes les requêtes ont un écart nul, p = 1.
- Correction de Holm pour une famille de tests : la i-ème plus petite valeur p est multipliée par
  (m − i + 1), les valeurs corrigées ne décroissent jamais et sont plafonnées à 1.
"""
from collections.abc import Sequence

import numpy as np
from scipy.stats import wilcoxon


def wilcoxon_p_value(scores_a: Sequence[float], scores_b: Sequence[float]) -> float:
    if len(scores_a) != len(scores_b):
        raise ValueError("les deux listes de scores doivent avoir la même longueur")
    differences = np.asarray(scores_a, dtype=float) - np.asarray(scores_b, dtype=float)
    if not np.any(differences):
        return 1.0
    return float(wilcoxon(differences, zero_method="wilcox", alternative="two-sided").pvalue)


def holm_adjust(p_values: Sequence[float]) -> list[float]:
    order = np.argsort(p_values)
    m = len(p_values)
    adjusted = np.empty(m)
    running_max = 0.0
    for rank, index in enumerate(order):
        running_max = max(running_max, min(1.0, (m - rank) * p_values[index]))
        adjusted[index] = running_max
    return adjusted.tolist()
