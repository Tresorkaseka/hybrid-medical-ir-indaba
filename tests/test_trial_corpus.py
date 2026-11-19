import zipfile
from itertools import islice
from pathlib import Path

import pytest
from helpers import make_trial_xml
from hybrid_ir.data.trial_corpus import iter_trial_records

REAL_ARCHIVE = Path("data/raw/ir_datasets/clinicaltrials/docs_2021_1.zip")


@pytest.fixture
def small_archive(tmp_path):
    path = tmp_path / "part.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("part1/NCT0000xxxx/", "")  # entrée de dossier, comme dans les vraies archives
        archive.writestr("part1/NCT0000xxxx/NCT00000001.xml", make_trial_xml(nct_id="NCT00000001"))
        archive.writestr("part1/NCT0000xxxx/NCT00000002.xml", make_trial_xml(nct_id="NCT00000002", gender="Male"))
        archive.writestr("part1/LISEZMOI.txt", "pas un essai")
    return path


def test_yields_one_record_per_xml_file_and_ignores_the_rest(small_archive):
    records = list(iter_trial_records(small_archive))

    assert [r.nct_id for r in records] == ["NCT00000001", "NCT00000002"]
    assert records[1].gender == "Male"


@pytest.mark.skipif(not REAL_ARCHIVE.exists(), reason="archive TREC absente (voir README)")
def test_first_real_trials_all_parse_without_error():
    records = list(islice(iter_trial_records(REAL_ARCHIVE), 500))

    assert len(records) == 500
    assert all(r.nct_id.startswith("NCT") for r in records)
