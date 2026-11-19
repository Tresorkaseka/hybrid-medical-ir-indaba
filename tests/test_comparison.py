"""Comparaison de plusieurs systèmes sur les mêmes requêtes : intervalles par système, différences pairées,
Wilcoxon et Holm appliqué à toute la famille (toutes les paires × toutes les métriques de qualité)."""
import pytest
from hybrid_ir.evaluation.comparison import compare_systems
from hybrid_ir.evaluation.significance import holm_adjust, wilcoxon_p_value

QUERIES = [str(i) for i in range(12)]
SCORES = {
    "X": {"m1": {q: 0.1 * i for i, q in enumerate(QUERIES)}, "m2": {q: 0.5 for q in QUERIES}},
    "Y": {"m1": {q: 0.1 * i + 0.01 * (i % 5 + 1) for i, q in enumerate(QUERIES)}, "m2": {q: 0.5 + 0.02 * (i % 3) for i, q in enumerate(QUERIES)}},
    "Z": {"m1": {q: 0.05 * i for i, q in enumerate(QUERIES)}, "m2": {q: 0.4 for q in QUERIES}},
}


def test_every_system_gets_a_confidence_interval_per_metric():
    report = compare_systems(SCORES, QUERIES, pairs=[("Y", "X")], family=["m1", "m2"])

    assert set(report["systems"]) == {"X", "Y", "Z"}
    assert report["systems"]["X"]["m2"]["mean"] == pytest.approx(0.5)


def test_holm_is_applied_over_every_pair_and_metric_of_the_family():
    pairs = [("Y", "X"), ("Z", "X")]
    report = compare_systems(SCORES, QUERIES, pairs=pairs, family=["m1", "m2"])

    raw = [wilcoxon_p_value([SCORES[a][m][q] for q in QUERIES], [SCORES[b][m][q] for q in QUERIES]) for a, b in pairs for m in ("m1", "m2")]
    expected = holm_adjust(raw)
    got = [report["pairs"][f"{a} − {b}"][m]["p_holm"] for a, b in pairs for m in ("m1", "m2")]
    assert got == pytest.approx(expected)


def test_a_metric_outside_the_family_is_tested_but_not_corrected():
    report = compare_systems(SCORES, QUERIES, pairs=[("Y", "X")], family=["m1"])

    assert report["pairs"]["Y − X"]["m2"]["p_holm"] is None
    assert report["pairs"]["Y − X"]["m2"]["p"] < 1
    assert report["pairs"]["Y − X"]["m1"]["difference"]["mean"] > 0
