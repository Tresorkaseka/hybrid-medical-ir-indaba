"""Conditions (maladies visées) d'un essai, lues dans le XML brut.

Le champ `condition` fourni par `ir_datasets` est vide pour tous les essais : on lit donc les balises
`<condition>` nous-mêmes. Les termes MeSH ajoutés par ClinicalTrials.gov (`<condition_browse>`) ne sont
pas des conditions saisies et sont ignorés.
"""
import xml.etree.ElementTree as ET
import zipfile
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TrialConditions:
    nct_id: str
    conditions: tuple[str, ...]


def parse_trial_conditions(xml: bytes) -> TrialConditions:
    root = ET.fromstring(xml)
    nct_id = (root.findtext("id_info/nct_id") or "").strip()
    if not nct_id:
        raise ValueError("nct_id manquant dans le fichier XML")
    conditions = tuple(text for node in root.findall("condition") if (text := (node.text or "").strip()))
    return TrialConditions(nct_id, conditions)


def iter_trial_conditions(archive_path: Path) -> Iterator[TrialConditions]:
    with zipfile.ZipFile(archive_path) as archive:
        for name in archive.namelist():
            if name.endswith(".xml"):
                yield parse_trial_conditions(archive.read(name))
