#!/usr/bin/env python3
"""Étape 5c : prépare l'envoi vers Colab pour la recherche par le sens (configurations B et C).

Pour chaque requête : son texte, et le masque des essais gardés par le filtre SQL (âge et sexe extraits
par les règles de l'étape 3), dans l'ordre du corpus. L'empreinte SHA-256 de cet ordre permet au carnet
Colab de vérifier qu'il range les vecteurs exactement comme le PC.

Entrées : data/processed/{bm25_index/metadata.json, trials.sqlite, queries_*.jsonl}
Sortie  : data/processed/search_inputs.json.gz (non versionné, ≈ quelques Mo), à envoyer dans Colab
"""
import gzip
import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path

from hybrid_ir.data.trec_files import load_queries
from hybrid_ir.queries.demographics import extract_demographics
from hybrid_ir.retrieval.masks import pack_kept_mask
from hybrid_ir.retrieval.trial_filter import eligible_trial_ids

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data/processed"
OUTPUT = PROCESSED / "search_inputs.json.gz"


def main() -> None:
    doc_ids = json.loads((PROCESSED / "bm25_index/metadata.json").read_text(encoding="utf-8"))["doc_ids"]
    queries = []
    with closing(sqlite3.connect(PROCESSED / "trials.sqlite")) as conn:
        for year in (2021, 2022):
            for query_id, text in load_queries(PROCESSED / f"queries_{year}.jsonl").items():
                demographics = extract_demographics(text)
                kept = eligible_trial_ids(conn, demographics.age_years, demographics.sex)
                queries.append({"year": year, "query_id": query_id, "text": text, "n_kept": len(kept),
                                "kept_mask": pack_kept_mask(kept, doc_ids)})
    payload = {"n_docs": len(doc_ids), "doc_ids_sha256": hashlib.sha256("\n".join(doc_ids).encode()).hexdigest(), "queries": queries}
    OUTPUT.write_bytes(gzip.compress(json.dumps(payload).encode("utf-8"), 9))
    print(f"{len(queries)} requêtes, {len(doc_ids)} essais, empreinte {payload['doc_ids_sha256'][:12]} -> {OUTPUT} ({OUTPUT.stat().st_size // 1024} Ko)")


if __name__ == "__main__":
    main()
