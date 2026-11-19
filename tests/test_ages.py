import pytest

from hybrid_ir.data.ages import parse_age_in_years


@pytest.mark.parametrize(
    ("text", "expected_years"),
    [
        ("18 Years", 18.0),
        ("1 Year", 1.0),
        ("  65 Years ", 65.0),
        ("6 Months", 0.5),
        ("1 Month", 1 / 12),
        ("52 Weeks", 52 * 7 / 365.25),
        ("1 Week", 7 / 365.25),
        ("91 Days", 91 / 365.25),
        ("1 Day", 1 / 365.25),
        ("24 Hours", 1 / 365.25),
        ("1 Hour", 1 / (365.25 * 24)),
        ("2 Minutes", 2 / (365.25 * 24 * 60)),
    ],
)
def test_converts_every_unit_found_in_trec_to_years(text, expected_years):
    assert parse_age_in_years(text) == pytest.approx(expected_years)


@pytest.mark.parametrize("text", ["N/A", "", "   ", None])
def test_missing_or_unbounded_age_is_none(text):
    assert parse_age_in_years(text) is None


@pytest.mark.parametrize("text", ["5 Decades", "abc", "18", "Years"])
def test_unknown_format_fails_loudly_instead_of_guessing(text):
    with pytest.raises(ValueError):
        parse_age_in_years(text)
