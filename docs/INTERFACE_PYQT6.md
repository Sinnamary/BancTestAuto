# Conception de l’interface PyQt6 — Banc de test automatique

**Version :** 1.0  
**Date :** 7 février 2025  
**Objectif :** Décrire l’interface en détail **avant** la programmation Python, pour valider la maquette et guider l’implémentation.

**Références :** [Cahier des charges §4](CAHIER_DES_CHARGES.md), [Guide de développement §3](DEVELOPPEMENT.md), [Banc de test filtre §9](BANC_TEST_FILTRE.md).

---

## 1. Fenêtre principale

### 1.1 Structure générale

- **Classe PyQt6 :** `QMainWindow`
- **Titre :** « Banc de test automatique »
- **Taille minimale suggérée :** 900×700 px (redimensionnable)
- **Contenu central :** `QTabWidget` (onglets) — pas de zone « unique multimètre » en plein écran ; tout passe par les onglets pour garder une structure claire.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Banc de test automatique                                    [_] [□] [X]        │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Fichier   Édition   Outils   ?                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│  [Barre de connexion : pastille multimètre + label | pastille générateur + label | Paramètres] │
├─────────────────────────────────────────────────────────────────────────────────┤
│  [ Multimètre ]  [ Générateur ]  [ Enregistrement ]  [ Banc filtre ]              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  (Contenu de l’onglet sélectionné)                                               │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│  StatusBar : message (connexion, mesure en cours, erreur, etc.)                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Éléments fixes (hors onglets)

| Élément | Widget PyQt6 | Rôle |
|--------|---------------|------|
| Menu bar | `QMenuBar` | Fichier (Ouvrir config, Sauvegarder config, Enregistrer sous, Quitter), Édition, Outils (**Détecter les équipements** → détection par protocole, mise à jour JSON), Aide |
| Barre de connexion | `QWidget` + `QHBoxLayout` | Voir § 2.1 |
| Onglets | `QTabWidget` | 4 onglets : Multimètre, Générateur, Enregistrement, Banc filtre |
| Barre de statut | `QStatusBar` | Message temporaire (ex. « Connecté COM3 », « Mesure… », « Erreur SCPI ») |

**Menu Outils :** au moins une action **« Détecter les équipements »** : parcourt les ports COM, identifie le multimètre OWON (SCPI *IDN?) et le générateur FY6900 par protocole, affecte le bon port à chaque équipement et met à jour `config.json` (voir cahier des charges § 3.2). Implémentation côté logique : `core/device_detection.py`.

---

## 2. Barre de connexion (commune)

Zone en haut, sous la menu bar, toujours visible.

### 2.1 Maquette

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ● Multimètre: XDM2041 — COM3   |   ● Générateur: FY6900 — COM4   [Param.]     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

- **Deux indicateurs distincts :** une **pastille** (vert = connecté, rouge = déconnecté) par équipement, pour voir clairement le statut du multimètre et du générateur.
- **Séparateur** « | » entre les deux blocs pour distinguer visuellement les deux appareils.
- **Texte multimètre :** `QLabel` « Multimètre: XDM2041 — COM3 » (ou « Non connecté »).
- **Texte générateur :** `QLabel` « Générateur: FY6900 — COM4 » (ou « Non connecté »).
- **Bouton :** `QPushButton` « Paramètres » → ouvre le dialogue de configuration série (multimètre et/ou générateur) + accès à la sauvegarde JSON.

**Widgets PyQt6 :**
- Conteneur : `QWidget` avec `QHBoxLayout`
- **Pastille 1** (`QFrame` / `StatusIndicator`) + `QLabel` multimètre
- Séparateur `QLabel` « | »
- **Pastille 2** + `QLabel` générateur
- `QPushButton` (« Paramètres »)

---

## 3. Onglet « Multimètre »

Vue principale du multimètre OWON : modes, affichage, plages, maths, historique.

### 3.1 Structure en zones (layout)

- Conteneur principal : `QScrollArea` (contenu = `QWidget`) ou `QWidget` avec `QVBoxLayout` pour que tout tienne sans scroll si fenêtre suffisante.
- Chaque zone dans un `QGroupBox` (titre optionnel) ou `QFrame` pour le regroupement visuel.

### 3.2 Zone — Modes de mesure

- **Layout :** `QHBoxLayout` dans un `QGroupBox` (« Modes de mesure »).
- **Widgets :** 12 × `QPushButton` (ou boutons toggle) pour : V⎓, V~, A⎓, A~, Ω, Ω 4W, Hz, s, F, °C, Diode, Continuité.
- **Comportement :** un seul mode actif ; le bouton actif a un style différent (fond, bordure) — utiliser `setCheckable(True)` + `QButtonGroup` pour mutual exclusion.
- **PyQt6 :** `QButtonGroup` (exclusive) + 12 `QPushButton` avec `setCheckable(True)`.

### 3.3 Zone — Affichage principal et secondaire

- **Conteneur :** `QHBoxLayout` : à gauche l’affichage principal, à droite le secondaire.

| Partie | Widget | Détail |
|--------|--------|--------|
| Affichage principal | `QLabel` (ou widget custom) | Grand texte (police LCD-like, ex. 28–36 pt), monospace. Affiche valeur + unité (ex. « 12.345 V »). Fond sombre, texte clair. |
| Secondaire | `QCheckBox` « Afficher Hz » + `QLabel` | Si coché, un second `QLabel` affiche la fréquence (ex. « 1.234 kHz »). |

- **PyQt6 :** `QGroupBox` « Affichage » avec `QHBoxLayout` ; `QLabel` pour la valeur (policy size : MinimumExpanding), `QCheckBox`, `QLabel` pour Hz.

### 3.4 Zone — Plage et vitesse

- **Plage :** `QGroupBox` « Plage »
  - `QRadioButton` « Auto », `QRadioButton` « Manuel »
  - `QComboBox` pour la plage (liste selon le mode : 500 mV, 5 V, 50 V, …). Désactivé si Auto.
- **Vitesse :** `QGroupBox` « Vitesse »
  - 3 `QRadioButton` : « Rapide », « Moyenne », « Lente » (ou `QButtonGroup` + 3 `QPushButton` checkables).

### 3.5 Zone — Fonctions math

- **Conteneur :** `QGroupBox` « Fonctions math »
- **Choix :** 5 `QRadioButton` (ou boutons checkables) : « Aucun », « Rel », « dB », « dBm », « Moyenne »
- **Champs associés :**
  - Rel : `QLineEdit` ou `QDoubleSpinBox` (offset)
  - dB / dBm : `QComboBox` (référence en Ω : 50, 75, 600, …)
  - Moyenne : zone stats (Min, Max, Moyenne, N) en `QLabel` + bouton « Réinitialiser stats » `QPushButton`

### 3.6 Zone — Paramètres avancés (repliable)

- **Widget :** `QGroupBox` avec `QCollapsibleSection` ou `QFrame` dont le contenu est montré/caché par un bouton « Afficher / Masquer » (ou `QToolButton` avec flèche).
- **Contenu :** 
  - Température : `QComboBox` (type RTD), `QComboBox` (unité °C/°F/K), `QComboBox` (affichage TEMP/MEAS/ALL)
  - Continuité : `QDoubleSpinBox` (seuil Ω)
  - Buzzer : `QCheckBox` ON/OFF

### 3.7 Zone — Historique

- **Tableau :** `QTableWidget` (colonnes : #, Valeur, Unité, éventuellement Heure) — N dernières mesures (configurable, ex. 100).
- **Boutons :** `QPushButton` « Exporter CSV », `QPushButton` « Effacer »

### 3.8 Zone — Actions principales

- **Boutons :** `QPushButton` « Mesure » (mesure unique), « Mesure continue » (toggle), « Reset (*RST) », « Exporter CSV » (raccourci export historique).
- Raccourcis : F5 (mesure), Ctrl+M (continue), Ctrl+R (reset), Ctrl+E (export).

### 3.9 Résumé widgets PyQt6 — Onglet Multimètre

| Zone | Widgets principaux |
|------|--------------------|
| Modes | `QButtonGroup`, 12× `QPushButton` (checkable) |
| Affichage | `QLabel` (valeur), `QCheckBox`, `QLabel` (Hz) |
| Plage | `QRadioButton`×2, `QComboBox` |
| Vitesse | `QRadioButton`×3 ou `QButtonGroup` + 3 boutons |
| Math | `QRadioButton`×5, `QDoubleSpinBox`, `QComboBox`, `QLabel`×4, `QPushButton` |
| Avancés | `QGroupBox` repliable, `QComboBox`×3, `QDoubleSpinBox`, `QCheckBox` |
| Historique | `QTableWidget`, `QPushButton`×2 |
| Actions | `QPushButton`×4 |

---

## 4. Onglet « Générateur »

Commande individuelle du FeelTech FY6900 (deux voies). Les paramètres s’appliquent à la **voie sélectionnée**.

### 4.1 Maquette

```
┌─ Générateur FY6900 ────────────────────────────────────────────────────────────┐
│  Connexion: ● COM4   [Paramètres générateur]                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Forme d’onde    [Sinus ▼]    Fréquence (Hz)   [1000.000    ]    [Hz]          │
│  Amplitude (V)   [1.414    ]   Offset (V)       [0.000       ]                   │
│  Sortie          [○ OFF  ● ON]                                                 │
│  [Appliquer]  [Sortie ON]  [Sortie OFF]  (autres commandes selon protocole)     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Widgets PyQt6

| Paramètre | Widget | Remarque |
|-----------|--------|----------|
| **Voie** | `QRadioButton` Voie 1 / Voie 2 | FY6900 a deux voies ; les paramètres ci‑dessous s’appliquent à la voie choisie |
| Forme d’onde | `QComboBox` | Sinus, Triangle, Carré, etc. (WMW) |
| Fréquence | `QDoubleSpinBox` ou `QLineEdit` + validateur | Min/max selon FY6900, unité Hz (conversion vers µHz pour WMF) |
| Amplitude | `QDoubleSpinBox` | Crête en V (WMA) |
| Offset | `QDoubleSpinBox` | WMO |
| Sortie ON/OFF | `QRadioButton` ou 2× `QPushButton` | WMN 1 / 0 |
| Appliquer | `QPushButton` | Envoie les paramètres au générateur |

- **Option :** sections en `QGroupBox` (« Forme et fréquence », « Amplitude et offset », « Sortie »).
- **Barre de statut :** afficher un message après envoi (ex. « Paramètres envoyés »).

---

## 5. Onglet « Enregistrement »

Mode logging longue durée : **enregistrement des mesures du multimètre uniquement** (valeur, unité, mode à chaque intervalle). Config, graphique temps réel, relecture.

### 5.1 Layout global

- **Haut :** **texte explicatif** (ce qui est enregistré : multimètre, pas le générateur) puis panneau de configuration (intervalle, durée, mode mesure, dossier).
- **Milieu :** zone graphique (courbe valeur = f(temps)).
- **Bas :** boutons de contrôle + boutons relecture/comparaison.

### 5.2 Panneau de configuration

| Paramètre | Widget | Contraintes |
|-----------|--------|-------------|
| Intervalle | `QSpinBox` + `QComboBox` (s / min / h) | 1 s à 24 h |
| Durée | `QSpinBox` + `QComboBox` (s/min/h/j) ou « Illimité » | Durée fixe ou ∞ |
| Mode mesure | `QComboBox` | Liste des modes multimètre (comme onglet Multimètre) |
| Dossier | `QLineEdit` + `QPushButton` « Parcourir » | `QFileDialog.getExistingDirectory()` |

### 5.3 Contrôles et graphique

- **Boutons :** `QPushButton` « Démarrer », « Arrêter », « Mettre en pause ».
- **Graphique :** `pyqtgraph.PlotWidget` ou `matplotlib` dans `QWidget` (courbe temps réel ; axe X = temps, axe Y = valeur + unité).
- **Indicateur :** `QLabel` (statut, nombre de points, temps restant si durée définie).

### 5.4 Relecture et comparaison

- **Boutons :** « Ouvrir fichier » (`QFileDialog.getOpenFileName` .csv), « Comparer » (ouvrir un second fichier et superposer), « Exporter image ».
- **Graphique relecture :** même type de widget, chargement des données depuis le CSV.

---

## 6. Onglet « Banc filtre »

Caractérisation Bode : balayage en fréquence, tableau, courbe gain (dB) vs fréquence.

### 6.1 Maquette

```
┌─ Banc de test filtre ───────────────────────────────────────────────────────────┐
│  Voie générateur (○ Voie 1  ● Voie 2)   f_min [10] f_max [100000] Points [50] Échelle [Log ▼]  │
│  Délai stabilisation [200] ms   Ue (RMS) [1.0] V                                │
│  [Démarrer balayage]  [Arrêter]  [Exporter CSV]  [Exporter graphique]           │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Tableau:  f (Hz) | Us (V) | Us/Ue | Gain (dB)                                  │
│  [QTableWidget]                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Graphique Bode (semi-log)   [pyqtgraph ou matplotlib]                          │
│  Barre de progression       [QProgressBar]                                      │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Widgets PyQt6

| Élément | Widget |
|---------|--------|
| Voie générateur | `QRadioButton` Voie 1 / Voie 2 (FY6900 = 2 voies) |
| f_min, f_max | `QDoubleSpinBox` (ou `QSpinBox` si entier) |
| Nombre de points | `QSpinBox` |
| Échelle | `QComboBox` (Linéaire / Logarithmique) |
| Délai stabilisation | `QSpinBox` (ms) |
| Ue | `QDoubleSpinBox` (V RMS) |
| Boutons | `QPushButton` × 4 (Démarrer, Arrêter, Exporter CSV, Exporter graphique) |
| Tableau | `QTableWidget` (colonnes : f, Us, Us/Ue, Gain dB) |
| Graphique | `pyqtgraph.PlotWidget` (axe X log, axe Y linéaire dB) |
| Progression | `QProgressBar` (0–100 % pendant le balayage) |

- **Splitter :** `QSplitter` (vertical) entre tableau et graphique pour redimensionner.

---

## 7. Dialogues

### 7.1 Configuration série (multimètre et/ou générateur)

- **Classe :** `QDialog`
- **Champs :** Port (`QComboBox` rempli avec les ports disponibles), Débit (`QComboBox` : 9600, 19200, …), Timeout lecture, Timeout écriture (`QDoubleSpinBox`), « Logger les échanges » (`QCheckBox`).
- **Boutons :** `QDialogButtonBox` (OK, Annuler). Option : « Tester la connexion » (`QPushButton`).
- **Contexte :** selon l’appel, préremplir pour le multimètre ou le générateur (section `serial_multimeter` ou `serial_generator` du config).

### 7.2 Sauvegarde configuration JSON

- **Classe :** `QDialog` ou réutilisation d’un `QFileDialog` en mode sauvegarde.
- **Contenu :** chemin du fichier (`QLineEdit` + « Parcourir »), option « Enregistrer sous » (autre chemin). Fichier par défaut : `config/config.json`.
- **Boutons :** Enregistrer, Annuler.

### 7.3 Détecter les équipements (menu Outils)

- **Classe :** `QDialog` (`DeviceDetectionDialog`).
- **Rôle :** parcourir les ports COM, identifier le multimètre OWON (SCPI *IDN?) et le générateur FY6900 par protocole, afficher le résultat (port par équipement), permettre de **mettre à jour** `config.json` avec les ports détectés.
- **Contenu :** texte d’explication ; zone résultat (`QTextEdit` ou labels) ; bouton « Lancer la détection » ; barre de progression (pendant le scan) ; bouton « Mettre à jour config.json » ; Fermer.
- **Logique :** déléguée à `core/device_detection.py` (classe `DeviceDetection`).

---

## 8. Thème et apparence

### 8.1 Thème par défaut : sombre

- **Palette :** fond sombre (ex. `#1e1e1e`), texte clair (`#e0e0e0`), accents (boutons, sélection) dans une teinte lisible (ex. bleu/gris clair).
- **Application :** `QApplication.setStyle()` (ex. `Fusion`) + `QPalette` personnalisée ou feuille de style `QSS` dans `resources/themes/dark.qss`.

### 8.2 Polices

- **Affichage mesure (LCD-like) :** police monospace, grande taille (28–36 pt), ex. Consolas, JetBrains Mono, ou « DSEG » pour style LCD.
- **Interface générale :** police système ou une police lisible (Segoe UI, sans-serif) 10–12 pt.

### 8.3 Codes visuels

| Élément | Règle |
|--------|--------|
| Mode actif (multimètre) | Bordure ou fond différent (ex. bleu, ou fond légèrement plus clair) |
| Connexion | Pastille verte / rouge |
| Erreur | `QLabel` ou message dans la barre de statut, couleur d’alerte (rouge/orange) |
| Unités | Toujours affichées à côté des valeurs (V, A, Ω, Hz, etc.) |
| Bouton « en cours » | Désactiver le bouton ou afficher un indicateur (roue dentée / « En cours… ») pendant les requêtes longues |

### 8.4 Options de personnalisation (config.json)

- Taille de police des mesures : petit / moyen / grand (mapping vers 20 / 28 / 36 pt ou équivalent).
- Thème : clair / sombre (chargement du QSS correspondant).

---

## 9. Récapitulatif des widgets PyQt6 par fichier cible

À utiliser comme checklist pour l’implémentation (voir [DEVELOPPEMENT.md §3.2–3.3](DEVELOPPEMENT.md)).

| Fichier UI | Widgets / contenu principaux |
|------------|------------------------------|
| `main_window.py` | `QMainWindow`, `QMenuBar`, `QTabWidget`, `QStatusBar`, barre de connexion |
| `widgets/connection_status.py` | **Deux pastilles** (une par équipement) + labels multimètre/générateur + séparateur + bouton Paramètres |
| `widgets/measurement_display.py` | `QLabel` (valeur + unité), style LCD |
| `widgets/mode_bar.py` | `QButtonGroup` + boutons de mode |
| `widgets/range_selector.py` | Auto/Manuel + `QComboBox` plages |
| `widgets/rate_selector.py` | Rapide / Moyenne / Lente |
| `widgets/math_panel.py` | Rel, dB, dBm, Moyenne + champs associés |
| `widgets/history_table.py` | `QTableWidget` + boutons Export/Effacer |
| `widgets/secondary_display.py` | `QCheckBox` + `QLabel` Hz |
| `widgets/advanced_params.py` | Panneau repliable, temp/continuité/buzzer |
| `views/meter_view.py` | Assemblage des widgets multimètre |
| `views/generator_view.py` | **Choix Voie 1 / Voie 2** + forme, fréquence, amplitude, offset, sortie |
| `views/logging_view.py` | **Texte explicatif** (mesures multimètre uniquement) + config + graphique + contrôles + relecture |
| `views/filter_test_view.py` | **Voie générateur (1/2)** + config balayage + tableau + Bode + progression |
| `views/filter_config_panel.py` | Voie générateur (1/2), f_min, f_max, N, échelle, délai, Ue |
| `views/filter_results_table.py` | `QTableWidget` f | Us | Us/Ue | Gain dB |
| `views/bode_plot_widget.py` | Graphique semi-log (pyqtgraph) |
| `dialogs/serial_config_dialog.py` | Port, débit, timeouts, log |
| `dialogs/save_config_dialog.py` | Chemin fichier, Enregistrer sous |
| `dialogs/device_detection_dialog.py` | Détecter les équipements : résultat, Lancer détection, Mettre à jour config.json |

---

## 10. Ordre de réalisation suggéré (interface seule)

1. **Fenêtre vide** : `QMainWindow`, menu bar (dont Outils → Détecter les équipements), barre de statut, `QTabWidget` avec 4 onglets vides.
2. **Barre de connexion** : **deux pastilles** (multimètre + générateur) + labels + séparateur + bouton Paramètres (sans logique série).
3. **Onglet Multimètre** : zones une par une (modes → affichage → plage/vitesse → math → avancés → historique → boutons).
4. **Dialogues** : configuration série, sauvegarde JSON, **Détecter les équipements** (squelette).
5. **Onglet Générateur** : **choix Voie 1 / Voie 2** + formulaire complet.
6. **Onglet Enregistrement** : **texte explicatif** (multimètre uniquement) + config + zone graphique (données factices) + boutons.
7. **Onglet Banc filtre** : **voie générateur (1/2)** + config + tableau vide + graphique vide + barre de progression.
8. **Thème et polices** : QSS sombre, police LCD pour l’affichage mesure.

Une fois cette maquette validée (et ce document mis à jour si besoin), la programmation Python pourra brancher les signaux/slots et la logique métier (core/) sur ces vues.

---

## 11. Répertoire maquette (définir puis intégrer)

Pour **définir uniquement l’interface** et la valider avant de coder la logique métier, le projet dispose d’un répertoire **`maquette/`** :

1. **Contenu :** interface PyQt6 seule (fenêtre, onglets, barre de connexion, vues, dialogues), avec **données factices** — aucun appel à `core/` ni à `config/`.
2. **Lancement :** depuis la racine du projet, avec le même environnement que le logiciel :
   ```bash
   python maquette/main_maquette.py
   ```
3. **Validation :** on ajuste la disposition, les libellés et le thème dans la maquette jusqu’à validation.
4. **Intégration :** une fois validée, le code de `maquette/ui/` est **copié ou déplacé** vers `BancTestAuto/ui/` ; il ne reste qu’à connecter les signaux aux classes du `core/` et au chargement/sauvegarde de la configuration.

L’arborescence sous `maquette/ui/` **reproduit** celle prévue pour le projet (`main_window.py`, `widgets/`, `views/`, `dialogs/`), afin que l’intégration soit un simple branchement sur la couche métier.

Voir **[maquette/README.md](../maquette/README.md)** pour le détail du workflow et la structure du répertoire maquette.
