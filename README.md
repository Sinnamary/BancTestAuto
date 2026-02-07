# Banc de test automatique

Application PyQt6 pour **commander individuellement** le multimètre OWON XDM et le générateur FeelTech FY6900, avec **toutes les commandes implantées dans le matériel**. Configuration par défaut dans `config/config.json`. Le **banc de test filtre** permet de **caractériser un filtre au format Bode** (réponse en fréquence) avec un **balayage en fréquence modifiable** pour qualifier le filtre.

**Spécifications détaillées :** [Cahier des charges](docs/CAHIER_DES_CHARGES.md).

---

## Prérequis

- **Python 3.10+**
- **PyQt6**, **pyserial** — voir `requirements.txt`
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
├── main.py
├── clean.py             # Nettoyage __pycache__, logs (python clean.py)
├── maquette/            # Interface seule (PyQt6) — valider la maquette puis intégrer dans ui/
├── core/                # Série, SCPI, FY6900, mesure, data_logger, filter_test, device_detection, etc.
├── config/              # settings.py, config.json
├── ui/
│   ├── widgets/         # connection_status (2 indicateurs), measurement_display, mode_button, etc.
│   ├── dialogs/         # serial_config, save_config, device_detection (Détecter les équipements)
│   └── views/           # meter_view, generator_view (voie 1/2), logging_view, filter_test_view (voie générateur), etc.
└── resources/           # Icônes, thèmes
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

Rapport HTML : `htmlcov/index.html`.

---

## Nettoyage

Pour supprimer les `__pycache__/` et les fichiers dans `logs/` :

```bash
python clean.py
```

Avec `python clean.py --all`, supprime aussi le rapport de couverture `htmlcov/`.

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
| `logging` | Dossier de sortie, intervalle et durée par défaut |
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

---

## Matériel

- **Multimètre** OWON XDM1041 / XDM2041 (SCPI, USB)
- **Générateur** FeelTech FY6900 (optionnel ; requis pour le banc de test filtre)
