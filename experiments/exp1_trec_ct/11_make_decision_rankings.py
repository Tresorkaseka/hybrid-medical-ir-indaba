#!/usr/bin/env python3
"""Verify complete Colab scores; rerank top50 and retain original positions 51..1000.

No inference, qrels or metrics here. The output is a full 1000-document ranking:
D uses the B prefix and tail; E uses the C prefix and tail. Recall at ranks above
50 therefore includes unchanged first-stage candidates, not additional decisions.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from hybrid_ir.decision.benchmark import QUESTION
from hybrid_ir.decision.reranking import load_checkpoint_scores, rerank_with_scores

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, default=ROOT/'data/processed/decision_inputs.json.gz')
    parser.add_argument('--source-rankings', type=Path, default=ROOT/'results/exp1_rankings_bc.json.gz')
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--provenance', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT/'results/exp1_rankings_de.json.gz')
    args = parser.parse_args()
    inputs_blob = args.inputs.read_bytes()
    inputs = json.loads(gzip.decompress(inputs_blob))
    provenance = json.loads(args.provenance.read_text())
    if provenance.get('input_sha256') != hashlib.sha256(inputs_blob).hexdigest():
        raise ValueError('Input SHA256 differs from expected provenance')
    if provenance.get('prompt_sha256') != hashlib.sha256(QUESTION.encode()).hexdigest():
        raise ValueError('Prompt SHA256 differs from the verified question')
    source_blob = args.source_rankings.read_bytes()
    if inputs['source_rankings_sha256'] != hashlib.sha256(source_blob).hexdigest():
        raise ValueError('Source rankings SHA256 differs from exported candidates')
    source = json.loads(gzip.decompress(source_blob))
    if inputs['doc_ids_sha256'] != source['doc_ids_sha256']:
        raise ValueError('Corpus order differs')
    if inputs['top_n'] != 50 or source['top_k'] != 1000:
        raise ValueError('Expected top50 decisions and top1000 source rankings')
    for config in ('B', 'C'):
        if set(inputs['rankings'][config]) != set(source['rankings'][config]):
            raise ValueError(f'{config}: source query set differs')
        for key, ids in source['rankings'][config].items():
            if len(ids) != 1000 or ids[:50] != inputs['rankings'][config][key]:
                raise ValueError(f'{config}/{key}: source top50 or top1000 differs')
    scores = load_checkpoint_scores(inputs, args.checkpoint, provenance, require_complete=True)
    rankings = rerank_with_scores(source['rankings'], scores)
    result = {'schema_version': 1, 'top_k': 1000, 'rerank_top_n': 50,
              'tail_policy': 'Positions 51..1000 retained from B for D, C for E, in original order',
              'manifest': {'model': provenance['model_id'], 'revision': provenance['revision']},
              'provenance': provenance, 'source_rankings_sha256': inputs['source_rankings_sha256'],
              'checkpoint_sha256': hashlib.sha256(args.checkpoint.read_bytes()).hexdigest(),
              'doc_ids_sha256': inputs['doc_ids_sha256'], 'rankings': rankings}
    blob = gzip.compress(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                                   allow_nan=False).encode(), compresslevel=9, mtime=0)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(blob)
    print(f"{sum(len(v) for v in scores.values())} verified decisions; D/E with 950 unchanged tail candidates per query")
    print(f"{args.output}: {len(blob)} bytes, SHA256 {hashlib.sha256(blob).hexdigest()}")


if __name__ == '__main__':
    main()
