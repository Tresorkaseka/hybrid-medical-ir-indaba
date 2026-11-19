"""Decision reranking, strict resumability and unchanged first-stage tail."""
import json
import math

import pytest


def payload():
    return {'top_n': 2, 'queries': {'2021/1': 'patient one', '2022/1': 'patient two'},
            'trials': {'a': 'trial a', 'b': 'trial b', 'c': 'trial c'},
            'rankings': {'B': {'2021/1': ['a', 'b'], '2022/1': ['a', 'b']},
                         'C': {'2021/1': ['b', 'c'], '2022/1': ['b', 'c']}}}


def provenance():
    return {'input_sha256': 'input-hash', 'model_id': 'Eos', 'revision': 'rev', 'prompt_sha256': 'prompt-hash'}


def response(p):
    return {'answers': {'eligible': {'type': 'noul', 'noul': p}}}


def test_pairs_deduplicate_between_sources_but_never_between_patients():
    from hybrid_ir.decision.reranking import unique_pairs
    assert unique_pairs(payload()) == [('2021/1', 'a'), ('2021/1', 'b'), ('2022/1', 'a'),
                                       ('2022/1', 'b'), ('2021/1', 'c'), ('2022/1', 'c')]


def test_reranking_reorders_only_prefix_stably_and_preserves_tail():
    from hybrid_ir.decision.reranking import rerank_with_scores
    ranks = {'B': {'q': ['a', 'b', 'c', 'd']}, 'C': {'q': ['b', 'a', 'd', 'c']}}
    out = rerank_with_scores(ranks, {'q': {'a': 0.1, 'b': 0.9}}, top_n=2)
    assert out == {'D': {'q': ['b', 'a', 'c', 'd']}, 'E': {'q': ['b', 'a', 'd', 'c']}}
    tied = rerank_with_scores(ranks, {'q': {'a': .5, 'b': .5}}, top_n=2)
    assert tied['D']['q'][:2] == ['a', 'b']
    assert tied['E']['q'][:2] == ['b', 'a']
    assert ranks['B']['q'] == ['a', 'b', 'c', 'd']


@pytest.mark.parametrize('bad', ['missing', 'nan', 'duplicate', 'short', 'years'])
def test_reranking_rejects_missing_invalid_scores_and_rankings(bad):
    from hybrid_ir.decision.reranking import rerank_with_scores
    ranks = {'B': {'q': ['a', 'b', 'c']}, 'C': {'q': ['b', 'a', 'd']}}
    scores = {'q': {'a': .1, 'b': .9}}
    if bad == 'missing': del scores['q']['a']
    if bad == 'nan': scores['q']['a'] = math.nan
    if bad == 'duplicate': ranks['B']['q'][-1] = 'a'
    if bad == 'short': ranks['B']['q'] = ['a']
    if bad == 'years': ranks['C'] = {}
    with pytest.raises(ValueError): rerank_with_scores(ranks, scores, top_n=2)


def test_successes_are_flushed_before_callback_and_resume_never_repeats_a_pair(tmp_path):
    from hybrid_ir.decision.reranking import score_pairs
    checkpoint = tmp_path/'scores.jsonl'
    calls = []
    def scorer(**request):
        calls.append(request)
        return response(.8)
    def stop_after_first(record):
        assert len(checkpoint.read_text().splitlines()) == 2
        assert record['probability'] == .8
        raise RuntimeError('interrupt after saved result')
    with pytest.raises(RuntimeError, match='interrupt'):
        score_pairs(payload(), scorer, checkpoint, provenance(), stop_after_first)
    scores = score_pairs(payload(), scorer, checkpoint, provenance())
    assert len(calls) == 6
    assert scores == {'2021/1': {'a': .8, 'b': .8, 'c': .8}, '2022/1': {'a': .8, 'b': .8, 'c': .8}}
    assert len(checkpoint.read_text().splitlines()) == 7
    assert score_pairs(payload(), scorer, checkpoint, provenance()) == scores
    assert len(calls) == 6
    row = json.loads(checkpoint.read_text().splitlines()[1])
    assert row['raw'] == response(.8)
    assert row['seconds'] >= 0
    assert calls[0]['state'] == {'patient': 'patient one', 'clinical_trial': 'trial a'}


@pytest.mark.parametrize('failure', ['raised', 'invalid'])
def test_model_failure_stops_without_inventing_or_saving_a_score(tmp_path, failure):
    from hybrid_ir.decision.reranking import score_pairs
    checkpoint = tmp_path/'scores.jsonl'
    def scorer(**request):
        if failure == 'raised': raise RuntimeError('GPU failed')
        return response(math.nan)
    with pytest.raises((RuntimeError, ValueError)):
        score_pairs(payload(), scorer, checkpoint, provenance())
    assert len(checkpoint.read_text().splitlines()) == 1


@pytest.mark.parametrize('bad', ['provenance', 'duplicate', 'unknown', 'probability', 'raw-mismatch', 'seconds', 'truncated', 'missing-header'])
def test_corrupt_or_foreign_checkpoint_is_rejected_before_model_call(tmp_path, bad):
    from hybrid_ir.decision.reranking import score_pairs
    checkpoint = tmp_path/'scores.jsonl'
    header = {'type': 'provenance', 'schema_version': 1, 'provenance': provenance()}
    row = {'type': 'score', 'query_key': '2021/1', 'trial_id': 'a', 'probability': .8, 'raw': response(.8), 'seconds': 1.0}
    rows = [header, row]
    if bad == 'provenance': header['provenance']['revision'] = 'wrong'
    if bad == 'duplicate': rows.append(row)
    if bad == 'unknown': row['trial_id'] = 'unknown'
    if bad == 'probability': row['probability'] = 2
    if bad == 'raw-mismatch': row['raw'] = response(.3)
    if bad == 'seconds': row['seconds'] = -1
    if bad == 'missing-header': rows = [row]
    checkpoint.write_text('\n'.join(json.dumps(r) for r in rows)+'\n'+('{' if bad == 'truncated' else ''))
    calls = []
    with pytest.raises(ValueError): score_pairs(payload(), lambda **kw: calls.append(kw), checkpoint, provenance())
    assert not calls


def test_complete_checkpoint_loader_requires_every_expected_pair(tmp_path):
    from hybrid_ir.decision.reranking import load_checkpoint_scores, score_pairs
    checkpoint = tmp_path/'scores.jsonl'
    with pytest.raises(ValueError): load_checkpoint_scores(payload(), checkpoint, provenance(), require_complete=True)
    score_pairs(payload(), lambda **kw: response(.3), checkpoint, provenance())
    assert len(load_checkpoint_scores(payload(), checkpoint, provenance(), require_complete=True)) == 2
    lines = checkpoint.read_text().splitlines()
    checkpoint.write_text('\n'.join(lines[:-1])+'\n')
    with pytest.raises(ValueError): load_checkpoint_scores(payload(), checkpoint, provenance(), require_complete=True)


def test_local_export_verifies_checkpoint_and_preserves_positions_51_to_1000(tmp_path):
    import gzip
    import hashlib
    import subprocess
    import sys
    from pathlib import Path
    from hybrid_ir.decision.benchmark import QUESTION
    from hybrid_ir.decision.reranking import score_pairs
    ids = [f'NCT{i:05}' for i in range(1000)]
    source = {'top_k': 1000, 'doc_ids_sha256': 'order',
              'rankings': {'B': {'2021/1': ids}, 'C': {'2021/1': list(reversed(ids))}}}
    source_bytes = gzip.compress(json.dumps(source).encode())
    source_path = tmp_path/'source.json.gz'
    source_path.write_bytes(source_bytes)
    full = {'schema_version': 1, 'top_n': 50, 'queries': {'2021/1': 'patient'},
            'trials': {i: i for i in ids}, 'doc_ids_sha256': 'order',
            'source_rankings_sha256': hashlib.sha256(source_bytes).hexdigest(),
            'rankings': {s: {q: r[:50] for q, r in qs.items()} for s, qs in source['rankings'].items()}}
    inputs = tmp_path/'input.json.gz'
    inputs.write_bytes(gzip.compress(json.dumps(full).encode()))
    prov = {**provenance(), 'input_sha256': hashlib.sha256(inputs.read_bytes()).hexdigest(),
            'prompt_sha256': hashlib.sha256(QUESTION.encode()).hexdigest()}
    prov_path = tmp_path/'provenance.json'
    prov_path.write_text(json.dumps(prov))
    checkpoint = tmp_path/'score.jsonl'
    score_pairs(full, lambda **kw: response(int(kw['state']['clinical_trial'][3:])/1000), checkpoint, prov)
    output = tmp_path/'rankings.json.gz'
    script = Path(__file__).resolve().parents[1]/'experiments/exp1_trec_ct/11_make_decision_rankings.py'
    args = [sys.executable, str(script), '--inputs', str(inputs), '--source-rankings', str(source_path),
            '--checkpoint', str(checkpoint), '--provenance', str(prov_path), '--output', str(output)]
    completed = subprocess.run(args, capture_output=True, text=True)
    assert completed.returncode == 0, completed.stderr
    exported = json.loads(gzip.decompress(output.read_bytes()))
    assert exported['top_k'] == 1000
    assert exported['rerank_top_n'] == 50
    assert exported['rankings']['D']['2021/1'][:50] == list(reversed(ids[:50]))
    for dest, src in [('D', 'B'), ('E', 'C')]:
        assert exported['rankings'][dest]['2021/1'][50:] == source['rankings'][src]['2021/1'][50:]
        assert len(set(exported['rankings'][dest]['2021/1'])) == 1000
    prov['input_sha256'] = 'wrong'
    prov_path.write_text(json.dumps(prov))
    invalid = subprocess.run(args, capture_output=True, text=True)
    assert invalid.returncode != 0
    assert 'input' in invalid.stderr.lower()


@pytest.mark.parametrize('kind', ['eos', 'bge'])
def test_checkpoint_stream_is_closed_before_each_callback(tmp_path, monkeypatch, kind):
    from pathlib import Path
    from hybrid_ir.decision.reranking import score_pairs
    from hybrid_ir.decision.reranker_control import score_control_pairs
    checkpoint = tmp_path/'closed.jsonl'
    opened = []
    real_open = Path.open

    def track_open(path, mode='r', *args, **kwargs):
        stream = real_open(path, mode, *args, **kwargs)
        if path == checkpoint and mode in ('x', 'a'):
            opened.append(stream)
        return stream

    monkeypatch.setattr(Path, 'open', track_open)
    observed = []
    def callback(record):
        assert opened and all(stream.closed for stream in opened)
        rows = [json.loads(line) for line in checkpoint.read_text().splitlines()]
        assert rows[-1] == record
        observed.append(record)

    if kind == 'eos':
        score_pairs(payload(), lambda **kw: response(.8), checkpoint, provenance(), callback)
    else:
        prov = {**provenance(), 'preprocessing_sha256': 'preprocessing'}
        score_control_pairs(payload(), lambda patient, trial: {'logit': -2.5}, checkpoint, prov, callback)
    assert len(observed) == 6
    assert all(stream.closed for stream in opened)


@pytest.mark.parametrize('kind', ['eos', 'bge'])
def test_checkpoint_close_failure_stops_before_callback(tmp_path, monkeypatch, kind):
    from pathlib import Path
    from hybrid_ir.decision.reranking import score_pairs
    from hybrid_ir.decision.reranker_control import score_control_pairs
    checkpoint = tmp_path/'close-error.jsonl'
    real_open = Path.open
    observed = []

    class CloseFailure:
        def __init__(self, stream): self.stream = stream
        def __enter__(self): return self.stream
        def __exit__(self, *args):
            self.stream.close()
            raise OSError('Drive close failed')

    def failing_open(path, mode='r', *args, **kwargs):
        stream = real_open(path, mode, *args, **kwargs)
        return CloseFailure(stream) if path == checkpoint and mode == 'a' else stream

    monkeypatch.setattr(Path, 'open', failing_open)
    with pytest.raises(OSError, match='Drive close failed'):
        if kind == 'eos':
            score_pairs(payload(), lambda **kw: response(.8), checkpoint, provenance(), observed.append)
        else:
            prov = {**provenance(), 'preprocessing_sha256': 'preprocessing'}
            score_control_pairs(payload(), lambda patient, trial: {'logit': -2.5}, checkpoint, prov, observed.append)
    assert observed == []
    assert len(checkpoint.read_text().splitlines()) == 2
