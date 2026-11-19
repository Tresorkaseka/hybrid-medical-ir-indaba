# Banc d'essai des moteurs BM25 (28/10/2026)

Compare `rank-bm25`, `bm25s`, `bm25-turbo` (Rust), `tantivy` (Rust) et un prototype maison à matrice creuse,
sur le corpus TREC Clinical Trials (375 580 essais) et les 75 requêtes 2021. Résultats : `results/exp1_bm25_engine_benchmark.json`.
Justification du choix : `docs/reproducibilite.md`, section « Choix du moteur BM25 ».

Environnement séparé (hors du projet) : Python 3.13.5, `rank-bm25 0.2.2`, `bm25s 0.3.15`, `tantivy 0.27.0`,
`bm25-turbo 0.2.0`, `numpy 2.5.4`, `scipy`.

```bash
IR_DATASETS_HOME=data/raw/ir_datasets .venv/bin/python experiments/exp1_trec_ct/bm25_benchmark/export_corpus.py /tmp/bm25
/chemin/vers/env_banc/bin/python experiments/exp1_trec_ct/bm25_benchmark/bench.py <bibliothèque> <nb_essais> /tmp/bm25
/chemin/vers/env_banc/bin/python experiments/exp1_trec_ct/bm25_benchmark/proto_sparse.py /tmp/bm25
```

Précautions : plafonner la mémoire (`ulimit -v 9500000`) ; `bm25s` et `bm25-turbo` alimentés avec des listes de mots Python
dépassent 10 Go sur le corpus complet et peuvent figer un portable de 15 Go.
