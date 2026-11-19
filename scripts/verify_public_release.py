"""Verify the public inventory and report statistics without data or inference."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / 'PUBLIC_MANIFEST.json').read_text())
for name, entry in manifest['files'].items():
    path = ROOT / name
    if path.stat().st_size != entry['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
        raise ValueError(f'Published file differs: {name}')
report = json.loads((ROOT / 'results/exp1_decision_eos_bge.json').read_text())
if report['status'] != 'complete':
    raise ValueError('Incomplete evaluation')
for year, n_queries in [('2021', 75), ('2022', 50)]:
    data = report[year]
    family = data['holm_family']
    if not (family['n_tests'] == family['n_observed_tests'] == 99 and family['n_reserved_tests'] == 0):
        raise ValueError(f'{year}: unexpected test family')
    for system, metrics in data['per_query'].items():
        for metric, values in metrics.items():
            if len(values) != n_queries or not math.isclose(sum(values.values()) / n_queries, data['systems'][system][metric]['mean'], rel_tol=1e-12, abs_tol=1e-12):
                raise ValueError(f'{year}/{system}/{metric}: inconsistent mean')
    tests = [v for metrics in data['pairs'].values() for metric, v in metrics.items() if metric != 'Judged@10']
    previous = 0.0
    for rank, item in enumerate(sorted(tests, key=lambda x: x['p'])):
        previous = max(previous, min(1.0, item['p'] * (len(tests) - rank)))
        if not math.isclose(previous, item['p_holm'], rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError(f'{year}: inconsistent Holm adjustment')
print(f"PASS: {len(manifest['files'])} published file hashes; eight-system means and 99-test Holm families verified. No download or inference.")
