# Cahier des charges — Visualisation Bode (Banc filtre)

**Version :** 1.5  
**Date :** 11 février 2026  
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

### 2.2bis Affichage gain + phase (diagramme Bode complet)

Lorsque le CSV contient la colonne optionnelle **`Phase_deg`** (acquisition oscilloscope), le viewer affiche un **graphique à deux ordonnées** :

| Exigence | Description | Priorité |
|----------|-------------|----------|
| **Axe X partagé** | Fréquence (Hz), échelle **logarithmique** ; identique pour le gain et la phase | P0 |
| **Axe Y gauche** | Gain (dB) ou gain linéaire (Us/Ue) — courbe de gain | P0 |
| **Axe Y droit** | Phase en degrés (°) — courbe de phase | P0 |
| **Deux courbes** | Courbe gain (couleur configurable, ex. jaune) et courbe phase (ex. cyan) sur le **même** graphique, même plage de fréquences | P0 |
| **Visibilité** | Cases à cocher « Gain » et « Phase » dans le panneau Affichage pour n’afficher que le gain, que la phase, ou les deux (visibles uniquement si le CSV contient `Phase_deg`) | P1 ✓ |
| **Synchronisation** | Zoom, pan et plage manuelle (F min/max) s’appliquent à l’axe X commun ; les deux courbes commencent et finissent aux mêmes fréquences | P0 |

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

**Format minimal (acquisition multimètre ou historique) :**

```
f_Hz;Us_V;Us_Ue;Gain_dB
10.0;1.020893;1.020893;0.1796045196085701
20.309176209047358;1.017738;1.017738;0.15271980757736583
...
```

**Format étendu (acquisition oscilloscope) :** colonnes optionnelles **`Ue_V`** et **`Phase_deg`** ajoutées lorsque l’acquisition est faite via l’oscilloscope (Ch1=Ue, Ch2=Us, phase Ch2 vs Ch1) :

```
f_Hz;Us_V;Us_Ue;Gain_dB;Ue_V;Phase_deg
10.0;1.02;1.02;0.18;1.0;-2.1
100.0;0.71;0.71;-3.0;1.0;-45.0
...
```

- **Séparateur** : `;` (point-virgule)
- **Encodage** : UTF-8
- **En-tête** : obligatoire
- **Valeurs** : notation anglo-saxonne (`.` pour la virgule décimale)
- **Colonnes optionnelles** : le viewer détecte les colonnes par en-tête (insensible à la casse) ; si `Ue_V` ou `Phase_deg` sont présents, ils sont chargés pour usage (ex. courbe de Bode phase en Phase 5).

### 3.2 Structure de point Bode (interne)

Le viewer CSV utilise un type équivalent (ex. `BodeCsvPoint`) avec les champs obligatoires et optionnels :

```python
# BodeCsvPoint / équivalent BodePoint
  f_hz: float         # Fréquence en Hz
  us_v: float         # Tension de sortie en V
  gain_linear: float  # Us/Ue
  gain_db: float      # Gain en dB
  ue_v: Optional[float] = None    # Optionnel : tension d'entrée (acquisition oscilloscope)
  phase_deg: Optional[float] = None  # Optionnel : phase en degrés (acquisition oscilloscope)
```

### 3.3 Configuration JSON (fenêtre graphique Bode)

Les options d'affichage de la fenêtre du graphique Bode sont persistées dans le fichier de configuration de l'application (`config.json`) sous la clé **`bode_viewer`**. Cette section est chargée à l'ouverture du graphique et mise à jour en mémoire à la fermeture de la fenêtre ; l'enregistrement dans le fichier s'effectue via **Fichier → Sauvegarder config** (ou **Enregistrer config sous...**). La **police** des libellés et étiquettes du graphique suit la configuration applicative **`display.font_family`** (voir cahier des charges principal).

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

- **Sans phase** (CSV minimal) : un seul axe Y (gain). Courbe gain vs fréquence (log).
- **Avec phase** (CSV contenant `Phase_deg`) : **deux axes Y** — gain à gauche (dB), phase à droite (°) ; **deux courbes** sur le même graphique (même axe X = fréquence log) ; cases à cocher « Gain » et « Phase » dans le panneau Affichage.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Graphique Bode — bancfiltre_2026-02-08_16-06-36.csv                    │
├─────────────────────────────────────────────────────────────────────────┤
│  [Ordonnée]  ○ Gain linéaire (Us/Ue)  ● Gain en dB                      │
│  [Affichage]  Fond [Noir▼]  Couleur [Jaune▼]  ☑ Quadrillage  ☑ Mineur  ☑ Lissage  …  ☑ Gain  ☑ Phase  ☑ Pics/creux  │
│  [Recherche gain cible]  Gain (dB) [-3]  [Rechercher]  → f = … (résultat) │
│  [Échelles / Zoom]  F min  F max  Gain min  Gain max  [Appliquer les limites]  ☐ Zoom sur zone (glisser) │
├─────────────────────────────────────────────────────────────────────────┤
│  Gain (dB)     │                                                    Phase (°) │
│   0 dB ────────╲────────────────────────────────────────────── 0°     │
│  -3 dB  - - - - ╲____  fc = …                                    -45°  │
│  -20 dB         ╲_____                                            -90°  │
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
| **Graphique gain + phase** | Lorsque le CSV contient `Phase_deg`, un second ViewBox (axe Y droit) affiche la courbe phase (°) ; il partage l’axe X avec le ViewBox gain (même plage log10(Hz)) et utilise le **même principe de viewport** : axe X en **log10(Hz)** (mode log activé sur le ViewBox phase), pas en Hz linéaire, afin que les deux courbes soient alignées en fréquence. La plage X du ViewBox phase est recopiée depuis le ViewBox gain (coordonnées log10(Hz)). Cases à cocher Gain / Phase pour afficher l’un, l’autre ou les deux. |
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
| **Courbe de Bode** | Graphique gain (dB) vs fréquence (Hz), axe X en échelle log ; éventuellement **Bode complet** : gain (axe gauche) et phase en ° (axe droit) sur le même graphique, même axe X. |
| **Fréquence de coupure** | Fréquence à laquelle le gain chute de 3 dB par rapport au gain en bande passante ; repérée par l’intersection de la courbe avec la ligne horizontale à -3 dB |
| **Lissage** | Réduction du bruit de mesure par algorithme (moyenne glissante, spline, Savitzky-Golay) |
| **Quadrillage** | Grille de lignes de référence pour faciliter la lecture des valeurs |

---

*Document préparé pour la spécification de la visualisation Bode du Banc de test automatique.*

---

## 8. Analyse de conformité et pistes d’amélioration (étude de la courbe)

*Révision : 11 février 2026 (v1.4 — visualisation gain + phase, deux axes Y, même X)*

### 8.1 Conformité fonctionnelle

| Exigence | Statut |
|----------|--------|
| Menu **Fichier → Ouvrir CSV Banc filtre...** (libellé avec « ... ») | ✓ |
| Lecture CSV, colonnes flexibles, dossier par défaut `datas/csv/` | ✓ |
| Axe X log, axe Y dB ou linéaire, courbe principale, quadrillage, libellés | ✓ |
| **Graphique gain + phase** : si CSV contient `Phase_deg`, axe gauche = gain, axe droit = phase (°), même axe X (fréquence log), cases ☑ Gain / ☑ Phase | ✓ |
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
| **Courbe de Bode phase** | P1 | ✓ Implémenté (axe droit Phase ° si CSV avec Phase_deg ; courbe phase alignée en fréquence avec le gain) |
| **Détection pics/creux** | P1 (spec Phase 6) | ✓ Implémenté (case « Pics/creux », marqueurs jaune/bleu) |
| **Lissage Savitzky-Golay** | P2 | ✓ Implémenté (option Algo, nécessite scipy) |
| **Quadrillage mineur** | P1 (spec) | ✓ Implémenté (case « Quadrillage mineur ») |
| **Export des points** | P2 | ✓ Implémenté (bouton « Exporter les points CSV ») |

### 8.3 Note sur les algorithmes de lissage

Le cahier des charges mentionne en option le **spline cubique** (UnivariateSpline). L'implémentation actuelle propose la **moyenne glissante** et le **Savitzky-Golay** ; le spline n'est pas proposé. Les deux algorithmes disponibles couvrent les besoins de lissage et de préservation des pics.

---

## 9. Notes d’implémentation — Affichage phase et zoom sur zone

*Révision : 11 février 2026*

Lorsque le graphique Bode affiche **gain et phase** (deux axes Y), l’implémentation utilise **deux ViewBox pyqtgraph** superposés : le ViewBox principal (gain, axe gauche) et un ViewBox secondaire pour la phase (axe droit). Leur ordre d’affichage et la réception des événements souris sont pilotés par la **valeur z** (ordre de plan dans la scène Qt) et par le **fond** du ViewBox principal. Les problèmes rencontrés et les solutions sont résumés ci‑dessous.

### 9.1 Conventions Qt sur l’ordre de plan (z)

- En Qt, un **z plus élevé** signifie que l’item est **au‑dessus** : il est dessiné après (donc par‑dessus) et reçoit les clics en premier.
- Le ViewBox principal (gain) a par défaut un z négatif en pyqtgraph (ex. **-100**). Le **PlotItem** (conteneur du graphique) a typiquement un z proche de **0**.

### 9.2 Problème 1 : Zoom sur zone inactif (les clics ne déclenchaient pas le rectangle de zoom)

**Symptôme :** Avec la case « Zoom sur zone (glisser) » cochée, glisser sur le graphique ne dessinait pas le rectangle de zoom.

**Cause :** Le ViewBox phase était initialement à **z = 10**, donc **au‑dessus** du ViewBox principal (z = -100). Les clics arrivaient au ViewBox phase (ou à son rectangle de fond, `QGraphicsRectItem`), pas au ViewBox principal. Le zoom rect est géré par le ViewBox principal ; il ne recevait jamais les événements souris.

**Tentative rejetée :** Transférer les événements souris du viewport vers le ViewBox principal en créant un `QGraphicsSceneMouseEvent` et en appelant `QApplication.sendEvent(main_vb, ev)`. En **PyQt6**, `QGraphicsSceneMouseEvent` **ne peut pas être instancié** par l’application (« cannot be instantiated or sub-classed »), donc cette approche n’est pas utilisable.

**Solution retenue :** En mode « Zoom sur zone » actif, le ViewBox phase est **placé derrière** le ViewBox principal en lui donnant un **z inférieur** à celui du main : `right_vb.setZValue(main_vb.zValue() - 10)`. Ainsi le ViewBox principal est au‑dessus et reçoit les Press/Move/Release ; le zoom rect fonctionne. Pour que la courbe de phase reste visible alors qu’elle est derrière, le **fond du ViewBox principal** est rendu **transparent** (`setBackgroundColor(None)`) tant que le zoom sur zone est actif.

### 9.3 Problème 2 : Courbe de phase invisible au lancement

**Symptôme :** À l’ouverture du graphique (sans cocher « Zoom sur zone »), la courbe de phase n’apparaissait pas ; elle n’apparaissait qu’après avoir coché puis éventuellement décoché « Zoom sur zone ».

**Cause :** Au lancement, `set_rect_zoom_mode(False)` appelait `set_zoom_zone_active(False)`, qui fixait le z du ViewBox phase à **main_z + 10** (ex. -100 + 10 = **-90**). Le ViewBox phase (z = -90) était donc **en dessous** du PlotItem (z ≈ 0). Le PlotItem, dessiné après, recouvrait toute la zone avec le fond du graphique (noir ou blanc), ce qui **masquait** la courbe de phase.

**Solution retenue :** Lorsque le zoom sur zone est **désactivé**, le ViewBox phase doit être **au‑dessus** du PlotItem pour rester visible. On lui attribue un **z fixe élevé** (ex. **10**), et non plus `main_z + 10`. Ainsi, au lancement comme en mode pan, la phase est toujours dessinée au‑dessus et reste visible.

### 9.4 Récapitulatif des réglages z et du fond

| État de la case « Zoom sur zone » | z du ViewBox phase | Fond du ViewBox principal | Résultat |
|-----------------------------------|--------------------|---------------------------|----------|
| **Désactivée** (pan par défaut)   | **10** (fixe)      | Noir ou blanc (opaque)    | Phase visible au‑dessus ; pan / zoom molette sur le graphique. |
| **Activée**                       | **main_z − 10**    | **Transparent** (`None`)  | Phase derrière mais visible par transparence ; ViewBox principal reçoit la souris → zoom rect actif. |

**Fichiers concernés :**  
- `ui/bode_csv_viewer/viewbox_phase.py` : `set_zoom_zone_active(active)` (z du ViewBox phase).  
- `ui/bode_csv_viewer/plot_widget.py` : `set_rect_zoom_mode(enabled)` (appel à `set_zoom_zone_active`, puis `setBackgroundColor(None)` ou `_apply_background_style()` sur le ViewBox principal).
