# Filtrer, retrouver, décider · version pédagogique

Présentation en français pour des médecins et un public non spécialiste : **27 slides principales + 2 annexes**, environ **20–25 minutes** selon le rythme. Fond blanc, silhouettes, schéma Stack Diagram et apparitions progressives au clic.

## Le parcours

- Besoin du médecin et exemple fictif de patient.
- Recherche par les mots (BM25), par le sens (EmbeddingGemma 2), filtre SQL.
- Modèle de décision Eos, choix d’un modèle compact et motivation issue de la littérature.
- Architecture et configurations expliquées en langage courant.
- TREC, pertinence, précision, rappel, nDCG, MRR, R-Precision et couverture des jugements.
- Résultats vérifiés, interprétation, incertitude et positionnement dans la littérature.
- Ressources locales et perspectives ; aucune validation clinique annoncée.

## Documents

- [Slides en PDF](presentation.pdf)
- [Notes de présentation](NOTES.md)
- [Sources scientifiques](SOURCES.md)

## Texte, notes et sources

`NOTES.md` et notes intégrées dans chaque slide. `SOURCES.md` précise les résultats et les références. Les exemples d’explication sont fictifs ; les vrais scores proviennent des JSON conservés dans data/.

BGE exécuté, récupéré et évalué. RTX 3050, français, radiologie et déploiement hospitalier restent non validés. Les calculs de cette version sont terminés.
