"""Contrôle d'intégrité de la vérité terrain âge/sexe des requêtes TREC.

Chaque étiquette doit être sourcée : la citation qui la justifie doit figurer mot pour mot dans
le texte de la requête. Ces tests rendent la vérité terrain vérifiable par machine.
"""
import csv
import json
import re
from pathlib import Path

import pytest
from hybrid_ir.data.ages import parse_age_in_years

ROOT = Path(__file__).resolve().parents[1]
GOLD_PATH = ROOT / "experiments/exp1_trec_ct/gold/query_demographics_gold.csv"
QUERY_PATHS = {year: ROOT / f"data/processed/queries_{year}.jsonl" for year in (2021, 2022)}
SEX_LABELS = {"Male", "Female"}
SEX_BASES = {"explicit", "pronoun"}
SEX_WORDS = {
    "Male": {"man", "male", "boy", "gentleman", "he", "his", "him", "m"},
    "Female": {"woman", "female", "girl", "she", "her", "f"},
}

pytestmark = pytest.mark.skipif(
    not all(path.exists() for path in QUERY_PATHS.values()),
    reason="requêtes TREC absentes (lancer make data)",
)


@pytest.fixture(scope="module")
def gold_rows():
    with open(GOLD_PATH, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


@pytest.fixture(scope="module")
def query_texts():
    texts = {}
    for year, path in QUERY_PATHS.items():
        for line in open(path, encoding="utf-8"):
            query = json.loads(line)
            texts[(year, query["query_id"])] = query["text"]
    return texts


def key(row):
    return int(row["year"]), row["query_id"]


def test_gold_covers_every_query_exactly_once(gold_rows, query_texts):
    keys = [key(row) for row in gold_rows]

    assert len(keys) == len(set(keys))
    assert set(keys) == set(query_texts)


def test_every_evidence_is_quoted_verbatim_from_the_query(gold_rows, query_texts):
    for row in gold_rows:
        text = query_texts[key(row)]
        assert row["age_evidence"] in text, f"{key(row)} : citation d'âge absente du texte"
        assert row["sex_evidence"] in text, f"{key(row)} : citation de sexe absente du texte"


def test_age_labels_convert_to_years(gold_rows):
    for row in gold_rows:
        years = parse_age_in_years(f"{row['age_value']} {row['age_unit']}")
        assert years is not None and years > 0, key(row)


def test_sex_labels_are_known_and_have_a_basis(gold_rows):
    for row in gold_rows:
        assert row["sex"] in SEX_LABELS, key(row)
        assert row["sex_basis"] in SEX_BASES, key(row)


def test_every_label_records_who_made_it_and_its_verification_status(gold_rows):
    for row in gold_rows:
        assert row["labeler"], key(row)
        assert row["verification"], key(row)


def words(phrase):
    return {word.lower() for word in re.findall(r"[A-Za-z]+", phrase)}


def test_sex_label_agrees_with_the_words_of_its_evidence(gold_rows):
    opposite = {"Male": "Female", "Female": "Male"}
    for row in gold_rows:
        evidence_words = words(row["sex_evidence"])
        assert evidence_words & SEX_WORDS[row["sex"]], f"{key(row)} : la citation ne justifie pas {row['sex']}"
        assert not evidence_words & SEX_WORDS[opposite[row["sex"]]], f"{key(row)} : citation contradictoire"


def test_pronoun_basis_is_used_only_when_the_evidence_is_a_pronoun_phrase(gold_rows):
    for row in gold_rows:
        if row["sex_basis"] == "pronoun":
            assert words(row["sex_evidence"]) & {"he", "his", "him", "she", "her"}, key(row)
