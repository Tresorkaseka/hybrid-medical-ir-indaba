#!/usr/bin/env python3
"""Expérience 1, étape 3 : mesure l'extraction de l'âge et du sexe contre la vérité terrain vérifiée.

Entrées : experiments/exp1_trec_ct/gold/query_demographics_gold.csv, data/processed/queries_*.jsonl
Sortie  : results/exp1_demographics_extraction.json
"""
import csv
import json
from dataclasses import asdict
from pathlib import Path

from hybrid_ir.data.ages import parse_age_in_years
from hybrid_ir.evaluation.demographics_scoring import GoldLabel, score_extraction
from hybrid_ir.queries.demographics import extract_demographics

ROOT = Path(__file__).resolve().parents[2]
GOLD_PATH = ROOT / "experiments/exp1_trec_ct/gold/query_demographics_gold.csv"
OUTPUT = ROOT / "results/exp1_demographics_extraction.json"


def load_gold() -> dict[tuple[int, str], GoldLabel]:
    with open(GOLD_PATH, encoding="utf-8", newline="") as f:
        return {
            (int(row["year"]), row["query_id"]): GoldLabel(
                age_years=parse_age_in_years(f"{row['age_value']} {row['age_unit']}"),
                sex=row["sex"],
            )
            for row in csv.DictReader(f)
        }


def load_query_texts() -> dict[tuple[int, str], str]:
    texts = {}
    for year in (2021, 2022):
        with open(ROOT / f"data/processed/queries_{year}.jsonl", encoding="utf-8") as f:
            for line in f:
                query = json.loads(line)
                texts[(year, query["query_id"])] = query["text"]
    return texts


def field_summary(field_score) -> dict:
    return {
        "correct": field_score.correct,
        "wrong": field_score.wrong,
        "abstained": field_score.abstained,
        "found_rate": round(field_score.found_rate, 4),
        "precision_when_found": round(field_score.precision, 4),
    }


def main() -> None:
    gold, texts = load_gold(), load_query_texts()
    predictions = {key: extract_demographics(texts[key]) for key in gold}
    score = score_extraction(predictions, gold)
    summary = {
        "n_queries": score.n_queries,
        "age": field_summary(score.age),
        "sex": field_summary(score.sex),
        "errors": [
            {**asdict(error), "query_key": f"{error.query_key[0]}/{error.query_key[1]}"} for error in score.errors
        ],
    }
    OUTPUT.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("n_queries", "age", "sex")}, indent=2))
    for error in summary["errors"]:
        print("ERREUR", error)


if __name__ == "__main__":
    main()
