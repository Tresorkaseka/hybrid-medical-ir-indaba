# @title Témoin BGE : préflight, logits, checkpoint Drive et reprise
# Exécuter dans un NOUVEAU runtime GPU après la fin de Eos, jamais pendant son calcul.
import gzip
import hashlib
import importlib.metadata
import json
import pathlib
import subprocess
import sys
import time
import zipfile

import torch
from google.colab import drive, files
from transformers import AutoTokenizer, AutoModelForSequenceClassification

FULL_INPUT_SHA256 = '42988327922fcc5d1cc0c7f5431d531fae441265dc0111fbc9c813c766ff1bd8'
CODE_SHA256 = '54b827ac75407e3c697a766882aef553178e16bd326cf9fe77b60f378b7c36f1'
CODE_PATH = pathlib.Path('/content/bge_control_code.zip')
if not torch.cuda.is_available():
    raise RuntimeError('Choisir un runtime GPU T4 avant de lancer BGE')
if importlib.metadata.version('transformers') != '5.22.1':
    raise RuntimeError('Version transformers différente de la version figée')
if hashlib.sha256(CODE_PATH.read_bytes()).hexdigest() != CODE_SHA256:
    raise ValueError('Archive BGE différente du code testé')
if 'hybrid_ir' in sys.modules:
    raise RuntimeError('Ouvrir un nouveau runtime BGE après la fin de Eos ; ne pas réutiliser son processus')
with zipfile.ZipFile(CODE_PATH) as archive:
    for name in archive.namelist():
        if pathlib.PurePosixPath(name).is_absolute() or '..' in pathlib.PurePosixPath(name).parts:
            raise ValueError('Chemin interdit dans archive BGE')
    archive.extractall('/content/bge_control_code')
sys.path.insert(0, '/content/bge_control_code')
from hybrid_ir.decision.checkpoint import write_checkpoint_snapshot
from hybrid_ir.decision.reranking import unique_pairs
from hybrid_ir.decision.reranker_control import (
    BGE_MODEL, BGE_REVISION, BGE_MAX_LENGTH, PREPROCESSING, PREPROCESSING_SHA256,
    audit_control_lengths, load_control_scores, score_control_pairs,
)

# Le même compte AI Pro et le même Drive que les embeddings ; dossier de sortie distinct.
drive.mount('/content/drive')
RUN_DIR = pathlib.Path('/content/drive/MyDrive/hybrid_ir/exp1_bge_control_top50/953dc6f-42988327922f-closed-v2')
RUN_DIR.mkdir(parents=True, exist_ok=True)
INPUT_PATH = pathlib.Path('/content/decision_inputs.json.gz')
if not INPUT_PATH.exists():
    INPUT_PATH = RUN_DIR/'decision_inputs.json.gz'
if not INPUT_PATH.exists():
    INPUT_PATH = pathlib.Path('/content/drive/MyDrive/hybrid_ir/exp1_decision_eos_top50/52cad37-42988327922f-closed-v2/decision_inputs.json.gz')
blob = INPUT_PATH.read_bytes()
if hashlib.sha256(blob).hexdigest() != FULL_INPUT_SHA256:
    raise ValueError('Entrées BGE différentes des mêmes pools utilisés pour Eos')
payload = json.loads(gzip.decompress(blob))
pairs = unique_pairs(payload)
assert len(pairs) == 7340 and payload['top_n'] == 50
(RUN_DIR/'decision_inputs.json.gz').write_bytes(blob)
(RUN_DIR/'bge_control_code.zip').write_bytes(CODE_PATH.read_bytes())
provenance = {'input_sha256': FULL_INPUT_SHA256, 'model_id': BGE_MODEL, 'revision': BGE_REVISION,
              'preprocessing_sha256': PREPROCESSING_SHA256, 'code_sha256': CODE_SHA256,
              'dtype': 'float16', 'transformers': '5.22.1', 'torch': torch.__version__,
              'attention_implementation': 'sdpa', 'batch_size': 1}
CHECKPOINT = RUN_DIR/'scores_logits.jsonl'
previous = load_control_scores(payload, CHECKPOINT, provenance)
(RUN_DIR/'provenance.json').write_text(json.dumps(provenance, indent=2))
(RUN_DIR/'requirements.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True))

# Le tokenizer officiel de la même révision traite la requête et l'essai comme une paire.
# Préflight intégral CPU avant le chargement des poids GPU ; aucun texte tronqué.
tokenizer = AutoTokenizer.from_pretrained(BGE_MODEL, revision=BGE_REVISION, trust_remote_code=False)
assert tokenizer.model_max_length == BGE_MAX_LENGTH

def tokenize_ids(patient, trial):
    return tokenizer(patient, trial, truncation=False, add_special_tokens=True)['input_ids']

preflight = audit_control_lengths(payload, tokenize_ids)
preflight['preprocessing'] = PREPROCESSING
(RUN_DIR/'preflight.json').write_text(json.dumps(preflight, indent=2))
print('Préflight BGE :', json.dumps(preflight), flush=True)
if preflight['invalid']:
    raise RuntimeError('Au moins une paire dépasse 8 192 tokens BGE : arrêt sans troncature ni score ; voir preflight.json')

bge_model = AutoModelForSequenceClassification.from_pretrained(
    BGE_MODEL, revision=BGE_REVISION, trust_remote_code=False, use_safetensors=True,
    dtype=torch.float16, attn_implementation='sdpa',
).to('cuda').eval()
torch.cuda.reset_peak_memory_stats()

def bge_scorer(patient, trial):
    inputs = tokenizer(patient, trial, truncation=False, add_special_tokens=True,
                       return_token_type_ids=False, return_tensors='pt')
    n_tokens = inputs['input_ids'].shape[1]
    if n_tokens > BGE_MAX_LENGTH:
        raise ValueError('Dépassement contexte malgré le préflight')
    inputs = inputs.to('cuda')
    torch.cuda.synchronize()
    with torch.inference_mode():
        logits = bge_model(**inputs, return_dict=True).logits.reshape(-1).float()
    if logits.numel() != 1:
        raise ValueError('BGE doit retourner un seul logit par paire')
    value = logits.item()
    torch.cuda.synchronize()
    return {'logit': value, 'input_tokens': n_tokens, 'truncated': False}

completed = sum(len(v) for v in previous.values())
counter = [completed]
start = time.perf_counter()
print(f'BGE : reprise {completed}/{len(pairs)} ; logits réels, pas probabilités', flush=True)

def progress(record):
    counter[0] += 1
    if counter[0] % 50 == 0 or counter[0] == len(pairs):
        newly_saved = counter[0]-completed
        seconds_per_pair = (time.perf_counter()-start)/newly_saved
        remaining = (len(pairs)-counter[0])*seconds_per_pair
        snapshot = write_checkpoint_snapshot(CHECKPOINT, counter[0], prefix='scores_logits')
        print(f'BGE {counter[0]}/{len(pairs)} : fichier local du montage fermé ; snapshot {snapshot.name} fermé ; publication Drive non vérifiée ; {seconds_per_pair:.3f}s/paire ; reste estimé {remaining/60:.1f}min', flush=True)

try:
    scores = score_control_pairs(payload, bge_scorer, CHECKPOINT, provenance, progress)
finally:
    if CHECKPOINT.exists():
        verified = load_control_scores(payload, CHECKPOINT, provenance)
        snapshot = write_checkpoint_snapshot(CHECKPOINT, sum(len(v) for v in verified.values()), prefix='scores_logits')
        print('Snapshot final local fermé :', snapshot.name, '; publication Drive non vérifiée', flush=True)
load_control_scores(payload, CHECKPOINT, provenance, require_complete=True)
report = {'status': 'complete', 'n_pairs': len(pairs), 'n_saved': sum(len(v) for v in scores.values()),
          'n_reused': completed, 'wall_seconds_this_session': time.perf_counter()-start,
          'peak_cuda_bytes': torch.cuda.max_memory_allocated(), 'provenance': provenance,
          'score_kind': 'logit', 'truncation': False}
(RUN_DIR/'run_report.json').write_text(json.dumps(report, indent=2))
print('TERMINÉ BGE :', json.dumps(report), flush=True)
# Récupérer ces fichiers pour13_make_control_rankings.py ; publication Drive à vérifier séparément.
for path in [CHECKPOINT, RUN_DIR/'provenance.json', RUN_DIR/'run_report.json']:
    files.download(str(path))
