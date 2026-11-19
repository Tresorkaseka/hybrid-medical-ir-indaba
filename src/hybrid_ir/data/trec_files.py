"""Lecture des requêtes et des jugements TREC préparés par l'étape 0 (data/processed/)."""
import json
from collections import defaultdict
from pathlib import Path


def load_queries(path: Path) -> dict[str, str]:
    """Fichier JSONL : une requête par ligne, avec `query_id` et `text`."""
    with open(path, encoding="utf-8") as f:
        return {query["query_id"]: query["text"] for query in map(json.loads, f)}


def load_judgments(path: Path) -> dict[str, dict[str, int]]:
    """Fichier TSV : `identifiant de requête`, `identifiant d'essai`, `niveau`."""
    judgments: dict[str, dict[str, int]] = defaultdict(dict)
    with open(path, encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            fields = line.rstrip("\n").split("\t")
            if len(fields) != 3:
                raise ValueError(f"jugement mal formé à la ligne {line_number} de {path} : {line!r}")
            query_id, trial_id, level = fields
            judgments[query_id][trial_id] = int(level)
    return dict(judgments)
