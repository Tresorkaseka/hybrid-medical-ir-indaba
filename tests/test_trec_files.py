import json

import pytest
from hybrid_ir.data.trec_files import load_judgments, load_queries


def test_load_queries_maps_each_id_to_its_text(tmp_path):
    path = tmp_path / "queries.jsonl"
    path.write_text(
        json.dumps({"query_id": "1", "text": "45-year-old man"}) + "\n" + json.dumps({"query_id": "2", "text": "é"}) + "\n",
        encoding="utf-8",
    )

    assert load_queries(path) == {"1": "45-year-old man", "2": "é"}


def test_load_judgments_groups_levels_by_query(tmp_path):
    path = tmp_path / "qrels.tsv"
    path.write_text("1\tNCT1\t2\n1\tNCT2\t0\n2\tNCT3\t1\n", encoding="utf-8")

    assert load_judgments(path) == {"1": {"NCT1": 2, "NCT2": 0}, "2": {"NCT3": 1}}


def test_load_judgments_rejects_a_malformed_line(tmp_path):
    path = tmp_path / "qrels.tsv"
    path.write_text("1\tNCT1\n", encoding="utf-8")

    with pytest.raises(ValueError, match="ligne 1"):
        load_judgments(path)
