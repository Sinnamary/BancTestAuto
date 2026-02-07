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
├── core/                # Série, SCPI, FY6900, mesure, data_logger, filter_test, filter_sweep, bode_calc
├── config/              # settings.py, config.json
├── ui/
│   ├── widgets/         # measurement_display, mode_button, range_selector, math_panel, etc.
│   ├── dialogs/         # serial_config, save_config
│   └── views/           # meter_view, generator_view, logging_view, filter_test_view, bode_plot_widget
└── resources/           # Icônes, thèmes
```

Détail de l’arborescence : [Guide de développement § 3.2–3.3](docs/DEVELOPPEMENT.md) (arborescence complète et tableau des rôles).

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

- **Pilotage individuel** (onglet dédié) : forme d’onde (WMW), fréquence (WMF), amplitude (WMA), offset (WMO), sortie ON/OFF (WMN), etc. — toutes les commandes du protocole.
- Paramètres par défaut dans `config.json` ; optionnel pour le banc filtre.

### Banc de test filtre

- Caractérisation d’un filtre au **format Bode** (réponse en fréquence).
- **Balayage modifiable :** f_min, f_max, nombre de points, échelle lin/log, délai de stabilisation.
- Tableau et courbe **gain (dB) vs fréquence** ; export CSV et graphiques semi-log.

Voir [Banc de test filtre](docs/BANC_TEST_FILTRE.md).

### Mode enregistrement

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
| `display` | Taille de police, thème (clair/sombre), affichage secondaire |
| `logging` | Dossier de sortie, intervalle et durée par défaut |
| `filter_test` | f_min, f_max, nombre de points, échelle, délai, tension Ue |

Structure complète et valeurs typiques : [Cahier des charges § 2.7](docs/CAHIER_DES_CHARGES.md).

---

## Raccourcis clavier

| Raccourci | Action |
|-----------|--------|
| **F5** | Mesure unique |
| **Ctrl+M** | Mesure continue ON/OFF |
| **Ctrl+R** | Reset (*RST) |
| **Ctrl+E** | Export CSV |

---

## Interface et robustesse

- **Interface** par zones : barre de connexion, modes de mesure, affichage principal (type LCD), plage/vitesse, fonctions math, historique. Thème **sombre par défaut**. Détail dans le [cahier des charges § 4](docs/CAHIER_DES_CHARGES.md).
- **Robustesse :** timeout série configurable, reconnexion après déconnexion physique, messages d’erreur SCPI, indicateur « en cours » pour les requêtes longues.

---

## Documentation

| Document | Description |
|----------|-------------|
| [Cahier des charges](docs/CAHIER_DES_CHARGES.md) | Spécifications complètes, architecture, config, cas d’usage |
| [Guide de développement](docs/DEVELOPPEMENT.md) | Environnement, Git, arborescence, lancement |
| [Banc de test filtre](docs/BANC_TEST_FILTRE.md) | Caractérisation Bode, balayage, qualification filtre |

---

## Matériel

- **Multimètre** OWON XDM1041 / XDM2041 (SCPI, USB)
- **Générateur** FeelTech FY6900 (optionnel ; requis pour le banc de test filtre)
