# Méthode

## De la question aux candidats

Une description de patient est la requête ; un essai clinique est le document. Le corpus commun contient 375 580 essais ; les années 2021 et 2022 apportent respectivement 75 et 50 requêtes et leurs jugements.

BM25 cherche les mots. EmbeddingGemma 2 produit les représentations utilisées par la recherche cosinus exacte. Le filtre SQL vérifie l’âge et le sexe ; une information manquante ne suffit pas à exclure un essai. B cherche dans tout le corpus ; C applique le masque du filtre. A applique le même filtre avant BM25.

D et E reclassent les 50 premiers résultats de B et C avec Eos (`vllm-sr/Decision-2.0-Eos-0.8B`). D′ et E′ utilisent BGE (`BAAI/bge-reranker-v2-m3`) sur exactement les mêmes pools. Les rangs 51–1000 conservent leur ordre. Les 12 500 positions des pools donnent 7 340 paires patient–essai distinctes et 6 256 essais distincts ; chaque paire est évaluée une fois par modèle.

Les textes, modèles et prétraitements sont figés. Eos répond à une question fermée ; sa valeur de type probabilité n’a pas de calibration clinique démontrée. BGE produit un logit de pertinence, pas une probabilité. Les jugements de pertinence ne sont pas transmis aux modèles. Aucun modèle n’est entraîné sur les requêtes de l’étude.

## Mesurer

- P@5/10/20 : proportion d’essais jugés éligibles dans les premiers résultats.
- R@5/10/20 : fraction des essais jugés éligibles retrouvée à ces rangs.
- MRR : inverse du rang du premier essai éligible, moyenné sur les requêtes.
- R-Precision : précision au rang égal au nombre d’essais jugés éligibles pour la requête.
- nDCG@10 : classement gradué, gains linéaires 0/1/2 pour non pertinent/exclu/éligible.
- Judged@10 : part du top 10 ayant un jugement ; indicateur descriptif de couverture.

Les mesures binaires utilisent uniquement le grade 2 comme pertinent. Un document non jugé reçoit zéro dans la notation, ce qui n’équivaut pas à un verdict médical négatif.

Les 11 comparaisons et neuf mesures de qualité forment 99 tests observés par année ; aucun emplacement réservé. Wilcoxon pairé bilatéral, correction de Holm. IC bootstrap pairé : 10 000 rééchantillonnages, graine 20261028. Les IC et les tests corrigés répondent à des analyses distinctes. Les 10 000 valeurs métriques individuelles ont été recoupées avec `ir_measures` ; Judged@10 est hors famille de tests.

## Portée

Les règles âge/sexe ont été développées sur ces mêmes 125 requêtes. Les résultats décrivent un banc d’essai documentaire rétrospectif ; ils ne déterminent pas l’éligibilité médicale réelle d’un patient et ne remplacent pas la vérification des critères par une équipe clinique.
