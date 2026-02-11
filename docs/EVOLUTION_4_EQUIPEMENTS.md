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
- **Connexion / déconnexion globale** depuis la barre (connecter/déconnecter les 4).
- **Exception terminal série** : en mode terminal série, déconnecter les 4 équipements et ne garder que la connexion terminal.

Contrainte Phase 1 : modules et classes **réutilisables** (détection, état, contrôleur), **sans modifier l’UI** ; l’UI actuelle et la future s’appuient sur les mêmes classes.

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

### Phase 2 — Détection 4 équipements + dialogue — **À FAIRE**

| Tâche | Statut |
|-------|--------|
| Dialogue de détection pour les 4 équipements (Multimètre, Générateur, Alimentation, Oscilloscope) | À faire |
| Utiliser `run_detection(bench_equipment_kinds(), log_lines)` et afficher `BenchDetectionResult` | À faire |
| Mise à jour config pour les 4 (serial + USB oscillo si applicable) | À faire |
| Remplacer l’ancien dialogue 2 équipements par le nouveau | À faire |

---

### Phase 3 — Connexion / déconnexion globale — **À FAIRE**

| Tâche | Statut |
|-------|--------|
| Barre : 4 pastilles (Multimètre, Générateur, Alimentation, Oscilloscope) | À faire |
| Boutons Connexion globale / Déconnexion globale (ou équivalent) | À faire |
| Brancher `CallbackConnectionController` dans MainWindow (`_reconnect_serial`, construction de `BenchConnectionState`) | À faire |
| Supprimer les connexions dédiées dans les onglets Alimentation et Oscilloscope ; tout passer par le contrôleur / barre | À faire |

---

### Phase 4 — Règles terminal série — **À FAIRE**

| Tâche | Statut |
|-------|--------|
| Lors de l’ouverture du terminal série : déconnecter les 4 équipements, ne garder que la connexion terminal | À faire |
| Règles de cohérence (éviter un port utilisé à la fois par un équipement et le terminal) | À faire |

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
| **`ui/main_window.py`** | Connexion 2 équipements : `_multimeter_conn`, `_generator_conn`, `_scpi`, `_fy6900` ; `_reconnect_serial()`, `_update_connection_status()` (2 pastilles) ; `_on_detect_clicked()`, `_on_detection_result_5()` (détection tuple). Remplacer par `ConnectionController`, `BenchConnectionState`, barre 4 équipements. |
| **`ui/widgets/connection_status.py`** | Classe **ConnectionStatusBar** actuelle : 2 pastilles (multimètre, générateur). Remplacer par 4 pastilles + boutons connexion/déconnexion globale. |

### Tag UI_CHANGES_VIA_MAQUETTE (ne pas modifier l’UI ici)

Fichiers pour lesquels **toute évolution d’interface** doit se faire **dans la maquette** ; ne pas modifier ici sauf pour reporter des changements déjà validés dans la maquette. Tagué par `# UI_CHANGES_VIA_MAQUETTE`.

| Fichier | Règle |
|---------|--------|
| **`ui/main_window.py`** | Évolutions d’interface (barre, menu, onglets) → faire dans la maquette, puis reporter. |
| **`ui/widgets/connection_status.py`** | Nouvelle barre 4 équipements, boutons globaux → concevoir dans la maquette. |
| **`ui/dialogs/serial_config_dialog.py`** | Évolution vers 4 équipements (onglets ou formulaire) → faire dans la maquette. |

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
