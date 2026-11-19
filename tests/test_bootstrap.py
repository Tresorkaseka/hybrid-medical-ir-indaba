"""Intervalles de confiance par bootstrap sur les requêtes (percentiles, graine fixée)."""
import random

import pytest
from hybrid_ir.evaluation.bootstrap import bootstrap_ci, paired_bootstrap_ci


def noisy_scores(n, seed):
    rng = random.Random(seed)
    return [rng.random() for _ in range(n)]


def test_ci_of_constant_scores_is_that_constant():
    result = bootstrap_ci([0.4] * 30)

    assert (result.mean, result.low, result.high) == pytest.approx((0.4, 0.4, 0.4))


def test_ci_contains_the_mean_and_is_reproducible_with_the_same_seed():
    scores = noisy_scores(50, seed=1)

    first, second = bootstrap_ci(scores, seed=7), bootstrap_ci(scores, seed=7)

    assert first == second
    assert first.low <= first.mean <= first.high
    assert first.mean == pytest.approx(sum(scores) / len(scores))


def test_ci_is_narrower_with_more_queries():
    small, large = bootstrap_ci(noisy_scores(20, seed=2)), bootstrap_ci(noisy_scores(500, seed=2))

    assert (large.high - large.low) < (small.high - small.low)


def test_paired_ci_of_identical_systems_is_zero():
    scores = noisy_scores(40, seed=3)

    result = paired_bootstrap_ci(scores, scores)

    assert (result.mean, result.low, result.high) == pytest.approx((0.0, 0.0, 0.0))


def test_paired_ci_excludes_zero_when_one_system_is_always_better():
    base = noisy_scores(40, seed=4)
    better = [score + 0.05 for score in base]

    result = paired_bootstrap_ci(better, base)

    assert result.mean == pytest.approx(0.05)
    assert result.low > 0


def test_paired_ci_includes_zero_when_the_differences_are_noise():
    a, b = noisy_scores(40, seed=5), noisy_scores(40, seed=6)

    result = paired_bootstrap_ci(a, b)

    assert result.low < 0 < result.high


def test_invalid_inputs_are_errors():
    with pytest.raises(ValueError, match="vide"):
        bootstrap_ci([])
    with pytest.raises(ValueError, match="même longueur"):
        paired_bootstrap_ci([0.1, 0.2], [0.1])
