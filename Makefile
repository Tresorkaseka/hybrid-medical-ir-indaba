PY  := .venv/bin/python
PIP := .venv/bin/pip

.PHONY: setup test figures data lengths db inventory crosscheck review-sheet demographics verify-data

setup:            ## environnement Python isolé, versions figées
	python3 -m venv .venv
	$(PIP) install -r requirements-lock.txt
	$(PIP) install -e . --no-deps

test:             ## tests unitaires
	.venv/bin/pytest

data:             ## étape 0 : télécharge TREC CT 2021 et 2022 (≈ 1,8 Go) et vérifie les effectifs
	$(PY) experiments/exp1_trec_ct/00_download_and_check.py

lengths:          ## étape 1 : longueurs des essais et des requêtes en tokens
	$(PY) experiments/exp1_trec_ct/01_measure_lengths.py

db:               ## étape 2 : base SQLite des champs structurés des essais
	$(PY) experiments/exp1_trec_ct/02_build_trial_db.py

inventory:        ## étape 2a : inventaire indépendant des champs structurés (expressions régulières)
	$(PY) experiments/exp1_trec_ct/02a_inventory_structured_fields.py

crosscheck:       ## étape 2b : recoupe la base SQLite avec l'inventaire (échoue au moindre écart)
	$(PY) experiments/exp1_trec_ct/02b_crosscheck_db.py

review-sheet:     ## étape 3a : fiche de vérification de la vérité terrain âge/sexe (HTML)
	$(PY) experiments/exp1_trec_ct/gold/make_review_sheet.py

demographics:     ## étape 3 : mesure l'extraction âge/sexe contre la vérité terrain vérifiée
	$(PY) experiments/exp1_trec_ct/03_evaluate_demographics.py

bm25-index:       ## étape 4 : index BM25 maison sur les 375 580 essais (≈ 2,5 min, ≈ 4,3 Go de mémoire)
	(ulimit -v 9500000; IR_DATASETS_HOME=data/raw/ir_datasets $(PY) experiments/exp1_trec_ct/04_build_bm25_index.py)

filter-risk:      ## étape 4b : risque du filtre SQL âge/sexe sur les jugements TREC (recoupé sans SQL)
	$(PY) experiments/exp1_trec_ct/05_measure_filter_risk.py

evaluate-a:      ## étape 4c : évalue le témoin BM25 et la configuration A (recoupé avec ir_measures)
	(ulimit -v 9500000; $(PY) -W ignore experiments/exp1_trec_ct/06_evaluate_bm25_and_config_a.py)

embedding-sample: ## étape 5a : 500 essais tirés au hasard pour le test d'encodage sur Colab
	(ulimit -v 9500000; IR_DATASETS_HOME=data/raw/ir_datasets $(PY) -W ignore experiments/exp1_trec_ct/07_make_embedding_sample.py)

STACK_DIAGRAM ?= $(HOME)/.claude/skills/stack-diagram
FIG_ICONS     := data/processed/figure-icons
FIG_PY        ?= python3
figures:          ## figures d'architecture (skill stack-diagram, commit 1ed53e3) : HTML + PNG dans paper/figures
	python3 $(STACK_DIAGRAM)/scripts/fetch_icons.py $(FIG_ICONS) sqlite qdrant google "query:lucide/file-search" "split:lucide/split" "corpus:lucide/database" "pool:lucide/combine" "decision:lucide/scale" "topk:lucide/list-ordered" "table:lucide/table-2" "bm25:lucide/text-search"
	cd paper/figures && python3 make_paper_fig.py
	for n in architecture architecture-fr architecture-paper architecture-paper-fr; do \
	  python3 $(STACK_DIAGRAM)/scripts/build.py paper/figures/$$n.src.html $(FIG_ICONS) paper/figures/$$n.html --fonts $(STACK_DIAGRAM)/assets/fonts || exit 1; done
	for n in architecture architecture-fr; do $(FIG_PY) $(STACK_DIAGRAM)/scripts/render_png.py paper/figures/$$n.html paper/figures/$$n.png --selector .canvas --scale 2 || exit 1; done
	for n in architecture-paper architecture-paper-fr; do $(FIG_PY) $(STACK_DIAGRAM)/scripts/render_png.py paper/figures/$$n.html paper/figures/$$n.png --selector .canvas --scale 3 --single || exit 1; done

search-inputs:    ## étape 5c : requêtes et masques du filtre SQL à envoyer dans Colab (recherche B et C)
	$(PY) -W ignore experiments/exp1_trec_ct/08_make_search_inputs.py

.PHONY: decision-inputs
decision-inputs:  ## top-50 B/C et benchmark 24 paires pour le modèle de décision (aucun jugement)
	IR_DATASETS_HOME=data/raw/ir_datasets $(PY) -W ignore experiments/exp1_trec_ct/10_make_decision_inputs.py

evaluate-semantic: ## étape 5d : évalue B et C face à BM25 et A (classements venus de Colab, recoupés avec ir_measures)
	$(PY) -W ignore experiments/exp1_trec_ct/09_evaluate_semantic.py

docs-pdf:         ## PDF « Reproductibilité et choix » (à régénérer à chaque étape)
	$(PY) docs/build_reproducibilite.py

decision-notebook: ## reconstruit le carnet de test depuis la bibliothèque et le SHA256 du benchmark (après decision-inputs)
	$(PY) notebooks/build_decision_benchmark.py

decision-full-notebook: decision-notebook ## archive du code testée + carnet Eos complet avec sauvegarde Drive
	$(PY) notebooks/build_decision_full.py

verify-data:      ## compare les fichiers de data/raw aux empreintes SHA-256 enregistrées
	sha256sum -c docs/data_checksums.sha256

noise-inputs: ## requêtes bruitées figées, journal des mutations et masques SQL pour Colab
	$(PY) -W ignore experiments/exp1_trec_ct/14_prepare_noise.py

evaluate-noise-lexical: ## robustesse BM25/A et extraction, sans toucher aux résultats propres
	(ulimit -v 9500000; $(PY) -W ignore experiments/exp1_trec_ct/15_evaluate_noise_lexical.py)


noise-search-notebook: ## B/C bruités, mêmes embeddings et gabarit que le propre
	$(PY) notebooks/build_noise_search.py

evaluate-noise-semantic: ## vérifie le retour Colab B/C bruité puis métriques et comparaison au propre
	$(PY) -W ignore experiments/exp1_trec_ct/16_evaluate_noise_semantic.py
