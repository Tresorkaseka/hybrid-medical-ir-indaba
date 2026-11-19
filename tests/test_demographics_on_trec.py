"""Garde-fou de non-régression : les règles doivent retrouver la vérité terrain vérifiée des 125 requêtes TREC.

Attention : les règles ont été conçues après lecture de ces mêmes requêtes. Ce test protège le
comportement actuel ; il ne mesure pas la généralisation à de nouvelles requêtes.
"""
import importlib.util
from pathlib import Path

import pytest
from hybrid_ir.evaluation.demographics_scoring import score_extraction
from hybrid_ir.queries.demographics import extract_demographics

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments/exp1_trec_ct/03_evaluate_demographics.py"
QUERIES_PRESENT = all((ROOT / f"data/processed/queries_{y}.jsonl").exists() for y in (2021, 2022))


@pytest.mark.skipif(not QUERIES_PRESENT, reason="requêtes TREC absentes (lancer make data)")
def test_rules_agree_with_the_verified_gold_standard_on_every_query():
    spec = importlib.util.spec_from_file_location("evaluate_demographics", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    gold, texts = module.load_gold(), module.load_query_texts()

    score = score_extraction({key: extract_demographics(texts[key]) for key in gold}, gold)

    assert score.errors == []
    assert score.age.abstained == 0 and score.sex.abstained == 0
