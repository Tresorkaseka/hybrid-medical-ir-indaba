"""Model inputs preserve candidate order and exclude evaluation labels."""
import copy
from types import SimpleNamespace

import pytest


def fixtures():
    queries = [{"year": year, "query_id": str(q), "text": f"patient {year}/{q}", "qrels": "DO NOT EXPORT"}
               for year in (2021, 2022) for q in range(1, 7)]
    search = {"doc_ids_sha256": "same-order", "queries": queries}
    ranks = {"doc_ids_sha256": "same-order", "rankings": {
        source: {f"{q['year']}/{q['query_id']}": [f"NCT{i}" for i in range(60)] for q in queries}
        for source in ("B", "C")}}
    return search, ranks


def build(search=None, ranks=None, trials=None):
    from hybrid_ir.decision.candidates import make_decision_inputs
    default_search, default_ranks = fixtures()
    return make_decision_inputs(search or default_search, ranks or default_ranks,
                                trials if trials is not None else {f"NCT{i}": f"text {i}" for i in range(50)},
                                source_rankings_sha256="source-hash")


def test_preserves_top_50_and_only_exports_model_text_and_provenance():
    out = build()
    assert out['schema_version'] == 1
    assert out['top_n'] == 50
    assert out['source_rankings_sha256'] == 'source-hash'
    assert out['rankings']['B']['2021/1'] == [f'NCT{i}' for i in range(50)]
    assert out['queries']['2021/1'] == 'patient 2021/1'
    assert set(out) == {'schema_version', 'top_n', 'source_rankings_sha256', 'doc_ids_sha256', 'queries', 'rankings', 'trials'}
    assert len(out['trials']) == 50


@pytest.mark.parametrize('problem', ['order', 'missing-query', 'duplicate-query', 'short-pool', 'duplicate-trial', 'missing-trial', 'empty-text', 'empty-source'])
def test_rejects_corrupt_or_incomplete_model_inputs(problem):
    search, ranks = fixtures()
    trials = {f'NCT{i}': f'text {i}' for i in range(50)}
    if problem == 'order': ranks['doc_ids_sha256'] = 'other-order'
    if problem == 'missing-query': del ranks['rankings']['C']['2021/1']
    if problem == 'duplicate-query': search['queries'].append(copy.deepcopy(search['queries'][0]))
    if problem == 'short-pool': ranks['rankings']['B']['2021/1'] = ['NCT0']
    if problem == 'duplicate-trial': ranks['rankings']['B']['2021/1'][5] = 'NCT0'
    if problem == 'missing-trial': del trials['NCT0']
    if problem == 'empty-text': trials['NCT0'] = '  '
    if problem == 'empty-source': ranks['rankings']['B'] = {}
    with pytest.raises(ValueError): build(search, ranks, trials)


def test_full_text_matches_embedding_composition_including_normalization():
    from hybrid_ir.decision.candidates import compose_trial_text
    doc = SimpleNamespace(title='A trial', summary=' A\n summary ', detailed_description='Long\t detail', eligibility='  Adults ', doc_id='NCT1')
    assert compose_trial_text(doc, ['Disease one', 'Disease two']) == 'title: A trial | text: Disease one; Disease two A summary Long detail Adults'
    doc.title = None
    doc.summary = None
    assert compose_trial_text(doc, []) == 'title: none | text: Long detail Adults'


def test_benchmark_is_deterministic_balanced_and_has_no_unneeded_text():
    from hybrid_ir.decision.candidates import make_benchmark_inputs
    full = build()
    bench = make_benchmark_inputs(full)
    assert bench == make_benchmark_inputs(full)
    assert len(bench['benchmark_pairs']) == 24
    for year in ('2021', '2022'):
        pairs = [p for p in bench['benchmark_pairs'] if p['query_key'].startswith(year+'/')]
        assert len(pairs) == 12
        assert len({p['query_key'] for p in pairs}) == 6
        for source in ('B', 'C'):
            assert len([p for p in pairs if p['source'] == source]) == 6
        for rank in (1, 10, 50):
            assert len([p for p in pairs if p['rank'] == rank]) == 4
    assert set(bench['trials']) == {p['trial_id'] for p in bench['benchmark_pairs']}
    for p in bench['benchmark_pairs']:
        assert p['trial_id'] == full['rankings'][p['source']][p['query_key']][p['rank']-1]
