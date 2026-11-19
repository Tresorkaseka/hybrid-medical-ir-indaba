# Résultats et lecture prudente

Source canonique : [`exp1_decision_eos_bge.json`](../../results/exp1_decision_eos_bge.json). Le tableau du README donne les huit moyennes nDCG@10 ; le JSON conserve IC, mesures par requête, tests bruts et p corrigés.

## Contributions

B−BM25 est concluant en nDCG@10 les deux années. C−B, D−B et E−C ne le sont pas sur cette métrique après Holm. D−B et E−C améliorent P@20 et R@20 les deux années. En 2022, E−C améliore aussi R@10 et R-Precision.

En 2022, P@20 passe de 0,272 pour C à 0,338 pour E : environ 5,44 à 6,76 essais jugés éligibles parmi les 20 premiers, en moyenne. Ce n’est pas une promesse pour chaque patient.

Eos a des moyennes nDCG supérieures à BGE ; les écarts D−D′ et E−E′ restent non concluants après Holm. E−E′ améliore R@20 les deux années, P@20/R@10 en 2022 ; D−D′ améliore R@5/R@10 en 2022. Aucun gain D′−B/E′−C n’est concluant parmi les neuf mesures. L’absence de preuve d’un écart ne démontre pas l’équivalence.

## Temps observés

| Modèle | Paires | Durée | Contexte |
|---|---:|---:|---|
| Eos | 7 340 | 5 507,75 s, soit 91,80 min | T4, BF16 et tête FP32 |
| BGE | 7 340 | 500,61 s, soit 8,34 min | T4, FP16, SDPA, batch 1 |

Sauvegardes comprises ; chargement et préflight exclus. Runtimes et précisions différents : ne pas interpréter leur rapport comme une efficacité intrinsèque ni une latence d’application. Préflights complets, sans troncature. Le pic alloué PyTorch BGE de 1,19 Gio n’est pas la mémoire GPU totale.

## Pool et fautes

Le rappel des éligibles dans le pool 50 vaut B : 0,1595/0,1723 et C : 0,1797/0,1922 (2021/2022). Un reranker ne peut faire entrer de nouveaux documents dans ce pool ; ce rappel ne borne pas directement la nDCG graduée.

Bruit sur les mots alphabétiques des requêtes uniquement, 5 % et 10 %, un seul tirage imbriqué, graine 20261117. BM25/A/B/C mesurés. Les huit moyennes bruitées B/C baissent ; trois IC pairés sont entièrement négatifs, cinq incluent zéro. Pas de test direct de différence de sensibilité B contre C, pas de variabilité entre plusieurs tirages estimée. Eos et BGE sur bruit restent à mesurer.

## Ouvert

Compléter deux thèmes bibliographiques dans les manuscrits et vérifier les consignes de soumission. Étudier français, calibration, conditions hospitalières, données privées, exécution locale et recherche texte–image. IU Chest X-ray et RTX 3050 ne sont pas évalués ici.
