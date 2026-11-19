"""Classical cross-encoder controls: real logits, separate from decision probabilities."""
import hashlib
import json
import math
import time
from collections.abc import Callable
from pathlib import Path

from hybrid_ir.decision.reranking import unique_pairs, _validate_rankings

BGE_MODEL = 'BAAI/bge-reranker-v2-m3'
BGE_REVISION = '953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e'
BGE_MAX_LENGTH = 8192
PREPROCESSING = {'input': ['patient description', 'complete trial embedding text'],
                 'pair_tokenization': True, 'add_special_tokens': True,
                 'truncation': False, 'maximum_pair_tokens': BGE_MAX_LENGTH,
                 'normalization': 'none', 'score_kind': 'raw sequence-classification logit'}
PREPROCESSING_SHA256 = hashlib.sha256(json.dumps(PREPROCESSING, sort_keys=True).encode()).hexdigest()


def relevance_logit(raw: dict) -> float:
    value = raw.get('logit') if isinstance(raw, dict) else None
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or 'error' in raw):
        raise ValueError(f'Invalid reranker logit: {raw!r}')
    return float(value)


def load_control_scores(payload: dict, checkpoint_path: str | Path, provenance: dict,
                        *, require_complete: bool = False) -> dict:
    fields = {'input_sha256', 'model_id', 'revision', 'preprocessing_sha256'}
    if not fields.issubset(provenance) or any(not isinstance(provenance[k], str) or not provenance[k] for k in fields):
        raise ValueError('Missing reranker provenance')
    expected = set(unique_pairs(payload))
    path, scores, seen = Path(checkpoint_path), {}, set()
    if path.exists():
        try:
            text = path.read_text(encoding='utf-8')
            if not text.endswith('\n'):
                raise ValueError('Incomplete reranker checkpoint line')
            lines = text.splitlines()
            if json.loads(lines[0]) != {'type': 'provenance', 'schema_version': 1, 'score_kind': 'logit', 'provenance': provenance}:
                raise ValueError('Reranker checkpoint provenance or score kind differs')
            for line in lines[1:]:
                row = json.loads(line)
                pair = row['query_key'], row['trial_id']
                if row['type'] != 'logit_score' or pair not in expected or pair in seen:
                    raise ValueError(f'Unknown or duplicate reranker pair: {pair}')
                logit = relevance_logit(row)
                if relevance_logit(row['raw']) != logit:
                    raise ValueError(f'Raw logit differs: {pair}')
                seconds = row['seconds']
                if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds < 0:
                    raise ValueError(f'Invalid scoring time: {pair}')
                seen.add(pair)
                scores.setdefault(pair[0], {})[pair[1]] = logit
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError(f'Invalid reranker checkpoint: {path}') from exc
    if require_complete and seen != expected:
        raise ValueError(f'Incomplete reranker checkpoint: {len(seen)}/{len(expected)}')
    return scores


def score_control_pairs(payload: dict, scorer: Callable, checkpoint_path: str | Path,
                        provenance: dict, on_record: Callable | None = None) -> dict:
    """Persist each logit in a closed append before callback; stop on any error."""
    scores = load_control_scores(payload, checkpoint_path, provenance)
    path = Path(checkpoint_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with path.open('x', encoding='utf-8') as stream:
            stream.write(json.dumps({'type': 'provenance', 'schema_version': 1, 'score_kind': 'logit', 'provenance': provenance}, allow_nan=False)+'\n')
            stream.flush()
    for key, trial_id in unique_pairs(payload):
        if trial_id in scores.get(key, {}):
            continue
        start = time.perf_counter()
        raw = scorer(payload['queries'][key], payload['trials'][trial_id])
        logit = relevance_logit(raw)
        record = {'type': 'logit_score', 'query_key': key, 'trial_id': trial_id,
                  'logit': logit, 'raw': raw, 'seconds': time.perf_counter()-start}
        with path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False)+'\n')
            stream.flush()
        scores.setdefault(key, {})[trial_id] = logit
        if on_record is not None:
            on_record(record)
    return scores


def rerank_with_logits(rankings: dict, scores: dict, top_n: int = 50) -> dict:
    """Stable raw-logit ranking of top_n; leave all later first-stage IDs in place."""
    _validate_rankings(rankings, top_n)
    result = {}
    for source, dest in [('B', 'Dprime'), ('C', 'Eprime')]:
        result[dest] = {}
        for key, ids in rankings[source].items():
            for trial_id in ids[:top_n]:
                relevance_logit({'logit': scores.get(key, {}).get(trial_id)})
            result[dest][key] = sorted(ids[:top_n], key=lambda trial_id: -scores[key][trial_id]) + ids[top_n:]
    return result


def audit_control_lengths(payload: dict, tokenize_pair: Callable, max_length: int = BGE_MAX_LENGTH) -> dict:
    """Count untruncated paired token IDs before any GPU scoring."""
    pairs, invalid, lengths = unique_pairs(payload), [], []
    for key, trial_id in pairs:
        length = len(tokenize_pair(payload['queries'][key], payload['trials'][trial_id]))
        lengths.append(length)
        if length > max_length:
            invalid.append({'query_key': key, 'trial_id': trial_id, 'tokens': length})
    return {'n_pairs': len(pairs), 'n_valid': len(pairs)-len(invalid), 'context_limit': max_length,
            'max_tokens': max(lengths), 'invalid': invalid}
