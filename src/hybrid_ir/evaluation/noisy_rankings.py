"""Contrôles des classements B/C bruités avant accès aux jugements."""
from hybrid_ir.retrieval.masks import unpack_kept_mask


def validate_noisy_semantic_run(result: dict, clean: dict, inputs: dict,
                                input_sha256: str, doc_ids: list[str]) -> dict:
    if (result.get('input_sha256') != input_sha256
            or result.get('noise_sha256') != inputs['noise_sha256']
            or result.get('doc_ids_sha256') != inputs['doc_ids_sha256']
            or any(result.get(k) != clean[k] for k in ('manifest', 'top_k', 'doc_ids_sha256', 'query_prefix'))
            or set(result.get('rankings', {})) != {'B', 'C'}):
        raise ValueError('Noisy semantic run differs from frozen clean/input provenance')
    rows = inputs['queries']
    expected = {f"{q['year']}/{q['query_id']}" for q in rows}
    if len(expected) != len(rows) or len(doc_ids) != inputs['n_docs'] or len(set(doc_ids)) != len(doc_ids):
        raise ValueError('Duplicate query keys or invalid corpus order')
    valid_docs = set(doc_ids)
    for system, run in result['rankings'].items():
        if set(run) != expected:
            raise ValueError(f'{system}: noisy query keys differ from frozen inputs')
    grouped = {}
    for query in rows:
        year, qid = query['original_key'].split('/')
        rate = str(float(query['noise_rate']))
        key = f"{query['year']}/{query['query_id']}"
        group = grouped.setdefault(rate, {}).setdefault(year, {'B': {}, 'C': {}})
        if str(query['year']) != year or qid in group['B']:
            raise ValueError('Invalid or duplicate original query key')
        mask = unpack_kept_mask(query['kept_mask'], len(doc_ids))
        kept = {trial_id for trial_id, allowed in zip(doc_ids, mask) if allowed}
        if len(kept) != query['n_kept']:
            raise ValueError('Noisy SQL mask count differs from n_kept')
        for system in ('B', 'C'):
            ids = result['rankings'][system][key]
            expected_depth = min(result['top_k'], inputs['n_docs'] if system == 'B' else query['n_kept'])
            if (not isinstance(ids, list) or len(ids) != expected_depth
                    or any(not isinstance(i, str) or i not in valid_docs for i in ids)
                    or len(set(ids)) != len(ids)):
                raise ValueError(f'{system}/{key}: invalid trial IDs or retrieval depth')
            if system == 'C' and not set(ids).issubset(kept):
                raise ValueError(f'C/{key}: trial outside noisy SQL mask')
            group[system][qid] = ids
    return grouped
