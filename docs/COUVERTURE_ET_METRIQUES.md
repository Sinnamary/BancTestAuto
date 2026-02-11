# Couverture de code et métriques — analyse et pistes d'amélioration

Document généré à partir des rapports **pytest-cov** (couverture) et **radon** (métriques : MI, CC).  
Pour régénérer les rapports : `python run_coverage.py` puis `python run_metrics.py`.

---

## 1. Synthèse couverture (état actuel : **73 %**)

### 1.1 Fichiers à 0 % de couverture

| Fichier | Raison probable | Piste |
|--------|------------------|--------|
| `core/connection_controller.py` | Protocol (interface) : pas de code exécutable à couvrir | Aucune action ; couvrir via l’implémentation ou des tests d’intégration. |
| `core/connection_controller_impl.py` | Implémentation pilotée par l’UI / matériel | Tests unitaires avec mocks (connexions, états) ou tests d’intégration. |
| `core/equipment_state.py` | Modèle pur (dataclasses) | **Tests unitaires directs** : `EquipmentState`, `BenchConnectionState`, `display_text()`, `get_state`, `set_state`, `is_connected`, `is_any_connected`, `all_kinds`. |

### 1.2 Fichiers très faiblement couverts (&lt; 30 %)

| Fichier | Couverture | Commentaire |
|---------|------------|-------------|
| `core/dos1102_usb_connection.py` | 9 % | Connexion USB / PyUSB ; fortement couplé au matériel. Tester avec mocks (backend USB, `usb.core`) ou laisser à l’intégration. |
| `core/detection/fy6900.py` | 21 % | Détection générateur ; ports série / réponses. Mocker la couche série et les réponses IDN. |
| `core/detection/owon.py` | 22 % | Idem, détection multimètre. |
| `core/detection/rs305p.py` | 20 % | Détection alimentation. Même approche : mocker série / Modbus. |
| `core/bode_measure_source.py` | 43 % | Source de mesures Bode (oscillo, générateur). Tester les chemins principaux avec mocks. |

### 1.3 Fichiers à améliorer (55–75 %)

- `core/dos1102_protocol.py` (55 %) : méthodes de protocole non appelées par les tests actuels.
- `core/serial_connection.py` (57 %) : branches d’erreur, timeouts, `read`/`write` partiels.
- `core/detection/runner.py` (57 %) : scénarios de détection (succès, échec, timeout).
- `core/measurement.py` (65 %) : modes et plages non testés.
- `core/scpi_protocol.py` (67 %) : autres commandes SCPI et branches d’erreur.

### 1.4 Objectifs recommandés

- **Court terme** : viser **75–78 %** en ajoutant les tests pour `equipment_state`, les getters config manquants et quelques branches `app_logger`.
- **Moyen terme** : **80 %+** sur `config`, `core` (hors USB/détection matérielle) en renforçant les tests de protocoles avec mocks.
- **Long terme** : garder la couverture sur les nouveaux modules ; accepter &lt; 50 % pour les parties dépendant du matériel (USB, série réelle) et les couvrir par des tests d’intégration ou manuels si besoin.

---

## 2. Métriques Radon (MI, CC)

### 2.1 Maintenabilité (MI) faible

- **`ui/main_window.py`** : MI ≈ 0,5 — fenêtre principale très grosse (CC_total élevé).  
  **Piste** : extraire des sous‑panneaux ou handlers dans des modules dédiés (ex. onglets, barre d’outils, raccourcis).
- **`ui/connection_bridge.py`** : MI ≈ 26 — forte complexité.  
  **Piste** : découper par responsabilité (connexion multimètre, générateur, alimentation, oscillo).
- **`ui/bode_csv_viewer/dialog.py`** : MI ≈ 26 — dialogue Bode chargé.  
  **Piste** : déplacer logique (calculs, config) dans des classes séparées ; garder le dialogue pour l’affichage et les signaux.
- **`ui/views/meter_view.py`** : MI ≈ 18.  
  **Piste** : extraire mise à jour affichage, gestion des modes, etc., dans des helpers ou sous‑vues.

### 2.2 Complexité cyclomatique (CC) élevée

- **`core/detection/runner.py`** : CC_max 22 — beaucoup de branches (équipements, états).  
  **Piste** : table de stratégies par type d’équipement, ou petits fonctions par cas.
- **`ui/connection_bridge.py`** : CC_max 29.  
  **Piste** : même chose que pour le MI (découpage par équipement / état).
- **`core/dos1102_measurements.py`** : CC_max 21.  
  **Piste** : découper le formatage des réponses (par type de mesure ou par canal).
- **`ui/bode_csv_viewer/csv_loader.py`** : CC_max 22.  
  **Piste** : parser en étapes (header, colonnes, lignes) avec des fonctions plus petites.

### 2.3 Bonnes pratiques et objectifs cibles (plan de refactorisation)

- **MI > 65** et **CC_max ≤ 10** par fonction : cible pour les nouveaux fichiers.
- **SLOC < 250** par fichier lorsque possible (objectif par phase).
- Réduire la taille des fonctions (idéalement < 50 lignes) et le nombre de branches par fonction.
- Voir `docs/REFACTORING_PLAN.md` pour le suivi des phases et les métriques avant/après.

### 2.4 Refactorings réalisés (réduction taille / complexité)

- **core/detection/runner.py** : table de dispatch `_SERIAL_DETECTORS` + `_run_detector_for_kind()` au lieu d’une longue chaîne if/elif → **CC_max 22 → 18**, logique par type d’équipement centralisée.
- **core/dos1102_measurements.py** : extraction de `_raw_to_text`, `_format_json_dict`, `_format_key_value_pairs`, `_format_long_comma_text` ; `format_meas_general_response` orchestre → **CC_max 21 → 8**, formateurs réutilisables.
- **ui/bode_csv_viewer/csv_loader.py** : table `_COLUMN_MATCHES` + `_normalize_header_cell` / `_column_name_for_key` au lieu d’un long if/elif dans `BodeCsvColumnMap` → **CC_max 22 → 18**, **CC_tot 67 → 50**.
- **ui/connection_bridge.py** (Phase 2) : `_create_multimeter_connection`, `_create_generator_connection`, `_create_power_supply_connection`, `_create_oscilloscope_connection` ; `_verify_power_supply`, `_verify_oscilloscope` ; `reconnect()` et `_verify_connections()` allégés → **CC_max 29 → 17** (idem maquette).
- **ui/main_window.py** (Phase 3) : `main_window_menus.py`, `main_window_central.py` (build_central_widget) → **SLOC 512 → 439**.
- **ui/bode_csv_viewer/dialog.py** (Phase 4) : `dialog_actions.py` → **SLOC 305 → 252**, **MI 26 → 33**.
- **ui/bode_csv_viewer/plot_widget.py** (Phase 4) : `plot_refresh.py` (refresh_bode_plot) → **SLOC 273 → 241**, **MI 28 → 31**.
- **core/dos1102_usb_connection.py** (Phase 6) : `core/dos1102_usb_backend.py` (get_usb_backend, list_usb_devices, is_usb_timeout_error, is_usb_device_error) ; read/readline utilisent les helpers → **CC_max 18 → 15**, **SLOC 285 → 217** ; **dos1102_usb_backend.py** (73 SLOC, MI=65, CC_max=9).

---

## 3. Actions concrètes déjà réalisées / proposées

1. **Tests ajoutés (objectif 80 %+)**  
   - `tests/test_equipment_state.py` : couverture complète de `core/equipment_state.py`.  
   - `tests/test_config_settings.py` : getters manquants (`get_usb_oscilloscope_config`, `get_serial_power_supply_config`, `get_bode_viewer_config`, `get_config_file_path`), cas de repli de `_resolve_config_path` et retour DEFAULT quand ni défaut ni repli n'existent.  
   - `tests/test_app_logger.py` : `get_latest_log_path` (répertoire absent, aucun log, un ou plusieurs logs) et fallback de `get_current_level_name` (niveau non présent dans `LEVELS`).  
   - **Avec mocks** :  
     - `tests/test_connection_controller_impl.py` : `CallbackConnectionController` (connect_all, disconnect_all, get_state, apply_config, connect/disconnect par kind).  
     - `tests/test_scpi_protocol.py` (étendu) : conf_voltage_dc, conf_current_ac, conf_res/fres/freq/per/cap, conf_temp_rtd/diod/cont, rate_m/rate_l, meas1, func2_none, calc_*, ask_calc_aver_all/ask_average/ask_maximum/ask_minimum, temp_rtd_*, cont_thre, beep_on.  
     - `tests/test_serial_connection.py` (étendu) : in_waiting (fermé/ouvert), open idempotent, close avec exception, write/readline/read avec log_exchanges et callback, read_until, read, update_params (timeout/write_timeout).  
     - `tests/test_measurement.py` (étendu) : set_voltage_dc, set_current_dc/ac, set_resistance, set_resistance_4w, set_frequency/per/capacitance, set_temperature_rtd/diode/continuity, set_auto_range(False), set_math_db/dbm/average, read_secondary_value, reset_stats (normal + exception), get_stats (exceptions sur min/max/avg), set_rtd_type/unit/show, set_continuity_threshold.  
     - `tests/test_filter_test.py` (étendu) : on_stabilization_started/ended, f_min zero (decades=1), get_measure_source, set_measure_source_kind quand non switchable.  
     - `tests/test_data_logger.py` : on_point qui lève (exception absorbée).  
   - **Tests supplémentaires** : `dos1102_measurements` (format_meas_general_response : JSON valeur non-dict, texte long avec virgules ; phase_deg_from_delay avec delay/period invalides), `bode_utils` (find_cutoff_3db : premier point sous seuil, g1==g0 ; find_peaks_and_valleys : creux).  
   - **Résultat** : couverture globale **79 %** (755 lignes non couvertes). Pour atteindre 80 % : poursuivre avec des tests mockés sur `dos1102_protocol`, `detection/runner`, ou branches restantes de `serial_connection` / `scpi_protocol`).

2. **Consulter les rapports**  
   - Couverture HTML : `python serve_htmlcov.py` (port 8765).  
   - Métriques HTML : `python run_metrics.py` puis `python serve_metrics.py` (port 8766).

3. **CI**  
   - Ajouter une étape qui lance `run_coverage.py` et exige un seuil minimal (ex. `--cov-fail-under=75`) une fois les nouveaux tests en place.

4. **Exclusions**  
   - Garder `connection_controller.py` (Protocol) hors objectif de couverture si besoin, ou ne pas compter ses lignes dans le total.

---

## 4. Règles pour réduire la taille et décomposer

- **Tables de dispatch** : remplacer les longues chaînes `if kind == A: ... elif kind == B: ...` par un dictionnaire `{ Kind.A: handler_a, ... }` et une fonction qui fait `return handlers.get(kind)(...)`.
- **Formateurs / étapes** : une grosse fonction qui fait « décoder → essai JSON → essai regex → repli » → extraire des fonctions `_étape_1`, `_étape_2` réutilisables et une fonction publique qui les enchaîne.
- **Mapping d’en-têtes / colonnes** : définir une liste de `(motifs, nom_logique)` et une fonction `_match(normalized_key)` au lieu d’un if/elif par colonne.
- **Connexions / ports** : factoriser `open`/`close`/`verify` dans des helpers `_safe_open(conn, label)`, `_safe_close(conn)`, `_verify_xxx(conn, ...)` pour éviter la répétition par équipement.
- **Objectif par fichier** : &lt; 200 SLOC si possible ; &lt; 150 lignes pour un module « métier » ; classes &lt; 80 lignes, méthodes &lt; 30 lignes.

## 5. Commandes utiles

```bash
# Couverture
python run_coverage.py
python serve_htmlcov.py

# Métriques
python run_metrics.py
python serve_metrics.py

# Seuil de couverture (exemple 75 %)
pytest tests -v --cov=config --cov=core --cov=ui.bode_csv_viewer --cov-report=term-missing --cov-fail-under=75
```

(Voir section 2.4 pour les refactorings déjà appliqués.)
