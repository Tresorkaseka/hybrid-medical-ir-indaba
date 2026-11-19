#!/usr/bin/env python3
"""Export top-50 B/C texts and a balanced 24-pair benchmark, without judgments."""
import gzip
import hashlib
import json
import time
from pathlib import Path

import ir_datasets

from hybrid_ir.data.trial_conditions import iter_trial_conditions
from hybrid_ir.decision.candidates import (
    candidate_rankings, compose_trial_text, make_benchmark_inputs, make_decision_inputs,
)

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / 'data/processed'
RANKINGS = ROOT / 'results/exp1_rankings_bc.json.gz'


def main() -> None:
    started = time.monotonic()
    source_bytes = RANKINGS.read_bytes()
    source = json.loads(gzip.decompress(source_bytes))
    search = json.loads(gzip.decompress((PROCESSED / 'search_inputs.json.gz').read_bytes()))
    _, ranks = candidate_rankings(search, source)
    needed = {trial_id for ranking in ranks.values() for ids in ranking.values() for trial_id in ids}
    print(f'{len(needed)} trial texts required', flush=True)
    archives = sorted((ROOT / 'data/raw/ir_datasets/clinicaltrials').glob('docs_2021_*.zip'))
    if not archives:
        raise ValueError('No local clinicaltrials XML archives')
    conditions = {}
    for archive in archives:
        for trial in iter_trial_conditions(archive):
            if trial.nct_id in needed:
                if trial.nct_id in conditions:
                    raise ValueError(f'Duplicate XML trial: {trial.nct_id}')
                conditions[trial.nct_id] = trial.conditions
    if set(conditions) != needed:
        raise ValueError(f'Missing XML trials: {sorted(needed - set(conditions))[:5]}')
    print('Corrected XML conditions loaded', flush=True)
    texts = {}
    for doc in ir_datasets.load('clinicaltrials/2021/trec-ct-2021').docs_iter():
        if doc.doc_id in needed:
            if doc.doc_id in texts:
                raise ValueError(f'Duplicate corpus trial: {doc.doc_id}')
            texts[doc.doc_id] = compose_trial_text(doc, conditions[doc.doc_id])
    payload = make_decision_inputs(search, source, texts,
                                  source_rankings_sha256=hashlib.sha256(source_bytes).hexdigest())
    benchmark = make_benchmark_inputs(payload)
    outputs = {}
    for name, data in [('decision_inputs.json.gz', payload), ('decision_benchmark_inputs.json.gz', benchmark)]:
        blob = gzip.compress(json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode(), compresslevel=9, mtime=0)
        (PROCESSED / name).write_bytes(blob)
        outputs[name] = {'sha256': hashlib.sha256(blob).hexdigest(), 'bytes': len(blob),
                         'n_queries': len(data['queries']), 'n_trials': len(data['trials'])}
    manifest = {'schema_version': 1, 'top_n': 50, 'source_rankings_sha256': payload['source_rankings_sha256'],
                'doc_ids_sha256': payload['doc_ids_sha256'], 'files': outputs,
                'benchmark_pairs': benchmark['benchmark_pairs'], 'elapsed_seconds': round(time.monotonic()-started, 3)}
    (PROCESSED / 'decision_inputs_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
