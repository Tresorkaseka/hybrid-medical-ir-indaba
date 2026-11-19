# Artefacts et provenance

## Ce qui est distribué

| Artefact | Chemin |
|---|---|
| Rapport final huit systèmes | `results/exp1_decision_eos_bge.json` |
| Classements B/C, D/E, D′/E′ | `results/exp1_rankings_*.json.gz` |
| 7 340 scores Eos | `results/eos-v2-raw/scores-07340.jsonl` |
| 7 340 logits BGE | `results/bge-control-raw/scores_logits-07340.jsonl` |
| Révisions, empreintes et préflights | Sous-dossiers bruts Eos/BGE |
| Pool 50 et bruit BM25/A/B/C | `results/exp1_pool_recall50.json`, `exp1_noise_*.json` |
| Intégrité de la publication | `PUBLIC_MANIFEST.json`, `scripts/verify_public_release.py` |
| Supports | `paper/`, `poster/`, `presentation/` |

Entrées communes Eos/BGE : SHA256 `42988327922fcc5d1cc0c7f5431d531fae441265dc0111fbc9c813c766ff1bd8`. Les fichiers publiés de scores, rapports et classements sont copiés à l’identique des artefacts vérifiés. Les carnets publiés sont des copies sans sorties : leur empreinte diffère du carnet exécuté, ce qui ne change pas celle du code figé ou des scores.

Le manifeste public est un inventaire d’intégrité, pas une signature cryptographique de l’auteur. Il exclut son propre fichier et le répertoire Git. La version du dépôt se cite aussi par son commit.

## Données non distribuées

Le corpus intégral, les textes des requêtes, les poids des modèles et les embeddings ne sont pas inclus. Les commandes de préparation des données sont décrites dans le [guide de reproduction](reproduire.md). Les exemples fictifs et les extraits cités dans les manuscrits gardent leur contexte.

## Ce que permet la vérification

Le manifeste permet de contrôler les fichiers distribués. Le script de vérification recalcule les moyennes et la correction de Holm à partir du rapport. La reproduction complète des classements et métriques nécessite les entrées TREC identifiées dans le protocole. Ces contrôles ne constituent pas une validation clinique.
