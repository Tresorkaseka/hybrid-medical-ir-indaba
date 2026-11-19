import zipfile
from collections.abc import Iterator
from pathlib import Path

from hybrid_ir.data.trial_xml import TrialRecord, parse_trial_xml


def iter_trial_records(archive_path: Path) -> Iterator[TrialRecord]:
    """Lit un à un les essais d'une archive TREC, sans tout charger en mémoire."""
    with zipfile.ZipFile(archive_path) as archive:
        for name in archive.namelist():
            if name.endswith(".xml"):
                yield parse_trial_xml(archive.read(name))
