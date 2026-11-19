"""Filtre SQL des essais selon l'âge et le sexe du patient.

Règle de prudence : une information absente dans l'essai (borne d'âge, sexe) veut dire « pas de
contrainte ». On n'écarte jamais un essai faute d'information. Un âge ou un sexe absent côté
patient désactive le filtre sur ce champ.
"""
import sqlite3

SEXES = ("Male", "Female")

_QUERY = """
SELECT nct_id FROM trials
WHERE (:age IS NULL OR min_age_years IS NULL OR min_age_years <= :age)
  AND (:age IS NULL OR max_age_years IS NULL OR max_age_years >= :age)
  AND (:sex IS NULL OR gender IS NULL OR gender = 'All' OR gender = :sex)
"""


def eligible_trial_ids(conn: sqlite3.Connection, age_years: float | None, sex: str | None) -> set[str]:
    if sex is not None and sex not in SEXES:
        raise ValueError(f"sexe inconnu : {sex!r} (attendu : {SEXES})")
    rows = conn.execute(_QUERY, {"age": age_years, "sex": sex})
    return {nct_id for (nct_id,) in rows}
