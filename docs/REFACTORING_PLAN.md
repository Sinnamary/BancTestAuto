# Plan de refactorisation par étapes

Objectif : améliorer les métriques Radon (MI, CC, SLOC) en décomposant les gros fichiers et les classes complexes, sans casser le comportement.

Référence : `python run_metrics.py` et rapport `tools/code_metrics_report/index.html`. Contexte métriques : `docs/COUVERTURE_ET_METRIQUES.md`.

---

## Commandes de référence

| Action | Commande |
|--------|----------|
| Lancer les tests | `pytest tests/ -v` |
| Métriques (Radon + rapport HTML) | `python run_metrics.py` |
| Consulter le rapport | Ouvrir `tools/code_metrics_report/index.html` ou `python serve_metrics.py` |
| Valider la maquette | `python maquette/main_maquette.py` |
| Sync UI → maquette (avant de modifier la maquette) | `python tools/sync_ui_to_maquette.py` |
| Report maquette → UI | **Manuel** (copie des fichiers modifiés), cf. `.cursor/rules/ui-via-maquette.mdc` |

---

## Phase 0 — Préparation (1 session)

- [x] **0.1** Créer une branche dédiée au refactoring (ex. `refactor/metrics`).
- [ ] **0.2** Lancer les tests et les métriques : `pytest tests/ -v` puis `python run_metrics.py` ; noter les valeurs de référence (MI, CC_max, SLOC) dans une baseline (ex. section *Baseline Phase 0* en fin de document ou `docs/BASELINE_METRICS.md`).
- [ ] **0.3** S’assurer que la suite de tests passe à 100 % avant toute modification.

**Livrable :** baseline métriques consignée + tests verts.

*Conseil :* committer après chaque phase (ou sous-étape majeure) pour pouvoir revenir en arrière proprement.

---

## Phase 1 — Tests Bode CSV viewer (faible risque, fort impact métriques)

Fichier : `tests/test_bode_csv_viewer.py` (MI=0, CC_tot=401, 845 SLOC).  
Le fichier contient déjà des classes de test bien délimitées ; on le scinde en plusieurs modules.

- [x] **1.1** Créer le sous-dossier `tests/bode_csv_viewer/` (ou `tests/ui/bode_csv_viewer/` si tu préfères regrouper par package).
- [x] **1.2** Découper par thème (un fichier = un sous-module du viewer) :
  - `test_model.py` — `TestBodeCsvPoint`, `TestBodeCsvDataset`
  - `test_view_state.py` — `TestBodeViewOptions`
  - `test_formatters.py` — `TestFormatFreqHz`
  - `test_csv_loader.py` — `TestBodeCsvColumnMap`, `TestBodeCsvFileLoader`
  - `test_cutoff.py` — `TestCutoffResult`, `TestCutoff3DbFinder`
  - `test_smoothing.py` — `TestMovingAverageSmoother`, `TestSmoothSavgol`
  - `test_plot_range.py` — `TestComputeDataRange`, `TestApplyAndReadViewRange`
  - `test_plot_style.py` — `TestFormatHoverText`, `TestBodeCurveDrawer`, `TestPlotStyle`
  - `test_plot_widget.py` — `TestBodeCsvPlotWidget`, `TestBodePeaksOverlay`, `TestZoomModeController`, `TestPhaseOverlay`
  - `test_dialog.py` — `TestOpenViewer`, `TestPanelBuilders`, `TestBodeCsvViewerDialog`
- [x] **1.3** Ajouter `tests/bode_csv_viewer/__init__.py` (vide ou réexport si besoin). Si des fixtures sont propres au viewer, les regrouper dans `tests/bode_csv_viewer/conftest.py`.
- [x] **1.4** Supprimer l’ancien `tests/test_bode_csv_viewer.py`, lancer `pytest tests/ -v` puis `pytest tests/bode_csv_viewer/ -v` pour valider la découverte et les tests.
- [x] **1.5** Relancer `python run_metrics.py` et vérifier que les nouveaux fichiers ont un MI et un CC acceptables.

**Livrable :** tests Bode CSV viewer répartis en ~10 fichiers plus petits, métriques améliorées sur ce périmètre.

---

## Phase 2 — Connection bridge (réduction de la complexité)

Fichiers : `ui/connection_bridge.py` et `maquette/ui/connection_bridge.py` (MI≈28, CC_max=29, ~283 SLOC).  
Objectif : extraire la logique de création/vérification des connexions pour diminuer le CC.

- [x] **2.1** Travailler dans **maquette** en priorité (règle projet : évolutions UI via maquette). Au besoin, synchroniser d'abord avec `python tools/sync_ui_to_maquette.py`, puis modifier `maquette/ui/connection_bridge.py`.
- [x] **2.2** Extraire la construction des connexions dans des fonctions ou une petite classe dédiée, par type d’équipement :
  - ex. `_create_multimeter_connection(config)`, `_create_generator_connection(config)`, `_create_power_supply_connection(config)`, `_create_oscilloscope_connection(config)`.
- [x] **2.3** Extraire la vérification (IDN, FY6900, etc.) dans des helpers déjà partiellement présents (`_verify_serial_idn`, `_verify_generator_off`) et ajouter si besoin `_verify_power_supply`, `_verify_oscilloscope` pour éviter un gros bloc conditionnel dans une seule méthode.
- [x] **2.4** Garder `MainWindowConnectionBridge` comme orchestrateur fin : il appelle ces créateurs/vérificateurs et conserve l’état. Vérifier que les tests et la maquette passent.
- [x] **2.5** Reporter les changements de `maquette/ui/connection_bridge.py` vers `ui/connection_bridge.py` (copie manuelle, cf. commandes de référence).
- [x] **2.6** Relancer métriques et tests.

**Livrable :** CC_max et CC_tot réduits sur `connection_bridge`, MI augmenté.

---

## Phase 3 — Main window (décomposition de la fenêtre principale)

Fichiers : `ui/main_window.py` et `maquette/ui/main_window.py` (MI=0.5, CC_max=28, 512 SLOC).  
Objectif : alléger la classe en extrayant menus, construction des onglets et handlers.

- [x] **3.1** Travailler dans **maquette** : `maquette/ui/main_window.py`.
- [x] **3.2** Extraire la construction du menu dans un module dédié, ex. `maquette/ui/main_window_menus.py` :
  - fonctions ou builders : `build_file_menu(main_window)`, `build_tools_menu(...)`, `build_config_menu(...)`, `build_help_menu(...)`.
  - la fenêtre principale appelle ces builders dans `_build_menu()`. Réduire le nombre de branches dans une seule méthode.
- [x] **3.3** Extraire la construction du contenu central (barre de connexion + onglets) dans ex. `maquette/ui/main_window_central.py` :
  - une fonction `build_central_widget(main_window)` qui crée le layout, la barre, le séparateur, le `QTabWidget` et les vues. La fenêtre n’a plus qu’à appeler cette fonction dans `_build_central()`.
- [ ] **3.4** (Optionnel) Grouper les handlers “fichier” (config, CSV, log) dans un petit module ex. `main_window_file_actions.py` et les raccourcis dans `main_window_shortcuts.py`, pour réduire encore la taille de `main_window.py`.
- [x] **3.5** Vérifier le comportement dans la maquette (menus, onglets, connexion, raccourcis). Puis reporter vers `ui/main_window.py`.
- [x] **3.6** Métriques et tests.

**Livrable :** `main_window.py` sous ~250–300 SLOC, MI > 20, CC_max < 15.

---

## Phase 4 — Bode CSV viewer (dialog et plot_widget)

**Dépendance :** Phase 1 (tests Bode déjà découpés).  
Fichiers : `*/(ui|maquette)/bode_csv_viewer/dialog.py` (MI≈26, 305 SLOC), `plot_widget.py` (MI≈28, 273 SLOC).

- [x] **4.1** Travailler dans **maquette** : `maquette/ui/bode_csv_viewer/`.
- [x] **4.2** **dialog.py** : s’appuyer sur les modules de panneaux existants (`panel_buttons.py`, `panel_display.py`, `panel_scale.py`, `panel_search.py`, `panel_y_axis.py`) pour déléguer la construction ; éventuellement regrouper les builders dans un module dédié si besoin. Extraire la logique de validation / chargement dans un module `dialog_actions.py` ou l’intégrer au modèle. Garder `dialog.py` comme assemblage et signaux/slots légers.
- [x] **4.3** **plot_widget.py** : extraire les comportements (zoom, sélection, gestion des courbes) dans des classes ou modules dédiés (ex. `plot_behavior.py`, `plot_zoom.py`) pour réduire CC et SLOC du widget principal.
- [x] **4.4** Tests Bode CSV viewer (déjà en plusieurs fichiers après Phase 1) et maquette. Puis report vers `ui/bode_csv_viewer/`.
- [x] **4.5** Métriques.

**Livrable :** dialog et plot_widget plus petits, MI et CC améliorés.

---

## Phase 5 — Vues volumineuses (meter, filter_calculator, filter_test, logging, serial_terminal)

Fichiers avec MI faible ou SLOC élevé :  
`meter_view.py`, `filter_calculator_view.py`, `filter_test_view.py`, `logging_view.py`, `serial_terminal_view.py` (dans `ui/` et `maquette/ui/views/`).

- [ ] **5.1** Pour chaque vue, dans **maquette** :
  - extraire les panneaux ou blocs logiques dans des sous-widgets (ex. `MeterView` → `MeterDisplayPanel`, `MeterControlPanel`),
  - déplacer la logique métier (calculs, formatage) dans des modules `core/` ou des helpers dans un module dédié à la vue (ex. `meter_view_helpers.py`).
- [ ] **5.2** Traiter une vue à la fois : refactor → tests → métriques → report vers `ui/`.
- [ ] **5.3** Ordre suggéré : `meter_view` (le plus gros CC_tot), puis `filter_calculator_view`, `filter_test_view`, `logging_view`, `serial_terminal_view`.

**Livrable :** Chaque vue < 250 SLOC, CC_max < 10, MI amélioré.

---

## Phase 6 — Core (dos1102_usb_connection, autres)

Fichier : `core/dos1102_usb_connection.py` (MI≈39, CC_max=18, 285 SLOC).

- [x] **6.1** Extraire les parties “protocole” ou “commandes” dans des modules dédiés : `core/dos1102_commands.py` et `core/dos1102_protocol.py` existent déjà ; vérifier si une partie de la logique USB peut y être déplacée ou dans un `dos1102_usb_io.py`.
- [x] **6.2** Séparer la machine d’états ou les gros blocs conditionnels en petites fonctions nommées (réduction du CC).
- [x] **6.3** Tests existants et métriques.

**Livrable :** `dos1102_usb_connection.py` avec MI > 50, CC_max < 12. **Résultat :** MI=40.6, CC_max=15, SLOC=217 (CC_max 18→15, SLOC 285→217 ; backend 73 SLOC, MI=65).

---

## Phase 7 — Consolidation et suivi

- [x] **7.1** Relancer `python run_metrics.py` sur toute la codebase et comparer à la baseline (Phase 0).
- [x] **7.2** Mettre à jour ce document avec les métriques avant/après et les leçons apprises (voir section Refactorings réalisés dans `docs/COUVERTURE_ET_METRIQUES.md`).
- [x] **7.3** Compléter `docs/COUVERTURE_ET_METRIQUES.md` avec les refactorings Phases 2–4 et 6 et objectifs cibles (SLOC < 250, CC_max < 10, MI > 50 pour nouveaux modules).
- [ ] **7.4** Fusion de la branche refactoring après revue.

---

## Résumé des priorités

| Phase | Cible principale              | Risque | Impact métriques | Durée estimée |
|-------|-------------------------------|--------|-------------------|----------------|
| 0     | Préparation                   | -      | -                 | 1 session      |
| 1     | test_bode_csv_viewer (split)  | Faible | Élevé             | 1–2 h          |
| 2     | connection_bridge             | Moyen  | Élevé             | 2–3 h          |
| 3     | main_window                   | Moyen  | Très élevé        | 3–4 h          |
| 4     | bode_csv_viewer dialog/plot   | Moyen  | Élevé             | 2–3 h          |
| 5     | Vues (meter, filter, etc.)    | Moyen  | Moyen             | 4–6 h          |
| 6     | core dos1102_usb_connection   | Moyen  | Moyen             | 2–3 h          |
| 7     | Consolidation                 | Faible | -                 | 1 h            |

Règle projet : pour **ui** et **maquette/ui**, faire les évolutions dans la maquette, valider, puis reporter manuellement vers `ui/`. Voir `.cursor/rules/ui-via-maquette.mdc` et `docs/DEVELOPPEMENT.md`.

---

## Critères de succès globaux

- Tous les tests passent (`pytest tests/ -v`).
- Aucune régression fonctionnelle sur l’application et la maquette.
- Métriques Radon améliorées par rapport à la baseline (Phase 0), en particulier :
  - Fichiers ciblés : MI augmenté, CC_max et CC_tot réduits, SLOC < 250 par fichier où applicable.
- Objectifs documentés dans `docs/COUVERTURE_ET_METRIQUES.md`.

---

## Métriques après refactorisation (Phases 1–6)

| Fichier / périmètre | MI | CC_max | CC_tot | SLOC | Note |
|---------------------|-----|--------|--------|------|------|
| tests/bode_csv_viewer/ (10 modules) | — | — | — | — | Phase 1 : split depuis test_bode_csv_viewer.py |
| ui/connection_bridge.py | 21.6 | 17 | 139 | 311 | Phase 2 : CC_max 29→17 |
| ui/main_window.py | 3.0 | 28 | 212 | 439 | Phase 3 : SLOC 512→439 ; menus/central extraits |
| bode_csv_viewer/dialog.py | 33.2 | 11 | 60 | 252 | Phase 4 : dialog_actions.py |
| bode_csv_viewer/plot_widget.py | 30.8 | 12 | 69 | 241 | Phase 4 : plot_refresh.py |
| core/dos1102_usb_connection.py | 40.6 | 15 | 58 | 217 | Phase 6 : dos1102_usb_backend.py (73 SLOC, MI=65) |
| core/dos1102_usb_backend.py | 65.0 | 9 | 20 | 73 | Phase 6 : nouveau module |

---

## Baseline Phase 0 (référence avant refactoring)

| Fichier / périmètre | MI | CC_max | CC_tot | SLOC |
|---------------------|-----|--------|--------|------|
| tests/test_bode_csv_viewer.py | 0 | — | 401 | 845 |
| ui/connection_bridge.py | ≈28 | 29 | — | ≈283 |
| ui/main_window.py | 0.5 | 28 | — | 512 |
| bode_csv_viewer/dialog.py | ≈26 | — | — | 305 |
| bode_csv_viewer/plot_widget.py | ≈28 | — | — | 273 |
| core/dos1102_usb_connection.py | ≈39 | 18 | — | 285 |
