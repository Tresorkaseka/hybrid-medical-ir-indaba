#!/usr/bin/env python3
"""Expérience 1, étape 1 : longueur des essais et des requêtes en tokens (piste 3 validée).

Question : quelle part des essais dépasse la limite de lecture du modèle de décision ?
Le tokenizer est celui de Decision-2.0-Eos-0.8B (Qwen3.5), version épinglée ; seul tokenizer.json
(≈ 20 Mo) est téléchargé, aucun code du dépôt n'est exécuté.

Mesures par essai (en tokens) :
  core = titre + condition + critères d'éligibilité   (ce que le modèle doit lire)
  elig = critères d'éligibilité seuls
  full = tous les champs

Sorties : data/processed/trial_lengths.csv (hors dépôt), results/exp1_trial_lengths.json
"""
import csv
import json
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
RES = ROOT / "results"
os.environ.setdefault("IR_DATASETS_HOME", str(RAW / "ir_datasets"))

import numpy as np  # noqa: E402
import ir_datasets  # noqa: E402
from huggingface_hub import hf_hub_download  # noqa: E402
from tokenizers import Tokenizer  # noqa: E402

REPO = "vllm-sr/Decision-2.0-Eos-0.8B"
REVISION = "52cad37ef21f598302fe964cbfa164739cb965d5"
BATCH = 2000
PROMPT_OVERHEAD = 150  # tokens estimés pour l'instruction et la question
CTX_LIMITS = [512, 1024, 2048, 4096, 8192, 16384]
PCTS = [50, 75, 90, 95, 99, 99.9]

tok_path = hf_hub_download(REPO, "tokenizer.json", revision=REVISION,
                           local_dir=RAW / "tokenizers" / "eos-0.8b")
tok = Tokenizer.from_file(tok_path)


def n_tokens(texts):
    return [len(e.ids) for e in tok.encode_batch(texts, add_special_tokens=False)]


def s(x):
    return x if isinstance(x, str) else ""


ds = ir_datasets.load("clinicaltrials/2021/trec-ct-2021")
ids, elig, core, full = [], [], [], []
buf = []


def flush():
    if not buf:
        return
    e = n_tokens([b[1] for b in buf])
    c = n_tokens([b[2] for b in buf])
    f = n_tokens([b[3] for b in buf])
    ids.extend(b[0] for b in buf)
    elig.extend(e)
    core.extend(c)
    full.extend(f)
    buf.clear()


for i, d in enumerate(ds.docs_iter(), 1):
    t, c, e = s(d.title), s(d.condition), s(d.eligibility)
    buf.append((d.doc_id, e, f"{t}\n{c}\n{e}",
                f"{t}\n{c}\n{s(d.summary)}\n{s(d.detailed_description)}\n{e}"))
    if len(buf) >= BATCH:
        flush()
        if (i // BATCH) % 25 == 0:
            print(f"{i} essais traités", flush=True)
flush()

elig, core, full = map(np.array, (elig, core, full))
with open(PROC / "trial_lengths.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["doc_id", "tok_elig", "tok_core", "tok_full"])
    w.writerows(zip(ids, elig.tolist(), core.tolist(), full.tolist()))


def summary(arr):
    return {
        "n": int(len(arr)),
        "mean": round(float(arr.mean()), 1),
        "max": int(arr.max()),
        "percentiles": {str(p): int(np.percentile(arr, p)) for p in PCTS},
    }


def exceed(arr, extra=0):
    return {str(k): round(float((arr + extra > k).mean()) * 100, 2) for k in CTX_LIMITS}


# requêtes (descriptions de patients)
q_tokens = {}
for year in (2021, 2022):
    texts = [json.loads(line)["text"] for line in open(PROC / f"queries_{year}.jsonl", encoding="utf-8")]
    q_tokens[year] = np.array(n_tokens(texts))

# essais jugés (2021 + 2022)
judged = set()
for year in (2021, 2022):
    for line in open(PROC / f"qrels_{year}.tsv", encoding="utf-8"):
        judged.add(line.split("\t")[1])
mask = np.array([i in judged for i in ids])

q_max = int(max(q_tokens[2021].max(), q_tokens[2022].max()))
out = {
    "tokenizer": {"repo": REPO, "revision": REVISION},
    "prompt_overhead_tokens": PROMPT_OVERHEAD,
    "all_trials": {"elig": summary(elig), "core": summary(core), "full": summary(full)},
    "judged_trials": {"elig": summary(elig[mask]), "core": summary(core[mask]), "full": summary(full[mask])},
    "queries": {str(y): summary(a) for y, a in q_tokens.items()},
    "percent_of_trials_over_limit": {
        "note": "requête la plus longue + core + surcoût d'instruction > limite de contexte",
        "all_trials_core_plus_longest_query": exceed(core, q_max + PROMPT_OVERHEAD),
        "judged_trials_core_plus_longest_query": exceed(core[mask], q_max + PROMPT_OVERHEAD),
        "all_trials_core_only": exceed(core),
        "all_trials_full_only": exceed(full),
    },
}
(RES / "exp1_trial_lengths.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(out, indent=2, ensure_ascii=False))
