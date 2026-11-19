"""Score candidate pairs with strict JSONL checkpoints, without ML dependencies."""
import json
import math
import time
from collections.abc import Callable, Mapping
from pathlib import Path

from hybrid_ir.decision.benchmark import decision_request, yes_probability

PROVENANCE_FIELDS = {'input_sha256', 'model_id', 'revision', 'prompt_sha256'}


def _check_provenance(provenance: dict) -> None:
    if not PROVENANCE_FIELDS.issubset(provenance) or any(
        not isinstance(provenance[k], str) or not provenance[k].strip() for k in PROVENANCE_FIELDS
    ):
        raise ValueError('Missing checkpoint provenance')


def _valid_probability(value: float) -> bool:
    return (not isinstance(value, bool) and isinstance(value, (float, int))
            and math.isfinite(value) and 0 <= value <= 1)


def _validate_rankings(rankings: Mapping, top_n: int) -> None:
    if isinstance(top_n, bool) or not isinstance(top_n, int) or top_n < 1:
        raise ValueError('top_n must be a positive integer')
    if not rankings.get('B') or set(rankings['B']) != set(rankings.get('C', {})):
        raise ValueError('B/C query sets differ or are empty')
    for source in ('B', 'C'):
        for key, ids in rankings[source].items():
            if not isinstance(key, str) or not isinstance(ids, list) or len(ids) < top_n:
                raise ValueError(f'Missing candidates: {source}/{key}')
            if any(not isinstance(i, str) or not i for i in ids) or len(ids) != len(set(ids)):
                raise ValueError(f'Invalid or duplicate candidate: {source}/{key}')


def unique_pairs(payload: dict) -> list[tuple[str, str]]:
    """B then C insertion order, sharing a score only for the same patient/trial."""
    top_n = payload.get('top_n', 50)
    rankings = payload['rankings']
    _validate_rankings(rankings, top_n)
    if set(rankings['B']) != set(payload['queries']):
        raise ValueError('Payload query set differs from rankings')
    pairs = dict.fromkeys((q, trial_id) for source in ('B', 'C')
                          for q, ids in rankings[source].items() for trial_id in ids[:top_n])
    for key, trial_id in pairs:
        if (not isinstance(payload['queries'][key], str) or not payload['queries'][key].strip()
                or not isinstance(payload['trials'].get(trial_id), str) or not payload['trials'][trial_id].strip()):
            raise ValueError(f'Missing input text: {key}/{trial_id}')
    return list(pairs)


def load_checkpoint_scores(payload: dict, checkpoint_path: str | Path, provenance: dict,
                           *, require_complete: bool = False) -> dict[str, dict[str, float]]:
    """Validate the entire file before any reuse; even identical duplicate rows fail."""
    _check_provenance(provenance)
    expected = set(unique_pairs(payload))
    path = Path(checkpoint_path)
    scores = {}
    seen = set()
    if path.exists():
        try:
            text = path.read_text(encoding='utf-8')
            if not text.endswith('\n'):
                raise ValueError('Incomplete checkpoint line')
            rows = text.splitlines()
            header = json.loads(rows[0])
            if header != {'type': 'provenance', 'schema_version': 1, 'provenance': provenance}:
                raise ValueError('Checkpoint provenance differs')
            for line in rows[1:]:
                row = json.loads(line)
                pair = (row['query_key'], row['trial_id'])
                if row.get('type') != 'score' or pair not in expected or pair in seen:
                    raise ValueError(f'Unknown or duplicate checkpoint pair: {pair}')
                probability, seconds = row['probability'], row['seconds']
                if (not _valid_probability(probability) or yes_probability(row['raw']) != probability
                        or isinstance(seconds, bool) or not isinstance(seconds, (float, int))
                        or not math.isfinite(seconds) or seconds < 0):
                    raise ValueError(f'Invalid checkpoint result: {pair}')
                seen.add(pair)
                scores.setdefault(pair[0], {})[pair[1]] = float(probability)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError(f'Invalid checkpoint: {path}') from exc
    if require_complete and seen != expected:
        raise ValueError(f'Incomplete checkpoint: {len(seen)}/{len(expected)} pairs')
    return scores


def score_pairs(payload: dict, scorer: Callable, checkpoint_path: str | Path, provenance: dict,
                on_record: Callable | None = None) -> dict[str, dict[str, float]]:
    """Append, flush and close each valid score before notifying the callback."""
    scores = load_checkpoint_scores(payload, checkpoint_path, provenance)
    pairs = unique_pairs(payload)
    path = Path(checkpoint_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with path.open('x', encoding='utf-8') as stream:
            stream.write(json.dumps({'type': 'provenance', 'schema_version': 1, 'provenance': provenance}, allow_nan=False)+'\n')
            stream.flush()
    for key, trial_id in pairs:
        if trial_id in scores.get(key, {}):
            continue
        start = time.perf_counter()
        raw = scorer(**decision_request(payload['queries'][key], payload['trials'][trial_id]))
        probability = yes_probability(raw)
        record = {'type': 'score', 'query_key': key, 'trial_id': trial_id,
                  'probability': probability, 'raw': raw, 'seconds': time.perf_counter()-start}
        encoded = json.dumps(record, ensure_ascii=False, allow_nan=False)
        with path.open('a', encoding='utf-8') as stream:
            stream.write(encoded+'\n')
            stream.flush()
        scores.setdefault(key, {})[trial_id] = probability
        if on_record is not None:
            on_record(record)
    return scores


def rerank_with_scores(rankings: dict, scores: dict, top_n: int = 50) -> dict:
    """D reranks B, E reranks C; positions after top_n stay in their original order."""
    _validate_rankings(rankings, top_n)
    result = {}
    for source, destination in (('B', 'D'), ('C', 'E')):
        result[destination] = {}
        for key, ids in rankings[source].items():
            for trial_id in ids[:top_n]:
                probability = scores.get(key, {}).get(trial_id)
                if not _valid_probability(probability):
                    raise ValueError(f'Missing or invalid score: {key}/{trial_id}')
            prefix = sorted(ids[:top_n], key=lambda trial_id: -scores[key][trial_id])
            result[destination][key] = prefix + ids[top_n:]
    return result
