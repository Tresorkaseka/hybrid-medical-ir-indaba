#!/usr/bin/env python3
"""Étape 5a : tire 500 essais au hasard (graine fixée) pour le test d'encodage EmbeddingGemma 2 sur Colab.

Chaque essai garde ses champs séparés (titre, conditions lues dans le XML brut, résumé, description,
critères) pour que le carnet Colab mesure plusieurs façons de composer le texte à encoder.
Tirage uniforme sur les 375 580 essais (échantillonnage par réservoir).

Usage  : IR_DATASETS_HOME=data/raw/ir_datasets .venv/bin/python experiments/exp1_trec_ct/07_make_embedding_sample.py
Sortie : data/processed/embedding_sample_500.json.gz (non versionné), à envoyer dans Colab
"""
import gzip
import json
import random
from pathlib import Path

import ir_datasets

from hybrid_ir.data.trial_conditions import iter_trial_conditions

ROOT = Path(__file__).resolve().parents[2]
ARCHIVES = sorted((ROOT / "data/raw/ir_datasets/clinicaltrials").glob("docs_2021_*.zip"))
OUTPUT = ROOT / "data/processed/embedding_sample_500.json.gz"
SAMPLE_SIZE, SEED = 500, 20261028


def main() -> None:
    conditions = {t.nct_id: list(t.conditions) for archive in ARCHIVES for t in iter_trial_conditions(archive)}
    rng, sample = random.Random(SEED), []
    for position, doc in enumerate(ir_datasets.load("clinicaltrials/2021/trec-ct-2021").docs_iter()):
        trial = {
            "id": doc.doc_id, "title": doc.title or "", "conditions": conditions.get(doc.doc_id, []),
            "summary": doc.summary or "", "detailed_description": doc.detailed_description or "",
            "eligibility": doc.eligibility or "",
        }
        if len(sample) < SAMPLE_SIZE:
            sample.append(trial)
        elif (slot := rng.randint(0, position)) < SAMPLE_SIZE:
            sample[slot] = trial
    OUTPUT.write_bytes(gzip.compress(json.dumps(sample, ensure_ascii=False).encode("utf-8"), 9))
    with_conditions = sum(bool(t["conditions"]) for t in sample)
    print(f"{len(sample)} essais ({with_conditions} avec conditions) -> {OUTPUT} ({OUTPUT.stat().st_size // 1024} Ko)")


if __name__ == "__main__":
    main()
