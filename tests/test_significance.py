"""Test de Wilcoxon apparié et correction de Holm, vérifiés sur des cas calculables à la main."""
import pytest
from hybrid_ir.evaluation.significance import holm_adjust, wilcoxon_p_value


def test_holm_multiplies_by_the_rank_and_keeps_adjusted_values_monotone():
    # triées : 0,01 x 3 = 0,03 ; 0,03 x 2 = 0,06 ; 0,04 x 1 = 0,04 -> 0,06 (jamais plus petite que la précédente)
    assert holm_adjust([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])


def test_holm_never_exceeds_one():
    assert holm_adjust([0.5, 0.6]) == pytest.approx([1.0, 1.0])


def test_wilcoxon_is_one_when_both_systems_score_the_same_on_every_query():
    assert wilcoxon_p_value([0.2, 0.5, 0.1], [0.2, 0.5, 0.1]) == 1.0


def test_wilcoxon_exact_p_value_when_one_system_wins_on_every_query():
    better = [0.1 * i + 0.05 for i in range(1, 21)]
    base = [0.1 * i for i in range(1, 21)]
    better = [b + 0.001 * i for i, b in enumerate(better)]  # écarts tous positifs et tous différents

    assert wilcoxon_p_value(better, base) == pytest.approx(2 / 2**20)  # bilatéral, loi exacte


def test_wilcoxon_rejects_lists_of_different_lengths():
    with pytest.raises(ValueError, match="même longueur"):
        wilcoxon_p_value([0.1, 0.2], [0.1])
