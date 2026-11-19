"""Valide et évalue B/C bruités après retour Colab ; aucune exécution GPU ici."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from hybrid_ir.data.trec_files import load_judgments
from hybrid_ir.evaluation.noisy_rankings import validate_noisy_semantic_run
from hybrid_ir.evaluation.robustness import compare_noisy_to_clean
from hybrid_ir.evaluation.run_scoring import score_run
from hybrid_ir.evaluation.trec_eval_check import crosscheck_with_ir_measures

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data/processed'


def read_gzip(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rankings', type=Path, default=ROOT / 'results/exp1_rankings_bc_noise.json.gz')
    args = parser.parse_args()
    input_blob = (DATA / 'search_inputs_noise.json.gz').read_bytes()
    inputs = json.loads(gzip.decompress(input_blob))
    clean_blob = (ROOT / 'results/exp1_semantic_bc.json').read_bytes()
    clean_scores = json.loads(clean_blob)
    clean_run = read_gzip(ROOT / 'results/exp1_rankings_bc.json.gz')
    result = read_gzip(args.rankings)
    doc_ids = json.loads((DATA / 'bm25_index/metadata.json').read_text())['doc_ids']
    if hashlib.sha256('\n'.join(doc_ids).encode()).hexdigest() != inputs['doc_ids_sha256']:
        raise ValueError('Corpus order differs from frozen noisy input')
    grouped = validate_noisy_semantic_run(result, clean_run, inputs,
        hashlib.sha256(input_blob).hexdigest(), doc_ids)
    report = dict(provenance={k: v for k, v in result.items() if k != 'rankings'},
                  rankings_sha256=hashlib.sha256(args.rankings.read_bytes()).hexdigest(),
                  clean_results_sha256=hashlib.sha256(clean_blob).hexdigest(), years={})
    for rate, years in grouped.items():
        for year, runs in years.items():
            judgments = load_judgments(DATA / f'qrels_{year}.tsv')
            if any(set(run) != set(judgments) for run in runs.values()):
                raise ValueError('Noisy queries differ from clean evaluation query set')
            scores = {system: score_run(run, judgments) for system, run in runs.items()}
            checked = sum(crosscheck_with_ir_measures(run, judgments, scores[system])
                          for system, run in runs.items())
            comparisons = {system: compare_noisy_to_clean(clean_scores[year]['per_query'][system]['nDCG@10'],
                                                         metrics['nDCG@10']) for system, metrics in scores.items()}
            report['years'].setdefault(year, {})[rate] = dict(systems=comparisons, per_query=scores,
                values_crosschecked_with_ir_measures=checked)
            print(year, rate, {s: v['relative_loss'] for s, v in comparisons.items()})
    (ROOT / 'results/exp1_noise_semantic.json').write_text(json.dumps(report, ensure_ascii=False, indent=1)+'\n')


if __name__ == '__main__':
    main()
