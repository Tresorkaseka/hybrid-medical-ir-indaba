"""Emballe les modules testés et prépare le carnet Eos complet, sans dépendance ML."""
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'data/processed/decision_code.zip'
MODULES = ['hybrid_ir/__init__.py', 'hybrid_ir/decision/__init__.py',
           'hybrid_ir/decision/benchmark.py', 'hybrid_ir/decision/checkpoint.py',
           'hybrid_ir/decision/reranking.py']
with zipfile.ZipFile(PACKAGE, 'w') as archive:
    for module in MODULES:
        info = zipfile.ZipInfo(module, date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        archive.writestr(info, (ROOT/'src'/module).read_bytes())
code_hash = hashlib.sha256(PACKAGE.read_bytes()).hexdigest()
driver_path = ROOT / 'notebooks/run_decision_full_colab.py'
driver = re.sub(r"CODE_SHA256 = '[^']+'", f"CODE_SHA256 = '{code_hash}'", driver_path.read_text())
driver_path.write_text(driver)
compile(driver, str(driver_path), 'exec')
notebook = json.loads((ROOT/'notebooks/exp1_decision_benchmark.ipynb').read_text())
notebook['cells'][0]['source'] += ['\n\n## Calcul complet Eos (D/E)\n',
    'Importer aussi `decision_inputs.json.gz` et `decision_code.zip` dans le volet Fichiers.\n',
    'La dernière cellule monte le Drive du même compte AI Pro et ferme le fichier après chaque réponse ; snapshots complets fermés toutes les 50 paires et en fin. La publication distante doit être vérifiée séparément.\n',
    'Les 7 340 couples distincts sont traités une fois ; une reprise exige les mêmes empreintes.\n']
notebook['cells'].append({'cell_type':'code', 'id':'decision-eos-full', 'metadata':{},
                         'source':driver.splitlines(True),'outputs':[], 'execution_count':None})
notebook['metadata']['colab']['name'] = 'exp1_decision_eos_full.ipynb'
(ROOT/'notebooks/exp1_decision_eos_full.ipynb').write_text(json.dumps(notebook,indent=1,ensure_ascii=False)+'\n')
print('code_sha256:',code_hash,'archive bytes:',PACKAGE.stat().st_size)
