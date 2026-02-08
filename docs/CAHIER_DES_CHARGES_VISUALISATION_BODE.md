# Cahier des charges — Visualisation Bode (Banc filtre)

**Version :** 1.0  
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
- une **ligne de référence à -3 dB** (ligne horizontale en pointillé) pour lire les points de coupure sur tout type de filtre (passe-bas, coupe-bande, etc.).

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
| **Fond et couleur courbe** | Choix fond noir/blanc et couleur de la courbe via menus déroulants | P1 |
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
| **Plage manuelle** | Saisie de f_min, f_max, gain_min, gain_max pour forcer les limites | P1 |
| **Auto-ajustement** | Bouton « Ajuster vue » pour recadrer sur toutes les données | P1 |
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

### 2.6 Ligne de référence -3 dB

| Exigence | Description | Priorité |
|----------|-------------|----------|
| **Ligne horizontale -3 dB** | Une ligne de référence au niveau gain = -3 dB, affichée sur toute la largeur du graphique | P0 |
| **Style** | Ligne en **pointillé** (tirets), couleur **rouge**, bien visible sur fond noir et fond blanc | P0 |
| **Activation** | Case à cocher « Ligne à -3 dB » pour afficher/masquer la ligne | P0 |
| **Étiquette** | Libellé « -3 dB » affiché à droite de la ligne (référence coupure) | P1 |
| **Axe Y linéaire** | En mode gain linéaire (Us/Ue), la ligne est positionnée à 10^(-3/20) ≈ 0,708 | P0 |
| **Recherche de pics** | Détection des maxima locaux (creux ou pics selon le filtre) | P1 |
| **Recherche personnalisée** | Saisie d’un gain cible (ex. -6 dB) et affichage des fréquences correspondantes | P2 |

**Intérêt de la ligne horizontale :**
- Convient à tous les types de filtres : **passe-bas**, **passe-haut**, **coupe-bande** (deux intersections à -3 dB), etc.
- Les intersections courbe / ligne donnent visuellement les fréquences de coupure à -3 dB.

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

### 3.2 Structure BodePoint (interne)

```python
BodePoint:
  f_hz: float      # Fréquence en Hz
  us_v: float      # Tension de sortie en V
  gain_linear: float  # Us/Ue
  gain_db: float   # Gain en dB
```

---

## 4. Interface utilisateur

### 4.1 Menu Fichier

- **Ouvrir CSV Banc filtre...** : ouvre une boîte de dialogue de sélection de fichier, charge le CSV et affiche la fenêtre de graphique Bode.

### 4.2 Fenêtre graphique Bode

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Graphique Bode — bancfiltre_2026-02-08_16-06-36.csv                    │
├─────────────────────────────────────────────────────────────────────────┤
│  [Ordonnée]  ○ Gain linéaire (Us/Ue)  ● Gain en dB                      │
│  [Affichage]  Fond [Noir▼]  Couleur courbe [Jaune▼]  ☑ Quadrillage  ☑ Lissage  ☑ Ligne à -3 dB  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   0 dB ─────────────────────────────────────────────────────────────    │
│         ╲                                                               │
│  -10 dB  ╲                                                              │
│  -3 dB  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -   │  ← ligne rouge en pointillé
│           ╲____                                                         │
│  -20 dB         ╲_____                                                  │
│                        ╲____  (intersections = fréquences de coupure)   │
│  -40 dB                    ╲___________                                 │
│         |----|----|----|----|----|----|----|----|----|----|              │
│        10   100  1k  10k  100k  (f en Hz, échelle log)                  │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│  [Ajuster vue]  [Exporter PNG]  [Fermer]                                │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Ligne à -3 dB

| Élément | Description |
|--------|-------------|
| **Ligne** | Horizontale, rouge, en pointillé (bien visible sur fond noir et blanc) |
| **Position** | Gain = -3 dB (axe Y en dB) ou Us/Ue = 10^(-3/20) (axe Y linéaire) |
| **Étiquette** | « -3 dB » affichée à droite de la ligne |
| **Case à cocher** | « Ligne à -3 dB » : affiche ou masque la ligne de référence |

---

## 5. Contraintes techniques

| Contrainte | Description |
|------------|-------------|
| **Framework graphique** | pyqtgraph (déjà utilisé dans BodePlotWidget) |
| **Compatibilité** | PyQt6, Python 3.10+ |
| **Performances** | Gestion fluide de courbes jusqu’à ~10 000 points |
| **Thème** | Respect du thème clair/foncé (display.theme) |

---

## 6. Plan de mise en œuvre

| Phase | Contenu | Priorité |
|-------|---------|----------|
| **Phase 1** | Menu Ouvrir CSV + chargement + affichage courbe (déjà implémenté) | P0 ✓ |
| **Phase 2** | Quadrillage visible, échelles lisibles, export PNG | P0 |
| **Phase 3** | Lissage de la courbe (moyenne glissante ou spline) | P0 |
| **Phase 4** | Ligne horizontale à -3 dB (pointillé rouge, option afficher/masquer) | P0 ✓ |
| **Phase 5** | Plage manuelle des axes, bouton Ajuster vue | P1 |
| **Phase 6** | Détection pics/creux, marqueurs cliquables | P1 |
| **Phase 7** | Recherche personnalisée (gain cible), export points | P2 |

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
