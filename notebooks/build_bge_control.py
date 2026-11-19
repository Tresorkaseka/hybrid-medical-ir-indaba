"""Package tested BGE control modules and a separate Colab notebook; no model download."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MODULES = ['hybrid_ir/__init__.py', 'hybrid_ir/decision/__init__.py',
           'hybrid_ir/decision/benchmark.py', 'hybrid_ir/decision/checkpoint.py',
           'hybrid_ir/decision/reranking.py',
           'hybrid_ir/decision/reranker_control.py']


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT/'notebooks')
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    package = args.output_dir/'bge_control_code.zip'
    with zipfile.ZipFile(package, 'w') as archive:
        for module in MODULES:
            info = zipfile.ZipInfo(module, date_time=(1980,1,1,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (ROOT/'src'/module).read_bytes())
    code_hash = hashlib.sha256(package.read_bytes()).hexdigest()
    driver = re.sub(r"CODE_SHA256 = '[^']+'", f"CODE_SHA256 = '{code_hash}'",
                    (ROOT/'notebooks/run_bge_control_colab.py').read_text())
    compile(driver, 'run_bge_control_colab.py', 'exec')
    (args.output_dir/'run_bge_control_colab.py').write_text(driver)
    intro = '''# Témoin BGE-reranker-v2-m3 : D′ / E′\n
À lancer **après la fin du calcul Eos**, dans un nouveau runtime GPU T4, avec le même compte AI Pro et Drive. Aucun résultat Eos n'est modifié.\n
Importer `bge_control_code.zip` dans le volet Fichiers. `decision_inputs.json.gz` est le même export top50 (125 patients, 7 340 couples uniques), récupérable depuis le dossier Drive Eos existant ou à importer. Le code vérifie ses empreintes avant usage.\n
Modèle BAAI/bge-reranker-v2-m3, révision 953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e, Apache 2.0. Sortie : logit de pertinence, réel non borné ; aucune transformation en probabilité. Float16 pour T4, attention SDPA et batch 1 ; enregistrés dans la provenance.\n
Texte identique aux entrées Eos : description patient et texte complet de l'essai, sans instruction de décision. Contexte officiel 8 192 tokens, préflight de toutes les paires **sans troncature**. Si dépassement ou erreur modèle, arrêt explicite et conservation des seuls scores déjà valides.\n
Fichier fermé après chaque réponse et snapshots complets immuables toutes les 50 paires et en fin ; une fermeture locale ne confirme pas la publication distante. Checkpoint séparé dans `hybrid_ir/exp1_bge_control_top50/953dc6f-42988327922f-closed-v2/`, repris seulement avec provenance identique. Après calcul, récupérer `scores_logits.jsonl`, `provenance.json`, `run_report.json`, puis assembler Dprime/Eprime avec `13_make_control_rankings.py`. Positions 51–1000 conservées depuis B/C. Aucune exécution GPU n'a encore validé ce carnet.\n
Sources officielles vérifiées le 17 novembre 2026 : [fiche du modèle](https://huggingface.co/BAAI/bge-reranker-v2-m3), [config épinglée](https://huggingface.co/BAAI/bge-reranker-v2-m3/blob/953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e/config.json), [tokenizer épinglé](https://huggingface.co/BAAI/bge-reranker-v2-m3/blob/953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e/tokenizer_config.json).\n'''
    setup = "import subprocess, sys\nsubprocess.check_call([sys.executable, '-m', 'pip', 'install', '--quiet', 'transformers==5.22.1', 'sentencepiece==0.2.1'])\n"
    cells = [{'cell_type':'markdown', 'metadata':{}, 'source':intro.splitlines(True)}]
    for name, source in [('setup-bge',setup),('bge-controls',driver)]:
        cells.append({'cell_type':'code','id':name,'metadata':{},'execution_count':None,'outputs':[],'source':source.splitlines(True)})
    notebook = {'nbformat':4,'nbformat_minor':5,'metadata':{'accelerator':'GPU',
                'colab':{'name':'exp1_bge_control.ipynb'},'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}},'cells':cells}
    (args.output_dir/'exp1_bge_control.ipynb').write_text(json.dumps(notebook,indent=1,ensure_ascii=False)+'\n')
    print(json.dumps({'code_sha256':code_hash,'archive_bytes':package.stat().st_size,'notebook':str(args.output_dir/'exp1_bge_control.ipynb')}))


if __name__ == '__main__':
    main()
