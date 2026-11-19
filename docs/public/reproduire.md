# Reproduire, par niveaux

## 1. Vérifier la publication, sans données ni GPU

Depuis la racine, `python3 scripts/verify_public_release.py` contrôle les empreintes du manifeste public et les moyennes/Holm du rapport. Il ne télécharge rien et ne relance aucune inférence. Ce contrôle n’est pas l’audit complet de 591 contrôles : celui-ci a été exécuté avec les entrées locales originales, rapport conservé sous `results/indaba_coherence_audit.json`.

Installation de test :

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest -q
```

Les tests nécessitant les requêtes locales TREC sont ignorés tant qu’elles ne sont pas téléchargées. Le CSV de vérification humaine démographique n’est pas distribué : le test correspondant n’est pas une validation indépendante et n’est pas reproductible à partir de la seule publication. Pour reproduire toutes les régressions avec données, une annotation de référence de même format est nécessaire.

## 2. Préparer les données publiques

Consulter les conditions des sources TREC/NIST et ClinicalTrials.gov ; les données originales ne sont pas incluses. Les scripts gardent les entrées sous `data/`, ignoré par Git.

```bash
make data                 # environ 1,8 Go, téléchargement et préparation des requêtes/qrels
make db                   # base structurée
make bm25-index           # ordre du corpus et index
make search-inputs        # masques et textes, ordre figé
make decision-inputs      # reconstruit les 7 340 paires à partir des B/C publiés
```

Les empreintes attendues des sources sont dans `docs/data_checksums.sha256`. Les classements B/C publiés permettent de reconstruire les entrées de reclassement sans refaire les embeddings. `make decision-inputs` crée aussi le benchmark ; ne pas confondre son échantillon de 24 paires avec le calcul complet.

## 3. Rejouer les classements et les mesures, sans modèles

Après reconstruction des entrées :

```bash
python experiments/exp1_trec_ct/11_make_decision_rankings.py --checkpoint results/eos-v2-raw/scores-07340.jsonl --provenance results/eos-v2-raw/provenance.json
python experiments/exp1_trec_ct/13_make_control_rankings.py --checkpoint results/bge-control-raw/scores_logits-07340.jsonl --provenance results/bge-control-raw/provenance.json
python -W ignore experiments/exp1_trec_ct/12_evaluate_decision.py --controls results/exp1_rankings_bge_controls.json.gz
python scripts/audit_indaba.py
```

Les scripts exigent l’empreinte des entrées et des pools originaux ; ne pas contourner un échec de provenance. L’audit complet attend aussi les sources article et présentation incluses. Le rejeu complet de ces commandes depuis un téléchargement neuf n’a pas été exécuté pendant la publication ; l’audit original a été vérifié sur les entrées conservées.

## 4. Refaire l’inférence

Les carnets `notebooks/exp1_encode_corpus.ipynb`, `exp1_search_bc.ipynb`, `exp1_decision_eos_full.ipynb` et `exp1_bge_control.ipynb` montrent les étapes GPU. Les sorties des carnets sont effacées dans cette publication. Les chemins Drive sont des emplacements à adapter dans votre propre compte ; aucun accès au Drive de l’auteur n’est fourni.

Respecter modèles, révisions, questions, gabarits et empreintes. Les petites archives `artifacts/frozen-code/decision_code.zip` et `notebooks/bge_control_code.zip` conservent le code exact utilisé. Reconstruire une archive avec une nouvelle version ne doit pas être présenté comme l’ancien calcul. Les poids et embeddings complets ne sont pas distribués. Les conditions d’accès des modèles s’appliquent ; aucun achat ou service distant n’est déclenché par les commandes de vérification.

## Supports

Articles : `latexmk -pdf main.tex` puis `latexmk -pdf main_fr.tex` depuis `paper/`. Poster : LuaLaTeX avec fontspec, Lato et Raleway, ou Tectonic depuis `poster/` (`tectonic --keep-logs main.tex`). Le PDF livré a été compilé avec Tectonic existant ; LuaLaTeX est présent localement mais son module luaotfload manque, ce qui empêche de valider cette voie ici. Les PDF précompilés sont inclus. LaTeX, polices et outils graphiques sont des dépendances distinctes de l’installation Python.

Slides : serveur HTTP local sur `presentation/`. Le PDF de secours est inclus ; ce n’est pas un fichier PowerPoint éditable.
