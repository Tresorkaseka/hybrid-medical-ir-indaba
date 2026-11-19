import pytest

from hybrid_ir.retrieval.tokenizer import tokenize


def test_lowercases_and_splits_on_everything_that_is_not_a_letter_or_digit():
    assert tokenize("COPD-related cough, fever.") == ["copd", "related", "cough", "fever"]


def test_digits_are_kept_and_decimal_numbers_are_split():
    assert tokenize("HbA1c 7.2 on 2.5L") == ["hba1c", "7", "2", "on", "2", "5l"]


@pytest.mark.parametrize("text", ["", "   ", "...,;"])
def test_text_without_words_gives_an_empty_list(text):
    assert tokenize(text) == []


def test_the_same_word_appears_as_many_times_as_it_is_written():
    assert tokenize("rash itch rash") == ["rash", "itch", "rash"]
