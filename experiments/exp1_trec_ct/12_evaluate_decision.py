#!/usr/bin/env python3
"""Evaluate BM25/A/B/C/D/E without altering previous evaluation files.

BM25/A are replayed with the fixed existing index, demographics and SQL filter.
B/C and D/E come from verified saved rankings. Seven observable comparisons
share a prospective 99-test Holm family with 36 reserved p=1 positions for four
unavailable reranker-control comparisons. No witness scores are fabricated.
"""
import argparse
import gzip
import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path

from hybrid_ir.data.trec_files import load_judgments, load_queries
from hybrid_ir.evaluation.decision_evaluation import PROSPECTIVE_PAIRS, evaluate_decision_runs
from hybrid_ir.queries.demographics import extract_demographics
from hybrid_ir.retrieval.bm25 import Bm25Index
from hybrid_ir.retrieval.trial_filter import eligible_trial_ids

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--processed', type=Path, default=ROOT/'data/processed')
    parser.add_argument('--semantic', type=Path, default=ROOT/'results/exp1_rankings_bc.json.gz')
    parser.add_argument('--decision', type=Path, default=ROOT/'results/exp1_rankings_de.json.gz')
    parser.add_argument('--controls', type=Path, help='Optional verified Dprime/Eprime BGE rankings')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.output is None:
        args.output = ROOT/('results/exp1_decision_eos_bge.json' if args.controls else 'results/exp1_decision_eos.json')
    forbidden = {args.semantic.resolve(), args.decision.resolve(),
                 (ROOT/'results/exp1_semantic_bc.json').resolve(),
                 (ROOT/'results/exp1_bm25_and_config_a.json').resolve()}
    if args.controls:
        forbidden.add(args.controls.resolve())
        forbidden.add((ROOT/'results/exp1_decision_eos.json').resolve())
    if args.output.resolve() in forbidden:
        raise ValueError('Output must not overwrite source or previous evaluation results')
    semantic_bytes, decision_bytes = args.semantic.read_bytes(), args.decision.read_bytes()
    semantic = json.loads(gzip.decompress(semantic_bytes))
    decision = json.loads(gzip.decompress(decision_bytes))
    if set(semantic['rankings']) != {'B', 'C'} or set(decision['rankings']) != {'D', 'E'}:
        raise ValueError('B/C and D/E files must each contain exactly their own systems')
    controls_bytes = args.controls.read_bytes() if args.controls else None
    controls = json.loads(gzip.decompress(controls_bytes)) if controls_bytes is not None else None
    if semantic['top_k'] != 1000 or decision['top_k'] != 1000 or decision['rerank_top_n'] != 50:
        raise ValueError('Expected top1000 source rankings and top50 reranking')
    if decision['source_rankings_sha256'] != hashlib.sha256(semantic_bytes).hexdigest():
        raise ValueError('D/E source rankings SHA256 differs from B/C')
    if controls is not None:
        if (controls['top_k'] != 1000 or controls['rerank_top_n'] != 50 or controls.get('score_kind') != 'logit'
                or set(controls['rankings']) != {'Dprime', 'Eprime'}
                or controls['source_rankings_sha256'] != hashlib.sha256(semantic_bytes).hexdigest()):
            raise ValueError('Control rankings kind, metadata or source differs')
    index = Bm25Index.load(args.processed/'bm25_index')
    corpus_hash = hashlib.sha256('\n'.join(index.doc_ids).encode()).hexdigest()
    if semantic['doc_ids_sha256'] != corpus_hash or decision['doc_ids_sha256'] != corpus_hash:
        raise ValueError('Rankings corpus order differs from the local index')
    if controls is not None and controls['doc_ids_sha256'] != corpus_hash:
        raise ValueError('Control corpus order differs from the local index')
    corpus_ids = set(index.doc_ids)
    queries_by_year = {str(year): load_queries(args.processed/f'queries_{year}.jsonl') for year in (2021, 2022)}
    expected_keys = {f'{year}/{q}' for year, queries in queries_by_year.items() for q in queries}
    all_runs = {**semantic['rankings'], **decision['rankings']}
    expected_systems = {'B', 'C', 'D', 'E'}
    if controls is not None:
        all_runs.update(controls['rankings'])
        expected_systems.update({'Dprime', 'Eprime'})
    if set(all_runs) != expected_systems:
        raise ValueError('Expected exactly B/C/D/E incoming systems')
    for config, run in all_runs.items():
        if set(run) != expected_keys:
            raise ValueError(f'{config}: missing or extra query IDs')
        for key, ids in run.items():
            if not 50 <= len(ids) <= 1000 or not set(ids).issubset(corpus_ids):
                raise ValueError(f'{config}/{key}: missing candidates or unknown trial IDs')
    reranked_sources = [('D', 'B'), ('E', 'C')]
    if controls is not None:
        reranked_sources += [('Dprime', 'B'), ('Eprime', 'C')]
    for config, source in reranked_sources:
        for key, ids in all_runs[config].items():
            original = all_runs[source][key]
            if len(ids) != len(original) or set(ids[:50]) != set(original[:50]) or ids[50:] != original[50:]:
                raise ValueError(f'{config}/{key}: top50 pool or unchanged tail differs')
    results = {'schema_version': 1, 'status': 'complete' if controls is not None else 'intermediate_baselines_pending',
               'top_k': 1000, 'rerank_top_n': 50, 'n_trials': len(index.doc_ids),
               'bm25': {'k1': index.k1, 'b': index.b}, 'model': decision['manifest'],
               'pairs': [f'{a} − {b}' for a, b in PROSPECTIVE_PAIRS],
               'input_sha256': {'B/C': hashlib.sha256(semantic_bytes).hexdigest(),
                                'D/E': hashlib.sha256(decision_bytes).hexdigest()},
               'tail_policy': 'D/E positions 51..1000 retain the B/C first-stage order'}
    if controls is not None:
        results['control_model'] = controls['manifest']
        results['input_sha256']['Dprime/Eprime'] = hashlib.sha256(controls_bytes).hexdigest()
    with closing(sqlite3.connect(args.processed/'trials.sqlite')) as conn:
        for year, queries in queries_by_year.items():
            qrels_path = args.processed/f'qrels_{year}.tsv'
            judgments = load_judgments(qrels_path)
            if set(queries) != set(judgments):
                raise ValueError(f'{year}: query and judgment IDs differ')
            lexical = {'BM25': {}, 'A': {}}
            for key, text in queries.items():
                lexical['BM25'][key] = [hit.doc_id for hit in index.search(text, 1000)]
                demographics = extract_demographics(text)
                kept = eligible_trial_ids(conn, demographics.age_years, demographics.sex)
                lexical['A'][key] = [hit.doc_id for hit in index.search(text, 1000, allowed_doc_ids=kept)]
            runs = {**lexical, **{config: {key: run[f'{year}/{key}'] for key in queries}
                                 for config, run in all_runs.items()}}
            report = evaluate_decision_runs(runs, judgments)
            results[year] = {'n_queries': len(queries), 'qrels_sha256': hashlib.sha256(qrels_path.read_bytes()).hexdigest(), **report}
            print(f"{year}: {len(queries)} queries; {report['values_crosschecked_with_ir_measures']} values crosschecked; 99 Holm slots ({report['holm_family']['n_reserved_tests']} reserved)")
            print('nDCG@10: ' + ', '.join(f"{system}={report['systems'][system]['nDCG@10']['mean']:.4f}" for system in runs))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, ensure_ascii=False, indent=1, allow_nan=False)+'\n', encoding='utf-8')
    print(args.output)


if __name__ == '__main__':
    main()
