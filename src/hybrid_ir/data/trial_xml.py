import xml.etree.ElementTree as ET
from dataclasses import dataclass

from hybrid_ir.data.ages import parse_age_in_years

_VALID_GENDERS = {"All", "Male", "Female"}
_HEALTHY_VOLUNTEERS = {"Accepts Healthy Volunteers": True, "No": False}


@dataclass(frozen=True)
class TrialRecord:
    """Champs structurés d'un essai, tels qu'ils servent de filtres SQL."""

    nct_id: str
    gender: str | None
    min_age_years: float | None
    max_age_years: float | None
    accepts_healthy_volunteers: bool | None
    phase: str | None


def parse_trial_xml(xml: bytes) -> TrialRecord:
    root = ET.fromstring(xml)
    return TrialRecord(
        nct_id=_parse_nct_id(root),
        gender=_parse_gender(_text(root, "eligibility/gender")),
        min_age_years=parse_age_in_years(_text(root, "eligibility/minimum_age")),
        max_age_years=parse_age_in_years(_text(root, "eligibility/maximum_age")),
        accepts_healthy_volunteers=_parse_healthy_volunteers(_text(root, "eligibility/healthy_volunteers")),
        phase=_text(root, "phase"),
    )


def _text(root: ET.Element, path: str) -> str | None:
    value = root.findtext(path)
    if value is None:
        return None
    return value.strip() or None


def _parse_nct_id(root: ET.Element) -> str:
    nct_id = _text(root, "id_info/nct_id")
    if nct_id is None:
        raise ValueError("nct_id manquant dans le fichier XML")
    return nct_id


def _parse_gender(value: str | None) -> str | None:
    if value is not None and value not in _VALID_GENDERS:
        raise ValueError(f"Valeur inconnue pour gender : {value!r}")
    return value


def _parse_healthy_volunteers(value: str | None) -> bool | None:
    if value is None:
        return None
    if value not in _HEALTHY_VOLUNTEERS:
        raise ValueError(f"Valeur inconnue pour healthy_volunteers : {value!r}")
    return _HEALTHY_VOLUNTEERS[value]
