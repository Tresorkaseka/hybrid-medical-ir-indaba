"""Immutable complete checkpoint copies, without any remote-upload assertion."""
import json
from pathlib import Path

import pytest


def checkpoint_bytes(count):
    header = {'type': 'provenance', 'schema_version': 1, 'provenance': {'model_id': 'fixed'}}
    rows = [header]+[{'type': 'score', 'query_key': 'q', 'trial_id': str(i), 'probability': .8} for i in range(count)]
    return ('\n'.join(json.dumps(row) for row in rows)+'\n').encode()


@pytest.mark.parametrize('prefix', ['scores', 'scores_logits'])
def test_snapshot_is_complete_closed_and_keeps_checkpoint_bytes(tmp_path, monkeypatch, prefix):
    from hybrid_ir.decision.checkpoint import write_checkpoint_snapshot
    source = tmp_path/'checkpoint.jsonl'
    source.write_bytes(checkpoint_bytes(50))
    real_open, writes = Path.open, []
    def track(path, mode='r', *args, **kwargs):
        stream = real_open(path, mode, *args, **kwargs)
        if mode == 'xb': writes.append(stream)
        return stream
    monkeypatch.setattr(Path, 'open', track)
    result = write_checkpoint_snapshot(source, 50, prefix=prefix)
    assert result == tmp_path/f'{prefix}-00050.jsonl'
    assert result.read_bytes() == source.read_bytes()
    assert writes and all(stream.closed for stream in writes)
    assert write_checkpoint_snapshot(source, 50, prefix=prefix) == result


def test_snapshot_never_overwrites_different_existing_content(tmp_path):
    from hybrid_ir.decision.checkpoint import write_checkpoint_snapshot
    source = tmp_path/'checkpoint.jsonl'; source.write_bytes(checkpoint_bytes(1))
    destination = tmp_path/'scores-00001.jsonl'; destination.write_bytes(b'old artifact\n')
    with pytest.raises(ValueError, match='differs'):
        write_checkpoint_snapshot(source, 1)
    assert destination.read_bytes() == b'old artifact\n'


@pytest.mark.parametrize('bad', ['count', 'truncated', 'header', 'json', 'prefix'])
def test_snapshot_refuses_invalid_or_mislabelled_checkpoint(tmp_path, bad):
    from hybrid_ir.decision.checkpoint import write_checkpoint_snapshot
    source = tmp_path/'checkpoint.jsonl'; blob = checkpoint_bytes(1)
    if bad == 'truncated': blob = blob[:-1]
    if bad == 'header': blob = b'{}\n'+blob.split(b'\n',1)[1]
    if bad == 'json': blob = b'{\n'+blob.split(b'\n',1)[1]
    source.write_bytes(blob)
    with pytest.raises(ValueError):
        write_checkpoint_snapshot(source, 2 if bad == 'count' else 1, prefix='../bad' if bad == 'prefix' else 'scores')
    assert list(tmp_path.glob('scores-*.jsonl')) == []


@pytest.mark.parametrize('driver,name,prefix', [
    ('run_decision_full_colab.py', 'show_progress', 'scores'),
    ('run_bge_control_colab.py', 'progress', 'scores_logits'),
])
def test_driver_callback_writes_full_snapshot_at_fifty_without_remote_claim(
        tmp_path, capsys, driver, name, prefix):
    import ast
    import types
    from hybrid_ir.decision.checkpoint import write_checkpoint_snapshot
    source = Path(__file__).resolve().parents[1]/'notebooks'/driver
    tree = ast.parse(source.read_text())
    callback = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)
    checkpoint = tmp_path/'checkpoint.jsonl'; checkpoint.write_bytes(checkpoint_bytes(50))
    scope = {'counter': [49], 'all_pairs': list(range(100)), 'pairs': list(range(100)),
             'CHECKPOINT': checkpoint, 'write_checkpoint_snapshot': write_checkpoint_snapshot,
             'completed': 0, 'start': 0, 'time': types.SimpleNamespace(perf_counter=lambda: 1)}
    exec(compile(ast.Module(body=[callback], type_ignores=[]), str(source), 'exec'), scope)
    scope[name]({'seconds': .5})
    assert (tmp_path/f'{prefix}-00050.jsonl').read_bytes() == checkpoint.read_bytes()
    assert 'publication Drive non vérifiée' in capsys.readouterr().out
