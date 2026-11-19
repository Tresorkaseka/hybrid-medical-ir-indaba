import pytest

from hybrid_ir.queries.demographics import extract_demographics

DAYS_PER_YEAR = 365.25


def age_of(text):
    return extract_demographics(text).age_years


@pytest.mark.parametrize(
    ("text", "years"),
    [
        ("A 45-year-old woman comes to the clinic", 45),
        ("This is a 44 year old female with PMH of PCOS", 44),
        ("A 57-year old farmer was diagnosed", 57),
        ("This is a 70 year-old woman with a history of CAD", 70),
    ],
)
def test_age_written_in_the_narrative_style(text, years):
    assert age_of(text) == pytest.approx(years)


@pytest.mark.parametrize(
    ("text", "years"),
    [
        ("A 32 yo woman who presents following a severe headache", 32),
        ("Patient is a 55yo woman with h/o ESRD", 55),
        ("70 y/o with COPD on 2.5-3.5L O2 at baseline", 70),
        ("Pt is a 22yo F otherwise healthy", 22),
        ("60 yo M with Hep C cirrhosis", 60),
    ],
)
def test_age_written_in_clinical_shorthand(text, years):
    assert age_of(text) == pytest.approx(years)


@pytest.mark.parametrize(
    ("text", "years"),
    [
        ("48 M with a h/o HTN hyperlipidemia", 48),
        ("74M hx of CAD s/p CABG", 74),
    ],
)
def test_age_followed_directly_by_a_sex_letter(text, years):
    assert age_of(text) == pytest.approx(years)


def test_age_written_without_the_word_old():
    assert age_of("Fernandez is a 41 year man who is a professional soccer player") == pytest.approx(41)


@pytest.mark.parametrize(
    ("text", "years"),
    [
        ("A 3-day-old Asian female infant presents with jaundice", 3 / DAYS_PER_YEAR),
        ("A 5 months old male brought to the pediatrics clinic", 5 / 12),
        ("A 7-month-old boy is brought to emergency", 7 / 12),
        ("A 15-week-old infant brought to the clinic", 15 * 7 / DAYS_PER_YEAR),
    ],
)
def test_age_of_infants_in_days_weeks_or_months_is_converted_to_years(text, years):
    assert age_of(text) == pytest.approx(years)


def test_the_first_age_mentioned_is_the_patients_not_a_relatives():
    text = "A 15-week-old infant brought to the clinic. He was born to a 39-year-old woman."

    assert age_of(text) == pytest.approx(15 * 7 / DAYS_PER_YEAR)


def test_durations_that_are_not_ages_are_ignored():
    assert age_of("22yo F otherwise healthy with a 5 yr history of mastocytosis") == pytest.approx(22)
    assert age_of("Patient presents with cough for 3 days and a 5 year history of asthma") is None


def test_no_age_gives_none():
    assert age_of("Patient presents with cough and fever") is None


def sex_of(text):
    return extract_demographics(text).sex


@pytest.mark.parametrize(
    ("text", "sex"),
    [
        ("A 45-year-old woman comes to the clinic", "Female"),
        ("A 17 year old boy complains of vomiting", "Male"),
        ("A 62 yo male with hx of CVA", "Male"),
        ("This is a 57-year-old gentleman with CLL", "Male"),
        ("A 15 year old girl with the history of recurrent headache", "Female"),
        ("The patient is a 31-year-old woman complaining of abdominal pain", "Female"),
    ],
)
def test_sex_word_right_after_the_age(text, sex):
    assert sex_of(text) == sex


@pytest.mark.parametrize(
    ("text", "sex"),
    [
        ("The patient is a 47-year-old Asian woman complaining", "Female"),
        ("The patient is a 34-year-old African American man with sickle cell", "Male"),
        ("The patient is a 32-year-old obese woman who came to the clinic", "Female"),
        ("The patients is a 25-year-old G1 P1 pregnant woman", "Female"),
        ("A 20 year old Caucasian female presents to the clinic", "Female"),
        ("19 yo Hispanic female G1P1 at 32+ 6 weeks", "Female"),
        ("A 3-day-old Asian female infant presents with jaundice", "Female"),
    ],
)
def test_sex_word_after_a_few_describing_words(text, sex):
    assert sex_of(text) == sex


@pytest.mark.parametrize(
    ("text", "sex"),
    [
        ("48 M with a h/o HTN hyperlipidemia", "Male"),
        ("74M hx of CAD s/p CABG", "Male"),
        ("Pt is a 22yo F otherwise healthy", "Female"),
        ("60 yo M with Hep C cirrhosis", "Male"),
        ("79 yo F with multifactorial chronic hypoxemia", "Female"),
        ("Fernandez is a 41 year man who is a professional soccer player", "Male"),
        ("A 5 months old male brought to the pediatrics surgery clinic", "Male"),
    ],
)
def test_sex_in_clinical_shorthand(text, sex):
    assert sex_of(text) == sex


def test_the_sex_word_must_be_attached_to_the_age_not_found_anywhere():
    text = "A 15-week-old infant brought to the clinic. He was born to a 39-year-old woman."

    assert sex_of(text) != "Female"


def test_lowercase_letters_are_not_a_sex():
    assert sex_of("A 45 yo with f/u in 2 weeks and m/c complaints") is None


def test_no_sex_information_gives_none():
    assert sex_of("A 45-year-old presents with cough and fever") is None
    assert sex_of("Patient presents with cough") is None


def test_pronouns_give_the_sex_when_no_word_is_attached_to_the_age():
    text = "A 57-year old farmer was diagnosed with Parkinson's disease a year ago. He experiences slowness of movement. His past history is significant."

    assert sex_of(text) == "Male"


def test_female_pronouns_give_female():
    text = "70 y/o with COPD now presents with agitation. Daughter noted edema and called her PCP. She has had decreased appetite."

    assert sex_of(text) == "Female"


def test_the_infant_is_male_even_though_his_mother_is_described_as_a_woman():
    text = (
        "A 15-week-old infant brought to the clinic for the follow up. The infant has flat facies. "
        "He was born on 39th week to a 39-year-old woman who didn't have prenatal care."
    )

    demographics = extract_demographics(text)

    assert demographics.sex == "Male"
    assert demographics.age_years == pytest.approx(15 * 7 / DAYS_PER_YEAR)


def test_mixed_pronouns_are_ambiguous_so_no_sex_is_returned():
    text = "A 40 y/o with cough. He came with his wife and she reports fever."

    assert sex_of(text) is None


def test_an_explicit_word_next_to_the_age_wins_over_pronouns():
    text = "A 45-year-old woman presents with cough. Her husband said he is worried."

    assert sex_of(text) == "Female"


def test_pronouns_are_used_even_when_no_age_is_written():
    assert sex_of("Patient presents with cough. He has a fever and his cough is dry.") == "Male"


def test_reflexive_pronouns_count_too():
    assert sex_of("A 40 y/o who hurt herself while cooking") == "Female"
