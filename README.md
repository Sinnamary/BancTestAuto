# Banc de test automatique

Application PyQt6 pour **commander individuellement** le multimètre OWON XDM, le générateur FeelTech FY6900 et l'alimentation Rockseed RS305P, avec **toutes les commandes implantées dans le matériel**. Configuration par défaut dans `config/config.json`. Le **banc de test filtre** permet de **caractériser un filtre au format Bode** (réponse en fréquence) avec un **balayage en fréquence modifiable** pour qualifier le filtre.

**Spécifications détaillées :** [Cahier des charges](docs/CAHIER_DES_CHARGES.md).

---

## Prérequis

- **Python 3.10+**
- **PyQt6**, **pyserial**, **pyqtgraph**, **markdown** — voir `requirements.txt`
- **Plateformes :** Windows (ports `COMx`) et Linux (ports `/dev/ttyUSBx`)

---

## Démarrage rapide

```bash
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

---

## Structure du projet

```
BancTestAuto/
├── main.py              # Point d'entrée : config, logging, thème, MainWindow
├── clean.py             # Nettoyage __pycache__, logs (python clean.py [--all])
├── bump_version.py      # Incrément de version (patch|minor|major) dans core/version.py
├── build_exe.py         # Construction de l'exécutable (PyInstaller, à lancer depuis le venv)
├── serve_htmlcov.py     # Serveur local + ouverture du rapport de couverture (htmlcov) dans le navigateur
├── maquette/            # Interface seule (PyQt6) — valider la maquette puis intégrer dans ui/
├── core/                # app_logger, app_paths, bode_calc, data_logger, device_detection, filter_sweep,
│                        # filter_test, fy6900_commands, fy6900_protocol, measurement, rs305p_protocol,
│                        # scpi_commands, scpi_protocol, serial_connection, serial_exchange_logger, version
├── config/              # settings.py (chargement/sauvegarde), config.json
├── ui/
│   ├── widgets/         # connection_status, measurement_display, mode_bar, range_selector, rate_selector,
│   │                    # math_panel, history_table, advanced_params
│   ├── dialogs/         # serial_config, save_config, device_detection, view_config, view_log,
│   │                    # help_dialog (F1), about_dialog
│   └── views/           # meter_view, generator_view (voie 1/2), logging_view, filter_test_view,
│                        # bode_plot_widget, power_supply_view (Alimentation RS305P)
└── resources/themes/    # dark.qss, light.qss (thèmes clair/foncé)
```

**Maquette :** le répertoire `maquette/` permet de développer et valider **uniquement l’interface** (données factices), puis d’intégrer le code validé dans le logiciel. Lancer avec `python maquette/main_maquette.py`. Voir [maquette/README.md](maquette/README.md).

Détail de l’arborescence : [Guide de développement § 3.2–3.3](docs/DEVELOPPEMENT.md) (arborescence complète et tableau des rôles).

---

## Tests (pytest)

Les tests couvrent les **classes et la logique métier** (`config/`, `core/`) ; l’interface GUI (`ui/`) n’est pas testée.

```bash
pip install -r requirements.txt   # inclut pytest et pytest-cov
pytest                             # lancer les tests
pytest --cov=config --cov=core --cov-report=term-missing --cov-report=html   # avec couverture de code
```

Rapport HTML : `htmlcov/index.html`. Pour le visualiser dans le navigateur avec un serveur local :

```bash
python serve_htmlcov.py
```

---

## Nettoyage

Pour supprimer les `__pycache__/` et les fichiers dans `logs/` :

```bash
python clean.py
```

Avec `python clean.py --all`, supprime aussi le rapport de couverture `htmlcov/`.

---

## Version

Le numéro de version et la date sont centralisés dans **`core/version.py`**. Pour les mettre à jour après une modification :

```bash
python bump_version.py patch   # 1.0.0 → 1.0.1 (correctif)
python bump_version.py minor   # 1.0.1 → 1.1.0 (nouvelle fonctionnalité)
python bump_version.py major   # 1.1.0 → 2.0.0 (changement majeur)
```

La date `__version_date__` est mise à jour automatiquement avec la date du jour.

---

## Exécutable Windows

Pour générer un **exécutable unique** (`BancTestAuto.exe`) avec PyInstaller, **depuis l'environnement virtuel** :

```bash
# Activer le venv puis lancer le script de build
.\.venv\Scripts\Activate.ps1   # Windows
python build_exe.py
```

Ou manuellement : `pip install pyinstaller` puis `pyinstaller BancTestAuto.spec`.

L’exe est créé dans `dist/BancTestAuto.exe`. Au premier lancement, `config.json` et le dossier `logs/` sont créés à côté de l’exécutable. Voir [Créer l’exécutable](docs/BUILD_EXE.md) pour le détail.

---

## Fonctionnalités

### Multimètre OWON (SCPI)

- **Modes de mesure :** tension DC/AC, courant DC/AC, résistance 2 et 4 fils, fréquence, période, capacité, température RTD, diode, continuité
- **Plages :** auto ou manuelle selon le mode
- **Vitesse :** rapide / moyenne / lente
- **Affichage secondaire :** fréquence (Hz) en mode tension/courant
- **Fonctions math :** Rel (offset), dB, dBm, moyenne avec statistiques (min, max, moy.)
- **Historique** des mesures et **export CSV**

### Générateur FeelTech FY6900

- **Pilotage individuel** (onglet dédié) : **choix de la voie (Voie 1 / Voie 2)** ; forme d’onde (WMW), fréquence (WMF), amplitude (WMA), offset (WMO), sortie ON/OFF (WMN), etc. — toutes les commandes du protocole.
- Paramètres par défaut dans `config.json` ; optionnel pour le banc filtre.

### Banc de test filtre

- Caractérisation d’un filtre au **format Bode** (réponse en fréquence).
- **Choix de la voie du générateur** (Voie 1 ou 2) pour le balayage.
- **Balayage modifiable :** f_min, f_max, nombre de points, échelle lin/log, délai de stabilisation.
- Tableau et courbe **gain (dB) vs fréquence** ; export CSV et graphiques semi-log.

Voir [Banc de test filtre](docs/BANC_TEST_FILTRE.md).

### Alimentation Rockseed RS305P

- **Onglet dédié** (connexion et déconnexion gérées dans l'onglet, aucun paramètre dans `config.json`).
- **Préréglages** : boutons rapides 3,3 V, 5 V, 9 V, 12 V (0,5 A, sortie OFF).
- **Contrôles** : tension et courant configurables, sortie ON/OFF, valeurs mesurées (tension et courant affichés).
- Protocole Modbus RTU (9600 baud). Voir [Commandes RS305P](docs/COMMANDES_RS305P.md).

### Mode enregistrement

- **Enregistrement des mesures du multimètre** uniquement (valeur, unité, mode à chaque intervalle).
- **Logging longue durée** : intervalle et durée configurables (ou illimité).
- Fichiers CSV **horodatés** (timestamp, valeur, unité, mode) ; graphique **temps réel**.
- **Relecture** de fichiers et **comparaison** de plusieurs courbes.

### Export et sauvegarde

- **Export :** CSV (mesures, historique, banc filtre), graphiques semi-log pour impression.
- **Sauvegarde JSON :** configuration (série, mesure, affichage, banc filtre, etc.) dans `config/config.json` ou « Enregistrer sous ».

---

## Configuration

Les réglages par défaut sont dans **`config/config.json`**. Principales sections :

| Section | Contenu |
|--------|---------|
| `serial_multimeter` | Port, débit, timeouts, log des échanges (multimètre) |
| `serial_generator` | Port, débit, timeouts (générateur FY6900) |
| `measurement` | Vitesse par défaut, auto-plage, intervalle de rafraîchissement |
| `display` | Taille de police, **thème (clair/foncé)**, affichage secondaire |
| `limits` | Taille de l'historique, options de débit série |
| `logging` | Dossier de sortie, niveau de log, intervalle et durée par défaut |
| `generator` | Voie, forme d’onde, fréquence, amplitude crête, offset (défauts + config. initiale banc filtre) pour l’onglet Générateur |
| `filter_test` | Voie générateur (1 ou 2), f_min, f_max, nombre de points, échelle, délai, tension Ue |

Structure complète et valeurs typiques : [Cahier des charges § 2.7](docs/CAHIER_DES_CHARGES.md).

### Thème d’affichage (clair / foncé)

- **Changer le thème :** menu **Configuration → Thème** puis **Clair** ou **Foncé**. L’interface est mise à jour immédiatement.
- **Sauvegarder le thème pour les prochains lancements :** après avoir choisi un thème, enregistrer la configuration :
  - **Fichier → Sauvegarder config** pour écrire dans `config/config.json`, ou  
  - **Fichier → Enregistrer config sous...** pour un autre fichier.
- La valeur est stockée dans la section `display` sous la clé `theme` : `"light"` (clair) ou `"dark"` (foncé). Au démarrage, l’application charge le thème indiqué dans ce fichier.
- Fichiers de style : `resources/themes/dark.qss` et `resources/themes/light.qss`.

---

## Raccourcis clavier

| Raccourci | Action |
|-----------|--------|
| **F1** | Aide (manuel utilisateur avec recherche) |
| **F5** | Mesure unique |
| **Ctrl+M** | Mesure continue ON/OFF |
| **Ctrl+R** | Reset (*RST) |
| **Ctrl+E** | Export CSV |

---

## Interface et robustesse

- **Interface** par zones : **barre de connexion** (une pastille de statut par équipement : multimètre et générateur), menu **Outils → Détecter les équipements** (détection des ports par protocole, mise à jour du JSON), **Configuration → Thème** (clair / foncé), modes de mesure, affichage principal (type LCD), plage/vitesse, fonctions math, historique. Thème **sombre par défaut** ; le thème peut être changé et sauvegardé (voir [§ Thème d’affichage](#thème-daffichage-clair--foncé)). Détail dans le [cahier des charges § 4](docs/CAHIER_DES_CHARGES.md) et la [conception interface](docs/INTERFACE_PYQT6.md).
- **Robustesse :** timeout série configurable, reconnexion après déconnexion physique, messages d’erreur SCPI, indicateur « en cours » pour les requêtes longues.

---

## Documentation

| Document | Description |
|----------|-------------|
| **Aide intégrée** | Menu **Aide → Manuel** ou touche **F1** : manuel avec recherche (fichier `docs/AIDE.md`) |
| [Cahier des charges](docs/CAHIER_DES_CHARGES.md) | Spécifications complètes, architecture, config, cas d’usage |
| [Guide de développement](docs/DEVELOPPEMENT.md) | Environnement, Git, arborescence, lancement |
| [Banc de test filtre](docs/BANC_TEST_FILTRE.md) | Caractérisation Bode, balayage, qualification filtre |
| [Conception interface PyQt6](docs/INTERFACE_PYQT6.md) | Maquette et widgets par vue — à valider avant la programmation |
| [Audit documentation / code](docs/DOC_AUDIT.md) | Synthèse doc ↔ code, structure cible vs actuelle, redondances |
| [Commandes OWON (multimètre)](docs/COMMANDES_OWON.md) | Tableau des commandes SCPI implémentées pour le multimètre OWON XDM |
| [Commandes FY6900 (générateur)](docs/COMMANDES_FY6900.md) | Tableau des commandes série implémentées pour le générateur FeelTech FY6900 |
| [Commandes RS305P (alimentation)](docs/COMMANDES_RS305P.md) | Protocole Modbus RTU et registres pour l'alimentation Rockseed RS305P |

---

## Matériel

- **Multimètre** OWON XDM1041 / XDM2041 (SCPI, USB)
- **Générateur** FeelTech FY6900 (optionnel ; requis pour le banc de test filtre)
- **Alimentation** Rockseed RS305P (Modbus RTU, USB ; optionnel, onglet autonome)