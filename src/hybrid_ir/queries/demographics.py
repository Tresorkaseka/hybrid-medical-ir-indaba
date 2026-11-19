import re
from dataclasses import dataclass

from hybrid_ir.data.ages import parse_age_in_years

MALE, FEMALE = "Male", "Female"

_SEX_WORDS = {
    "man": MALE, "male": MALE, "boy": MALE, "gentleman": MALE,
    "woman": FEMALE, "female": FEMALE, "girl": FEMALE,
}
_SEX_LETTERS = {"M": MALE, "F": FEMALE}  # majuscules seulement : « f/u » ou « m/c » ne sont pas un sexe
_MALE_PRONOUNS = {"he", "his", "him", "himself"}
_FEMALE_PRONOUNS = {"she", "her", "hers", "herself"}
_WORDS_CHECKED_AFTER_AGE = 5
_CLAUSE_END = re.compile(r"[,.;:()]")

_UNITS = {"": "year", "y": "year", "yr": "year", "year": "year", "month": "month", "week": "week", "day": "day"}

_AGE_PATTERNS = (
    # « 45-year-old », « 44 year old », « 3-day-old », « 5 months old »
    re.compile(r"(?P<number>\d+)[\s-]*(?P<unit>year|yr|month|week|day)s?[\s-]*old", re.IGNORECASE),
    # « 32 yo », « 55yo », « 70 y/o »
    re.compile(r"(?P<number>\d+)\s*(?P<unit>y)(?:/o|o)\b", re.IGNORECASE),
    # « 48 M », « 74M » : l'âge suivi directement d'une lettre de sexe
    re.compile(r"(?P<number>\d+)\s*(?P<unit>)(?P<sex_letter>[MF])\b"),
    # « 41 year man » : « old » est absent, un mot de sexe suit
    re.compile(r"(?P<number>\d+)[\s-]*(?P<unit>year)s?(?=\s+(?:man|woman|male|female|gentleman|boy|girl)\b)", re.IGNORECASE),
)


@dataclass(frozen=True)
class PatientDemographics:
    age_years: float | None
    sex: str | None


@dataclass(frozen=True)
class _AgeMention:
    years: float
    start: int
    end: int
    sex: str | None = None


def extract_demographics(text: str) -> PatientDemographics:
    age = _find_patient_age(text)
    sex_next_to_age = (age.sex or _sex_right_after(text, age)) if age else None
    return PatientDemographics(
        age_years=age.years if age else None,
        sex=sex_next_to_age or _sex_from_pronouns(text),
    )


def _find_patient_age(text: str) -> _AgeMention | None:
    """Le premier âge cité est celui du patient : un proche n'est mentionné qu'ensuite."""
    mentions = [mention for pattern in _AGE_PATTERNS for mention in _mentions(pattern, text)]
    return min(mentions, key=lambda mention: mention.start, default=None)


def _mentions(pattern: re.Pattern, text: str):
    for match in pattern.finditer(text):
        unit = _UNITS[match["unit"].lower()]
        years = parse_age_in_years(f"{match['number']} {unit}")
        sex_letter = match.groupdict().get("sex_letter")
        yield _AgeMention(
            years=years,
            start=match.start(),
            end=match.end(),
            sex=_SEX_LETTERS[sex_letter] if sex_letter else None,
        )


def _sex_right_after(text: str, age: _AgeMention) -> str | None:
    """Cherche le sexe parmi les quelques mots qui suivent l'âge, dans la même proposition."""
    clause = _CLAUSE_END.split(text[age.end:], maxsplit=1)[0]
    for word in clause.split()[:_WORDS_CHECKED_AFTER_AGE]:
        sex = _SEX_WORDS.get(word.lower()) or _SEX_LETTERS.get(word)
        if sex:
            return sex
    return None


def _sex_from_pronouns(text: str) -> str | None:
    """Sexe déduit des pronoms, seulement s'ils vont tous dans le même sens."""
    words = {word.lower() for word in re.findall(r"[A-Za-z]+", text)}
    sexes = set()
    if words & _MALE_PRONOUNS:
        sexes.add(MALE)
    if words & _FEMALE_PRONOUNS:
        sexes.add(FEMALE)
    return sexes.pop() if len(sexes) == 1 else None
