# Sources de la présentation

État figé au 18 novembre 2026. BGE est évalué, la famille99est entièrement observée.

## Résultats du projet

- `data/exp1_decision_eos_bge.json` : copie du rapport canonique `results/exp1_decision_eos_bge.json`, moyennes, IC, Wilcoxon, famille prospective de 99 tests par année. nDCG@10 arrondi à trois décimales dans slides.js.
- `data/exp1_noise_semantic.json` : copie du rapport canonique de robustesse, bruit synthétique unique et imbriqué, seed 20261117. Pas de test direct de sensibilité B/C.
- `../results/eos-v2-raw/` : scores et provenance du calcul Eos terminé, 7 340 paires. Durée globale 5 507,75 s, sauvegardes comprises, hors chargement/préflight. Aucune latence de consultation ni compatibilité RTX 3050 mesurée.
- `../paper/main.tex`, `../paper/main_fr.tex`, `../docs/public/resultats.md` : contexte, protocole et limites.
- `assets/architecture.html` : schéma autonome. Recherche cosinus exacte, masque SQL, reranking top 50, sans RRF. Les rangs 51–1000 restent inchangés.

## Littérature citée

- Pradeep, R., Li, Y., Wang, Y., Lin, J. (2022). *Neural Query Synthesis and Domain-Specific Ranking Templates for Multi-Stage Clinical Trial Matching*. SIGIR. https://doi.org/10.1145/3477495.3531853
- Jin, Q. et al. (2024). *Matching patients to clinical trials with large language models*. Nature Communications. https://doi.org/10.1038/s41467-024-53081-z
- Zhao, Z. et al. (2025). *CliniQ: A Multi-faceted Benchmark for Electronic Health Record Retrieval with Semantic Match Assessment*. https://arxiv.org/abs/2502.06252

Ces publications motivent le problème ; leurs chiffres ne sont pas présentés comme une comparaison expérimentale directe avec notre architecture. CliniQ porte sur les dossiers médicaux ; TrialGPT suit un autre cadre expérimental.

## Ressources visuelles et logicielles

- Illustration originale générée : voir assets/PROVENANCE.md.
- Schéma : pictogrammes Lucide (ISC), sans revendication de logos officiels des modèles. Crédit dans le HTML autonome.
- Reveal.js 5.2.1 : licence MIT conservée dans vendor/LICENSE-reveal.
- Raleway et Lato : licences OFL conservées dans assets/.

## Vérification des modèles pour la version pédagogique · 18/11/2026

- [Fiche officielle Google DeepMind : EmbeddingGemma 2](https://huggingface.co/google/embeddinggemma-2) et [documentation Google](https://ai.google.dev/gemma/docs/embeddinggemma) : encodeur à poids ouverts, représentations 768 dimensions, conception compacte avec composante texte. Le choix répond à l’objectif de ressources accessibles ; aucune supériorité universelle en médecine ni performance locale de notre pipeline n’en est déduite. Seul le texte est évalué ici.
- [Fiche officielle Decision 2.0 Eos 0.8B](https://huggingface.co/vllm-sr/Decision-2.0-Eos-0.8B) : modèle de décision pour questions fermées, sortie typée sans génération de texte. Taille commerciale 0,8B, environ0,75B paramètres selon la fiche. Aucun chiffre de latence marketing n’est repris comme mesure de notre expérience.
- [Rapport officiel TREC Clinical Trials 2022](https://trec.nist.gov/pubs/trec31/papers/Overview_trials.pdf) : meilleur run monoT5, nDCG@10 0,6125 (arrondi0,613), point de repère distinct de notreE0,4791. Pas de comparaison contrôlée réexécutée.

Les listes illustrant précision, rappel, nDCG et MRR/R-Precision sont fictives et signalées comme telles. Les valeurs P@20/R@20 des configurations C/E sont extraites du rapport canonique, en pourcentages à une décimale. L’équivalent2022 d’environ5,4→6,8 essais éligibles sur20 est obtenu par 20×P@20, pas un nouveau résultat clinique.

BGE : results/bge-control-raw,7340logits complets,8,34min,préflight7340/7340max5986/8192sans troncature. ModèleBAAI/bge-reranker-v2-m3,révision953dc6f,FP16. 10000valeurs recoupées ; comparaisonqualité surmêmespools, précisions/runtimesdifférents pourlescoûts.
