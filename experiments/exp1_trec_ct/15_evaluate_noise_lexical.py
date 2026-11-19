"""Évalue BM25/A sur les requêtes bruitées figées, sans reconstruire l'index."""
import gzip
import hashlib
import json
import sqlite3
import time
from pathlib import Path

from hybrid_ir.data.trec_files import load_judgments
from hybrid_ir.evaluation.robustness import compare_noisy_to_clean
from hybrid_ir.evaluation.run_scoring import score_run
from hybrid_ir.evaluation.trec_eval_check import crosscheck_with_ir_measures
from hybrid_ir.queries.demographics import extract_demographics
from hybrid_ir.retrieval.bm25 import Bm25Index
from hybrid_ir.retrieval.trial_filter import eligible_trial_ids

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data/processed'


def main():
    noise_bytes = (DATA / 'noise_queries.json').read_bytes()
    noise = json.loads(noise_bytes)
    clean_bytes = (ROOT / 'results/exp1_bm25_and_config_a.json').read_bytes()
    clean = json.loads(clean_bytes)
    index = Bm25Index.load(DATA / 'bm25_index')
    provenance = dict(noise_sha256=hashlib.sha256(noise_bytes).hexdigest(),
        clean_results_sha256=hashlib.sha256(clean_bytes).hexdigest(),
        doc_ids_sha256=hashlib.sha256('\n'.join(index.doc_ids).encode()).hexdigest(),
        top_k=1000, k1=index.k1, b=index.b, seed=noise['seed'])
    report = dict(provenance=provenance, years={})
    all_rankings = {'BM25': {}, 'A': {}}
    started = time.perf_counter()
    with sqlite3.connect(DATA / 'trials.sqlite') as conn:
        for year in ('2021', '2022'):
            judgments = load_judgments(DATA / f'qrels_{year}.tsv')
            report['years'][year] = {}
            for rate, records in noise['noisy'].items():
                runs = {'BM25': {}, 'A': {}}
                for qid in judgments:
                    text = records[f'{year}/{qid}']['text']
                    demographics = extract_demographics(text)
                    allowed = eligible_trial_ids(conn, demographics.age_years, demographics.sex)
                    runs['BM25'][qid] = [h.doc_id for h in index.search(text, 1000)]
                    runs['A'][qid] = [h.doc_id for h in index.search(text, 1000, allowed_doc_ids=allowed)]
                    for system in runs:
                        key = f'{year}/{qid}@noise{round(float(rate)*100):02}'
                        all_rankings[system][key] = runs[system][qid]
                scores = {system: score_run(run, judgments) for system, run in runs.items()}
                checked = sum(crosscheck_with_ir_measures(run, judgments, scores[system])
                              for system, run in runs.items())
                clean_names = {'BM25': 'BM25 (témoin, sans filtre)', 'A': 'Configuration A (filtre SQL + BM25)'}
                comparisons = {system: compare_noisy_to_clean(clean[year]['per_query'][clean_names[system]]['nDCG@10'],
                                                             metrics['nDCG@10'])
                               for system, metrics in scores.items()}
                report['years'][year][rate] = dict(systems=comparisons, per_query=scores,
                                                  values_crosschecked_with_ir_measures=checked)
                print(year, rate, {s: {'clean': v['clean_mean'], 'noisy': v['noisy_mean'],
                                      'relative_loss': v['relative_loss']} for s, v in comparisons.items()}, flush=True)
    report['seconds'] = time.perf_counter() - started
    (ROOT / 'results/exp1_noise_lexical.json').write_text(json.dumps(report, indent=1, ensure_ascii=False)+'\n')
    ranking_payload = dict(provenance=provenance, rankings=all_rankings)
    (ROOT / 'results/exp1_rankings_noise_lexical.json.gz').write_bytes(
        gzip.compress(json.dumps(ranking_payload).encode(), mtime=0))
    print('Terminé en', report['seconds'], 'secondes', flush=True)


if __name__ == '__main__':
    main()
