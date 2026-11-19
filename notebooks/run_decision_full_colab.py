# @title 8. Calculer D/E avec Eos : top-50, déduplication et reprise Drive
# À exécuter après le benchmark et le contrôle du tokenizer dans le même runtime.
import importlib
import shutil
import zipfile
from google.colab import drive

assert report['status'] == 'complete' and report['n_valid'] == 24
assert report['tokenizer_audit']['mismatches'] == []
assert MODEL == 'vllm-sr/Decision-2.0-Eos-0.8B'
assert REVISION == '52cad37ef21f598302fe964cbfa164739cb965d5'
FULL_INPUT_SHA256 = '42988327922fcc5d1cc0c7f5431d531fae441265dc0111fbc9c813c766ff1bd8'
CODE_PATH = pathlib.Path('/content/decision_code.zip')
CODE_SHA256 = '1b705a9c0bcf12f7f43a9363f079f75235c2378b4eaa9e962aa8437f7468ea34'
if hashlib.sha256(CODE_PATH.read_bytes()).hexdigest() != CODE_SHA256:
    raise ValueError('Archive du code différente du code testé sur le PC')
# Recharger uniquement nos modules depuis l'archive vérifiée, y compris après une tentative v1.
for module_name in list(sys.modules):
    if module_name == 'hybrid_ir' or module_name.startswith('hybrid_ir.'):
        del sys.modules[module_name]
with zipfile.ZipFile(CODE_PATH) as archive:
    for name in archive.namelist():
        if pathlib.PurePosixPath(name).is_absolute() or '..' in pathlib.PurePosixPath(name).parts:
            raise ValueError('Chemin interdit dans archive du code')
    archive.extractall('/content/hybrid_decision_code')
sys.path.insert(0, '/content/hybrid_decision_code')
from hybrid_ir.decision.checkpoint import write_checkpoint_snapshot
from hybrid_ir.decision.benchmark import QUESTION, decision_request
from hybrid_ir.decision.reranking import unique_pairs, load_checkpoint_scores, score_pairs

drive.mount('/content/drive')
RUN_DIR = pathlib.Path('/content/drive/MyDrive/hybrid_ir/exp1_decision_eos_top50/52cad37-42988327922f-closed-v2')
RUN_DIR.mkdir(parents=True, exist_ok=True)
FULL_INPUT_PATH = pathlib.Path('/content/decision_inputs.json.gz')
if not FULL_INPUT_PATH.exists():
    FULL_INPUT_PATH = RUN_DIR / 'decision_inputs.json.gz'
full_bytes = FULL_INPUT_PATH.read_bytes()
if hashlib.sha256(full_bytes).hexdigest() != FULL_INPUT_SHA256:
    raise ValueError('Empreinte du fichier complet incorrecte')
full_payload = json.loads(gzip.decompress(full_bytes))
all_pairs = unique_pairs(full_payload)
assert len(all_pairs) == 7340
assert full_payload['top_n'] == 50
if not (RUN_DIR / 'decision_inputs.json.gz').exists():
    (RUN_DIR / 'decision_inputs.json.gz').write_bytes(full_bytes)
shutil.copyfile(CODE_PATH, RUN_DIR / CODE_PATH.name)
shutil.copyfile(LOCK_PATH, RUN_DIR / 'requirements-benchmark.txt')
shutil.copyfile(REPORT_PATH, RUN_DIR / 'benchmark.json')
provenance = {'input_sha256': FULL_INPUT_SHA256, 'model_id': MODEL, 'revision': REVISION,
              'prompt_sha256': hashlib.sha256(QUESTION.encode()).hexdigest(), 'code_sha256': CODE_SHA256}
(RUN_DIR / 'provenance.json').write_text(json.dumps(provenance, indent=2))
print('Dossier local du montage Drive :', RUN_DIR, '; publication distante non vérifiée', flush=True)
print('Paires distinctes :', len(all_pairs), flush=True)

# Préflight CPU : exactement l'encodeur et le format du runtime officiel figé.
# Aucun texte n'est tronqué et aucun appel GPU de classement ne précède ce contrôle.
runtime_package = model.runtime.backend.__class__.__module__.rsplit('.', 1)[0]
encoder_module = importlib.import_module(runtime_package + '._vendor.dev2model.decision_model')
infer_module = importlib.import_module(runtime_package + '._vendor.dev2model.infer')
encode = model.runtime.backend.encode_fn or encoder_module.encode
lengths, invalid = [], []
for key, trial_id in all_pairs:
    request = decision_request(full_payload['queries'][key], full_payload['trials'][trial_id])
    try:
        row = infer_module.question_to_row({'id': key + '/' + trial_id, 'state': request['state']},
                                          'eligible', request['questions']['eligible'])
        encoded = encode(row, model.runtime.backend.tokenizer, model.runtime.backend.cap)
        lengths.append(len(encoded['ids']))
    except ValueError as exc:
        invalid.append({'query_key': key, 'trial_id': trial_id, 'error': str(exc)})
preflight = {'n_pairs': len(all_pairs), 'n_valid': len(lengths), 'invalid': invalid,
             'max_tokens': max(lengths) if lengths else None,
             'mean_tokens': sum(lengths)/len(lengths) if lengths else None,
             'context_limit': model.runtime.backend.cap}
(RUN_DIR / 'preflight.json').write_text(json.dumps(preflight, indent=2))
print('Préflight :', json.dumps(preflight), flush=True)
if invalid:
    raise RuntimeError('Entrées hors contexte ou invalides : voir preflight.json ; aucun score complet lancé')

CHECKPOINT = RUN_DIR / 'scores.jsonl'
previous = load_checkpoint_scores(full_payload, CHECKPOINT, provenance)
completed = sum(len(v) for v in previous.values())
counter = [completed]
print(f'Reprise : {completed}/{len(all_pairs)} paires déjà calculées', flush=True)

def synchronized_scorer(**request):
    torch.cuda.synchronize()
    response = model.system_one(**request)
    torch.cuda.synchronize()
    return response

def show_progress(record):
    counter[0] += 1
    if counter[0] % 50 == 0 or counter[0] == len(all_pairs):
        snapshot = write_checkpoint_snapshot(CHECKPOINT, counter[0])
        print(f'{counter[0]}/{len(all_pairs)} : fichier local du montage fermé ; snapshot {snapshot.name} fermé ; publication Drive non vérifiée ; dernière {record["seconds"]:.2f} s', flush=True)

full_started = time.perf_counter()
full_status = {'status': 'running', 'n_expected': len(all_pairs), 'n_reused': completed,
               'provenance': provenance, 'environment': env, 'preflight': preflight}
(RUN_DIR / 'status.json').write_text(json.dumps(full_status, indent=2))
try:
    full_scores = score_pairs(full_payload, synchronized_scorer, CHECKPOINT, provenance, on_record=show_progress)
    full_status.update(status='complete', n_scored=sum(len(v) for v in full_scores.values()))
except Exception as exc:
    full_status.update(status='failed', n_scored=counter[0], error=f'{type(exc).__name__}: {exc}')
    raise
finally:
    if CHECKPOINT.exists():
        verified = load_checkpoint_scores(full_payload, CHECKPOINT, provenance)
        snapshot = write_checkpoint_snapshot(CHECKPOINT, sum(len(v) for v in verified.values()))
        print('Snapshot final local fermé :', snapshot.name, '; publication Drive non vérifiée', flush=True)
    full_status['this_run_seconds'] = time.perf_counter() - full_started
    (RUN_DIR / 'status.json').write_text(json.dumps(full_status, indent=2))
    print(json.dumps(full_status, indent=2), flush=True)
print('D/E EOS : SCORES LOCAUX TERMINÉS ; publication Drive non vérifiée. Vérifier/récupérer scores.jsonl ou le snapshot complet + provenance.json pour évaluation sur le PC.', flush=True)
