#!/usr/bin/env python3
"""Exporte le corpus TREC en JSONL (id, texte) et copie les requêtes 2021 pour le banc d'essai BM25.

Usage : IR_DATASETS_HOME=data/raw/ir_datasets .venv/bin/python export_corpus.py <dossier_de_sortie>
"""
import json
import shutil
import sys
from pathlib import Path

import ir_datasets

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
dataset = ir_datasets.load("clinicaltrials/2021/trec-ct-2021")
with open(out / "corpus.jsonl", "w", encoding="utf-8") as f:
    for doc in dataset.docs_iter():
        text = " ".join(x or "" for x in (doc.title, doc.condition, doc.summary, doc.detailed_description, doc.eligibility))
        f.write(json.dumps({"id": doc.doc_id, "text": text}, ensure_ascii=False) + "\n")
shutil.copy(Path(__file__).resolve().parents[3] / "data/processed/queries_2021.jsonl", out / "queries_2021.jsonl")
