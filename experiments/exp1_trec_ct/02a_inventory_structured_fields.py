#!/usr/bin/env python3
"""Expérience 1, étape 2a : inventaire indépendant des champs structurés des essais.

Méthode volontairement différente du lecteur de la bibliothèque : expressions régulières sur le
texte brut des fichiers XML, sans analyseur XML. Sert de seconde méthode pour recouper la base
SQLite (voir 02b_crosscheck_db.py) et a guidé la conception du lecteur (formes d'âge réelles).

Entrée : data/raw/ir_datasets/clinicaltrials/docs_2021_*.zip
Sortie : results/exp1_structured_fields_inventory.json
"""
import collections
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARCHIVES = sorted((ROOT / "data/raw/ir_datasets/clinicaltrials").glob("docs_2021_*.zip"))
OUTPUT = ROOT / "results/exp1_structured_fields_inventory.json"

FIELDS = ("gender", "minimum_age", "maximum_age", "healthy_volunteers", "phase")
PATTERNS = {field: re.compile(rb"<%s>(.*?)</%s>" % (field.encode(), field.encode()), re.S) for field in FIELDS}
HEALTHY_AS_FLAG = {"No": "0", "Accepts Healthy Volunteers": "1"}
NUMBER = re.compile(r"\d+")


def raw_value(field: str, xml: bytes) -> str | None:
    match = PATTERNS[field].search(xml)
    return match.group(1).decode().strip() if match else None


def main() -> None:
    counts = {field: collections.Counter() for field in FIELDS}
    age_formats = collections.Counter()
    n_trials = 0
    for archive_path in ARCHIVES:
        with zipfile.ZipFile(archive_path) as archive:
            for name in archive.namelist():
                if not name.endswith(".xml"):
                    continue
                xml = archive.read(name)
                n_trials += 1
                for field in FIELDS:
                    value = raw_value(field, xml)
                    counts[field][value] += 1
                    if field.endswith("_age"):
                        age_formats[(field, NUMBER.sub("#", value) if value else None)] += 1

    as_text = lambda counter: {str(key): n for key, n in counter.items()}  # noqa: E731
    healthy = collections.Counter()
    for value, n in counts["healthy_volunteers"].items():
        healthy[HEALTHY_AS_FLAG.get(value, str(value))] += n
    inventory = {
        "n_trials": n_trials,
        "gender": as_text(counts["gender"]),
        "accepts_healthy_volunteers": as_text(healthy),
        "phase": as_text(counts["phase"]),
        "missing_min_age": counts["minimum_age"]["N/A"] + counts["minimum_age"][None],
        "missing_max_age": counts["maximum_age"]["N/A"] + counts["maximum_age"][None],
        "age_formats": {f"{field}: {shape}": n for (field, shape), n in sorted(age_formats.items(), key=lambda kv: -kv[1])},
    }
    OUTPUT.write_text(json.dumps(inventory, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{n_trials} essais inventoriés -> {OUTPUT}")


if __name__ == "__main__":
    main()
