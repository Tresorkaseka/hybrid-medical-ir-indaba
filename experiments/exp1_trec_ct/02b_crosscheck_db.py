#!/usr/bin/env python3
"""Expérience 1, étape 2b : recoupe la base SQLite avec l'inventaire indépendant.

Compare results/exp1_trial_db_summary.json (lecteur de la bibliothèque) à
results/exp1_structured_fields_inventory.json (expressions régulières). Code de sortie 1 au
moindre écart.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKED = ("n_trials", "gender", "accepts_healthy_volunteers", "phase", "missing_min_age", "missing_max_age")


def load(name: str) -> dict:
    return json.loads((ROOT / "results" / name).read_text(encoding="utf-8"))


def main() -> int:
    database, inventory = load("exp1_trial_db_summary.json"), load("exp1_structured_fields_inventory.json")
    failures = [key for key in CHECKED if database[key] != inventory[key]]
    for key in CHECKED:
        print(f"{key:28s} {'DIFFÉRENT' if key in failures else 'identique'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
