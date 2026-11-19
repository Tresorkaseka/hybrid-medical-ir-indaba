# Notes de présentation

## 1. Filtrer. Retrouver. Décider.

Objectif de cette présentation : comprendre le raisonnement, pas apprendre des noms de modèles. Filtrer, retrouver, décider désigne trois opérations informatiques. La décision d’inclusion reste médicale. Parcours principal environ20minutes ; annexes facultatives.

## 2. Un médecin. Un patient. Des essais à retrouver.

Notre exemple simplifié est un patient de 45 ans avec insuffisance cardiaque. La silhouette reste la même consultation anonyme, sans identité ni données réelles. Les données expérimentales sont anglophones ; les phrases françaises de démonstration n’attestent pas une performance en français. Retrouver une fiche intéressante n’est pas certifier l’éligibilité.

## 3. Chercher les mêmes mots : la recherche « lexicale ».

Lexical signifie relatif aux mots. BM25 n’est pas un modèle génératif ni un système qui vérifie les critères médicaux. Il pondère les correspondances de termes. Il ne suffit pas de compter mécaniquement tous les mots. L’exemple français illustre le mécanisme ; l’expérience utilise un corpus anglais.

## 4. Chercher une idée proche : la recherche « sémantique ».

Un encodeur est un modèle qui transforme le texte en représentation numérique. Les composantes de cette liste ne sont pas des variables cliniques lisibles une à une. Les deux formulations de l’exemple ne sont pas des synonymes interchangeables dans toutes les situations : on illustre seulement une proximité de sujet. Le modèle peut se tromper, notamment sur la négation ou les conditions d’éligibilité.

## 5. Pourquoi EmbeddingGemma 2 de Google ?

EmbeddingGemma2 est un modèle à poids ouverts de GoogleDeepMind. Ce choix correspond à l’objectif de ressources accessibles et à une extension multimodale éventuelle ; ce n’est pas la démonstration qu’il serait le meilleur modèle médical. Nous utilisons la composante texte et768dimensions. La similarité est calculée exactement sur les vecteurs normalisés. On peut expliquer le cosinus comme une mesure d’orientation proche entre deux représentations numériques, sans formule au tableau. Le français et les images ne font pas partie de l’évaluation actuelle. Source officielle consultée le18novembre2026.

## 6. Une ressemblance de sens ne garantit pas les bons critères.

Le nom du moteur utilisé est SQLite. Les règles d’extraction lisent l’âge et le sexe dans la description. Si elles se trompent, le filtre peut exclure à tort un essai pertinent. Il ne vérifie pas la totalité des critères, notamment l’historique thérapeutique ou les valeurs biologiques. Un champ de borne d’âge absent n’exclut pas l’essai. Les règles ont été développées sur les125requêtes, ce qui limite la généralisation.

## 7. Un modèle de décision répond à une question fermée.

Un modèle de décision, au sens de cette famille, reçoit un contexte et des questions fermées : oui/non, choix ou score. Nous utilisons le format oui/non officiel. Le modèle renvoie des valeurs de probabilité selon son apprentissage, mais elles ne sont pas calibrées pour l’éligibilité clinique ; on les appelle ici scores de classement. Le texte complet disponible du patient et de l’essai, dont l’éligibilité, alimente chaque paire. Aucun raisonnement textuel ou contrôle de chaque critère n’est évalué séparément. Il ne s’agit pas de laisser le modèle décider de l’accès aux soins.

## 8. Pourquoi commencer par un petit modèle ?

La taille commerciale0,8B est une approximation ; la fiche indique environ0,75milliard de paramètres. Nous avons retenu un membre compact d’une famille à poids ouverts pour un premier test accessible. Ce n’est pas une étude contrôlée de l’effet de la taille : Sol et les grandes tailles ne sont pas mesurés. Les poids téléchargeables permettent d’envisager une exécution locale ; aucune référence RTX3050 ouCPU n’est établie. Le calcul sur Colab est dans le cloud. Un modèle compact n’est ni nécessairement rapide pour tous les textes ni automatiquement précis.

## 9. Ce que les travaux précédents nous ont amenés à tester.

Nous ne revendiquons pas l’invention de SQL, de la recherche dense ou des architectures à plusieurs étages. Notre interrogation est leur complémentarité mesurable avec un petit modèle de décision sur un benchmark médical public. Pradeep utilise notamment un reranker monoT5, c’est-à-dire un modèle qui attribue une pertinence à un couple requête/document. Sans entraînement adapté, certaines variantes avaient des résultats inférieurs au premier étage. CliniQ concerne les dossiers, pas notre corpus d’essais : on en retient la nécessité de mesurer sur la bonne tâche, pas un score directement comparable.

## 10. Notre approche : trois rôles, trois questions différentes.

Ce que l’on mélange, ce sont des fonctions complémentaires. Dans le système final, il n’y a pas de mélange des scores BM25 et sémantiques : BM25 sert de référence séparée. Chaque étage doit justifier sa présence dans l’évaluation. L’admissibilité finale reste hors de ce classement automatique.

## 11. Comment circule la demande ?

Suivre la description à gauche. Une branche produit les contraintes et l’autre la représentation du texte. Le masque SQL restreint les essais autorisés, puis le cosinus exact classe les vecteurs du corpus. Top50 signifie les50premiers candidats de ce classement, pas les50meilleurs essais connus dans tout le corpus. Eos réordonne seulement ce groupe. Les rangs51à1000 sont conservés. Le rappel moyen des essais jugés éligibles à50est0,1595/0,1723pourB et0,1797/0,1922pourC (2021/2022) ; un essai manqué au premier étage ne peut pas être promu par Eos.

## 12. Huit façons de chercher, pour comprendre ce qui apporte quoi.

Lire les colonnes comme des ingrédients que l’on active ou non. A est la version lexicale filtrée. Le tableau doit rester disponible pour relire les graphiques. Aucun système ne fusionne BM25 et les vecteurs. Une ablation signifie ici comparer le système avec et sans un composant pour mesurer sa contribution.

## 13. Une comparaison, une question à la fois.

Ces comparaisons partagent les mêmes requêtes et jugements. D contreB mesure également Eos, mais sans le filtre. E contreD regarde le filtre après ajout d’Eos. Le témoin BGE est mesuré sur les mêmes pools : Eos obtient de meilleures moyennes nDCG, mais sans écart concluant après Holm. Eos ne démontre donc pas une supériorité générale.

## 14. TREC : un terrain commun pour tester les moteurs de recherche.

Une requête est ici une description de patient, pas forcément une question courte. Un corpus est l’ensemble des documents dans lequel on cherche. Les descriptions sont des sujets de benchmark, pas une cohorte de patients suivis par notre système. TREC organise une évaluation reproductible. Le rapport officiel annonce375581essais ; ir_datasets en charge375580, notre corpus vérifié. Les deux années ont des requêtes et jugements différents. Source principale : overviewTREC2022, consulté localement et archivé.

## 15. Comment sait-on qu’un résultat est pertinent ?

Les jugements TREC sont faits par des évaluateurs médicaux/biomédicaux et ne couvrent pas toutes les paires. Eligible correspond à2, Excludedà1 etNotRelevantà0 dans le nDCG. Les autres métriques considèrent uniquementEligible comme pertinent. Le lieu et le recrutement ne sont pas des critères évalués par cette tâche. Le rang d’un essai exclu peut donc apporter un gain au nDCG gradué : cela ne signifie pas que cet essai doit être proposé pour inclusion.

## 16. Précision et rappel : deux questions complémentaires.

Les nombres sont une démonstration entièrement fictive, pas un résultat mesuré. La précision mesure la part utile de la shortlist. Le rappel mesure sa couverture des essais pertinents jugés pour cette requête. Un grand nombre d’essais pertinents connus rend un rappel à20forcément plus difficile ; on ne doit pas le lire comme une sensibilité clinique. Dans notre exemple, Exclu est non pertinent pour précision et rappel, comme dans le protocole.

## 17. nDCG : les meilleurs essais arrivent-ils en premier ?

nDCG signifie normalized Discounted Cumulative Gain. En clair : on donne un gain aux documents selon leur niveau de pertinence, on réduit le poids de ceux qui sont loin dans la liste, puis on rapporte le gain au meilleur ordre possible. La normalisation permet de comparer des requêtes différentes. TREC utilise trois niveaux, y compris un gain intermédiaire pourExclu. Les listes sont fictives et n’ont pas de score numérique calculé ici. UnnDCGde0,479n’est pas47,9% de patients correctement appariés.

## 18. Deux autres façons de lire une liste de résultats.

MRR ne regarde que le premier essai éligible trouvé ; il ne mesure pas la qualité du reste de la liste. R-Precision utilise R égal au nombre total d’essais éligibles jugés pour cette requête. Les chiffres1,4et6sont des exemples pédagogiques, pas des résultats. Ces métriques, les précisions à5/10/20, les rappels à5/10/20etnDCG@10forment les9métriques de qualité de notre protocole.

## 19. Le corrigé est incomplet. Il faut aussi le montrer.

Les jugements sont issus des résultats soumis à la campagne, ce qu’on appelle le pooling. Les évaluations traitent les documents non jugés comme non pertinents. Un système qui découvre d’autres essais intéressants peut donc être pénalisé. NotreJudged@10deEest0,571en2021et0,676en2022. Ce n’est ni une précision ni un taux de dossiers vérifiés cliniquement.

## 20. Les résultats mesurés : le sens dépasse les mots.

Maintenant seulement, présenter les chiffres. En2021BM25a0,275etB0,396 ; en2022respectivement0,254et0,411. La comparaisonBmoinsBM25est concluante ennDCG@10après correction, dans les deux années. Les moyennes deEatteignent0,415et0,479, mais on ne doit pas attribuer tous ces écarts au reclassement : il faut comparerEàC. Tous les systèmes utilisent les mêmes requêtes et le même corpus.

## 21. Eos améliore la liste des 20 essais à examiner.

Les tableaux montrent les valeurs deC etE, pour rendre lisible l’apport d’Eos en présence du filtre. En2022laP@20passe de27,2à33,8%, et leR@20de11,16à14,34%. La précision de33,8% signifie en moyenne33,8% des20premiers sont jugés éligibles ; ce n’est pas un taux d’éligibilité des patients. Les améliorationsP@20etR@20sont concluantes pourDmoinsB etEmoinsC lesdeuxannées aprèsHolm. Tous les autres gains ne sont pas forcément concluants.

## 22. Une meilleure moyenne ne suffit pas pour conclure.

Une différence non concluante ne démontre ni absence d’effet ni équivalence. Nous utilisons des tests pairés sur les requêtes et la correction deHolm. Les intervalles bootstrap et les tests deWilcoxon sont des analyses distinctes. En2022DmoinsB nDCGa unICexcluant0mais unpcorrigé0,416 ; ne pas résumer l’incertitude au signe d’un seul intervalle. La famille prospective inclut99tests/an ; détailenannexe.

## 23. Où nous situons-nous par rapport à la recherche ?

Le meilleur runTREC2022monoT5atteint0,6125, notreE0,479065. Ne pas calculer un pourcentage de retard assimilé à une différence de qualité clinique : les systèmes, prétraitements et entraînements diffèrent et nous n’avons pas réexécuté ce run dans notre protocole. Notre système est plus bas sur ce repère numérique. TrialGPTrapporte environ0,73dansun corpusréduit ; on ne met pas ces nombres sur un graphique compétitif. Les résultats sont cohérents avec l’intérêt des systèmes à étages, tout en rappelant l’avertissement dePradeep : ajouter un reranker ne garantit pas chaque métrique. BGE est maintenant mesuré : aucun écart nDCG Eos−BGE ne passe Holm, malgré de meilleures moyennes Eos.

## 24. Que se passe-t-il si la description contient des fautes ?

Le bruit touche seulement les requêtes, pas le corpus. Les taux sont des mots modifiés ; les chiffres d’âge ne sont pas perturbés directement. Les règles sont réappliquées au texte bruité. Ce test est exploratoire, non une simulation clinique validée. Pas de comparaison directe de sensibilitéBcontreC : on ne dit pasCplusrobuste. TroisICdevariation B/Cexcluentzéro ; lesautresincluentzéro. Seed20261117, un tirage imbriqué, détailsdansrapport.

## 25. Des ressources locales : un objectif, puis des mesures.

La motivation pour le contexte africain tient au coût, à la connectivité et à la maîtrise des ressources. L’étude n’est pas un déploiement hospitalier. Eos a traité7340paires uniques pour12500positions de candidats partagées entreB/C. La durée totale5507,75secondes exclut le chargement et lepréflight, inclut les sauvegardes. Pas de picVRAMcompletdocumenté. On ne généralise pas les éventuels chiffres marketing de modèle à notre implémentation ni à uneRTX3050.

## 26. Un autre modèle permet-il de faire aussi bien ?

BGE-reranker-v2-m3 est un modèle de reclassement de BAAI. D′ remplace Eos sur B ; E′ le remplace sur C. Ses sorties sont des logits, pas des probabilités. E−E′ nDCG pHolm1en2021 et0,709en2022 : pas d’équivalence ni supériorité générale démontrée. E−E′ R@20concluant les deux années, P@20etR@10en2022. D−D′ R@5etR@10concluants en2022. Calcul BGE8,34min contre Eos91,80min avec sauvegardes, horschargement/préflight, précisions/runtimesdifférents. Le français,laRTX3050etIU X-ray ne sont pas validés.

## 27. Des mots au sens. Du sens aux critères. Des résultats aux preuves.

Récapituler : les mots sont notre référence, le sens retrouve des formulations proches, les critères explicites et le modèle de décision jouent des rôles distincts. Le sémantique dépasse notreBM25. EosamélioreP/Rà20sans conclusion générale ennDCG@10. La contribution est l’évaluation transparente d’une combinaison accessible. Pas de diagnostic ni inclusion automatique. Les deuxslides suivantes sont des annexes facultatives pour discussion, pas la conclusion du récit principal.

## 28. Annexe · Toutes les mesures, sans confondre leurs questions.

Expliquer les métriques secondaires à la demande. Toutes les moyennes sont sur les requêtes de l’année. Les ratios individuels sont moyennés, pas nécessairement le quotient de sommes agrégées. Les valeurs restent des mesures de recherche dans un benchmark, pas des indicateurs de santé ou de décision clinique.

## 29. Annexe · Comment sécuriser les conclusions statistiques ?

La famille99a été fixée avant de voir D/E. Elle est maintenant entièrement observée avec BGE : aucun emplacement réservé ni score imputé. La correction limite les faux positifs parmi plusieurs comparaisons. Non significatif ne prouve ni absence d’effet ni équivalence.

