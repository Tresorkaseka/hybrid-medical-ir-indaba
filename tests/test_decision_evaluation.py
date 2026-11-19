"""The prospective family keeps space for unavailable reranker controls."""
import copy

import pytest

from hybrid_ir.evaluation.run_scoring import METRIC_NAMES
from hybrid_ir.evaluation.significance import holm_adjust


def toy_runs():
    judgments = {str(i): {'yes': 2, 'maybe': 1, 'no': 0} for i in range(1, 13)}
    runs = {name: {q: (['yes', 'maybe', 'no'] if name in ('D', 'E') else ['no', 'maybe', 'yes'])
                   for q in judgments} for name in ('BM25', 'A', 'B', 'C', 'D', 'E')}
    return runs, judgments


def test_six_real_systems_are_scored_with_existing_metrics_and_family99():
    from hybrid_ir.evaluation.decision_evaluation import evaluate_decision_runs, PROSPECTIVE_PAIRS
    runs, judgments = toy_runs()
    report = evaluate_decision_runs(runs, judgments)
    assert set(report['systems']) == set(runs)
    assert set(report['per_query']['D']) == set(METRIC_NAMES)
    assert report['systems']['D']['nDCG@10']['mean'] == pytest.approx(1)
    assert report['systems']['D']['nDCG@10']['mean'] > report['systems']['B']['nDCG@10']['mean']
    assert report['values_crosschecked_with_ir_measures'] == 6*12*10
    assert len(report['pairs']) == 11
    assert report['holm_family']['n_tests'] == 99
    assert report['holm_family']['n_observed_tests'] == 63
    assert report['holm_family']['n_reserved_tests'] == 36
    quality = [m for m in METRIC_NAMES if m != 'Judged@10']
    raw = [report['pairs'][f'{a} − {b}'][m]['p'] if a in runs and b in runs else 1.
           for a, b in PROSPECTIVE_PAIRS for m in quality]
    expected = holm_adjust(raw)
    for (a, b), offset in zip(PROSPECTIVE_PAIRS, range(0, 99, 9)):
        key = f'{a} − {b}'
        if a in runs and b in runs:
            assert report['pair_availability'][key] == 'computed'
            assert [report['pairs'][key][m]['p_holm'] for m in quality] == pytest.approx(expected[offset:offset+9])
            assert report['pairs'][key]['Judged@10']['p_holm'] is None
        else:
            assert report['pair_availability'][key] == 'not_computed'
            assert report['pairs'][key]['nDCG@10'] == {'difference': None, 'p': None, 'p_holm': None, 'holm_reserved_p': 1.0}
    assert not {'Dprime', 'Eprime'}.intersection(report['systems'])


@pytest.mark.parametrize('bad', ['missing-system', 'missing-query', 'extra-query', 'duplicate-id', 'empty-judgments'])
def test_missing_or_misaligned_data_fails_instead_of_becoming_zero_scores(bad):
    from hybrid_ir.evaluation.decision_evaluation import evaluate_decision_runs
    runs, judgments = toy_runs()
    if bad == 'missing-system': del runs['D']
    if bad == 'missing-query': del runs['E']['1']
    if bad == 'extra-query': runs['E']['other'] = ['yes']
    if bad == 'duplicate-id': runs['D']['1'] = ['yes', 'yes']
    if bad == 'empty-judgments': judgments = {}
    with pytest.raises(ValueError): evaluate_decision_runs(runs, judgments)


def test_optional_rerankers_fill_the_reserved_tests_without_changing_family():
    from hybrid_ir.evaluation.decision_evaluation import evaluate_decision_runs
    runs, judgments = toy_runs()
    runs['Dprime'] = copy.deepcopy(runs['B'])
    runs['Eprime'] = copy.deepcopy(runs['C'])
    report = evaluate_decision_runs(runs, judgments)
    assert report['holm_family']['n_tests'] == report['holm_family']['n_observed_tests'] == 99
    assert report['holm_family']['n_reserved_tests'] == 0
    assert set(report['pair_availability'].values()) == {'computed'}


def test_orchestrator_runs_on_a_small_corpus_without_touching_old_results(tmp_path):
    import gzip
    import hashlib
    import json
    import sqlite3
    import subprocess
    import sys
    from pathlib import Path
    from hybrid_ir.data.trial_db import create_schema, insert_trials
    from hybrid_ir.data.trial_xml import TrialRecord
    from hybrid_ir.retrieval.bm25 import Bm25Index
    processed = tmp_path/'processed'
    processed.mkdir()
    ids = [f'NCT{i:03}' for i in range(60)]
    Bm25Index.build((i, 'diabetes') for i in ids).save(processed/'bm25_index')
    with sqlite3.connect(processed/'trials.sqlite') as conn:
        create_schema(conn)
        insert_trials(conn, [TrialRecord(i, 'All', None, None, None, None) for i in ids])
    for year in ('2021', '2022'):
        (processed/f'queries_{year}.jsonl').write_text(json.dumps({'query_id': '1', 'text': '45-year-old man diabetes'})+'\n')
        (processed/f'qrels_{year}.tsv').write_text('1\tNCT000\t2\n1\tNCT001\t0\n')
    semantic = {'top_k': 1000, 'doc_ids_sha256': hashlib.sha256('\n'.join(ids).encode()).hexdigest(),
                'rankings': {s: {f'{y}/1': ids for y in ('2021', '2022')} for s in ('B', 'C')}}
    semantic_path = tmp_path/'bc.json.gz'
    semantic_blob = gzip.compress(json.dumps(semantic).encode())
    semantic_path.write_bytes(semantic_blob)
    decision = {'top_k': 1000, 'rerank_top_n': 50, 'doc_ids_sha256': semantic['doc_ids_sha256'],
                'source_rankings_sha256': hashlib.sha256(semantic_blob).hexdigest(),
                'manifest': {'model': 'test Eos', 'revision': 'test-rev'},
                'rankings': {s: {f'{y}/1': [ids[1], ids[0]]+ids[2:] for y in ('2021', '2022')} for s in ('D', 'E')}}
    decision_path = tmp_path/'de.json.gz'
    decision_path.write_bytes(gzip.compress(json.dumps(decision).encode()))
    old_path = tmp_path/'exp1_semantic_bc.json'
    old_path.write_text('original scientific results')
    output = tmp_path/'decision_eos.json'
    script = Path(__file__).resolve().parents[1]/'experiments/exp1_trec_ct/12_evaluate_decision.py'
    args = [sys.executable, str(script), '--processed', str(processed), '--semantic', str(semantic_path),
            '--decision', str(decision_path), '--output', str(output)]
    completed = subprocess.run(args, capture_output=True, text=True)
    assert completed.returncode == 0, completed.stderr
    result = json.loads(output.read_text())
    for year in ('2021', '2022'):
        assert result[year]['n_queries'] == 1
        assert result[year]['holm_family']['n_tests'] == 99
        assert result[year]['holm_family']['n_reserved_tests'] == 36
        assert set(result[year]['systems']) == {'BM25', 'A', 'B', 'C', 'D', 'E'}
        assert result[year]['values_crosschecked_with_ir_measures'] == 60
    assert old_path.read_text() == 'original scientific results'
    decision['rankings']['E']['2022/1'][-1] = 'NCT-unknown'
    decision_path.write_bytes(gzip.compress(json.dumps(decision).encode()))
    failed = subprocess.run(args, capture_output=True, text=True)
    assert failed.returncode != 0


def test_orchestrator_accepts_control_rankings_and_completes_the99_test_family(tmp_path):
    import gzip, hashlib, json, sqlite3, subprocess, sys
    from pathlib import Path
    from hybrid_ir.data.trial_db import create_schema, insert_trials
    from hybrid_ir.data.trial_xml import TrialRecord
    from hybrid_ir.retrieval.bm25 import Bm25Index
    processed = tmp_path/'processed'; processed.mkdir()
    ids = [f'NCT{i:03}' for i in range(60)]
    Bm25Index.build((i,'diabetes') for i in ids).save(processed/'bm25_index')
    with sqlite3.connect(processed/'trials.sqlite') as conn:
        create_schema(conn); insert_trials(conn,[TrialRecord(i,'All',None,None,None,None) for i in ids])
    for year in ('2021','2022'):
        (processed/f'queries_{year}.jsonl').write_text(json.dumps({'query_id':'1','text':'diabetes'})+'\n')
        (processed/f'qrels_{year}.tsv').write_text('1\tNCT000\t2\n1\tNCT001\t0\n')
    corpus_hash=hashlib.sha256('\n'.join(ids).encode()).hexdigest()
    semantic={'top_k':1000,'doc_ids_sha256':corpus_hash,'rankings':{s:{f'{y}/1':ids for y in ('2021','2022')} for s in ('B','C')}}
    src=tmp_path/'bc.gz'; src.write_bytes(gzip.compress(json.dumps(semantic).encode()))
    common={'top_k':1000,'rerank_top_n':50,'doc_ids_sha256':corpus_hash,
            'source_rankings_sha256':hashlib.sha256(src.read_bytes()).hexdigest(), 'manifest':{'model':'test','revision':'rev'}}
    decision={**common,'rankings':{s:{f'{y}/1':ids for y in ('2021','2022')} for s in ('D','E')}}
    controls={**common,'score_kind':'logit','rankings':{s:{f'{y}/1':ids for y in ('2021','2022')} for s in ('Dprime','Eprime')}}
    de=tmp_path/'de.gz'; de.write_bytes(gzip.compress(json.dumps(decision).encode()))
    bge=tmp_path/'controls.gz'; bge.write_bytes(gzip.compress(json.dumps(controls).encode()))
    output=tmp_path/'combined.json'
    script=Path(__file__).resolve().parents[1]/'experiments/exp1_trec_ct/12_evaluate_decision.py'
    proc=subprocess.run([sys.executable,str(script),'--processed',str(processed),'--semantic',str(src),
                         '--decision',str(de),'--controls',str(bge),'--output',str(output)],capture_output=True,text=True)
    assert proc.returncode==0,proc.stderr
    result=json.loads(output.read_text())
    for year in ('2021','2022'):
        assert result[year]['status']=='complete'
        assert result[year]['holm_family']['n_observed_tests']==99
        assert result[year]['holm_family']['n_reserved_tests']==0
        assert result[year]['values_crosschecked_with_ir_measures']==80
        assert set(result[year]['systems'])=={'BM25','A','B','C','D','E','Dprime','Eprime'}
    assert result['status']=='complete'
    # An otherwise identical B run must not be silently accepted inside a D/E file.
    decision['rankings']['B'] = semantic['rankings']['B']
    de.write_bytes(gzip.compress(json.dumps(decision).encode()))
    ambiguous = subprocess.run([sys.executable,str(script),'--processed',str(processed),'--semantic',str(src),
                                '--decision',str(de),'--controls',str(bge),'--output',str(output)],capture_output=True,text=True)
    assert ambiguous.returncode != 0
