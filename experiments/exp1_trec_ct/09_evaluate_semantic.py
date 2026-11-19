#!/usr/bin/env python3
"""Étape 5d : évalue les configurations B (sens seul) et C (filtre SQL + sens) face à BM25 et A.

Les classements B et C viennent du carnet Colab (`exp1_rankings_bc.json.gz`) ; leur ordre des essais est
vérifié par empreinte contre l'index BM25 du PC. Les scores par requête de BM25 et A sont repris de
l'étape 4c. Chaque valeur de B et C est recoupée avec `ir_measures`.

Paires comparées : B − BM25 (sens contre mots), A − BM25 et C − B (apport du filtre), C − A (sens contre
mots, filtre des deux côtés). Holm sur toute la famille d'une année : 4 paires × 9 métriques de qualité.

Usage  : .venv/bin/python experiments/exp1_trec_ct/09_evaluate_semantic.py [classements.json.gz] [sortie.json]
Entrées: results/exp1_rankings_bc.json.gz, results/exp1_bm25_and_config_a.json, data/processed/{qrels_*.tsv, bm25_index/metadata.json}
Sortie : results/exp1_semantic_bc.json
"""
import gzip
import hashlib
import json
import sys
from pathlib import Path

from hybrid_ir.data.trec_files import load_judgments
from hybrid_ir.evaluation.comparison import compare_systems
from hybrid_ir.evaluation.run_scoring import METRIC_NAMES, score_run
from hybrid_ir.evaluation.trec_eval_check import crosscheck_with_ir_measures

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data/processed"
RANKINGS = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "results/exp1_rankings_bc.json.gz"
OUTPUT = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "results/exp1_semantic_bc.json"
LEXICAL = ROOT / "results/exp1_bm25_and_config_a.json"
LEXICAL_NAMES = {"BM25": "BM25 (témoin, sans filtre)", "A": "Configuration A (filtre SQL + BM25)"}
PAIRS = [("B", "BM25"), ("A", "BM25"), ("C", "B"), ("C", "A")]
QUALITY_METRICS = [name for name in METRIC_NAMES if name != "Judged@10"]


def check_corpus_order(semantic: dict) -> None:
    doc_ids = json.loads((PROCESSED / "bm25_index/metadata.json").read_text(encoding="utf-8"))["doc_ids"]
    if semantic["doc_ids_sha256"] != hashlib.sha256("\n".join(doc_ids).encode()).hexdigest():
        raise SystemExit("ordre des essais du carnet différent de celui du PC : ne pas évaluer")


def main() -> None:
    semantic = json.loads(gzip.decompress(RANKINGS.read_bytes()))
    check_corpus_order(semantic)
    lexical = json.loads(LEXICAL.read_text(encoding="utf-8"))
    results = {"top_k": semantic["top_k"], "model": semantic["manifest"]["model"], "revision": semantic["manifest"]["revision"],
               "pairs": [f"{a} − {b}" for a, b in PAIRS], "holm_family": "4 paires × 9 métriques de qualité, par année"}
    for year in ("2021", "2022"):
        judgments = load_judgments(PROCESSED / f"qrels_{year}.tsv")
        query_ids = sorted(judgments, key=int)
        scores = {short: lexical[year]["per_query"][long] for short, long in LEXICAL_NAMES.items()}
        compared = 0
        for config in ("B", "C"):
            rankings = {key.split("/")[1]: ids for key, ids in semantic["rankings"][config].items() if key.startswith(year + "/")}
            scores[config] = score_run(rankings, judgments)
            compared += crosscheck_with_ir_measures(rankings, judgments, scores[config])
        report = compare_systems(scores, query_ids, PAIRS, QUALITY_METRICS)
        results[year] = {"n_queries": len(query_ids), "values_crosschecked_with_ir_measures": compared, **report,
                         "per_query": {config: scores[config] for config in ("B", "C")}}
        print(f"\n=== TREC CT {year} : {len(query_ids)} requêtes, {compared} valeurs de B et C recoupées avec ir_measures ===")
        print("moyennes      " + "  ".join(f"{s:>6s}" for s in ("BM25", "A", "B", "C")))
        for metric in METRIC_NAMES:
            print(f"{metric:12s}  " + "  ".join(f"{report['systems'][s][metric]['mean']:6.3f}" for s in ("BM25", "A", "B", "C")))
        for pair, metrics in report["pairs"].items():
            m = metrics["nDCG@10"]
            print(f"{pair:10s} nDCG@10 {m['difference']['mean']:+.3f} [{m['difference']['low']:+.3f} ; {m['difference']['high']:+.3f}]  p_Holm {m['p_holm']:.2g}")
    OUTPUT.write_text(json.dumps(results, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
