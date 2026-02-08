# Cahier des charges — Visualisation Bode (Banc filtre)

**Version :** 1.3  
**Date :** 8 février 2026  
**Référence :** Banc de test automatique — Banc filtre

**Documents associés :**
- [Banc de test de filtre](BANC_TEST_FILTRE.md)
- [Cahier des charges principal](CAHIER_DES_CHARGES.md)

---

## 1. Objectifs

Définir les spécifications complètes de la visualisation des courbes de Bode (réponse en fréquence) issues du banc filtre, afin de permettre :

- la **lecture et l'affichage** de fichiers CSV historiques ;
- une **visualisation de qualité** (échelles, quadrillage, lisibilité) ;
- le **lissage** des courbes pour réduire le bruit de mesure ;
- une **recherche gain cible** (ligne horizontale + intersections) pour lire les points de coupure à -3 dB ou tout autre niveau, sur tout type de filtre (passe-bas, coupe-bande, etc.).

---

## 2. Périmètre fonctionnel

### 2.1 Chargement des données

| Exigence | Description | Priorité |
|----------|-------------|----------|
| **Lecture CSV** | Charger un fichier CSV Banc filtre via le menu **Fichier → Ouvrir CSV Banc filtre...** | P0 |
| **Format CSV** | Colonnes attendues : `f_Hz` ; `Us_V` ; `Us_Ue` ; `Gain_dB` (séparateur `;`) | P0 |
| **Colonnes flexibles** | Détection automatique des colonnes par en-tête (noms insensibles à la casse) | P1 |
| **Dossier par défaut** | Ouvrir par défaut dans `datas/csv/` si présent | P1 |

### 2.2 Affichage de la courbe

| Exigence | Description | Priorité |
|----------|-------------|----------|
| **Axe X** | Fréquence (Hz), échelle **logarithmique** | P0 |
| **Axe Y** | Gain en dB ou gain linéaire (Us/Ue), au choix de l'utilisateur | P0 |
| **Courbe principale** | Tracé continu des points (f, gain) | P0 |
| **Échelles visibles** | Libellés des axes clairs, unités affichées (Hz, dB) | P0 |
| **Quadrillage** | Grille de référence pour faciliter la lecture des valeurs | P0 |
| **Fond et couleur courbe** | Choix fond noir/blanc et couleur de la courbe via menus déroulants. **Fond noir par défaut.** | P1 |
| **Réglage des axes** | Possibilité de zoomer, dézoomer, recentrer sur une plage | P0 |

### 2.3 Quadrillage (grille)

| Exigence | Description | Priorité |
|----------|-------------|----------|
| **Quadrillage majeur** | Lignes principales (ex. 10, 100, 1000 Hz ; 0 dB, -20 dB, etc.) | P0 |
| **Quadrillage mineur** | Lignes intermédiaires pour une lecture fine | P1 |
| **Activation/désactivation** | Case à cocher ou option pour afficher/masquer le quadrillage | P1 |
| **Style** | Traits discrets, bonne lisibilité sur fond sombre et clair | P1 |

### 2.4 Échelles

| Exigence | Description | Priorité |
|----------|-------------|----------|
| **Échelle X (fréquence)** | Log10 ; plage adaptée automatiquement aux données (f_min, f_max) | P0 |
| **Échelle Y (gain)** | Linéaire ; plage adaptée avec marge (ex. min - 5 dB, max + 5 dB) | P0 |
| **Plage manuelle** | Saisie de F min, F max (Hz), gain min, gain max ; bouton « Appliquer les limites » pour forcer les bornes des axes | P1 ✓ |
| **Auto-ajustement** | Bouton « Ajuster vue » pour recadrer sur toutes les données | P1 ✓ |
| **Mise en évidence des échelles** | Graduations lisibles, pas de chevauchement avec la courbe | P1 |

### 2.5 Lissage de la courbe

| Exigence | Description | Priorité |
|----------|-------------|----------|
| **Activation du lissage** | Option pour activer/désactiver le lissage | P0 |
| **Algorithme de lissage** | Lissage par moyenne glissante (fenêtre configurable) ou spline | P0 |
| **Paramètre de lissage** | Fenêtre (ex. 3, 5, 7 points) ou degré de spline | P1 |
| **Courbe brute + lissée** | Possibilité d'afficher les deux (brute en gris, lissée en couleur) | P1 |
| **Préservation des extrêmes** | Le lissage ne doit pas déformer significativement la forme (coupure, pic) | P0 |

**Détail technique suggéré :**
- **Moyenne glissante** : fenêtre de 3 à 11 points, centrée
- **Spline cubique** : `scipy.interpolate.UnivariateSpline` avec paramètre de lissage `s` ajustable
- **Alternative** : filtre Savitzky-Golay (scipy.signal.savgol_filter) pour conserver les pics

### 2.6 Ligne de référence et recherche gain cible

| Exigence | Description | Priorité |
|----------|-------------|----------|
| **Recherche gain cible** | Saisie d'un gain (dB), bouton « Rechercher » : ligne horizontale (pointillé) + fréquences d'intersection (lignes verticales + étiquettes fc) | P0 |
| **Intersections** | Affichage des fréquences où la courbe coupe le niveau choisi (ex. -3 dB par défaut) | P0 |
| **Étiquette** | Libellé « -3 dB » affiché à droite de la ligne (référence coupure) | P1 |
| **Axe Y linéaire** | En mode gain linéaire (Us/Ue), la ligne est positionnée à 10^(-3/20) ≈ 0,708 | P0 |
| **Recherche de pics** | Détection des maxima locaux (creux ou pics selon le filtre) | P1 |

**Intérêt de la recherche gain cible :**
- **Un seul outil** pour -3 dB (valeur par défaut) et tout autre gain (ex. -6 dB) : plus flexible et plus intéressant qu'une case dédiée.
- Convient à tous les types de filtres : **passe-bas**, **passe-haut**, **coupe-bande** (plusieurs intersections), etc.
- Les intersections courbe / ligne donnent visuellement les fréquences de coupure au niveau choisi.

### 2.7 Contrôles utilisateur

| Exigence | Description | Priorité |
|----------|-------------|----------|
| **Choix échelle Y** | Boutons radio : Gain linéaire (Us/Ue) / Gain en dB | P0 |
| **Export PNG** | Bouton pour enregistrer le graphique en image | P0 |
| **Zoom** | Molette ou geste pour zoomer/dézoomer | P1 |
| **Pan** | Glisser pour déplacer la vue | P1 |
| **Réinitialiser vue** | Bouton pour revenir à la vue complète | P1 |

---

## 3. Structure des données

### 3.1 Format CSV Banc filtre

```
f_Hz;Us_V;Us_Ue;Gain_dB
10.0;1.020893;1.020893;0.1796045196085701
20.309176209047358;1.017738;1.017738;0.15271980757736583
...
```

- **Séparateur** : `;` (point-virgule)
- **Encodage** : UTF-8
- **En-tête** : obligatoire
- **Valeurs** : notation anglo-saxonne (`.` pour la virgule décimale)

### 3.2 Structure de point Bode (interne)

Le viewer CSV utilise un type équivalent (ex. `BodeCsvPoint`) avec les mêmes champs :

```python
# BodeCsvPoint / équivalent BodePoint
  f_hz: float         # Fréquence en Hz
  us_v: float         # Tension de sortie en V
  gain_linear: float  # Us/Ue
  gain_db: float      # Gain en dB
```

### 3.3 Configuration JSON (fenêtre graphique Bode)

Les options d'affichage de la fenêtre du graphique Bode sont persistées dans le fichier de configuration de l'application (`config.json`) sous la clé **`bode_viewer`**. Cette section est chargée à l'ouverture du graphique et mise à jour en mémoire à la fermeture de la fenêtre ; l'enregistrement dans le fichier s'effectue via **Fichier → Sauvegarder config** (ou **Enregistrer config sous...**).

| Clé | Type | Défaut | Description |
|-----|------|--------|-------------|
| `plot_background_dark` | bool | `true` | `true` = fond noir, `false` = fond blanc |
| `curve_color` | string | `"#e0c040"` | Couleur de la courbe principale (hexadécimal) |
| `grid_visible` | bool | `true` | Afficher le quadrillage majeur |
| `grid_minor_visible` | bool | `false` | Afficher le quadrillage mineur |
| `smooth_window` | int | `0` | Fenêtre de lissage (0 = désactivé, 3, 5, 7, 9 ou 11 points) |
| `show_raw_curve` | bool | `false` | Afficher la courbe brute en plus de la courbe lissée |
| `smooth_savgol` | bool | `false` | `true` = algorithme Savitzky-Golay, `false` = moyenne glissante |
| `y_linear` | bool | `false` | `true` = axe Y en gain linéaire (Us/Ue), `false` = gain en dB |
| `peaks_visible` | bool | `false` | Afficher les marqueurs pics/creux (maxima et minima locaux) |

**Exemple dans `config.json` :**

```json
"bode_viewer": {
  "plot_background_dark": true,
  "curve_color": "#e0c040",
  "grid_visible": true,
  "grid_minor_visible": false,
  "smooth_window": 0,
  "show_raw_curve": false,
  "smooth_savgol": false,
  "y_linear": false,
  "peaks_visible": false
}
```

---

## 4. Interface utilisateur

### 4.1 Menu Fichier

- **Ouvrir CSV Banc filtre...** : ouvre une boîte de dialogue de sélection de fichier, charge le CSV et affiche la fenêtre de graphique Bode. Les options d'affichage de cette fenêtre sont initialisées depuis la section **`bode_viewer`** de la configuration (voir § 3.3).
- **Sauvegarder config** / **Enregistrer config sous...** : enregistre la configuration applicative dans un fichier JSON. Inclut la section **`bode_viewer`** si la fenêtre graphique Bode a été ouverte et fermée au moins une fois (les options courantes sont alors mises à jour en mémoire à la fermeture du graphique).

### 4.2 Fenêtre graphique Bode

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Graphique Bode — bancfiltre_2026-02-08_16-06-36.csv                    │
├─────────────────────────────────────────────────────────────────────────┤
│  [Ordonnée]  ○ Gain linéaire (Us/Ue)  ● Gain en dB                      │
│  [Affichage]  Fond [Noir▼]  Couleur [Jaune▼]  ☑ Quadrillage  ☑ Mineur  ☑ Lissage  Fenêtre [5▼] Algo [Moyenne glissante▼]  ☑ Courbe brute+lissée  ☑ Pics/creux  │
│  [Recherche gain cible]  Gain (dB) [-3]  [Rechercher]  → f = … (résultat) │
│  [Échelles / Zoom]  F min  F max  Gain min  Gain max  [Appliquer les limites]  ☐ Zoom sur zone (glisser) │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   0 dB ─────────────────────────────────────────────────────────────    │
│         ╲                                                               │
│  -3 dB  - - - - (ligne gain cible, cyan, si « Rechercher » activé)       │
│           ╲____     fc = … (marqueurs verticaux aux intersections)       │
│  -20 dB         ╲_____                                                  │
│         |----|----|----|----|----|----|----|----|----|----|              │
│        10   100  1k  10k  100k  (f en Hz, échelle log)                  │
├─────────────────────────────────────────────────────────────────────────┤
│  fc = …  |  G_max = … dB  |  N = … points                               │
│  [Ajuster vue]  [Exporter en PNG]  [Exporter les points CSV]  [Fermer]   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Ligne de référence et recherche de gain (dont -3 dB)

| Élément | Description |
|--------|-------------|
| **Recherche gain cible** | Saisie d’un gain (dB), bouton « Rechercher » : affiche une **ligne horizontale** (couleur cyan, pointillé) à ce niveau et les **fréquences d’intersection** (lignes verticales + étiquettes). Par défaut -3 dB pour retrouver le comportement « ligne à -3 dB ». |
| **Position** | Gain = valeur saisie (axe Y en dB). En mode gain linéaire (Us/Ue), la ligne est tracée à la position 10^(gain_dB/20) sur l’axe (ex. -3 dB → ≈ 0,708) ; les intersections correspondent au même niveau. |
| **Étiquette** | Libellé du gain cible (ex. « -3.0 dB ») à droite de la ligne. |
| **Panneau d’infos** | Sous le graphique : fc (-3 dB), G_max, N points (calculés automatiquement). |

---

## 5. Contraintes techniques

| Contrainte | Description |
|------------|-------------|
| **Framework graphique** | pyqtgraph (déjà utilisé dans BodePlotWidget) |
| **Compatibilité** | PyQt6, Python 3.10+ |
| **Performances** | Gestion fluide de courbes jusqu’à ~10 000 points |
| **Thème / options par défaut** | À l'ouverture, les options du graphique Bode sont lues depuis la section **`bode_viewer`** de la config JSON (§ 3.3). Valeurs par défaut : fond noir, courbe jaune. |
| **Axe X logarithmique** | En mode log, la ViewBox pyqtgraph attend la plage en **log10(Hz)** (exposants), pas en Hz. L’implémentation convertit les bornes F min / F max (Hz) en log10 avant d’appliquer la plage, et interprète la plage renvoyée par la vue en Hz pour les champs F min / F max, afin que « Appliquer les limites » et « Ajuster vue » affichent une échelle de fréquences correcte (0,1 ; 1 ; 10 ; 100 ; … Hz). |
| **Config fenêtre Bode** | Les options d'affichage sont stockées dans `config.json` sous la clé **`bode_viewer`**. À la fermeture du graphique (Fermer ou croix), les options courantes sont écrites dans la config en mémoire ; l'enregistrement dans le fichier se fait via **Fichier → Sauvegarder config** (voir § 3.3). |

## 6. Plan de mise en œuvre

| Phase | Contenu | Priorité |
|-------|---------|----------|
| **Phase 1** | Menu Ouvrir CSV + chargement + affichage courbe (déjà implémenté) | P0 ✓ |
| **Phase 2** | Quadrillage visible, échelles lisibles, export PNG | P0 |
| **Phase 3** | Lissage de la courbe (moyenne glissante ou spline) | P0 |
| **Phase 4** | Ligne de référence (ex. -3 dB) : via Recherche gain cible (ligne + intersections) | P0 ✓ |
| **Phase 5** | Plage manuelle des axes (F min, F max, gain min/max), bouton Appliquer les limites, bouton Ajuster vue | P1 ✓ |
| **Phase 6** | Détection pics/creux, marqueurs cliquables | P1 |
| **Phase 7** | Recherche gain cible (tout niveau), export points | P2 |

---

## 7. Glossaire

| Terme | Définition |
|-------|------------|
| **Courbe de Bode** | Graphique gain (dB) vs fréquence (Hz), axe X en échelle log |
| **Fréquence de coupure** | Fréquence à laquelle le gain chute de 3 dB par rapport au gain en bande passante ; repérée par l’intersection de la courbe avec la ligne horizontale à -3 dB |
| **Lissage** | Réduction du bruit de mesure par algorithme (moyenne glissante, spline, Savitzky-Golay) |
| **Quadrillage** | Grille de lignes de référence pour faciliter la lecture des valeurs |

---

*Document préparé pour la spécification de la visualisation Bode du Banc de test automatique.*

---

## 8. Analyse de conformité et pistes d’amélioration (étude de la courbe)

*Révision : 8 février 2026 (v1.3 — conformité 100 %, config JSON bode_viewer documentée)*

### 8.1 Conformité fonctionnelle

| Exigence | Statut |
|----------|--------|
| Menu **Fichier → Ouvrir CSV Banc filtre...** (libellé avec « ... ») | ✓ |
| Lecture CSV, colonnes flexibles, dossier par défaut `datas/csv/` | ✓ |
| Axe X log, axe Y dB ou linéaire, courbe principale, quadrillage, libellés | ✓ |
| Fond noir/blanc, couleur courbe, courbe brute + lissée | ✓ |
| Options du graphique Bode chargées/sauvegardées via `config.json` (section **bode_viewer**) et menu Fichier → Sauvegarder config | ✓ |
| Lissage moyenne glissante (fenêtre 3–11), option activer/désactiver | ✓ |
| Référence -3 dB : **Recherche gain cible** (ligne + intersections) ; panneau fc, G_max, N | ✓ |
| **Axe Y linéaire** : ligne de gain cible positionnée à 10^(gain_dB/20) (ex. -3 dB → ≈ 0,708) | ✓ |
| Plage manuelle (F min/max, gain min/max), Appliquer les limites, Ajuster vue | ✓ |
| Zoom molette, zoom sur zone (glisser), pan | ✓ |
| Export PNG, export points CSV | ✓ |

### 8.2 Améliorations déjà en place (étude de la courbe)

| Piste | Priorité | Statut |
|-------|----------|--------|
| **Marqueurs des fréquences de coupure** | P1 | ✓ Implémenté (lignes verticales + étiquettes fc, fc1/fc2) |
| **Coordonnées au survol** | P1 | ✓ Implémenté (f, G au survol du graphique) |
| **Panneau d’infos** | P1 | ✓ Implémenté (fc, G_max, N points) |
| **Recherche gain cible** | P2 | ✓ Implémenté (gain saisi, bouton Rechercher, fréquences d’intersection) |
| **Détection pics/creux** | P1 (spec Phase 6) | ✓ Implémenté (case « Pics/creux », marqueurs jaune/bleu) |
| **Lissage Savitzky-Golay** | P2 | ✓ Implémenté (option Algo, nécessite scipy) |
| **Quadrillage mineur** | P1 (spec) | ✓ Implémenté (case « Quadrillage mineur ») |
| **Export des points** | P2 | ✓ Implémenté (bouton « Exporter les points CSV ») |

### 8.3 Note sur les algorithmes de lissage

Le cahier des charges mentionne en option le **spline cubique** (UnivariateSpline). L'implémentation actuelle propose la **moyenne glissante** et le **Savitzky-Golay** ; le spline n'est pas proposé. Les deux algorithmes disponibles couvrent les besoins de lissage et de préservation des pics.
