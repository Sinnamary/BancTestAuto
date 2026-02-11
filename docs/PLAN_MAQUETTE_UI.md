# Plan concret : synchroniser la maquette sur l’UI réelle

**Objectif :** Reprendre l’UI actuelle du programme principal dans la maquette (uniquement l’interface, sans logique métier), puis faire les évolutions UI dans la maquette avant de les reporter dans l’application principale.

**Référence :** [EVOLUTION_4_EQUIPEMENTS.md](EVOLUTION_4_EQUIPEMENTS.md) (4 équipements, connexion globale).

---

## Principe

1. **Copier** l’arborescence complète de `ui/` (programme réel) vers `maquette/ui/` en écrasant/complétant les fichiers existants.
2. **Stubber** les dépendances : lorsque cette UI importe `config` ou `core`, la maquette fournit des modules factices (pas de vraie config, pas de ports série) pour que l’interface s’affiche sans erreur.
3. **Lancer** la maquette depuis `maquette/main_maquette.py` avec `sys.path = [maquette_dir]` pour que `import config` et `import core` chargent les stubs, et `import ui` charge `maquette/ui/`.
4. **Ensuite** : faire les évolutions (4 pastilles, connexion globale, etc.) dans la maquette, valider, puis reporter les changements dans `ui/`.

---

## Phase 1 — Créer les stubs

**Option retenue :** `sys.path = [maquette_dir]`. On copie tout `ui/` dans `maquette/ui/` et on crée `maquette/config/` et `maquette/core/` avec des stubs. Ainsi on ne touche pas au programme principal.

### 1.1 Structure des stubs à créer

| Emplacement | Rôle |
|-------------|------|
| `maquette/config/__init__.py` | Vide. |
| `maquette/config/settings.py` | `load_config()` → `{}`, `save_config(config)` → None, `get_serial_multimeter_config(config)`, `get_serial_generator_config(config)`, `get_filter_test_config(config)`, `get_generator_config(config)`, `get_config_file_path()`, `DEFAULT_CONFIG_PATH`. |
| `maquette/core/__init__.py` | Vide. |
| `maquette/core/app_paths.py` | `get_base_path()` → racine du projet (parent de `maquette/`) pour que `resources/themes` soit trouvé. |
| `maquette/core/app_logger.py` | `get_logger(name)`, `set_level(level)`, `get_current_level_name()`, `get_latest_log_path()` (no-op ou factice). |
| `maquette/core/device_detection.py` | `detect_devices()` → `(None, None, None, None, [])`, `update_config_ports(config, ...)` → copie de config, `list_serial_ports()` → `[]`. |
| `maquette/core/serial_connection.py` | Classe `SerialConnection` factice (méthodes no-op). |
| `maquette/core/scpi_protocol.py` | Classe `ScpiProtocol` factice. |
| `maquette/core/measurement.py` | Classe `Measurement` factice, `MODE_IDS` (dict pour les modes). |
| `maquette/core/fy6900_protocol.py` | Classe `Fy6900Protocol` factice. |
| `maquette/core/filter_test.py` | `FilterTest`, `FilterTestConfig`, `BodePoint` factices. |
| `maquette/core/data_logger.py` | Classe `DataLogger` factice. |
| `maquette/core/serial_exchange_logger.py` | Classe ou module factice (ou `None` si import optionnel). |
| `maquette/core/filter_calculator.py` | Symboles utilisés par `filter_calculator_view`. |
| `maquette/core/dos1102_measurements.py` | Symboles utilisés par `oscilloscope/measurement_panel.py`. |

Les stubs peuvent être minimaux : classes vides ou `pass`, fonctions qui retournent `None`, `{}`, `[]`, ou des valeurs par défaut.

### 1.2 Ressources (thèmes)

`get_base_path()` dans le stub doit renvoyer la **racine du projet** (parent de `maquette/`) pour que `resources/themes/dark.qss` et `light.qss` soient chargés.

---

## Phase 2 — Copier l’UI réelle dans la maquette

### 2.1 Arborescence cible sous `maquette/ui/`

Copier récursivement tout le contenu de `ui/` vers `maquette/ui/` (écraser les fichiers existants) :

- `main_window.py`, `theme_loader.py`
- `bode_csv_viewer/` (tous les fichiers)
- `dialogs/` (about_dialog, device_detection_dialog, help_dialog, save_config_dialog, serial_config_dialog, serial_form, view_config_dialog, view_log_dialog)
- `oscilloscope/` (tous les fichiers)
- `views/` (toutes les vues)
- `widgets/` (tous les widgets)
- `workers/` (detection_worker, sweep_worker)

Aucune modification des imports dans les fichiers copiés : ils continuent d’utiliser `from config.settings import ...` et `from core.xxx import ...`, résolus par les stubs.

### 2.2 Point d’entrée maquette

Dans `maquette/main_maquette.py` :

- Garder `sys.path.insert(0, maquette_dir)` pour que `config`, `core` et `ui` soient pris dans la maquette.
- Après création des stubs, appliquer thème et police comme dans `main.py` (lecture depuis la config factice) pour que le rendu soit identique au programme réel (optionnel en Phase 1, recommandé après).

---

## Phase 3 — Ordre d’exécution recommandé

1. **Créer les stubs** (Phase 1) : d’abord `config/settings.py` et `core/app_paths.py`, `core/app_logger.py`, `core/device_detection.py`, puis les autres modules core au fur et à mesure des erreurs d’import au lancement.
2. **Copier l’UI** (Phase 2) : copie complète de `ui/` vers `maquette/ui/`.
3. **Lancer** `python maquette/main_maquette.py` depuis la racine du projet et corriger les imports manquants (ajouter les stubs nécessaires).
4. **Optionnel** : appliquer thème (dark/light) et police dans `main_maquette.py` comme dans `main.py`.

---

## Phase 4 — Après synchronisation

- Faire les évolutions UI (4 équipements, connexion globale, etc.) **dans la maquette**.
- Valider visuellement et fonctionnellement.
- **Reporter** les changements (fichiers modifiés dans `maquette/ui/`) vers `ui/` du programme principal **à la main** (pas de script prévu pour ce sens).

## Script de synchronisation (programme → maquette)

- **`tools/sync_ui_to_maquette.py`** : copie récursivement `ui/` vers `maquette/ui/` (écrase les fichiers existants). À lancer depuis la racine du projet : `python tools/sync_ui_to_maquette.py`. À exécuter après toute modification de l’UI dans le programme principal pour realigner la maquette.

---

## Fichiers UI qui importent config ou core (pour cibler les stubs)

| Fichier | Imports |
|---------|---------|
| `ui/main_window.py` | config.settings, core.device_detection, core.serial_connection, core.scpi_protocol, core.measurement, core.fy6900_protocol, core.filter_test, core.data_logger, core.serial_exchange_logger, core.app_logger, ui.theme_loader, ui.workers |
| `ui/theme_loader.py` | core.app_paths |
| `ui/views/filter_calculator_view.py` | core.app_paths, core.filter_calculator |
| `ui/views/serial_terminal_view.py` | core.app_logger |
| `ui/views/meter_view.py` | core.measurement (MODE_IDS) |
| `ui/oscilloscope/measurement_panel.py` | core.dos1102_measurements |
| `ui/bode_csv_viewer/` (dialog, plot_range, plot_widget) | core.app_logger |

Les dialogues (serial_config_dialog, device_detection_dialog, etc.) importent souvent `config.settings` ou `core.device_detection` ; les stubs `config` et `core` couvrent ces besoins.
