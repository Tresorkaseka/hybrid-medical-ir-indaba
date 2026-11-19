import json,pathlib,hashlib
root=pathlib.Path(__file__).resolve().parents[1]
cells=[]
def md(s):cells.append({'cell_type':'markdown','metadata':{},'source':s.splitlines(True)})
def code(s):cells.append({'cell_type':'code','metadata':{},'source':s.splitlines(True),'execution_count':None,'outputs':[]})
md('''# Test de vitesse — Decision 2.0 Eos / TREC Clinical Trials

Objectif : mesurer la faisabilité des configurations D et E avant leur exécution complète.
24 paires patient–essai issues des résultats B/C, sans jugements de pertinence.

**Compte Google AI Pro, GPU T4.** Exécution → Modifier le type d’exécution → T4, puis Tout exécuter.
À la demande d’import, choisir `decision_benchmark_inputs.json.gz`.
Le modèle est téléchargé depuis son dépôt officiel Hugging Face, à une révision figée.
Aucun montage de Drive, aucun achat de crédits. Le rapport est téléchargé en fin de test.

Le runtime officiel impose BF16 sur GPU, avec tête FP32 : ce carnet ne force pas FP16.
Le résultat de ce test est une mesure de vitesse, pas une mesure de qualité clinique.
''')
code('''# @title 1. Vérifier le GPU avant toute installation
import json, sys, subprocess, platform, time, pathlib, hashlib, traceback
import torch
if not torch.cuda.is_available():
    raise RuntimeError("GPU absent. Exécution > Modifier le type d'exécution > GPU T4, puis relancer.")
env = {"python": sys.version, "platform": platform.platform(), "torch": torch.__version__,
       "cuda": torch.version.cuda, "gpu": torch.cuda.get_device_name(0),
       "capability": list(torch.cuda.get_device_capability(0)),
       "memory_total_bytes": torch.cuda.get_device_properties(0).total_memory,
       "bf16_reported": torch.cuda.is_bf16_supported()}
try:
    env["bf16_native"] = torch.cuda.is_bf16_supported(including_emulation=False)
except TypeError:
    env["bf16_native"] = None
print(json.dumps(env, indent=2))
if not env["bf16_reported"]:
    raise RuntimeError("Le runtime officiel refuse ce GPU sans BF16. Ne pas modifier silencieusement la précision.")
''')
code('''# @title 2. Installer les dépendances du runtime officiel
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "transformers==5.22.1", "safetensors", "huggingface_hub"], check=True)
import importlib.metadata
for package in ("torch", "transformers", "safetensors", "huggingface_hub", "tokenizers"):
    env[package] = importlib.metadata.version(package)
print(json.dumps(env, indent=2))
''')
bench=root/'data/processed/decision_benchmark_inputs.json.gz'
h=hashlib.sha256(bench.read_bytes()).hexdigest()
code('''# @title 3. Importer uniquement le petit fichier de test
from google.colab import files
import gzip
EXPECTED_SHA256 = '''+repr(h)+'''
INPUT_NAME = "decision_benchmark_inputs.json.gz"
if not pathlib.Path(INPUT_NAME).exists():
    uploaded = files.upload()
    if INPUT_NAME not in uploaded:
        raise ValueError("Choisir le fichier " + INPUT_NAME)
input_bytes = pathlib.Path(INPUT_NAME).read_bytes()
input_sha = hashlib.sha256(input_bytes).hexdigest()
if input_sha != EXPECTED_SHA256:
    raise ValueError("Empreinte d'entrée différente de celle préparée sur le PC : " + input_sha)
payload = json.loads(gzip.decompress(input_bytes))
assert payload["schema_version"] == 1
assert len(payload["benchmark_pairs"]) == 24
print("Entrée vérifiée :", len(payload["benchmark_pairs"]), "paires ; SHA256", input_sha)
''')
module=(root/'src/hybrid_ir/decision/benchmark.py').read_text()
code('# @title 4. Fonctions du projet (copie vérifiée par les tests locaux)\n'+module)
code('''# @title 5. Charger Eos et mesurer (limite de dix minutes de test hors chargement)
from transformers import AutoModel
MODEL = "vllm-sr/Decision-2.0-Eos-0.8B"
REVISION = "52cad37ef21f598302fe964cbfa164739cb965d5"
REPORT_PATH = pathlib.Path("decision_benchmark_result.json")
LOCK_PATH = pathlib.Path("decision_benchmark_requirements.txt")
PARTIAL_PATH = pathlib.Path("decision_benchmark_records.jsonl")
report = {"model": MODEL, "revision": REVISION, "input_sha256": input_sha,
          "environment": env, "status": "starting", "schema_version": 1,
          "precision": "official runtime: BF16 backbone/autocast, FP32 head; no FP16 override"}
REPORT_PATH.write_text(json.dumps(report, indent=2))
LOCK_PATH.write_text(subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True))
try:
    load_start = time.perf_counter()
    model = AutoModel.from_pretrained(MODEL, revision=REVISION, trust_remote_code=True, device="cuda:0")
    report["load_seconds"] = time.perf_counter() - load_start
    report["model_manifest"] = model.manifest
    first = payload["benchmark_pairs"][0]
    torch.cuda.synchronize()
    warm_start = time.perf_counter()
    warm = model.system_one(**decision_request(payload["queries"][first["query_key"]], payload["trials"][first["trial_id"]]))
    torch.cuda.synchronize()
    report["warmup_seconds"] = time.perf_counter() - warm_start
    yes_probability(warm)
    report["warmup_raw"] = warm
    torch.cuda.reset_peak_memory_stats()
    PARTIAL_PATH.write_text("")
    def save_record(record):
        with PARTIAL_PATH.open("a") as out:
            out.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\\n")
        print(f"{record['source']} {record['query_key']} rang {record['rank']} : {record['seconds']:.2f} s ; " +
              (f"p={record['probability']:.4f}" if "probability" in record else record["error"]), flush=True)
    report.update(benchmark_pairs(payload, model.system_one, synchronize=torch.cuda.synchronize,
                                  max_seconds=600, on_record=save_record))
    report["peak_memory_allocated_bytes"] = torch.cuda.max_memory_allocated()
    report["peak_memory_reserved_bytes"] = torch.cuda.max_memory_reserved()
    if report["status"] == "complete":
        mean_seconds = sum(r["seconds"] for r in report["records"]) / report["n_valid"]
        report["mean_seconds_per_pair"] = mean_seconds
        report["rough_hours_for_12500_pairs_without_deduplication"] = mean_seconds * 12500 / 3600
        report["estimate_note"] = "Extrapolation sur 24 paires, non un temps garanti ; longueurs et chargement à considérer."
except Exception as exc:
    report["status"] = "failed"
    report["error"] = f"{type(exc).__name__}: {exc}"
    report["traceback"] = traceback.format_exc()
finally:
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))
print(json.dumps({k:v for k,v in report.items() if k not in ("records", "model_manifest", "warmup_raw")}, indent=2, ensure_ascii=False))
''')
code('''# @title 6. Récupérer le rapport sur le PC
files.download(str(REPORT_PATH))
files.download(str(LOCK_PATH))
if PARTIAL_PATH.exists():
    files.download(str(PARTIAL_PATH))
print("TEST TERMINÉ :", report["status"])
print("Après récupération, déconnecter et supprimer l'environnement d'exécution si aucun autre calcul ne suit.")
''')
code((root/'notebooks/decision_tokenizer_audit.py').read_text())
nb={'cells':cells,'metadata':{'colab':{'name':'exp1_decision_benchmark.ipynb'},'accelerator':'GPU','kernelspec':{'display_name':'Python 3','name':'python3'},'language_info':{'name':'python'}},'nbformat':4,'nbformat_minor':5}
for i,c in enumerate(cells):
 c['id']=f'decision-benchmark-{i}'
 if c['cell_type']=='code':compile(''.join(c['source']),f'cell{i}','exec')
p=root/'notebooks/exp1_decision_benchmark.ipynb';p.write_text(json.dumps(nb,indent=1,ensure_ascii=False)+'\n');print(p,'input_hash',h)
