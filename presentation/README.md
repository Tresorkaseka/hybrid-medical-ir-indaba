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

## Présenter hors connexion

Ouvrir `index.html` ou servir ce dossier :

```bash
python3 -m http.server 8790 --bind 127.0.0.1
```

Puis http://127.0.0.1:8790/index.html . Droite/gauche révèlent ou masquent les étapes avant de changer de slide ; Échap ouvre la vue d’ensemble ; F active le plein écran ; S ouvre les notes (fenêtre à autoriser si nécessaire). Toutes les dépendances sont locales. Le PDF est statique, avec toutes les étapes visibles, et reste un support de secours ; ce n’est pas un PowerPoint éditable.

## Texte, notes et sources

`NOTES.md` et notes intégrées dans chaque slide. `SOURCES.md` précise les résultats et les références. Les exemples d’explication sont fictifs ; les vrais scores proviennent des JSON conservés dans data/.

## Régénérer le PDF

`python3 scripts/export_pdf.py` depuis ce dossier, avec Playwright/Chromium disponible. Le script dérive `print.html` des mêmes sections et données et produit 29 pages paysage.

BGE exécuté, récupéré et évalué. RTX 3050, français, radiologie et déploiement hospitalier restent non validés. Les calculs de cette version sont terminés.
