"""Closed immutable checkpoint copies; local persistence is not a cloud receipt."""
import json
from pathlib import Path


def write_checkpoint_snapshot(checkpoint_path: str | Path, count: int,
                              *, prefix: str = 'scores') -> Path:
    """Copy the entire closed JSONL verbatim, rejecting mismatches and overwrites."""
    if (isinstance(count, bool) or not isinstance(count, int) or count < 0
            or prefix not in ('scores', 'scores_logits')):
        raise ValueError('Invalid snapshot count or prefix')
    source = Path(checkpoint_path)
    blob = source.read_bytes()
    try:
        rows = [json.loads(line) for line in blob.decode('utf-8').splitlines()]
        if (not blob.endswith(b'\n') or len(rows) != count + 1
                or rows[0].get('type') != 'provenance'
                or rows[0].get('schema_version') != 1
                or not isinstance(rows[0].get('provenance'), dict)):
            raise ValueError('Incomplete or mislabelled snapshot checkpoint')
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError, IndexError) as exc:
        raise ValueError('Invalid snapshot checkpoint') from exc
    target = source.parent / f'{prefix}-{count:05d}.jsonl'
    try:
        with target.open('xb') as stream:
            stream.write(blob)
            stream.flush()
    except FileExistsError:
        if target.read_bytes() != blob:
            raise ValueError(f'Existing snapshot differs: {target}')
    return target
