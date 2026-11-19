#!/usr/bin/env python3
"""Étape 4 : construit l'index BM25 maison sur les 375 580 essais TREC et le sauvegarde.

Texte indexé d'un essai : titre, conditions, résumé, description détaillée, critères d'éligibilité.
Les conditions (maladies visées) sont lues dans le XML brut : le champ `condition` d'`ir_datasets` est vide
pour tous les essais (défaut découvert le 28/10/2026 ; l'index d'avant, sans conditions, est conservé dans
results/exp1_bm25_index_build_without_conditions.json).
Réglages k1=0,9 et b=0,4 : défauts de Pyserini, fixés avant tout résultat.

Usage  : IR_DATASETS_HOME=data/raw/ir_datasets .venv/bin/python experiments/exp1_trec_ct/04_build_bm25_index.py
Entrées: corpus `clinicaltrials/2021/trec-ct-2021` (ir_datasets) et archives XML docs_2021_*.zip (conditions)
Sorties: data/processed/bm25_index/ (non versionné) ; results/exp1_bm25_index_build.json (versionné)
"""
import json
import resource
import time
from pathlib import Path

import ir_datasets

from hybrid_ir.data.trial_conditions import iter_trial_conditions
from hybrid_ir.retrieval.bm25 import Bm25Index

ROOT = Path(__file__).resolve().parents[2]
INDEX_DIR = ROOT / "data/processed/bm25_index"
SUMMARY_PATH = ROOT / "results/exp1_bm25_index_build.json"
ARCHIVES = sorted((ROOT / "data/raw/ir_datasets/clinicaltrials").glob("docs_2021_*.zip"))
TEXT_FIELDS = ("title", "conditions (XML brut)", "summary", "detailed_description", "eligibility")


def load_conditions() -> dict[str, str]:
    return {t.nct_id: "; ".join(t.conditions) for archive in ARCHIVES for t in iter_trial_conditions(archive)}


def trial_documents(conditions: dict[str, str]):
    for doc in ir_datasets.load("clinicaltrials/2021/trec-ct-2021").docs_iter():
        parts = (doc.title, conditions.get(doc.doc_id, ""), doc.summary, doc.detailed_description, doc.eligibility)
        yield doc.doc_id, " ".join(part or "" for part in parts)


def main() -> None:
    if not ARCHIVES:
        raise SystemExit("archives XML absentes : lancer make data")
    started = time.perf_counter()
    conditions = load_conditions()
    index = Bm25Index.build(trial_documents(conditions))
    build_seconds = time.perf_counter() - started
    index.save(INDEX_DIR)
    summary = {
        "n_documents": len(index.doc_ids),
        "n_distinct_words": len(index._vocabulary),
        "k1": index.k1,
        "b": index.b,
        "text_fields": list(TEXT_FIELDS),
        "n_trials_with_conditions": sum(bool(text) for text in conditions.values()),
        "build_seconds": round(build_seconds, 1),
        "peak_memory_gb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2, 2),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
