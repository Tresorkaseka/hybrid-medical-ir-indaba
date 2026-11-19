import copy

import pytest

from hybrid_ir.evaluation.noisy_rankings import validate_noisy_semantic_run


def fixture():
    clean = dict(manifest={'model': 'fixed-model', 'revision': 'fixed-revision'}, top_k=2,
                 doc_ids_sha256='corpus', query_prefix='query: ')
    inputs = dict(noise_sha256='noise', doc_ids_sha256='corpus', n_docs=3,
                  queries=[dict(year=2021, query_id='1@noise05', original_key='2021/1',
                                noise_rate=.05, n_kept=2, kept_mask='YA==')])
    result = dict(**clean, input_sha256='input', noise_sha256='noise',
                  rankings={'B': {'2021/1@noise05': ['a', 'b']}, 'C': {'2021/1@noise05': ['b', 'c']}})
    return clean, inputs, result


def test_validates_complete_frozen_inputs_and_returns_original_keys_by_noise_level():
    clean, inputs, result = fixture()
    grouped = validate_noisy_semantic_run(result, clean, inputs, 'input', ['a', 'b', 'c'])
    assert grouped == {'0.05': {'2021': {'B': {'1': ['a', 'b']}, 'C': {'1': ['b', 'c']}}}}


@pytest.mark.parametrize('mutation', [
    lambda r: r.update(input_sha256='different'),
    lambda r: r.update(noise_sha256='different'),
    lambda r: r.update(query_prefix='document: '),
    lambda r: r.update(doc_ids_sha256='different'),
    lambda r: r['manifest'].update(revision='another'),
    lambda r: r.update(top_k=3),
    lambda r: r['rankings']['B'].update({'2021/1@noise05': ['a', 'a']}),
    lambda r: r['rankings']['C'].update({'2021/1@noise05': ['b', 'unknown']}),
    lambda r: r['rankings']['C'].clear(),
    lambda r: r['rankings'].update(D={}),
])
def test_drift_or_invalid_results_rejected(mutation):
    clean, inputs, result = fixture()
    # Manifest must remain independent to detect drift rather than mutating the reference.
    result = copy.deepcopy(result)
    mutation(result)
    with pytest.raises(ValueError):
        validate_noisy_semantic_run(result, clean, inputs, 'input', ['a', 'b', 'c'])


def test_duplicate_query_rows_are_not_silently_overwritten():
    clean, inputs, result = fixture()
    inputs['queries'].append(dict(inputs['queries'][0]))
    with pytest.raises(ValueError):
        validate_noisy_semantic_run(result, clean, inputs, 'input', ['a', 'b', 'c'])


def test_c_must_respect_the_actual_noisy_sql_mask():
    clean, inputs, result = fixture()
    result['rankings']['C']['2021/1@noise05'] = ['a', 'b']
    with pytest.raises(ValueError, match='mask'):
        validate_noisy_semantic_run(result, clean, inputs, 'input', ['a', 'b', 'c'])


def test_mask_count_cannot_disagree_with_n_kept():
    clean, inputs, result = fixture()
    inputs['queries'][0]['kept_mask'] = '4A=='
    with pytest.raises(ValueError, match='mask'):
        validate_noisy_semantic_run(result, clean, inputs, 'input', ['a', 'b', 'c'])
