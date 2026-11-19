import re

_DAYS_PER_YEAR = 365.25
_YEARS_PER_UNIT = {
    "year": 1.0,
    "month": 1 / 12,
    "week": 7 / _DAYS_PER_YEAR,
    "day": 1 / _DAYS_PER_YEAR,
    "hour": 1 / (_DAYS_PER_YEAR * 24),
    "minute": 1 / (_DAYS_PER_YEAR * 24 * 60),
}
_AGE_PATTERN = re.compile(r"(\d+)\s+(year|month|week|day|hour|minute)s?", re.IGNORECASE)
_NO_BOUND = ("", "N/A")


def parse_age_in_years(text: str | None) -> float | None:
    """Convertit un âge ClinicalTrials.gov (« 18 Years », « 6 Months »…) en années.

    Renvoie None quand la borne est absente ou illimitée (« N/A »). Un format
    inconnu lève ValueError : mieux vaut un arrêt net qu'un âge deviné.
    """
    if text is None:
        return None
    cleaned = text.strip()
    if cleaned in _NO_BOUND:
        return None
    match = _AGE_PATTERN.fullmatch(cleaned)
    if match is None:
        raise ValueError(f"Format d'âge inconnu : {text!r}")
    quantity, unit = match.groups()
    return int(quantity) * _YEARS_PER_UNIT[unit.lower()]
