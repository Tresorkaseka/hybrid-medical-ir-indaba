import math
import re

import pytest

from hybrid_ir.queries.typo_noise import perturb_queries


TEXT = 'A 45-year-old woman has severe cardiac disease and recurrent chest pain, without fever.'


def test_reproducible_and_independent_of_query_order():
    a = perturb_queries({'2021/1': TEXT, '2021/2': TEXT}, seed=73)
    b = perturb_queries({'2021/2': TEXT, '2021/1': TEXT}, seed=73)
    assert a == b
    assert a == perturb_queries({'2021/1': TEXT, '2021/2': TEXT}, seed=73)


def test_nested_word_selection_and_exact_changes_preserve_offsets():
    outputs = perturb_queries({'q': TEXT}, seed=4)
    mild, strong = outputs['0.05']['q'], outputs['0.1']['q']
    mild_by_span = {(e['start'], e['end']): e for e in mild['edits']}
    strong_by_span = {(e['start'], e['end']): e for e in strong['edits']}
    assert mild_by_span.items() <= strong_by_span.items()
    for record in (mild, strong):
        rebuilt = TEXT
        for edit in sorted(record['edits'], key=lambda e: e['start'], reverse=True):
            assert TEXT[edit['start']:edit['end']] == edit['before']
            assert edit['before'] != edit['after']
            assert edit['operation'] in {'swap', 'delete', 'insert', 'substitute'}
            rebuilt = rebuilt[:edit['start']] + edit['after'] + rebuilt[edit['end']:]
        assert record['text'] == rebuilt
        assert re.findall(r'\d+|[^\w\s]', record['text']) == re.findall(r'\d+|[^\w\s]', TEXT)
        assert record['n_eligible_words'] == len(re.findall(r'[A-Za-z]{2,}', TEXT))


def test_requested_fraction_uses_nearest_word_half_up():
    text = ' '.join(['cardiac'] * 30)
    outputs = perturb_queries({'q': text}, seed=5)
    assert len(outputs['0.05']['q']['edits']) == 2
    assert len(outputs['0.1']['q']['edits']) == 3


def test_short_and_empty_queries_never_fabricate_words():
    outputs = perturb_queries({'empty': '', 'single': 'M 45 !', 'word': 'aa'}, seed=7)
    for level in outputs.values():
        assert level['empty']['text'] == ''
        assert level['single']['text'] == 'M 45 !'
        assert len(level['word']['edits']) == 1
        assert level['word']['text'] != 'aa'


def test_all_edit_types_occur_without_identity_edits_or_empty_words():
    outputs = perturb_queries({'q': ' '.join(['Aa', 'aaa', 'trial', 'Patient'] * 100)}, rates=(1.0,), seed=7)
    edits = outputs['1.0']['q']['edits']
    assert {e['operation'] for e in edits} == {'swap', 'delete', 'insert', 'substitute'}
    assert all(e['after'] and e['before'] != e['after'] for e in edits)


@pytest.mark.parametrize('rates', [(0,), (-0.1,), (1.1,), (math.nan,), (True,), (0.1, 0.1)])
def test_invalid_rates_fail_explicitly(rates):
    with pytest.raises(ValueError):
        perturb_queries({'q': TEXT}, rates=rates)
