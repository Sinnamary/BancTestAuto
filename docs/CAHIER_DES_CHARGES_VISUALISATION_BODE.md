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
- la **recherche et l'affichage de points significatifs** (fréquence de coupure, pics, etc.).

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

### 2.6 Points significatifs

| Exigence | Description | Priorité |
|----------|-------------|----------|
| **Détection automatique** | Recherche de la fréquence de coupure -3 dB (premier point sous gain_ref - 3 dB) | P0 |
| **Fréquence de coupure** | Affichage marqué (ligne verticale ou marqueur) + étiquette (ex. « fc = 1250 Hz ») | P0 |
| **Recherche de pics** | Détection des maxima locaux (creux ou pics selon le filtre) | P1 |
| **Marqueurs cliquables** | Clic sur un point significatif pour afficher (f, gain) dans une infobulle ou panneau | P1 |
| **Recherche personnalisée** | Saisie d’un gain cible (ex. -6 dB) et affichage des fréquences correspondantes | P2 |
| **Export des points** | Bouton pour exporter la liste des points significatifs en CSV ou copier dans le presse-papier | P2 |

**Points significatifs typiques :**
- Fréquence de coupure à -3 dB (filtre passe-bas/haut)
- Bande passante (-3 dB)
- Pics et creux (résonance, anti-résonance)
- Point à 0 dB (fréquence de transition)

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
│  [Affichage]  ☑ Quadrillage  ☑ Lissage [Fenêtre: 5▼]  ☐ Points signif.  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   0 dB ─────────────────────────────────────────────────────────────    │
│         ╲                                                               │
│  -10 dB  ╲                                                              │
│           ╲____                                                         │
│  -20 dB         ╲_____                                                  │
│                        ╲____  ← fc ≈ 1250 Hz (marqueur)                 │
│  -40 dB                    ╲___________                                 │
│         |----|----|----|----|----|----|----|----|----|----|              │
│        10   100  1k  10k  100k  (f en Hz, échelle log)                  │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│  [Ajuster vue]  [Exporter PNG]  [Fermer]                                │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Panneau des points significatifs (optionnel)

| Champ | Description |
|-------|-------------|
| fc (-3 dB) | Fréquence de coupure à -3 dB |
| Bande passante | Plage de fréquence où gain ≥ gain_ref - 3 dB |
| Autres | Selon type de filtre (pic, creux, etc.) |

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
| **Phase 4** | Détection et affichage fc (-3 dB) | P0 |
| **Phase 5** | Plage manuelle des axes, bouton Ajuster vue | P1 |
| **Phase 6** | Détection pics/creux, marqueurs cliquables | P1 |
| **Phase 7** | Recherche personnalisée (gain cible), export points | P2 |

---

## 7. Glossaire

| Terme | Définition |
|-------|------------|
| **Courbe de Bode** | Graphique gain (dB) vs fréquence (Hz), axe X en échelle log |
| **Fréquence de coupure** | Fréquence à laquelle le gain chute de 3 dB par rapport au gain en bande passante |
| **Lissage** | Réduction du bruit de mesure par algorithme (moyenne glissante, spline, Savitzky-Golay) |
| **Quadrillage** | Grille de lignes de référence pour faciliter la lecture des valeurs |

---

*Document préparé pour la spécification de la visualisation Bode du Banc de test automatique.*
