"""Classical reranker logits are unrestricted real scores, never Eos probabilities."""
import json
import math

import pytest


def payload():
    return {'top_n': 2, 'queries': {'2021/1': 'patient'}, 'trials': {'a': 'trial a', 'b': 'trial b', 'c': 'trial c'},
            'rankings': {'B': {'2021/1': ['a', 'b']}, 'C': {'2021/1': ['b', 'c']}}}


def provenance():
    return {'input_sha256': 'input', 'model_id': 'BGE', 'revision': 'revision', 'preprocessing_sha256': 'prep'}


@pytest.mark.parametrize('logit', [-100., -1.2, 0, .8, 9.3, 100.])
def test_logits_accept_finite_real_values_outside_probability_range(logit):
    from hybrid_ir.decision.reranker_control import relevance_logit
    assert relevance_logit({'logit': logit}) == logit


@pytest.mark.parametrize('raw', [{'logit': math.nan}, {'logit': math.inf}, {'logit': True}, {'logit': '.2'}, {'probability': .8}, {'error': 'oom'}])
def test_invalid_logits_and_probability_contract_are_rejected(raw):
    from hybrid_ir.decision.reranker_control import relevance_logit
    with pytest.raises(ValueError): relevance_logit(raw)


def test_logit_reranking_is_stable_and_preserves_the_tail():
    from hybrid_ir.decision.reranker_control import rerank_with_logits
    ranks = {'B': {'q': ['a', 'b', 'tail']}, 'C': {'q': ['b', 'a', 'other']}}
    assert rerank_with_logits(ranks, {'q': {'a': -8, 'b': 3}}, top_n=2) == {
        'Dprime': {'q': ['b', 'a', 'tail']}, 'Eprime': {'q': ['b', 'a', 'other']}}
    tied = rerank_with_logits(ranks, {'q': {'a': -8, 'b': -8}}, top_n=2)
    assert tied['Dprime']['q'] == ranks['B']['q']
    assert tied['Eprime']['q'] == ranks['C']['q']


def test_checkpoint_flushes_then_resumes_shared_pairs_once(tmp_path):
    from hybrid_ir.decision.reranker_control import score_control_pairs, load_control_scores
    path = tmp_path/'bge.jsonl'
    calls = []
    def scorer(patient, trial):
        calls.append((patient, trial))
        return {'logit': -7.5, 'input_tokens': 50}
    def interrupt(record):
        assert len(path.read_text().splitlines()) == 2
        assert record['logit'] == -7.5 and 'probability' not in record
        raise RuntimeError('interrupt')
    with pytest.raises(RuntimeError): score_control_pairs(payload(), scorer, path, provenance(), interrupt)
    scores = score_control_pairs(payload(), scorer, path, provenance())
    assert len(calls) == 3
    assert scores == {'2021/1': {'a': -7.5, 'b': -7.5, 'c': -7.5}}
    assert load_control_scores(payload(), path, provenance(), require_complete=True) == scores
    score_control_pairs(payload(), scorer, path, provenance())
    assert len(calls) == 3
    header = json.loads(path.read_text().splitlines()[0])
    assert header['score_kind'] == 'logit'


@pytest.mark.parametrize('bad', ['duplicate', 'unknown', 'provenance', 'probability-header', 'raw-mismatch', 'truncated', 'seconds'])
def test_invalid_or_eos_checkpoints_are_rejected_before_scoring(tmp_path, bad):
    from hybrid_ir.decision.reranker_control import score_control_pairs
    path = tmp_path/'bge.jsonl'
    score_control_pairs(payload(), lambda p,t: {'logit': -2.}, path, provenance())
    lines = path.read_text().splitlines()
    header, row = json.loads(lines[0]), json.loads(lines[1])
    if bad == 'duplicate': lines.append(lines[1])
    if bad == 'unknown': row['trial_id'] = 'unknown'
    if bad == 'provenance': header['provenance']['revision'] = 'wrong'
    if bad == 'probability-header': header.pop('score_kind')
    if bad == 'raw-mismatch': row['raw']['logit'] = 5.
    if bad == 'seconds': row['seconds'] = -1
    lines[:2] = [json.dumps(header), json.dumps(row)]
    path.write_text('\n'.join(lines)+'\n'+('{' if bad == 'truncated' else ''))
    calls = []
    with pytest.raises(ValueError): score_control_pairs(payload(), lambda p,t: calls.append(1), path, provenance())
    assert calls == []


def test_model_failure_stops_without_saving_a_logit(tmp_path):
    from hybrid_ir.decision.reranker_control import score_control_pairs, load_control_scores
    path = tmp_path/'bge.jsonl'
    with pytest.raises(ValueError):
        score_control_pairs(payload(), lambda p,t: {'logit': math.nan}, path, provenance())
    assert len(path.read_text().splitlines()) == 1
    with pytest.raises(ValueError): load_control_scores(payload(), path, provenance(), require_complete=True)


def test_length_preflight_counts_full_pairs_and_exposes_overflow_without_truncation():
    from hybrid_ir.decision.reranker_control import audit_control_lengths
    lengths = audit_control_lengths(payload(), lambda p,t: [1]*({'trial a': 3, 'trial b': 5, 'trial c': 9}[t]), max_length=8)
    assert lengths == {'n_pairs': 3, 'n_valid': 2, 'context_limit': 8, 'max_tokens': 9,
                       'invalid': [{'query_key': '2021/1', 'trial_id': 'c', 'tokens': 9}]}


def test_local_control_export_uses_raw_logits_and_retains_source_tail(tmp_path):
    import gzip,hashlib,subprocess,sys
    from pathlib import Path
    from hybrid_ir.decision.reranker_control import (BGE_MODEL, BGE_REVISION, PREPROCESSING_SHA256, score_control_pairs)
    ids = [f'NCT{i:04}' for i in range(1000)]
    source = {'top_k': 1000, 'doc_ids_sha256': 'order', 'rankings': {
        'B': {'2021/1': ids}, 'C': {'2021/1': list(reversed(ids))}}}
    srcpath = tmp_path/'bc.gz'
    srcblob = gzip.compress(json.dumps(source).encode()); srcpath.write_bytes(srcblob)
    full = {'top_n': 50, 'queries': {'2021/1': 'patient'}, 'trials': {i:i for i in ids},
            'rankings': {s: {q:r[:50] for q,r in qs.items()} for s,qs in source['rankings'].items()},
            'source_rankings_sha256': hashlib.sha256(srcblob).hexdigest(), 'doc_ids_sha256': 'order'}
    inpath = tmp_path/'inputs.gz'; inpath.write_bytes(gzip.compress(json.dumps(full).encode()))
    prov = {'input_sha256':hashlib.sha256(inpath.read_bytes()).hexdigest(), 'model_id': BGE_MODEL,
            'revision':BGE_REVISION, 'preprocessing_sha256':PREPROCESSING_SHA256}
    provpath = tmp_path/'provenance.json'; provpath.write_text(json.dumps(prov))
    checkpoint = tmp_path/'bge.jsonl'
    score_control_pairs(full, lambda p,t: {'logit':int(t[3:])-500}, checkpoint, prov)
    output = tmp_path/'controls.gz'
    script = Path(__file__).resolve().parents[1]/'experiments/exp1_trec_ct/13_make_control_rankings.py'
    proc = subprocess.run([sys.executable,str(script),'--inputs',str(inpath),'--source-rankings',str(srcpath),
                           '--checkpoint',str(checkpoint),'--provenance',str(provpath),'--output',str(output)],capture_output=True,text=True)
    assert proc.returncode == 0, proc.stderr
    out = json.loads(gzip.decompress(output.read_bytes()))
    assert out['score_kind'] == 'logit'
    assert set(out['rankings']) == {'Dprime','Eprime'}
    assert out['rankings']['Dprime']['2021/1'][:50] == list(reversed(ids[:50]))
    for dest,src in [('Dprime','B'),('Eprime','C')]:
        assert out['rankings'][dest]['2021/1'][50:] == source['rankings'][src]['2021/1'][50:]


def test_bge_notebook_builder_produces_separate_pinned_offline_valid_artifacts(tmp_path):
    import ast,subprocess,sys,zipfile
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    builder = root/'notebooks/build_bge_control.py'
    proc = subprocess.run([sys.executable,str(builder),'--output-dir',str(tmp_path)],capture_output=True,text=True)
    assert proc.returncode == 0, proc.stderr
    notebook = json.loads((tmp_path/'exp1_bge_control.ipynb').read_text())
    for cell in notebook['cells']:
        if cell['cell_type']=='code': ast.parse(''.join(cell['source']))
    text = ''.join(''.join(c['source']) for c in notebook['cells'])
    assert '953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e' in text
    assert 'truncation=False' in text
    assert 'score_control_pairs' in text
    assert 'exp1_bge_control_top50' in text
    assert 'torch.inference_mode' in text
    assert 'sigmoid' not in text
    with zipfile.ZipFile(tmp_path/'bge_control_code.zip') as z:
        assert 'hybrid_ir/decision/reranker_control.py' in z.namelist()
