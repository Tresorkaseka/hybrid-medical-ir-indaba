---
name: Filtrer, retrouver, décider — présentation
description: Présentation scientifique hors connexion, silhouettes sur blanc et architecture fonctionnelle.
colors:
  ink: "#171717"
  muted: "#595959"
  paper: "#fff"
  line: "#c8c8c8"
  emphasis: "#f1f1f1"
  bar: "#a4a4a4"
  bar-axis: "#999"
  shadow-word: "#e4e4e4"
  shadow-bar: "#ededed"
typography:
  display:
    fontFamily: "Raleway, Arial, sans-serif"
    fontSize: "64pt"
    fontWeight: 700
    lineHeight: 1.07
    letterSpacing: "-1.5px"
  headline:
    fontFamily: "Raleway, Arial, sans-serif"
    fontSize: "37pt"
    fontWeight: 700
    lineHeight: 1.18
    letterSpacing: "-1.5px"
  title:
    fontFamily: "Raleway, Arial, sans-serif"
    fontSize: "23pt"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.5px"
  body:
    fontFamily: "Lato, Arial, sans-serif"
    fontSize: "22pt"
    lineHeight: 1.4
  evidence:
    fontFamily: "Lato, Arial, sans-serif"
    fontSize: "19pt"
    lineHeight: 1.5
  takeaway:
    fontFamily: "Lato, Arial, sans-serif"
    fontSize: "21pt"
    lineHeight: 1.35
  footnote:
    fontFamily: "Lato, Arial, sans-serif"
    fontSize: "12pt"
    lineHeight: 1.4
  metric:
    fontFamily: "Raleway, Arial, sans-serif"
    fontSize: "45pt"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-2px"
spacing:
  slide-horizontal: "64px"
  slide-top: "48px"
  slide-bottom: "50px"
  paragraph: "16px"
  column-top: "25px"
  rule-gap: "22px"
components:
  slide:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    padding: "48px 64px 50px"
    width: "1280px"
    height: "720px"
  metric-column:
    textColor: "{colors.ink}"
    padding: "20px 0 0"
  evidence-row-highlight:
    backgroundColor: "{colors.emphasis}"
    textColor: "{colors.ink}"
  margin-note:
    textColor: "{colors.ink}"
    padding: "0 0 0 32px"
  chart-bar:
    backgroundColor: "{colors.bar}"
    height: "23px"
  chart-bar-final:
    backgroundColor: "{colors.ink}"
    height: "23px"
---

# Design System: Filtrer, retrouver, décider — présentation

## Overview

**Creative North Star: "Le théâtre des preuves"**

Le théâtre des preuves : une consultation en ombres chinoises accompagne une lecture scientifique sobre. Le fond blanc, les caractères noirs et les silhouettes récurrentes rapprochent les résultats de leur besoin humain sans transformer le classement algorithmique en décision clinique.

Le mode de surface est **Read** : les titres annoncent une conclusion, les tableaux et graphiques portent les preuves, les notes visibles en précisent les limites. La mise en scène de type Experience reste un soutien visuel ; elle ne remplace jamais la lecture des données.

**Key Characteristics:**
- Blanc pur et gris neutres, sans accent chromatique.
- Raleway pour la hiérarchie, Lato pour les explications.
- La même médecin et le même patient comme fil conducteur.
- Architecture par fonctions, résultats assortis de limites.
- Présentation fixe, polices et dépendances locales.

Ce système est propre au dossier `presentation/`. Il décrit les 29 diapositives livrées (27 principales et deux annexes facultatives), prévues pour 20–25 minutes ; il ne remplace pas le système du manuscrit ou du poster.

## Colors

Palette achromatique : l’encre hiérarchise, les gris structurent, le blanc laisse respirer les preuves. Les valeurs normatives figurent dans le frontmatter.

### Primary
- **Encre** : titres, texte principal, règles des colonnes, progression et configuration E du graphique.

### Neutral
- **Papier** : fond intégral des diapositives.
- **Gris de lecture secondaire** : sources, limites et légendes.
- **Trait** : séparateurs de tableaux et de promesses.
- **Emphase** : fond discret de la configuration E dans le tableau d’ablation.
- **Barre et axe** : comparateurs du graphique ; E reçoit l’encre.
- **Ombres de mot et de barre** : profondeur graphique ponctuelle, sans effet de carte flottante.

## Typography

**Display Font:** Raleway, avec Arial puis sans-serif.
**Body Font:** Lato, avec Arial puis sans-serif.

Les fichiers Regular de Lato et Regular/Bold de Raleway sont chargés localement. Les titres utilisent le gras de Raleway, une chasse resserrée et la casse naturelle ; Lato privilégie la lecture des explications et des chiffres.

### Hierarchy
- **Display** : titre initial sur trois lignes.
- **Headline** : conclusions principales, souvent sur deux lignes.
- **Title** : sous-titres des colonnes.
- **Body** : paragraphes explicatifs ; les colonnes denses utilisent le rôle evidence.
- **Takeaway** : synthèse pédagogique séparée par un trait, avec 18px de retrait supérieur et 24px de marge supérieure ; une comparaison bibliographique dense utilise 20pt.
- **Footnote** : réserves, sources et précision du protocole.
- **Metric** : grands nombres ; les valeurs des barres utilisent des chiffres tabulaires.

Variantes observées : phrases fortes en 28pt, verbes de rôles en 35pt, titre final en 41pt, corps de tableau en 19pt et valeurs de barres en 16pt. Les notes orateur portent les explications longues ; elles ne dispensent pas d’afficher une réserve indispensable.

**The Evidence Rule.** Une différence de moyenne reste distincte d’un résultat statistique concluant ; les limites accompagnent le résultat concerné.

## Layout

Une scène fixe 1280 × 720, 29 sections (27 principales et deux annexes), mise à l’échelle par Reveal sans recomposition mobile. Marges constantes définies dans les tokens ; chaque section occupe 720px de haut et masque les débordements. À l’écran, les sections directes de Reveal prêt sont positionnées en absolu afin de préserver ses transitions natives ; dans le support statique et en export PDF, elles redeviennent relatives pour la pagination. Titres en haut, preuves en dessous, limites ancrées en bas. Colonnes souples à deux ou trois unités, écarts observés de 34 à 70px selon la densité. Les tableaux utilisent toute la largeur utile ; l’architecture occupe 1152px au maximum.

Les scènes récurrentes sont positionnées en absolu derrière les titres : largeur générale effective 1050px, droite 25px et bas 95px ; le titre utilise désormais 1030px, et la conclusion 1020px avec droite 20px et bas 60px. Le texte passe au-dessus avec un niveau de superposition explicite. Les exports print et PDF préservent les mêmes marges.

**The Function First Rule.** Le schéma d’architecture expose le parcours et le rôle des composants avant leurs noms de modèles.

## Elevation & Depth

La profondeur vient principalement des silhouettes et de leur contraste sur blanc. Les tableaux et colonnes restent plats et se séparent par des règles. Deux ombres ponctuelles existent dans le code : `5px 6px #e4e4e4` sur les verbes et `3px 4px 0 #ededed` sur les barres. Ce sont des traces de la direction d’ombres explicitement choisie, pas une élévation générale à appliquer aux conteneurs.

**The Same Consultation Rule.** Réutiliser la même illustration de consultation pour ouvrir, rappeler le besoin et conclure.

## Shapes

Géométrie rectiligne et sans coins arrondis déclarés. Règles de 1px dans les tableaux, de 2px au-dessus des colonnes et de 3px au-dessus des colonnes de littérature. La note de marge se distingue par un trait gauche de 2px. L’illustration de consultation apporte la forme humaine ; le diagramme d’architecture conserve une géométrie fonctionnelle.

## Components

### Colonnes de preuve
Colonnes plates avec une règle supérieure ; grand nombre ou sous-titre, puis explication. Les colonnes de métriques ont un espacement supérieur de 20px ; les rôles et paires utilisent 25px. Ni fond de carte, ni élévation interactive.

### Tableaux
Texte aligné à gauche, séparateurs horizontaux et en-têtes secondaires. Cellules avec 13px verticaux et 18px à droite ; l’ablation resserre les espacements verticaux à 10px. La configuration E reçoit le fond d’emphase.

### Graphique de qualité
Deux groupes annuels, huit lignes chacun ; labels et valeurs restent lisibles indépendamment des barres. Pistes de 23px, ligne complète de 38px sur la version BGE ; largeur calculée sur un domaine commun de 0 à 0,5, valeurs françaises arrondies à trois décimales. E est noir et les autres configurations grises. Chaque année apparaît comme fragment au clic, puis les barres se déploient depuis leur origine gauche. La portée statistique reste explicitée sur la diapositive d’incertitude et en annexe ; le graphique seul présente des moyennes.

### Exemples pédagogiques
Les exemples fictifs expliquent le mécanisme avant le nom du modèle ou la métrique : demande de patient, correspondances lexicales et sémantiques, critère d’âge, reclassement, jugements TREC et ordre des résultats. Ils sont identifiés comme fictifs et distincts des résultats mesurés. Les feuilles d’exemple sont délimitées par un trait supérieur de 2px et inférieur de 1px, sans carte en relief. La demande du patient occupe une largeur de 560px.

La démonstration de précision/rappel présente cinq cellules de résultats, espacées de 12px : les résultats éligibles inversent encre et papier, sans ajouter de couleur. Les cellules ont une hauteur minimale de 72px et un texte de 16pt. Les listes de rang restent en 22pt ; la variante nDCG resserre l’interligne à 1,3. Le cas de décision utilise un corps compact de 19pt et une question de 26pt ; les tableaux d’annexe descendent à 17pt. Cette compacité reste locale aux exemples ou annexes.

### Comparaison bibliographique
Le tableau distingue le résultat propre, le repère TREC et le protocole réduit de TrialGPT. Il n’assimile pas des protocoles différents à une compétition contrôlée et ne transforme pas les chiffres de littérature en nouveaux résultats expérimentaux. Texte courant de 18pt, cellules de 15px verticalement, synthèse de 20pt.

### Note de marge et réserve de bas de page
La note latérale utilise un trait et un retrait de 32px. La réserve de bas de page est ancrée à 34px du bas, alignée aux marges du contenu ; aucune limite essentielle ne doit dépendre seulement des notes orateur.

### Architecture fonctionnelle
Image locale représentant contraintes SQL, recherche cosinus exacte et reclassement Eos top 50, avec maintien des rangs suivants. Le texte alternatif décrit le trajet. Les symboles nomment des fonctions et ne sont pas des identités commerciales.

### Navigation de présentation
Contrôles Reveal, progression de 3px et compteur courant/total de 10pt. Navigation par hash, notes orateur locales et transition native slide à vitesse default et fragments au clic. Les fragments fade-up utilisent 320ms et un déplacement de 16px ; barres et arrivée des silhouettes utilisent 650ms, avec la courbe cubic-bezier(.16,1,.3,1). Le mode de mouvement réduit désactive les transitions et animations et suit les changements de préférence sans rechargement. À l’impression, tous les fragments et barres sont visibles, sans transformation. Les contrôles disparaissent à l’impression.

## Do's and Don'ts

### Do:
- **Do** conserver le mode Read et les limites scientifiques visibles.
- **Do** garder les fontes, Reveal et les illustrations dans les assets locaux.
- **Do** conserver le même patient et la même médecin dans les scènes récurrentes.
- **Do** donner aux tableaux, aux barres et aux nombres un rôle de preuve explicite.
- **Do** préserver l’ordre des rangs 51–1000 et le périmètre top 50 dans toute représentation du pipeline.

### Don't:
- **Don't** suggérer une décision clinique automatisée ou une validation clinique.
- **Don't** présenter le GPU local ou l’imagerie comme des résultats mesurés. BGE est mesuré dans le rapport complet du18/11.
- **Don't** utiliser la hauteur des barres comme preuve de significativité.
- **Don't** remplacer les symboles fonctionnels du schéma par des logos de modèles.


Non canonisé : les anciennes règles CSS de petits libellés supérieurs en capitales restent dans la feuille, sans devenir un composant de système. Les libellés actifs de conférence et de métrique utilisent désormais un texte secondaire sans espacement capitalisé. Aucune correction de surface n’est effectuée par cette documentation. Les collisions, débordements et contrastes en projection n’ont pas été vérifiés par rendu dans cette passe.
