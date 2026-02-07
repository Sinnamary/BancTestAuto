# Audit documentation / code — Banc de test automatique

**Date :** 7 février 2026 (mise à jour écarts)  
**Objectif :** Synthèse de la vérification documentation ↔ code et des redondances.

---

## 1. Correspondance documentation ↔ code

### 1.1 Ce qui est aligné

| Élément | Statut |
|--------|--------|
| **README** : structure projet, `main.py`, `clean.py`, `maquette/`, `core/`, `config/`, `ui/`, `resources/themes/` | Conforme au code |
| **Raccourci F1** (Aide) | Implémenté dans `ui/main_window.py` + `help_dialog.py` ; documenté dans README et AIDE.md |
| **core/** : serial_connection, scpi_*, measurement, fy6900_*, data_logger, filter_test, filter_sweep, bode_calc, device_detection, app_logger, serial_exchange_logger | Tous présents |
| **main.py** : chargement config, thème `display.theme`, MainWindow, theme_loader | Conforme au README |
| **AIDE.md** | Contenu cohérent avec les menus et l’usage réel |

### 1.2 Écarts documentés (structure cible vs actuelle)

Ces écarts ne sont pas des erreurs : la doc décrit parfois une **structure cible** (décomposition maximale) alors que le code a choisi une structure plus regroupée.

| Document | Description | Réalité actuelle |
|----------|-------------|------------------|
| **CAHIER_DES_CHARGES § 2.2** | Arborescence avec `filter_config_panel.py` et `filter_results_table.py` dans `ui/views/` | Ces panneaux sont **intégrés dans** `filter_test_view.py` (pas de fichiers séparés). |
| **CAHIER_DES_CHARGES & DEVELOPPEMENT** | Widgets cible : `measurement_display.py`, `mode_button.py`, `mode_bar.py`, `range_selector.py`, `rate_selector.py`, `math_panel.py`, `history_table.py`, `secondary_display.py`, `advanced_params.py` dans `ui/widgets/` | **Tous extraits sauf** `mode_button` et `secondary_display` (optionnels / intégrés dans MeasurementDisplay). `ui/widgets/` : connection_status, measurement_display, history_table, mode_bar, range_selector, rate_selector, math_panel, advanced_params. |
| **DEVELOPPEMENT § 3.1** | Liste des fichiers dans `docs/` | Inclus dans § 3.1 et § 3.2 (Niveau 1) : `AIDE.md`, `FIX_VENV.md`, `PLAN_IMPLEMENTATION.md`, `DOC_AUDIT.md`. |
| **DEVELOPPEMENT § 3.1** | Arborescence racine (fichiers à la racine) | Inclus : `main.py`, `clean.py` (aligné README). |
| **README** | « resources/ : Icônes, thèmes » | Seul `resources/themes/` existe ; pas de `resources/icons/` (optionnel, Phase 5 du plan). |
| **DEVELOPPEMENT § 1.3** | Version Python | Corrigé : **Python 3.10+** explicite en § 1.3 (aligné README). |

### 1.3 Règle à retenir

- **Structure cible** (CDC, DEVELOPPEMENT § 3.2) = décomposition maximale souhaitable (petits fichiers, un widget par fichier).
- **Structure actuelle** = nombreux widgets extraits dans `ui/widgets/` (connection_status, measurement_display, history_table, mode_bar, range_selector, rate_selector, math_panel, advanced_params). Les panneaux du banc filtre restent intégrés dans `filter_test_view.py`. `run_maquette.py` a été supprimé ; maquette lancée par `python maquette/main_maquette.py`. Script `clean.py` à la racine pour nettoyage __pycache__ et logs.

---

## 2. Redondances

### 2.1 Maquette vs application principale

| Aspect | Description |
|--------|-------------|
| **Maquette** (`maquette/ui/`) | Copie volontaire de l’interface (main_window, views, dialogs, widgets) avec **données factices**, sans `core/` ni `config/`. |
| **Risque** | Les deux arbres (maquette et `ui/`) peuvent diverger si on modifie l’un sans l’autre. |
| **Recommandation** | Suivre le flux du `maquette/README.md` : valider la maquette puis intégrer (copier/fusionner) vers `ui/` et brancher le `core/`. |

Ce n’est **pas** une redondance à supprimer : la maquette sert au prototypage interface sans matériel.

### 2.2 Au sein de l’application

- **core/** : pas de duplication de logique ; modules distincts (série, SCPI, FY6900, mesure, data_logger, filter_test, device_detection).
- **filter_test** : orchestration uniquement ; appelle les classes d’appareils sans dupliquer leurs commandes.
- **ui/** : vues qui utilisent le core sans répéter les protocoles.

---

## 3. Corrections appliquées lors de l’audit

| Fichier | Modification |
|---------|--------------|
| **docs/AIDE.md** | Ajout du raccourci **F1** (Aide) dans le tableau des raccourcis clavier. |
| **docs/FIX_VENV.md** | Message d’erreur générique (plus de chemin d’un autre projet type OWON). |

---

## 4. Liste de référence — docs/

| Fichier | Rôle |
|---------|------|
| **AIDE.md** | Manuel utilisateur (aide intégrée F1). |
| **BANC_TEST_FILTRE.md** | Spécifications banc filtre, Bode, balayage. |
| **CAHIER_DES_CHARGES.md** | Spécifications complètes, architecture, config. |
| **DEVELOPPEMENT.md** | Environnement, Git, arborescence, rôles des modules. |
| **DOC_AUDIT.md** | Ce document — audit doc/code et redondances. |
| **FIX_VENV.md** | Dépannage venv (erreur launcher). |
| **INTERFACE_PYQT6.md** | Conception interface, maquette, widgets. |
| **PLAN_IMPLEMENTATION.md** | Phases d’implémentation et jalons. |
| **FY6900_communication_protocol.pdf** | Protocole FeelTech. |
| **XDM1000_Digital_Multimeter_Programming_Manual.pdf** | SCPI multimètre OWON. |

---

## 5. Plan de réduction des écarts (s’approcher de la cible)

Pour rapprocher la structure actuelle de la **structure cible** (CDC, DEVELOPPEMENT § 3.2), appliquer les actions ci‑dessous par ordre de priorité. Chaque jalon peut être fait indépendamment.

### 5.1 Niveau 1 — Corrections documentation (rapide, sans impact code) ✅ Appliqué

| Action | Fichier(s) | Détail | Statut |
|--------|------------|--------|--------|
| Compléter la liste des fichiers dans `docs/` | DEVELOPPEMENT.md § 3.1 et § 3.2 | Arborescence complétée : `AIDE.md`, `FIX_VENV.md`, `PLAN_IMPLEMENTATION.md`, `DOC_AUDIT.md`. | ✅ Fait |
| Aligner la version Python | DEVELOPPEMENT.md § 1.3 | Expliciter « Python 3.10+ » (cohérent avec le README). | ✅ Fait |
| Mentionner `theme_loader.py` dans la structure actuelle | DEVELOPPEMENT.md § 3.1 | `ui/theme_loader.py` déjà présent dans le bloc `ui/`. | ✅ Déjà en place |

**Effort :** faible. **Bénéfice :** doc à jour, moins de confusion.

---

### 5.2 Niveau 2 — Extraction de widgets (réutilisabilité, lisibilité)

L’objectif était d’extraire des blocs de `meter_view.py` en widgets dédiés dans `ui/widgets/`. **Réalisé** pour l’essentiel : `meter_view.py` allégé ; seuls SecondaryDisplay (optionnel, inclus dans MeasurementDisplay) et mode_button (optionnel) ne sont pas extraits. Ordre recommandé (impact / réutilisation).

| Priorité | Widget cible | Contenu à extraire de `meter_view.py` | Fichier créé | Réutilisable par | Statut |
|----------|--------------|----------------------------------------|--------------|-------------------|--------|
| 1 | **MeasurementDisplay** | Zone affichage principal (valeur + unité, style LCD) + optionnel secondaire (Hz). | `ui/widgets/measurement_display.py` | meter_view, logging_view | ✅ Fait |
| 2 | **HistoryTable** | Tableau des N dernières mesures + boutons « Effacer », « Exporter CSV ». Signaux/slots pour alimentation et export. | `ui/widgets/history_table.py` | meter_view | ✅ Fait |
| 3 | **ModeBar** | Barre de boutons de mode (V⎓, V~, …) avec `QButtonGroup` ; signal `mode_changed(index)` ou `mode_id`. | `ui/widgets/mode_bar.py` | meter_view | ✅ Fait |
| 4 | **RangeSelector** | Auto / Manuel + `QComboBox` plages ; signaux pour `auto_toggled`, `range_changed`. | `ui/widgets/range_selector.py` | meter_view | ✅ Fait |
| 5 | **RateSelector** | Rapide / Moyenne / Lente (boutons radio ou similaires) ; signal `rate_changed(str)`. | `ui/widgets/rate_selector.py` | meter_view | ✅ Fait |
| 6 | **MathPanel** | Aucun, Rel, dB, dBm, Moyenne + champs (offset, référence Ω, stats). | `ui/widgets/math_panel.py` | meter_view | ✅ Fait |
| 7 | **SecondaryDisplay** | Case « Afficher Hz » + label valeur secondaire. | `ui/widgets/secondary_display.py` | meter_view (ou inclus dans MeasurementDisplay) | Optionnel |
| 8 | **AdvancedParamsPanel** | Panneau repliable : température RTD, continuité (seuil), buzzer. | `ui/widgets/advanced_params.py` | meter_view | ✅ Fait |

**Méthode :** pour chaque widget, créer le fichier, déplacer le code (layout + signaux), exposer une API claire (setters/getters, signaux), puis dans `meter_view.py` instancier le widget et connecter les signaux aux slots existants. Tester après chaque extraction.

**Effort :** moyen à élevé (1–2 h par widget selon la complexité). **Bénéfice :** `meter_view.py` plus court, widgets réutilisables et testables isolément.

---

### 5.3 Niveau 3 — Banc filtre (optionnel)

| Action | Détail |
|--------|--------|
| Extraire **FilterConfigPanel** | Créer `ui/views/filter_config_panel.py` (ou `ui/widgets/`) : groupe « Balayage en fréquence » (voie, f_min, f_max, points, échelle, délai, Ue). `FilterTestView` l’instancie et récupère les valeurs via getters ou signaux. |
| Extraire **FilterResultsTable** | Créer `ui/views/filter_results_table.py` (ou widget) : tableau fréquence / Us / gain lin / gain dB + export CSV. Alimenté par la vue ou le worker. |

**Effort :** moyen. **Bénéfice :** alignement avec la structure cible du CDC ; `filter_test_view.py` allégé.

---

### 5.4 Niveau 4 — Core et ressources (optionnel)

| Action | Détail |
|--------|--------|
| Créer **owon_ranges.py** | Extraire les plages par mode (tension DC/AC, courant, résistance, etc.) depuis `measurement.py` ou `scpi_commands.py` vers `core/owon_ranges.py`. Utilisé par `measurement` et par `range_selector` (widget existant). Voir PLAN_IMPLEMENTATION Phase 5. |
| Créer **resources/icons/** | Ajouter des icônes pour connexion, modes, export, etc. (Phase 5 du plan). |

**Effort :** variable. **Bénéfice :** maintenance des plages centralisée ; interface plus homogène avec icônes.

---

### 5.5 Ordre recommandé et jalons

1. **Niveau 1** : ✅ appliqué (corrections doc + structure actuelle).
2. **Niveau 2** : ✅ appliqué pour MeasurementDisplay, HistoryTable, ModeBar, RangeSelector, RateSelector, MathPanel, AdvancedParams ; SecondaryDisplay et mode_button restent optionnels.
3. **Niveaux 3 et 4** : selon le temps disponible et l’objectif de conformité stricte à la cible.

Après chaque jalon : lancer l’appli, tester les onglets concernés, mettre à jour DOC_AUDIT § 1.2 si la structure a changé.

---

*Document maintenu à jour après chaque audit documentation/code.*
