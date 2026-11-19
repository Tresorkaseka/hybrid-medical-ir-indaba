"""Fige les requêtes bruitées, évalue âge/sexe et exporte leurs masques pour Colab."""
import csv
import gzip
import hashlib
import json
import sqlite3
from dataclasses import asdict
from pathlib import Path

from hybrid_ir.data.ages import parse_age_in_years
from hybrid_ir.data.trec_files import load_queries
from hybrid_ir.evaluation.demographics_scoring import GoldLabel, score_extraction
from hybrid_ir.queries.demographics import extract_demographics
from hybrid_ir.queries.typo_noise import perturb_queries
from hybrid_ir.retrieval.masks import pack_kept_mask
from hybrid_ir.retrieval.trial_filter import eligible_trial_ids

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data/processed'
SEED = 20261117


def main():
    clean = {f'{year}/{qid}': text for year in (2021, 2022)
             for qid, text in load_queries(DATA / f'queries_{year}.jsonl').items()}
    noisy = perturb_queries(clean, seed=SEED)
    payload = dict(schema_version=1, seed=SEED, rates=[0.05, 0.1],
                   eligible_words='ASCII alphabetic runs of at least 2 letters',
                   counts='nearest integer, half up, minimum 1 if eligible words exist',
                   nested=True, clean=clean, noisy=noisy)
    noise_bytes = (json.dumps(payload, ensure_ascii=False, indent=1) + '\n').encode()
    (DATA / 'noise_queries.json').write_bytes(noise_bytes)
    noise_sha = hashlib.sha256(noise_bytes).hexdigest()
    with (ROOT / 'experiments/exp1_trec_ct/gold/query_demographics_gold.csv').open(newline='') as stream:
        gold = {f"{r['year']}/{r['query_id']}": GoldLabel(
            parse_age_in_years(f"{r['age_value']} {r['age_unit']}"), r['sex']) for r in csv.DictReader(stream)}
    report = dict(seed=SEED, noise_sha256=noise_sha, levels={})
    doc_ids = json.loads((DATA / 'bm25_index/metadata.json').read_text())['doc_ids']
    search_rows = []
    with sqlite3.connect(DATA / 'trials.sqlite') as conn:
        for rate, records in noisy.items():
            predictions = {key: extract_demographics(r['text']) for key, r in records.items()}
            score = score_extraction(predictions, gold)
            report['levels'][rate] = asdict(score)
            for field in ('age', 'sex'):
                fs = getattr(score, field)
                report['levels'][rate][field].update(found_rate=fs.found_rate,
                    precision_when_found=fs.precision, accuracy=fs.correct / score.n_queries)
            for key, record in records.items():
                year, qid = key.split('/')
                demographics = predictions[key]
                kept = eligible_trial_ids(conn, demographics.age_years, demographics.sex)
                search_rows.append(dict(year=int(year), query_id=f'{qid}@noise{round(float(rate)*100):02}',
                    original_key=key, noise_rate=float(rate), text=record['text'], n_kept=len(kept),
                    kept_mask=pack_kept_mask(kept, doc_ids)))
    search = dict(schema_version=1, noise_sha256=noise_sha, n_docs=len(doc_ids),
                  doc_ids_sha256=hashlib.sha256('\n'.join(doc_ids).encode()).hexdigest(), queries=search_rows)
    (DATA / 'search_inputs_noise.json.gz').write_bytes(gzip.compress(json.dumps(search).encode(), mtime=0))
    (ROOT / 'results/exp1_noise_demographics.json').write_text(json.dumps(report, ensure_ascii=False, indent=1)+'\n')
    print('noise_sha256:', noise_sha, '; Colab query rows:', len(search_rows))
    for rate, scores in report['levels'].items():
        print(rate, {field: scores[field] for field in ('age', 'sex')})


if __name__ == '__main__':
    main()
