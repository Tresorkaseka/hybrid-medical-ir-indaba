# Guide du dépôt public

Ce dépôt accompagne le poster IndabaX RDC. Il contient le code de recherche, les résultats mesurés, les scores et leur provenance, ainsi que les supports de présentation.

1. [Méthode et configurations](methode.md) : rôle de chaque composant et protocole figé.
2. [Résultats et limites](resultats.md) : ce qui progresse et ce qui reste incertain.
3. [Reproduction](reproduire.md) : distinguer vérification hors ligne, métriques et inférence GPU.
4. [Artefacts et provenance](artefacts.md) : fichiers, empreintes et exclusions de la publication.
5. [Droits et composants tiers](droits.md) : données et dépendances ne changent pas de licence.

Les requêtes TREC, le corpus intégral, les poids des modèles, les environnements locaux et les notes de travail ne sont pas distribués. Le dépôt privé de développement reste séparé. Les noms de fichiers historiques n’impliquent pas qu’une étape a été réexécutée lors de la publication.

## Validation de cette publication

Le 19 novembre 2026 : 302 tests réussis dans l’environnement du projet ; 292 réussis et 10 ignorés dans la copie publique sans données, avec les mêmes dépendances déjà installées. Une installation neuve depuis PyPI n’a pas été rejouée. Les avertissements concernent la dépréciation de `ast.Num`/`n` dans ir_measures sous Python3.13. Le poster avec QR code est compilé et inspecté ; aucun débordement LaTeX signalé.
