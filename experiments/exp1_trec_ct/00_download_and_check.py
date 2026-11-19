#!/usr/bin/env python3
"""Expérience 1, étape 0 : télécharge TREC Clinical Trials 2021 et 2022 et vérifie les effectifs.

Sorties (toutes hors dépôt sauf le JSON de résultats) :
  data/raw/ir_datasets/        archives et caches d'ir_datasets
  data/raw/trec_ct/qrels2022.txt   jugements 2022 (absents d'ir_datasets)
  data/processed/queries_2021.jsonl, queries_2022.jsonl
  data/processed/qrels_2021.tsv, qrels_2022.tsv
  results/exp1_data_check.json
"""
import collections
import hashlib
import json
import os
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
RES = ROOT / "results"
os.environ.setdefault("IR_DATASETS_HOME", str(RAW / "ir_datasets"))

import ir_datasets  # noqa: E402  (doit être importé après IR_DATASETS_HOME)

QRELS_2022_URL = "https://trec.nist.gov/data/trials/qrels2022.txt"
LEVELS = {0: "not_relevant", 1: "excluded", 2: "eligible"}

for d in (RAW / "trec_ct", PROC, RES):
    d.mkdir(parents=True, exist_ok=True)

out = {"ir_datasets_version": ir_datasets.__version__ if hasattr(ir_datasets, "__version__") else None}

# 1. Documents : l'itération déclenche le téléchargement des 5 archives (≈ 1,8 Go) puis l'analyse.
ds21 = ir_datasets.load("clinicaltrials/2021/trec-ct-2021")
ds22 = ir_datasets.load("clinicaltrials/2021/trec-ct-2022")
doc_ids = set()
n_docs = 0
for doc in ds21.docs_iter():
    n_docs += 1
    doc_ids.add(doc.doc_id)
out["n_docs"] = n_docs
out["n_unique_doc_ids"] = len(doc_ids)
print("documents :", n_docs, "ids uniques :", len(doc_ids), flush=True)

# 2. Requêtes
for year, ds in ((2021, ds21), (2022, ds22)):
    qs = list(ds.queries_iter())
    out[f"n_queries_{year}"] = len(qs)
    with open(PROC / f"queries_{year}.jsonl", "w", encoding="utf-8") as f:
        for q in qs:
            f.write(json.dumps({"query_id": q.query_id, "text": q.text}, ensure_ascii=False) + "\n")
    print(f"requêtes {year} :", len(qs), flush=True)

# 3. Jugements 2021 (ir_datasets)
qrels = {2021: [(q.query_id, q.doc_id, int(q.relevance)) for q in ds21.qrels_iter()]}

# 4. Jugements 2022 : téléchargement manuel depuis NIST
dest = RAW / "trec_ct" / "qrels2022.txt"
if not dest.exists():
    # Le serveur NIST refuse (403) l'agent par défaut de Python : on s'identifie explicitement.
    req = urllib.request.Request(QRELS_2022_URL, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) research-script"})
    with urllib.request.urlopen(req) as resp:
        dest.write_bytes(resp.read())
raw = dest.read_bytes()
out["qrels_2022_source"] = QRELS_2022_URL
out["qrels_2022_bytes"] = len(raw)
out["qrels_2022_sha256"] = hashlib.sha256(raw).hexdigest()
rows = []
for line in raw.decode("utf-8").splitlines():
    parts = line.split()
    if len(parts) == 4:
        rows.append((parts[0], parts[2], int(parts[3])))
qrels[2022] = rows

for year, rows in qrels.items():
    with open(PROC / f"qrels_{year}.tsv", "w", encoding="utf-8") as f:
        for qid, did, rel in rows:
            f.write(f"{qid}\t{did}\t{rel}\n")
    by_level = collections.Counter(LEVELS.get(r, str(r)) for _, _, r in rows)
    judged_docs = {d for _, d, _ in rows}
    out[f"qrels_{year}"] = {
        "n_judgments": len(rows),
        "n_topics": len({q for q, _, _ in rows}),
        "n_judged_docs_unique": len(judged_docs),
        "by_level": dict(by_level),
        "judged_docs_missing_from_corpus": len(judged_docs - doc_ids),
    }
    print(f"jugements {year} :", out[f"qrels_{year}"], flush=True)

(RES / "exp1_data_check.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print("écrit results/exp1_data_check.json")
