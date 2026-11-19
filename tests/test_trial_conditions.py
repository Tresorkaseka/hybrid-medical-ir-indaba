import zipfile
from pathlib import Path

import pytest
from helpers import make_trial_xml
from hybrid_ir.data.trial_conditions import iter_trial_conditions, parse_trial_conditions

REAL_ARCHIVE = Path("data/raw/ir_datasets/clinicaltrials/docs_2021_1.zip")


def test_reads_every_condition_in_order_and_strips_spaces():
    xml = make_trial_xml(nct_id="NCT00000134", conditions=["HIV Infections", "  Cytomegalovirus Retinitis \n"])

    trial = parse_trial_conditions(xml)

    assert trial.nct_id == "NCT00000134"
    assert trial.conditions == ("HIV Infections", "Cytomegalovirus Retinitis")


def test_mesh_terms_are_not_conditions():
    trial = parse_trial_conditions(make_trial_xml(conditions=["Asthma"]))

    assert "MESH TERM" not in trial.conditions


def test_a_trial_without_condition_gives_an_empty_tuple():
    assert parse_trial_conditions(make_trial_xml()).conditions == ()


def test_a_missing_nct_id_is_an_error():
    with pytest.raises(ValueError, match="nct_id"):
        parse_trial_conditions(b"<clinical_study><condition>x</condition></clinical_study>")


def test_iter_trial_conditions_reads_an_archive_and_ignores_non_xml_entries(tmp_path):
    path = tmp_path / "part.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("p/NCT00000001.xml", make_trial_xml(nct_id="NCT00000001", conditions=["Asthma"]))
        archive.writestr("p/NCT00000002.xml", make_trial_xml(nct_id="NCT00000002"))
        archive.writestr("p/LISEZMOI.txt", "pas un essai")

    assert [(t.nct_id, t.conditions) for t in iter_trial_conditions(path)] == [
        ("NCT00000001", ("Asthma",)),
        ("NCT00000002", ()),
    ]


@pytest.mark.skipif(not REAL_ARCHIVE.exists(), reason="archive TREC absente (lancer make data)")
def test_a_real_trial_has_its_condition():
    trial = next(t for t in iter_trial_conditions(REAL_ARCHIVE) if t.nct_id == "NCT00000102")

    assert trial.conditions == ("Congenital Adrenal Hyperplasia",)
