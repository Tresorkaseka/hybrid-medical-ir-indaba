#!/usr/bin/env python3
"""Étape 4b : risque du filtre SQL âge/sexe sur les jugements TREC.

Pour chaque requête : âge et sexe extraits par les règles de l'étape 3, filtre SQL, puis comptage des
essais jugés (éligible / exclu / non pertinent) gardés et écartés. Le filtre SQL est recoupé par une
seconde méthode (boucle Python sur la table, sans SQL) ; le script échoue au moindre écart.

Entrées : data/processed/{trials.sqlite, queries_*.jsonl, qrels_*.tsv}
Sortie  : results/exp1_filter_risk.json
"""
import json
import sqlite3
from collections import Counter
from contextlib import closing
from dataclasses import asdict
from pathlib import Path

from hybrid_ir.data.trec_files import load_judgments, load_queries
from hybrid_ir.evaluation.filter_risk import ELIGIBLE, FilterRisk, measure_filter_risk
from hybrid_ir.queries.demographics import extract_demographics
from hybrid_ir.retrieval.trial_filter import eligible_trial_ids

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data/processed"
OUTPUT = ROOT / "results/exp1_filter_risk.json"
YEARS = (2021, 2022)


def kept_without_sql(rows, age, sex) -> set[str]:
    """Seconde méthode, écrite indépendamment du SQL : même règle, boucle Python."""
    kept = set()
    for nct_id, gender, min_age, max_age in rows:
        sex_ok = sex is None or gender in (None, "All", sex)
        low_ok = age is None or min_age is None or min_age <= age
        high_ok = age is None or max_age is None or max_age >= age
        if sex_ok and low_ok and high_ok:
            kept.add(nct_id)
    return kept


def removal_reasons(row, age, sex) -> list[str]:
    _, gender, min_age, max_age = row
    reasons = []
    if sex is not None and gender not in (None, "All", sex):
        reasons.append("sexe")
    if age is not None and min_age is not None and min_age > age:
        reasons.append("âge sous le minimum")
    if age is not None and max_age is not None and max_age < age:
        reasons.append("âge au-dessus du maximum")
    return reasons


def add(total: dict, risk: FilterRisk) -> None:
    for name, value in asdict(risk).items():
        total[name] = total.get(name, 0) + value


def main() -> None:
    with closing(sqlite3.connect(PROCESSED / "trials.sqlite")) as conn:
        rows = conn.execute("SELECT nct_id, gender, min_age_years, max_age_years FROM trials").fetchall()
        rows_by_id = {row[0]: row for row in rows}
        summary, pool_sizes = {"n_trials": len(rows)}, []
        for year in YEARS:
            queries = load_queries(PROCESSED / f"queries_{year}.jsonl")
            judgments = load_judgments(PROCESSED / f"qrels_{year}.tsv")
            total, hurt_queries, reasons = {}, [], Counter()
            for query_id, text in queries.items():
                demographics = extract_demographics(text)
                kept = eligible_trial_ids(conn, demographics.age_years, demographics.sex)
                if kept != kept_without_sql(rows, demographics.age_years, demographics.sex):
                    raise SystemExit(f"ÉCART entre SQL et boucle Python : {year}/{query_id}")
                risk = measure_filter_risk(kept, judgments[query_id])
                add(total, risk)
                for trial_id, level in judgments[query_id].items():
                    if level == ELIGIBLE and trial_id not in kept:
                        reasons[" + ".join(removal_reasons(rows_by_id[trial_id], demographics.age_years, demographics.sex))] += 1
                pool_sizes.append(len(kept))
                if risk.eligible_removed:
                    hurt_queries.append({"query_id": query_id, **asdict(risk)})
            summary[str(year)] = {"n_queries": len(queries), **total, "eligible_removed_by_reason": dict(reasons), "queries_losing_eligible_trials": hurt_queries}
    summary["pool_size"] = {"mean": round(sum(pool_sizes) / len(pool_sizes)), "min": min(pool_sizes), "max": max(pool_sizes)}
    OUTPUT.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for year in YEARS:
        print(year, summary[str(year)]["eligible_removed_by_reason"])
    print("pool_size", summary["pool_size"])


if __name__ == "__main__":
    main()
