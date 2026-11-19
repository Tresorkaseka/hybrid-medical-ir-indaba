import math

import pytest

from hybrid_ir.evaluation.robustness import compare_noisy_to_clean


def test_relative_loss_is_ratio_of_means_and_difference_is_paired():
    report = compare_noisy_to_clean({'a': .2, 'b': .8}, {'b': .6, 'a': .2})
    assert report['clean_mean'] == pytest.approx(.5)
    assert report['noisy_mean'] == pytest.approx(.4)
    assert report['relative_loss'] == pytest.approx(.2)
    assert report['difference_noisy_minus_clean']['mean'] == pytest.approx(-.1)
    assert report['n_queries'] == 2
    assert report == compare_noisy_to_clean({'a': .2, 'b': .8}, {'b': .6, 'a': .2})


def test_improvement_can_have_negative_loss_and_zero_clean_is_undefined():
    assert compare_noisy_to_clean({'a': .5}, {'a': .7})['relative_loss'] == pytest.approx(-.4)
    assert compare_noisy_to_clean({'a': 0}, {'a': 0})['relative_loss'] is None


@pytest.mark.parametrize('clean,noisy', [({}, {}), ({'a': 1}, {'b': 1}),
                                       ({'a': math.nan}, {'a': 1}),
                                       ({'a': 1}, {'a': math.inf}),
                                       ({'a': -1}, {'a': 1}),
                                       ({'a': True}, {'a': 1})])
def test_invalid_scores_and_alignment_are_rejected(clean, noisy):
    with pytest.raises(ValueError):
        compare_noisy_to_clean(clean, noisy)
