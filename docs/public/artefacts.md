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
| Audit local original | `results/indaba_coherence_audit.json` |
| Intégrité de la publication | `PUBLIC_MANIFEST.json`, `scripts/verify_public_release.py` |
| Supports | `paper/`, `poster/`, `presentation/` |

Entrées communes Eos/BGE : SHA256 `42988327922fcc5d1cc0c7f5431d531fae441265dc0111fbc9c813c766ff1bd8`. Les fichiers publiés de scores, rapports et classements sont copiés à l’identique des artefacts vérifiés. Les carnets publiés sont des copies sans sorties : leur empreinte diffère du carnet exécuté, ce qui ne change pas celle du code figé ou des scores.

Le manifeste public est un inventaire d’intégrité, pas une signature cryptographique de l’auteur. Il exclut son propre fichier et le répertoire Git. La version du dépôt se cite aussi par son commit.

## Exclusions

Le dépôt public n’emporte pas l’historique Git du dépôt privé. Aucun corpus complet, texte de requête TREC en fichier de données, poids, embeddings, cache, environnement, cookie, clé, configuration de compte, capture de Drive ou journal de conversation n’est publié. Les notes de travail, Memory Bank et documents historiques intermédiaires restent privés. Les exemples fictifs et les extraits cités dans les manuscrits gardent leur contexte.

## Limites de la preuve

Les 591 contrôles portent sur la cohérence des artefacts locaux, pas sur une évaluation clinique ni une revue exhaustive des références. L’audit ne démontre pas à lui seul la généralisation du système. Le contrôle public vérifie les octets distribués et une partie des calculs statistiques ; une reconstruction complète exige les sources publiques et les entrées attendues.
