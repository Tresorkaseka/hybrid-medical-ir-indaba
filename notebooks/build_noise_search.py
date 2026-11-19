"""Prépare B/C bruités à partir du carnet propre, en conservant le calcul de similarité."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
input_path = ROOT / 'data/processed/search_inputs_noise.json.gz'
expected_hash = hashlib.sha256(input_path.read_bytes()).hexdigest()
book = json.loads((ROOT / 'notebooks/exp1_search_bc.ipynb').read_text())
book['metadata'].pop('accelerator', None)
book['metadata']['colab'].pop('gpuType', None)
book['cells'][0]['source'] = [
    '# Robustesse B/C : requêtes bruitées à 5 % et 10 %\n',
    'Environnement CPU, sur le même Drive que les 38 morceaux du corpus. Peut tourner pendant Eos.\n',
    'Importer `search_inputs_noise.json.gz` dans le volet Fichiers, puis Tout exécuter.\n',
    'Les 250 requêtes utilisent les textes et masques figés sur le PC. Aucun jugement transmis.\n',
    'Même modèle, révision, float32, préfixe et recherche exacte que le propre.\n',
    'Les sorties sont distinctes du propre ; le carnet ne modifie pas les embeddings.\n',
]
for cell in book['cells']:
    if cell['cell_type'] == 'code':
        cell['execution_count'] = None
        cell['outputs'] = []
source = ''.join(book['cells'][1]['source'])
source = source.replace('125 requêtes', '250 requêtes').replace('DEVICE = "cuda" if torch.cuda.is_available() else "cpu"', 'DEVICE = "cpu"')
book['cells'][1]['source'] = source.splitlines(True)
book['cells'][3]['source'] = f'''# Entrées bruitées, empreinte figée avant toute évaluation
import gzip, json, hashlib, base64
import numpy as np
from google.colab import files
from pathlib import Path
path = Path('/content/search_inputs_noise.json.gz')
if not path.exists():
    files.upload()
blob = path.read_bytes()
INPUT_SHA256 = '{expected_hash}'
assert hashlib.sha256(blob).hexdigest() == INPUT_SHA256, 'Entrées différentes du protocole figé'
inputs = json.loads(gzip.decompress(blob))
assert len(inputs['queries']) == 250
print(len(inputs['queries']), 'requêtes bruitées ;', inputs['noise_sha256'])
'''.splitlines(True)
source = ''.join(book['cells'][6]['source'])
source = source.replace('print(len(rankings["B"]), "requêtes ;", rankings["B"]["2021/1"][:3])',
                        'print(len(rankings["B"]), "requêtes bruitées")')
book['cells'][6]['source'] = source.splitlines(True)
source = ''.join(book['cells'][7]['source']).replace('exp1_rankings_bc.json.gz', 'exp1_rankings_bc_noise.json.gz')
source = source.replace('"query_prefix":', '"input_sha256": INPUT_SHA256, "noise_sha256": inputs["noise_sha256"], "query_prefix":')
source = source.replace('"query_prefix":', '"query_device": DEVICE, "query_dtype": str(Q.dtype), "query_versions": {"torch": torch.__version__, "sentence_transformers": sentence_transformers.__version__, "transformers": transformers.__version__}, "query_prefix":')
book['cells'][7]['source'] = source.splitlines(True)
book['metadata']['colab']['name'] = 'exp1_search_bc_noise.ipynb'
for i, cell in enumerate(book['cells']):
    if cell['cell_type'] == 'code':
        # L'unique commande magique pip est vérifiée séparément par sa structure d'origine.
        source = ''.join(cell['source'])
        compile('\n'.join(s for s in source.splitlines() if not s.startswith('!')), f'noise-cell-{i}', 'exec')
output = ROOT / 'notebooks/exp1_search_bc_noise.ipynb'
output.write_text(json.dumps(book, ensure_ascii=False, indent=1)+'\n')
print(output, 'input_sha256:', expected_hash)
