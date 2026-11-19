"""Intervalles de confiance par bootstrap sur les requêtes.

On rééchantillonne les requêtes avec remise `n_resamples` fois, on calcule la moyenne de chaque
rééchantillon, et l'intervalle est formé des percentiles de ces moyennes (méthode des percentiles).
La graine est fixée pour que le résultat soit reproductible.
"""
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

DEFAULT_RESAMPLES = 10_000
DEFAULT_CONFIDENCE = 0.95
DEFAULT_SEED = 20261028


@dataclass(frozen=True)
class ConfidenceInterval:
    mean: float
    low: float
    high: float


def bootstrap_ci(
    scores: Sequence[float], n_resamples: int = DEFAULT_RESAMPLES, confidence: float = DEFAULT_CONFIDENCE, seed: int = DEFAULT_SEED
) -> ConfidenceInterval:
    values = np.asarray(scores, dtype=float)
    if values.size == 0:
        raise ValueError("liste de scores vide")
    rng = np.random.default_rng(seed)
    resampled_means = values[rng.integers(0, values.size, size=(n_resamples, values.size))].mean(axis=1)
    tail = (1 - confidence) / 2 * 100
    low, high = np.percentile(resampled_means, [tail, 100 - tail])
    return ConfidenceInterval(mean=float(values.mean()), low=float(low), high=float(high))


def paired_bootstrap_ci(
    scores_a: Sequence[float], scores_b: Sequence[float], n_resamples: int = DEFAULT_RESAMPLES,
    confidence: float = DEFAULT_CONFIDENCE, seed: int = DEFAULT_SEED,
) -> ConfidenceInterval:
    """Intervalle de la différence moyenne A − B, requête par requête (mêmes requêtes dans les deux listes)."""
    if len(scores_a) != len(scores_b):
        raise ValueError("les deux listes de scores doivent avoir la même longueur")
    differences = np.asarray(scores_a, dtype=float) - np.asarray(scores_b, dtype=float)
    return bootstrap_ci(differences, n_resamples, confidence, seed)
