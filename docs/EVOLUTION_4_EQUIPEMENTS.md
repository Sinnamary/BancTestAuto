# Évolution : 4 équipements, connexion globale, exception terminal série

Document de suivi des phases d’évolution du banc de test (4 équipements en barre, connexion/déconnexion globale, règles terminal série).  
Voir aussi : [CAHIER_DES_CHARGES.md](CAHIER_DES_CHARGES.md), [DEVELOPPEMENT.md](DEVELOPPEMENT.md).

---

## Règles de travail

- **Modifications d’interface (UI)** : les évolutions d’interface (barre 4 équipements, connexion/déconnexion globale, dialogues de détection ou de config, etc.) se font **dans la maquette** ; après validation, reporter les changements vers `ui/` du programme principal. Ne pas modifier directement les fichiers sous `ui/` pour ces évolutions. Voir [PLAN_MAQUETTE_UI.md](PLAN_MAQUETTE_UI.md).
- **Logique métier** : les modifications de logique (détection, état, contrôleur, config) restent dans le programme principal (`core/`, `config/`).
- **Synchronisation UI programme → maquette** : après changement de l’UI dans le programme (correctifs, recopie depuis maquette), lancer `python tools/sync_ui_to_maquette.py` pour realigner la maquette.

---

## Objectif

- **4 équipements** en haut de fenêtre : Multimètre, Générateur, Alimentation, Oscilloscope (pastilles + état).
- **Connexion / déconnexion** depuis la barre : le menu (barre) en haut permet de connecter / déconnecter chaque équipement (ou tous en une fois). La connexion se lance uniquement depuis cette barre.
- **Terminal série** : comme le reste des onglets (Multimètre, Générateur, Alimentation, Oscilloscope), l’onglet **Terminal série** n’a **pas de connexion propre** — il utilise les connexions gérées par la barre. L’utilisateur choisit dans le terminal l’équipement avec lequel dialoguer (sélecteur) ; seuls les équipements déjà connectés sont proposés. Le terminal envoie/reçoit sur la connexion série de l’équipement sélectionné. **Confirmé** : même modèle que les autres onglets (connexion uniquement depuis la barre, l’onglet ne fait qu’utiliser l’équipement connecté).

Contrainte Phase 1 : modules et classes **réutilisables** (détection, état, contrôleur), **sans modifier l’UI** ; l’UI actuelle et la future s’appuient sur les mêmes classes.

---

## Analyse des métriques et prérequis (fichiers / classes)

**Recommandation : oui, il faut mieux gérer les fichiers et les classes avant de continuer l’évolution (Phases 2–5).**  
Les métriques (MI, complexité cyclomatique CC, LOC) montrent des points très sensibles ; modifier la MainWindow ou les vues concernées sans préparation augmente fortement le risque de régressions et de bugs.

### Points critiques (métriques)

| Fichier | MI (rang) | CC max | LOC | Problème |
|---------|-----------|--------|-----|----------|
| **ui/main_window.py** | 0,09 (C) | **217** | 676 | Classe monolithique : ~50 méthodes, toute la logique menu/config/connexion/onglets. Les Phases 2–4 toucheront directement ce fichier. |
| **maquette/ui/main_window.py** | 0,0 (C) | **217** | 669 | Même structure (sync maquette ↔ ui). |
| **ui/views/meter_view.py** | 18,29 (B) | **116** | 406 | Une des 4 vues « équipement » ; complexité élevée, à stabiliser avant d’y brancher le contrôleur. |
| **ui/views/serial_terminal_view.py** | 17,4 (B) | **98** | 468 | Ciblée par la Phase 4 (règles terminal série). |
| **tests/test_bode_csv_viewer.py** | 0,0 (C) | 40 | 971 | Fichier de test très long ; à découper pour garder des tests maintenables. |

Autres fichiers à garder en tête (CC élevé, non bloquant pour 2–4) : `core/dos1102_usb_connection.py` (CC 59), `core/measurement.py` (CC 57), `ui/bode_csv_viewer/dialog.py` (CC 66), `ui/oscilloscope/connection_panel.py` (CC 45).

### Ordre recommandé avant / pendant les phases

1. **MainWindow (ui + maquette)**  
   - **Objectif** : réduire la complexité et isoler la logique qui sera remplacée (Phase 3).  
   - **Actions** : extraire la logique de connexion série actuelle (`_reconnect_serial`, `_open_and_verify_connections`, `_update_connection_status`, `_on_detect_clicked`, `_on_detection_result_5`) dans un module ou une classe dédiée (ex. `MainWindowConnectionBridge` ou équivalent) que MainWindow utilise. Ainsi, au moment du branchement du `ConnectionController`, on remplace ce pont au lieu de toucher des dizaines de méthodes.  
   - Extraire si possible la construction des menus et la gestion config (charger / sauvegarder) dans des helpers ou sous-classes pour alléger la classe principale.  
   - Faire les mêmes extractions dans la maquette, puis resynchroniser.

2. **Vues meter_view et serial_terminal_view**  
   - **Objectif** : faire baisser la complexité cyclomatique (découper en méthodes plus petites, extraire des sous-widgets ou présentateurs si pertinent) pour que les changements Phase 3 (barre 4 équipements) et Phase 4 (terminal série) soient plus sûrs.  
   - Priorité : **serial_terminal_view** (Phase 4), puis **meter_view** (une des 4 pastilles).

3. **connection_status.py**  
   - Sera **remplacée** par la nouvelle barre 4 équipements ; pas de refactoring lourd, au plus petits ajustements si besoin.

4. **tests/test_bode_csv_viewer.py**  
   - Découper en plusieurs modules de tests (par thème : chargement, cutoff, affichage, etc.) pour retrouver un MI/CC acceptable et des tests plus lisibles.

### Synthèse

- **Faire d’abord** : extraction de la logique connexion + allègement de MainWindow (ui et maquette), puis refactoring ciblé de `serial_terminal_view` et `meter_view`.  
- **Ensuite** : enchaîner sereinement les Phases 2 (détection 4 équipements), 3 (barre 4 + contrôleur), 4 (terminal série), 5 (nettoyage et doc).  
- Les métriques (rapport dans `tools/code_metrics_report/`) peuvent être relancées après chaque refactoring pour suivre MI et CC.

---

## État des phases

### Phase 1 — Préparation (modules réutilisables) — **FAIT**

| Élément | Statut | Détail |
|--------|--------|--------|
| `core/equipment.py` | ✓ | `EquipmentKind`, noms d’affichage, clés config |
| `core/equipment_state.py` | ✓ | `EquipmentState`, `BenchConnectionState` (état par équipement, sans UI) |
| `core/detection/` | ✓ | `result`, `owon`, `fy6900`, `rs305p`, `runner`, `config_update` ; `run_detection(kinds)`, `list_serial_ports`, `update_config_from_detection` |
| `core/connection_controller.py` | ✓ | Interface : `get_state`, `connect_all`, `disconnect_all`, `apply_config`, `connect`/`disconnect` par kind |
| `core/connection_controller_impl.py` | ✓ | `CallbackConnectionController` (callbacks pour brancher MainWindow) |
| `core/device_detection.py` | ✓ | Façade : API historique `detect_devices`, `update_config_ports`, `list_serial_ports` → délègue à `core.detection` |
| Tests | ✓ | `tests/test_device_detection.py` adapté (mocks sur `core.detection`) |

**UI** : non modifiée (barre à 2 pastilles, connexions dans les onglets).

---

### Phase 1bis (recommandé) — Refactoring MainWindow et vues — **EN COURS**

| Tâche | Statut |
|-------|--------|
| Extraire la logique connexion (MainWindow) dans un pont/classe dédiée (ui + maquette) | **Fait** : `ui/connection_bridge.py` et `maquette/ui/connection_bridge.py` ; les deux main_window utilisent le bridge. Sync effectuée. |
| Alléger MainWindow : menus, config (helpers ou sous-modules) | À faire |
| Réduire la complexité de `serial_terminal_view` et `meter_view` (ui + maquette) | À faire |
| Découper `tests/test_bode_csv_viewer.py` en modules de tests | À faire |

Voir la section *Analyse des métriques et prérequis* ci-dessus pour le détail.

---

### Phase 2 — Détection 4 équipements + dialogue — **FAIT**

| Tâche | Statut |
|-------|--------|
| Dialogue de détection pour les 4 équipements (Multimètre, Générateur, Alimentation, Oscilloscope) | **Fait** : `DeviceDetectionDialog4` |
| Utiliser `run_detection(bench_equipment_kinds(), log_lines)` et afficher `BenchDetectionResult` | **Fait** : `DetectionWorker4` + affichage par équipement et log |
| Mise à jour config pour les 4 (serial + USB oscillo si applicable) | **Fait** : « Mettre à jour config (en mémoire) » → `update_config_from_detection` |
| Remplacer l’ancien dialogue 2 équipements par le nouveau | **Fait** : menu ouvre `DeviceDetectionDialog4` si dispo ; ancien conservé pour Phase 5 |

---

### Phase 3 — Connexion / déconnexion globale — **FAIT (ui + maquette)**

| Tâche | Statut |
|-------|--------|
| Barre : 4 pastilles (Multimètre, Générateur, Alimentation, Oscilloscope) | **Fait** : `ui/widgets/connection_status.py` et maquette (4 pastilles + Connecter tout / Déconnecter tout). |
| Boutons Connexion globale / Déconnexion globale (ou équivalent) | **Fait** : `ui/main_window.py` (`_on_connect_all` relit config et connecte les 4 équipements, `_on_disconnect_all` = bridge.close + mise à jour pastilles). Barre : **Détecter** (en premier), **Connecter tout**, **Déconnecter tout**. Plus de bouton Charger config ni Paramètres. Séparateur horizontal barre/onglets. |
| Brancher `CallbackConnectionController` dans MainWindow (`_reconnect_serial`, construction de `BenchConnectionState`) | À faire (pour l’instant bridge 2 équipements ; Alimentation et Oscilloscope affichés en « Non connecté »). |
| Supprimer les connexions dédiées dans les onglets Alimentation et Oscilloscope ; tout passer par le contrôleur / barre | **Fait** : Alimentation et Oscilloscope utilisent la connexion du bridge (`set_connection(conn)`), plus de panneau Connexion dans ces onglets. |

---

### Phase 4 — Terminal série (comme les autres onglets) — **FAIT**

**Principe** : l’onglet Terminal série se comporte comme les autres onglets : pas de connexion dédiée, il utilise les connexions gérées par la barre.

| Tâche | Statut |
|-------|--------|
| Barre : connexion/déconnexion des 4 équipements (Phase 3). La connexion ne se fait que depuis la barre. | Voir Phase 3 |
| Dans l’onglet terminal série : sélecteur « Équipement » (Multimètre, Générateur, Alimentation, Oscilloscope) | **Fait** : mode « Équipement (barre) » avec combo Équipement + bouton Actualiser. |
| N’afficher dans le sélecteur que les équipements **actuellement connectés** ; impossible de choisir un équipement non connecté | **Fait** : `get_connected_equipment_for_terminal()` (bridge) ; liste mise à jour après connexion/déconnexion. |
| Quand l’utilisateur choisit un équipement connecté, le terminal envoie/reçoit sur la connexion série de cet équipement (même modèle que les autres onglets) | **Fait** : envoi/réception via la connexion partagée (SerialConnection avec `in_waiting` pour le polling). |
| Règles de cohérence : un port série ne peut être utilisé que par un seul équipement (géré par le contrôleur) | Déjà garanti par le bridge (un port par équipement). |

---

### Phase 5 — Finition, tests, doc — **À FAIRE**

| Tâche | Statut |
|-------|--------|
| Nettoyage des modules obsolètes (voir ci‑dessous) | À faire |
| Tests (détection 4, contrôleur, UI) | À faire |
| Mise à jour doc (AIDE, INTERFACE_PYQT6, etc.) | À faire |

---

## Fichiers et classes tagués (nettoyage et évolution UI)

### Tag REMOVE_AFTER_PHASE5 (suppression après migration)

Les modules suivants sont **marqués pour suppression** une fois la migration terminée (Phase 5). Tagués dans le code par `# REMOVE_AFTER_PHASE5`.

| Module | Raison |
|--------|--------|
| **`core/device_detection.py`** | Façade de compatibilité (API `detect_devices`, `update_config_ports`). Une fois l’UI migrée vers `core.detection` et `ConnectionController`, supprimer et remplacer les appels par `core.detection.run_detection`, `update_config_from_detection`, `list_serial_ports`. |
| **`ui/workers/detection_worker.py`** | Worker actuel : tuple `(m_port, m_baud, g_port, g_baud, log_lines)`. Remplacer par un worker basé sur `run_detection` et `BenchDetectionResult`. Puis supprimer. |
| **`ui/dialogs/device_detection_dialog.py`** | Dialogue actuel « 2 équipements ». Remplacé par un dialogue 4 équipements. Supprimer après mise en place du nouveau. |
| **`maquette/ui/dialogs/device_detection_dialog.py`** | Squelette 2 équipements. Aligner sur le dialogue 4 équipements ou supprimer. |

### Tag OBSOLETE_AFTER_MIGRATION (remplacé après migration)

Code qui **ne sera plus valide** après la migration (Phase 3–5) : à remplacer par le contrôleur, la barre 4 équipements, etc. Tagué dans le code par `# OBSOLETE_AFTER_MIGRATION`.

| Fichier / classe | Élément obsolète |
|------------------|------------------|
| **`ui/main_window.py`** | Délègue déjà au `MainWindowConnectionBridge` (Phase 1bis). À terme : remplacer le bridge par `ConnectionController` + `BenchConnectionState` + barre 4 équipements (Phase 3). Détection tuple (`_on_detection_result_5`) à migrer vers `BenchDetectionResult`. |
| **`ui/widgets/connection_status.py`** | **ConnectionStatusBar** : 4 pastilles (Multimètre, Générateur, Alimentation, Oscilloscope) + Détecter, Connecter tout, Déconnecter tout. |

### Tag UI_CHANGES_VIA_MAQUETTE (ne pas modifier l’UI ici)

Fichiers pour lesquels **toute évolution d’interface** doit se faire **dans la maquette** ; ne pas modifier ici sauf pour reporter des changements déjà validés dans la maquette. Tagué par `# UI_CHANGES_VIA_MAQUETTE`.

| Fichier | Règle |
|---------|--------|
| **`ui/main_window.py`** | Évolutions d’interface (barre, menu, onglets) → faire dans la maquette, puis reporter. |
| **`ui/widgets/connection_status.py`** | Nouvelle barre 4 équipements, boutons globaux → concevoir dans la maquette. |
| **`ui/dialogs/serial_config_dialog.py`** | Plus utilisé par la barre (plus de bouton Paramètres) ; config via config.json. Optionnel pour évolution future. |

**À mettre à jour au nettoyage (sans tag UI)** : `ui/dialogs/serial_form.py` (changer imports `core.device_detection` → `core.detection` au moment du nettoyage).

### Commandes grep

```bash
grep -r "REMOVE_AFTER_PHASE5" --include="*.py" .
grep -r "OBSOLETE_AFTER_MIGRATION" --include="*.py" .
grep -r "UI_CHANGES_VIA_MAQUETTE" --include="*.py" .
```

---

## Référence rapide (Phase 1)

- **Détection** : `core.detection.run_detection(kinds, log_lines)` → `BenchDetectionResult` ; `core.detection.list_serial_ports()` ; `core.detection.update_config_from_detection(config, result)`.
- **État** : `core.equipment_state.BenchConnectionState`, `EquipmentState`.
- **Contrôleur** : `core.connection_controller.ConnectionController`, `core.connection_controller_impl.CallbackConnectionController`.
- **Équipements** : `core.equipment.EquipmentKind`, `bench_equipment_kinds()`.
