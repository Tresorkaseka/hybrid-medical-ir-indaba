#!/usr/bin/env python3
"""Étape 4c : évalue le témoin BM25 (sans filtre) et la configuration A (filtre SQL + BM25).

Même BM25 dans les deux cas (index de l'étape 4, k1 = 0,9 et b = 0,4, texte complet de la requête) ;
seule différence : A ne classe que les essais gardés par le filtre âge/sexe. Les 1000 premiers
résultats sont gardés (la R-précision a besoin d'aller jusqu'au nombre d'essais éligibles).

Métriques par requête (`score_run`), moyennes avec intervalle de confiance à 95 % par bootstrap sur les
requêtes, et différence A − BM25 pairée. Chaque valeur par requête est recoupée avec `ir_measures`.

Entrées : data/processed/{bm25_index/, trials.sqlite, queries_*.jsonl, qrels_*.tsv}
Sortie  : results/exp1_bm25_and_config_a.json
"""
import json
import sqlite3
import time
from contextlib import closing
from pathlib import Path

import ir_measures
from hybrid_ir.data.trec_files import load_judgments, load_queries
from hybrid_ir.evaluation.bootstrap import bootstrap_ci, paired_bootstrap_ci
from hybrid_ir.evaluation.run_scoring import METRIC_NAMES, score_run
from hybrid_ir.evaluation.significance import holm_adjust, wilcoxon_p_value
from hybrid_ir.queries.demographics import extract_demographics
from hybrid_ir.retrieval.bm25 import Bm25Index
from hybrid_ir.retrieval.trial_filter import eligible_trial_ids

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data/processed"
OUTPUT = ROOT / "results/exp1_bm25_and_config_a.json"
YEARS = (2021, 2022)
TOP_K = 1000
BASELINE, CONFIG_A = "BM25 (témoin, sans filtre)", "Configuration A (filtre SQL + BM25)"
IR_MEASURES_NAMES = {
    **{f"P@{k}": f"P(rel=2)@{k}" for k in (5, 10, 20)}, **{f"R@{k}": f"R(rel=2)@{k}" for k in (5, 10, 20)},
    "RPrec": "Rprec(rel=2)", "MRR": "RR(rel=2)", "nDCG@10": "nDCG@10", "Judged@10": "Judged@10",
}
QUALITY_METRICS = [name for name in METRIC_NAMES if name != "Judged@10"]  # famille de Holm : les 9 métriques de qualité


def run_systems(index, conn, queries):
    baseline, config_a = {}, {}
    for query_id, text in queries.items():
        baseline[query_id] = [hit.doc_id for hit in index.search(text, TOP_K)]
        demographics = extract_demographics(text)
        kept = eligible_trial_ids(conn, demographics.age_years, demographics.sex)
        config_a[query_id] = [hit.doc_id for hit in index.search(text, TOP_K, allowed_doc_ids=kept)]
    return {BASELINE: baseline, CONFIG_A: config_a}


def crosscheck_with_ir_measures(rankings, judgments, scores) -> int:
    """Compare chaque valeur par requête à `ir_measures` ; renvoie le nombre de valeurs comparées."""
    qrels = [ir_measures.Qrel(q, t, level) for q, levels in judgments.items() for t, level in levels.items()]
    run = [ir_measures.ScoredDoc(q, t, float(len(r) - rank)) for q, r in rankings.items() for rank, t in enumerate(r)]
    compared = 0
    for name, reference_name in IR_MEASURES_NAMES.items():
        measure = ir_measures.parse_measure(reference_name)
        for result in ir_measures.iter_calc([measure], qrels, run):
            ours = scores[name][result.query_id]
            if abs(ours - result.value) > 1e-9:
                raise SystemExit(f"ÉCART avec ir_measures : {name}, requête {result.query_id} : {ours} contre {result.value}")
            compared += 1
    return compared


def summarize(scores_by_system, query_ids):
    summary = {}
    for system, scores in scores_by_system.items():
        summary[system] = {
            name: vars(bootstrap_ci([scores[name][q] for q in query_ids])) for name in METRIC_NAMES
        }
    a, b = scores_by_system[CONFIG_A], scores_by_system[BASELINE]
    summary["différence A − BM25 (pairée)"] = {
        name: vars(paired_bootstrap_ci([a[name][q] for q in query_ids], [b[name][q] for q in query_ids])) for name in METRIC_NAMES
    }
    p_values = {name: wilcoxon_p_value([a[name][q] for q in query_ids], [b[name][q] for q in query_ids]) for name in METRIC_NAMES}
    holm = dict(zip(QUALITY_METRICS, holm_adjust([p_values[name] for name in QUALITY_METRICS])))
    summary["Wilcoxon A − BM25"] = {
        name: {"p": p_values[name], "p_holm": holm.get(name)} for name in METRIC_NAMES
    }
    return summary


def main() -> None:
    index = Bm25Index.load(PROCESSED / "bm25_index")
    results = {"top_k": TOP_K, "k1": index.k1, "b": index.b, "n_trials": len(index.doc_ids)}
    with closing(sqlite3.connect(PROCESSED / "trials.sqlite")) as conn:
        for year in YEARS:
            queries = load_queries(PROCESSED / f"queries_{year}.jsonl")
            judgments = load_judgments(PROCESSED / f"qrels_{year}.tsv")
            started = time.perf_counter()
            rankings = run_systems(index, conn, queries)
            seconds = time.perf_counter() - started
            scores_by_system = {system: score_run(r, judgments) for system, r in rankings.items()}
            compared = sum(crosscheck_with_ir_measures(rankings[s], judgments, scores_by_system[s]) for s in rankings)
            query_ids = sorted(judgments, key=int)
            results[str(year)] = {
                "n_queries": len(query_ids),
                "queries_without_eligible_trial": sum(2 not in levels.values() for levels in judgments.values()),
                "search_seconds": round(seconds, 1),
                "values_crosschecked_with_ir_measures": compared,
                "summary": summarize(scores_by_system, query_ids),
                "per_query": scores_by_system,
            }
            print(f"\n=== TREC CT {year} : {len(query_ids)} requêtes, {compared} valeurs recoupées avec ir_measures ===")
            summary = results[str(year)]["summary"]
            for system in (BASELINE, CONFIG_A, "différence A − BM25 (pairée)"):
                print(system)
                for name, ci in summary[system].items():
                    print(f"   {name:10s} {ci['mean']:+.4f}  [{ci['low']:+.4f} ; {ci['high']:+.4f}]")
            print("Wilcoxon A − BM25 : p (p corrigé par Holm)")
            for name, test in summary["Wilcoxon A − BM25"].items():
                holm_text = "—" if test["p_holm"] is None else f"{test['p_holm']:.2g}"
                print(f"   {name:10s} {test['p']:.2g} ({holm_text})")
    OUTPUT.write_text(json.dumps(results, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
