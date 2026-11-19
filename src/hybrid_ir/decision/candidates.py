"""Prepare candidate texts for decision models without relevance judgments."""
from collections.abc import Mapping, Sequence
from typing import Any


def compose_trial_text(doc: Any, conditions: Sequence[str]) -> str:
    """Use the exact document composition used during corpus embedding."""
    parts = ['; '.join(conditions), doc.summary or '', doc.detailed_description or '', doc.eligibility or '']
    body = ' '.join(' '.join(part.split()) for part in parts if part)
    return f"title: {doc.title or 'none'} | text: {body}"


def candidate_rankings(search_inputs: dict, source_rankings: dict, top_n: int = 50) -> tuple[dict, dict]:
    """Validate corpus order and retain the candidate prefix, never qrels."""
    if top_n < 1:
        raise ValueError('top_n must be positive')
    if not search_inputs.get('doc_ids_sha256') or search_inputs['doc_ids_sha256'] != source_rankings.get('doc_ids_sha256'):
        raise ValueError('Corpus-order SHA256 differs or is missing')
    queries = {}
    for q in search_inputs['queries']:
        key = f"{q['year']}/{q['query_id']}"
        if key in queries or not isinstance(q['text'], str) or not q['text'].strip():
            raise ValueError(f'Duplicate query or missing text: {key}')
        queries[key] = q['text']
    if not queries:
        raise ValueError('No queries')
    rankings = {}
    for source in ('B', 'C'):
        ranks = source_rankings.get('rankings', {}).get(source, {})
        if set(ranks) != set(queries):
            raise ValueError(f'{source}: query set differs')
        rankings[source] = {}
        for key, ids in ranks.items():
            if len(ids) < top_n or len(ids) != len(set(ids)):
                raise ValueError(f'{source}/{key}: insufficient candidates or duplicate trial')
            rankings[source][key] = list(ids[:top_n])
    return queries, rankings


def make_decision_inputs(search_inputs: dict, source_rankings: dict, trials: Mapping[str, str], *,
                         source_rankings_sha256: str, top_n: int = 50) -> dict:
    queries, rankings = candidate_rankings(search_inputs, source_rankings, top_n)
    needed = {trial_id for ranks in rankings.values() for ids in ranks.values() for trial_id in ids}
    for trial_id in sorted(needed):
        if trial_id not in trials or not isinstance(trials[trial_id], str) or not trials[trial_id].strip():
            raise ValueError(f'Missing trial text: {trial_id}')
    return {'schema_version': 1, 'top_n': top_n, 'source_rankings_sha256': source_rankings_sha256,
            'doc_ids_sha256': search_inputs['doc_ids_sha256'], 'queries': queries, 'rankings': rankings,
            'trials': {trial_id: trials[trial_id] for trial_id in sorted(needed)}}


def make_benchmark_inputs(full: dict) -> dict:
    """24 pairs: six queries per year, both sources, balanced ranks 1/10/50."""
    pairs = []
    for year in ('2021', '2022'):
        keys = sorted((k for k in full['queries'] if k.startswith(year+'/')), key=lambda k: int(k.split('/')[1]))[:6]
        if len(keys) < 6:
            raise ValueError(f'Benchmark requires six queries for {year}')
        for i, key in enumerate(keys):
            for offset, source in enumerate(('B', 'C')):
                rank = (1, 10, 50)[(i + offset) % 3]
                pairs.append({'query_key': key, 'trial_id': full['rankings'][source][key][rank-1],
                              'source': source, 'rank': rank})
    queries = {p['query_key']: full['queries'][p['query_key']] for p in pairs}
    trials = {p['trial_id']: full['trials'][p['trial_id']] for p in pairs}
    rankings = {source: {p['query_key']: [p['trial_id']] for p in pairs if p['source'] == source}
                for source in ('B', 'C')}
    return {**full, 'queries': queries, 'rankings': rankings, 'trials': trials, 'benchmark_pairs': pairs}
