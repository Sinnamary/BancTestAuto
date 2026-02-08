# Cahier des charges — Banc de test automatique (PyQt6)

**Version :** 1.0  
**Date :** 6 février 2025  
**Référence :** XDM1000_Digital_Multimeter_Programming_Manual.pdf

**Documents associés :**
- [Guide de développement](DEVELOPPEMENT.md) — environnement virtuel, Git, arborescence actuelle, procédure de lancement
- [Banc de test de filtre](BANC_TEST_FILTRE.md) — générateur FY6900 + multimètre, réponse en fréquence, courbe de Bode

---

## 1. Contexte et objectifs

### 1.1 Objectif général

Développer une application PyQt6 permettant de **commander individuellement chaque appareil** du banc de test :

- **Multimètre OWON** XDM1041/XDM2041 : pilotage via liaison série (USB/SCPI) avec **l’ensemble des commandes implantées dans le matériel** (modes de mesure, plages, vitesse, fonctions math, etc.).
- **Générateur de signaux** FeelTech FY6900 : pilotage via liaison série avec **toutes les commandes du protocole** (forme d’onde, fréquence, amplitude, offset, rapport cyclique, phase, sortie ON/OFF ; lecture de la réponse 0x0a entre chaque commande).
- **Alimentation stabilisée** Rockseed RS305P : pilotage via Modbus RTU (onglet autonome, connexion gérée dans l'onglet, aucun paramètre dans `config.json`).

Les paramètres par défaut (ports série, débits, plages, etc.) sont lus au démarrage depuis le fichier **`config/config.json`**. **Aucun port série n’est ouvert à l’ouverture de l’application** : les connexions multimètre et générateur sont établies après « Charger config » ou « Détecter les équipements » (ou validation des paramètres). Un **onglet Terminal série** permet d’envoyer et recevoir des commandes sur un port au choix (indépendant). Chaque appareil peut ainsi être utilisé seul ou dans le cadre du banc de test filtre.

### 1.2 Pilotage individuel et configuration par défaut

- **Commande individuelle** : l’utilisateur peut contrôler le multimètre et le générateur séparément, avec accès à toutes les fonctions disponibles côté matériel. Aucune fonction n’est masquée : l’interface expose les commandes SCPI (OWON) et le protocole FY6900 (FeelTech) de façon complète.
- **Configuration par défaut** : le fichier `config.json` centralise les réglages initiaux pour le multimètre (port, débit, mode, plage, etc.) et pour le générateur (port, débit, paramètres du banc filtre). L’application charge ces valeurs au lancement ; l’utilisateur peut les modifier via l’interface et les enregistrer.

### 1.3 Principes directeurs

- **Simplicité** : accès plus direct aux fonctions qu’avec les boutons physiques des appareils
- **Visibilité** : toutes les options disponibles côté matériel sont affichées clairement
- **Paramétrage rapide** : réglages en un ou deux clics, valeurs par défaut depuis `config.json`
- **Feedback continu** : affichage en temps réel des mesures et de l’état de chaque appareil
- **Modularité** : programmation modulaire, petits fichiers, classes réutilisables

---

## 2. Architecture technique

### 2.1 Stack technologique

| Composant     | Choix   |
|---------------|---------|
| Interface     | PyQt6   |
| Communication | pyserial + SCPI |
| Protocole     | SCPI (USB ou LAN) |
| Langage       | Python 3.10+ |

### 2.2 Structure de l'application

Vue d’ensemble (structure détaillée avec **décomposition maximale** et rôle de chaque fichier : **[Guide de développement § 3.2 et 3.3](DEVELOPPEMENT.md)**).

```
BancTestAuto/
├── main.py
├── core/                          # Logique métier : série, SCPI, FY6900, mesure, banc filtre
│   ├── serial_connection.py       # Liaison série (port, buffers, log)
│   ├── scpi_protocol.py           # SCPI (utilise SerialConnection)
│   ├── scpi_commands.py           # Constantes SCPI
│   ├── measurement.py             # Logique mesures OWON
│   ├── owon_ranges.py             # Plages par mode (données)
│   ├── fy6900_protocol.py         # Protocole FY6900
│   ├── fy6900_commands.py         # Format commandes FY6900
│   ├── data_logger.py             # Enregistrement CSV horodaté
│   ├── filter_test.py             # Orchestration banc filtre
│   ├── filter_sweep.py            # Génération fréquences (log/lin)
│   ├── bode_calc.py               # Calculs gain dB (réutilisable)
│   └── device_detection.py       # Détection automatique : quel port pour OWON, quel port pour FY6900
├── config/
│   ├── settings.py                # Chargement / sauvegarde config
│   └── config.json
├── ui/
│   ├── main_window.py             # Fenêtre principale, onglets
│   ├── widgets/                   # Un fichier = un widget réutilisable
│   │   ├── measurement_display.py
│   │   ├── mode_button.py
│   │   ├── mode_bar.py
│   │   ├── range_selector.py
│   │   ├── rate_selector.py
│   │   ├── math_panel.py
│   │   ├── history_table.py
│   │   ├── connection_status.py
│   │   ├── secondary_display.py
│   │   └── advanced_params.py
│   ├── dialogs/
│   │   ├── serial_config_dialog.py
│   │   └── save_config_dialog.py
│   └── views/                     # Vues composites (multimètre, générateur, logging, banc filtre, alimentation, terminal série)
│       ├── meter_view.py
│       ├── generator_view.py
│       ├── logging_view.py
│       ├── filter_test_view.py
│       ├── filter_config_panel.py
│       ├── filter_results_table.py
│       ├── power_supply_view.py
│       ├── serial_terminal_view.py
│       └── bode_plot_widget.py
└── resources/                     # Icônes, thèmes
```

Règle : **petits fichiers**, **une responsabilité par module**, **classes facilement réutilisables** (injection, utilisation en UI et par le banc de test). Arborescence complète et tableau des rôles : [DEVELOPPEMENT.md § 3.2–3.3](DEVELOPPEMENT.md).

### 2.3 Principes de modularité et développement

La programmation est **très modulaire** : **petits fichiers**, **classes distinctes pour chaque appareil de mesure**, responsabilités bien séparées. Les classes d’appareils sont **appelées pour piloter le banc de test** : le module banc (ex. `filter_test.py`) utilise les classes multimètre et générateur sans dupliquer leur logique.

| Règle | Description |
|-------|-------------|
| **Un fichier = une responsabilité** | Chaque module traite un aspect précis (série, SCPI, un appareil, affichage LCD, etc.) |
| **Une classe par appareil (ou protocole)** | Multimètre OWON et générateur FY6900 ont chacun leur(s) classe(s) dédiée(s), dans des fichiers distincts |
| **Banc de test = orchestration** | Le banc de test **appelle** les classes d’appareils pour piloter les mesures (balayage, lecture, calculs) |
| **Taille limitée** | Fichiers courts (idéalement &lt; 200 lignes) ; si trop long, découper en sous-modules |
| **Classes réutilisables** | Chaque classe est autonome, injectable : utilisable en commande individuelle (UI) et par le banc |
| **Injection de dépendances** | Éviter les couplages forts : passer les dépendances en constructeur ou via setters |
| **Interfaces claires** | Méthodes publiques bien définies ; logique interne encapsulée |
| **Tests unitaires facilités** | Classes petites et isolées = tests plus simples |

**Exemple de découpage :**
- **Liaison série par classe** : une classe dédiée (ex. `SerialConnection`) par liaison, avec buffers et option de log des échanges (voir § 2.5).
- Classes **par appareil** : `ScpiProtocol` / couche mesure pour OWON ; `Fy6900Protocol` (ou classe dédiée) pour le générateur — chacune dans son fichier, utilisant la classe série.
- **Banc de test** : `filter_test.py` **appelle** ces classes pour régler fréquence, lancer mesure, calculer gain
- Widgets UI : `MeasurementDisplay`, `ModeButton`, etc. (réutilisables)

### 2.5 Liaisons série par classe, buffers et logging des échanges

Les **liaisons série sont programmées par classe** (une classe dédiée, instanciée par port). Chaque instance gère un port, avec :

- **Buffers** : tampons d’entrée et de sortie pour l’émission et la réception (éviter pertes de données, découpler I/O et traitement). Taille et gestion (circulaire, file) à définir selon le débit et les messages attendus.
- **Possibilité d’arrêter / activer le logging des échanges** : option (configurable via `config.json` et/ou interface) pour enregistrer ou non les trames envoyées et reçues (debug). Quand le log est désactivé, aucun enregistrement des échanges ; quand il est activé, les échanges peuvent être tracés vers un fichier ou une fenêtre de debug. Permet de déboguer sans surcharge en production.

Les classes de protocole (SCPI, FY6900) s’appuient sur cette classe série et n’accèdent pas directement au port.

### 2.6 Utilisation de threads pour les I/O série (recommandée)

L’**utilisation de threads est optimale** pour les liaisons série dans une application PyQt6 :

- **Problème** : les lectures/écritures série sont bloquantes ; si elles s’exécutent dans le thread de l’interface, l’UI se fige pendant les échanges.
- **Solution** : exécuter les I/O série dans un **thread dédié** (ou un worker). Avec PyQt6, **QThread** (ou un worker dérivé) est adapté : le worker effectue open/read/write, et communique avec le thread principal par signaux/slots (ex. données reçues, erreur, connexion fermée).
- **Bénéfices** : interface restant réactive pendant les échanges ; pas de blocage lors des timeouts ; mesure continue et banc de test fluides. Une instance de classe série peut être associée à un thread (ou partagée avec synchronisation) selon l’architecture retenue.

Le guide de développement (DEVELOPPEMENT.md) détaille cette approche.

### 2.7 Fichier de configuration JSON

Tous les paramètres par défaut sont centralisés dans un fichier **`config.json`** (dossier `config/` ou racine du projet). L’application charge ces valeurs au démarrage pour **chaque appareil** :

**Chaque liaison série de chaque appareil** a ses **paramètres dans le fichier JSON** : une section dédiée par appareil (`serial_multimeter`, `serial_generator`). Ces paramètres sont **repris dans les classes** qui gèrent les liaisons série : chaque classe charge la section JSON qui la concerne. Les classes définissent aussi **des paramètres par défaut** (dans le code) ; les valeurs du JSON priment lorsqu’elles sont présentes, sinon les valeurs par défaut de la classe sont utilisées. Le JSON peut donc être partiel.

Les réglages servent de configuration initiale pour le pilotage individuel du multimètre et du générateur, ainsi que pour le mode « Banc de test filtre ». Toute modification via l’interface peut être réenregistrée dans ce fichier.

#### Structure du fichier `config.json`

```json
{
  "serial_multimeter": {
    "port": "COM3",
    "baudrate": 9600,
    "bytesize": 8,
    "parity": "N",
    "stopbits": 1,
    "timeout": 2.0,
    "write_timeout": 2.0,
    "log_exchanges": false
  },
  "serial_generator": {
    "port": "COM4",
    "baudrate": 115200,
    "bytesize": 8,
    "parity": "N",
    "stopbits": 1,
    "timeout": 2.0,
    "write_timeout": 2.0,
    "log_exchanges": false
  },
  "measurement": {
    "default_rate": "F",
    "default_auto_range": true,
    "refresh_interval_ms": 500
  },
  "display": {
    "font_size": "large",
    "theme": "dark",
    "secondary_display": false
  },
  "limits": {
    "history_size": 100,
    "baudrate_options": [9600, 19200, 38400, 57600, 115200]
  },
  "logging": {
    "output_dir": "./logs",
    "level": "INFO",
    "default_interval_s": 5,
    "default_duration_min": 60,
    "duration_unlimited": false
  },
  "generator": {
    "default_channel": 1,
    "waveform": 0,
    "frequency_hz": 1000,
    "amplitude_v_peak": 1.414,
    "offset_v": 0
  },
  "filter_test": {
    "generator_channel": 1,
    "f_min_hz": 10,
    "f_max_hz": 100000,
    "n_points": 50,
    "scale": "log",
    "settling_ms": 200,
    "ue_rms": 1.0
  }
}
```

#### Paramètres configurables

| Section     | Paramètre         | Description                        | Valeurs typiques                    |
|-------------|-------------------|------------------------------------|-------------------------------------|
| **serial_multimeter** | *(liaison série multimètre — repris par la classe avec paramètres par défaut)* | | |
|             | port              | Port série multimètre              | `"COM3"`, `"/dev/ttyUSB0"`          |
|             | baudrate          | Débit en bauds                     | 9600, 19200, 38400, 57600, 115200   |
|             | bytesize          | Nombre de bits de données          | 7, 8                                |
|             | parity            | Parité                             | `"N"`, `"E"`, `"O"`                 |
|             | stopbits          | Bits d'arrêt                       | 1, 2                                |
|             | timeout           | Timeout lecture (s)                | 0.5 – 10                            |
|             | write_timeout     | Timeout écriture (s)               | 0.5 – 10                            |
|             | log_exchanges     | Logger les échanges (debug)        | true, false                         |
| **serial_generator** | *(liaison série générateur FY6900 — repris par la classe avec paramètres par défaut)* | | |
|             | port              | Port série générateur               | `"COM4"`, `"/dev/ttyUSB1"`          |
|             | baudrate          | Débit (FY6900 : 115200)            | 115200                              |
|             | bytesize, parity, stopbits, timeout, write_timeout, log_exchanges | Idem structure que serial_multimeter | |
| **measurement** | default_rate   | Vitesse par défaut                 | `"F"`, `"M"`, `"L"`                 |
|             | default_auto_range| Plage auto au démarrage           | true, false                         |
|             | refresh_interval_ms | Intervalle rafraîchissement (ms) | 100 – 2000                          |
| **display** | font_size         | Taille affichage mesures           | `"small"`, `"medium"`, `"large"`    |
|             | theme             | Thème interface                    | `"dark"`, `"light"`                 |
|             | secondary_display | Affichage secondaire (Hz) par défaut | true, false                       |
| **limits**  | history_size      | Nombre max de mesures en historique| 10 – 1000                           |
|             | baudrate_options  | Débits disponibles dans l'UI       | liste de valeurs                    |
| **logging** | output_dir        | Répertoire des fichiers enregistrés| `"./logs"`                          |
|             | level             | Niveau de log application          | `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"` |
|             | default_interval_s| Intervalle par défaut (s)          | 1 – 86400                           |
|             | default_duration_min | Durée par défaut (min)          | 1 – 525600 (1 an)                   |
|             | duration_unlimited| Durée illimitée par défaut         | true, false                         |
| **generator** | default_channel  | Voie par défaut (onglet Générateur) | 1, 2                                |
|             | waveform         | Forme d’onde (0 = sinusoïde FY6900)  | 0                                   |
|             | frequency_hz     | Fréquence par défaut (Hz)           | 1 – 20e6                            |
|             | amplitude_v_peak| Amplitude crête (V) — 1,414 ≈ 1 V RMS | 0.01 – 20                        |
|             | offset_v         | Offset (V)                          | −20 – 20                            |
| **filter_test** | generator_channel | Voie du générateur pour le banc filtre | 1, 2                              |
|             | f_min_hz, f_max_hz | Plage de fréquence (Hz)            | 10 – 1 000 000                      |
|             | n_points        | Nombre de points du balayage        | 20 – 200                            |
|             | scale           | Échelle fréquence                   | `"log"`, `"lin"`                    |
|             | settling_ms     | Délai stabilisation après changement f | 100 – 1000                       |
|             | ue_rms          | Tension entrée filtre (V RMS)       | 1.0                                 |

- **Banc de test filtre — configuration connue :** au démarrage d’un balayage, le banc filtre **applique** la configuration générateur définie dans `config.json` (section `generator` : forme d’onde, amplitude crête, offset ; section `filter_test` : voie, `ue_rms` pour le niveau). Il **ne part pas** de la configuration précédente de l’équipement : on repart toujours d’un état connu et reproductible.
- **Emplacement** : `config/config.json` ou à la racine du projet.
- **Sauvegarde JSON** : **le logiciel doit permettre de sauvegarder un JSON** : la configuration (paramètres série, mesure, affichage, banc filtre, etc.) doit pouvoir être enregistrée dans un fichier JSON, sur action de l’utilisateur (ex. bouton « Sauvegarder la configuration » ou « Enregistrer » dans un dialogue de paramètres) et éventuellement à la fermeture de l’application. Le fichier cible est par défaut `config/config.json`, avec possibilité d’exporter vers un autre fichier (sauvegarde sous) si souhaité.
- **Thème d’affichage** : le thème (`display.theme`, `"dark"` ou `"light"`) est modifiable via le menu **Configuration → Thème → Clair / Foncé**. L’interface est mise à jour immédiatement ; pour conserver le choix au prochain lancement, l’utilisateur enregistre la configuration (Fichier → Sauvegarder config). Voir README § Thème d’affichage.
- **Priorité** : les valeurs du fichier priment sur les valeurs codées en dur au chargement ; après sauvegarde, le fichier JSON reflète l’état courant de la configuration.

---

## 3. Spécification fonctionnelle

### 3.1 Connexion et identification

| Fonctionnalité      | Commande SCPI | Description |
|---------------------|---------------|-------------|
| Connexion série     | —             | Port, débit, timeout : valeurs par défaut depuis `config.json` |
| **Sauvegarde JSON** | —             | **Le logiciel doit permettre de sauvegarder la configuration en fichier JSON** (bouton ou menu « Sauvegarder la configuration », par défaut `config/config.json`, option « Enregistrer sous » possible) |
| Identification      | `*IDN?`       | Affichage modèle, n° série, version firmware |
| Mode local/distant  | `SYST:LOC` / `SYST:REM` | Indicateur visuel du mode (Local/Remote) |
| Réinitialisation    | `*RST`        | Bouton « Reset » pour valeurs par défaut |

### 3.2 Détection automatique des équipements (menu Outils)

Dans le menu **Outils**, une action **« Détecter les équipements »** permet d’identifier automatiquement sur quels ports série sont connectés le **multimètre OWON** et le **générateur FY6900**, puis d’affecter le bon port au bon équipement et de **mettre à jour le fichier `config.json`**.

- **Principe :** le logiciel parcourt l’ensemble des ports COM disponibles (Windows : COM1, COM2, … ; Linux : /dev/ttyUSBx, /dev/ttyACMx, …). Pour chaque port, il tente une communication selon le **protocole adapté** :
  - **Multimètre OWON :** envoi de la commande SCPI `*IDN?` (débit type 9600 ou 115200) ; si la réponse contient un identifiant OWON / XDM, le port est considéré comme celui du multimètre.
  - **Générateur FY6900 :** envoi d’une commande du protocole FeelTech (ex. requête de statut ou commande sans effet de bord) ; si la réponse est cohérente avec le protocole FY6900, le port est considéré comme celui du générateur.
- **Résultat :** affectation du port détecté au bon équipement (multimètre vs générateur). Les champs `serial_multimeter.port` et `serial_generator.port` dans **`config.json`** sont mis à jour avec les ports trouvés ; l’utilisateur n’a plus à choisir manuellement le port pour chaque appareil à chaque démarrage.
- **Implémentation :** cette logique est encapsulée dans une **classe dédiée** `core/device_detection.py` (ex. `DeviceDetection`), réutilisable et testable, sans dépendance directe à l’interface. Le menu Outils appelle cette classe puis demande la sauvegarde du JSON (ou sauvegarde automatique après détection).

### 3.3 Sélection des modes de mesure (zone principale)

Tous les modes doivent être accessibles via des boutons ou une barre d'icônes.

| Mode                 | Commande CONFigure   | Icône / zone suggérée |
|----------------------|----------------------|------------------------|
| Tension DC           | `CONF:VOLT:DC`       | Bouton « V⎓ »         |
| Tension AC           | `CONF:VOLT:AC`       | Bouton « V~ »         |
| Courant DC           | `CONF:CURR:DC`       | Bouton « A⎓ »         |
| Courant AC           | `CONF:CURR:AC`       | Bouton « A~ »         |
| Résistance 2 fils    | `CONF:RES`           | Bouton « Ω »          |
| Résistance 4 fils    | `CONF:FRES`          | Bouton « Ω 4W »       |
| Fréquence            | `CONF:FREQ`          | Bouton « Hz »         |
| Période              | `CONF:PER`           | Bouton « s »          |
| Capacité             | `CONF:CAP`           | Bouton « F »          |
| Température RTD      | `CONF:TEMP:RTD`      | Bouton « °C »         |
| Diode                | `CONF:DIOD`          | Bouton symbole diode  |
| Continuité           | `CONF:CONT`          | Bouton symbole son    |

### 3.4 Plages de mesure (ranges)

Paramétrage via listes déroulantes ou boutons radio, selon le mode actif.

#### Tension DC
| Plage  | Valeur SCPI |
|--------|-------------|
| 500 mV | 500E-3      |
| 5 V    | 5           |
| 50 V   | 50          |
| 500 V  | 500         |
| 1000 V | 1000        |

#### Tension AC
| Plage  | Valeur SCPI |
|--------|-------------|
| 500 mV | 500E-3      |
| 5 V    | 5           |
| 50 V   | 50          |
| 500 V  | 500         |
| 750 V  | 750         |

#### Courant DC / AC
Plages : 50 mV, 500 mV, 5 V, 50 V, 500 V, 1000 V (shunts).

#### Résistance
| Plage | Valeur SCPI |
|-------|-------------|
| 500 Ω | 500         |
| 5 kΩ  | 5E3         |
| 50 kΩ | 50E3       |
| 500 kΩ| 500E3      |
| 5 MΩ  | 5E6        |
| 50 MΩ | 50E6       |
| 500 MΩ| 500E6      |

*Résistance 4 fils : plages jusqu'à 50 kΩ.*

#### Capacité
| Plage  | Valeur SCPI |
|--------|-------------|
| 50 nF  | 50E-9       |
| 500 nF | 500E-9      |
| 5 µF   | 5E-6        |
| 50 µF  | 50E-6       |
| 500 µF | 500E-6      |
| 5 mF   | 5E-3        |
| 50 mF  | 50E-3       |

#### Température
| Type RTD | Valeur SCPI |
|----------|-------------|
| KITS90   | KITS90      |
| PT100    | PT100       |

### 3.5 Auto-plage et plage manuelle

| Fonction         | Commande    | Interface                          |
|------------------|-------------|------------------------------------|
| Plage automatique| `AUTO` / `AUTO?` | Interrupteur / bouton « AUTO » |
| Plage manuelle   | `RANGE <n>` | Liste déroulante / barre de plages |

### 3.6 Vitesse de mesure (RATE)

| Vitesse | Commande | Libellé interface |
|---------|----------|-------------------|
| Rapide  | `RATE F` | « Rapide »        |
| Moyenne | `RATE M` | « Moyenne »       |
| Lente   | `RATE L` | « Lente »         |

Contrôle par boutons radio ou liste déroulante.

### 3.7 Affichage principal et secondaire

#### Affichage principal
- Grand écran numérique (similaire au LCD du multimètre)
- Rafraîchissement configurable (ex. 100 ms – 2 s)
- Mise en évidence des unités (V, A, Ω, Hz, F, °C, etc.)

#### Affichage secondaire (FUNCtion2)
| Option       | Commande       | Usage                            |
|--------------|----------------|-----------------------------------|
| Fréquence    | `FUNC2 "FREQ"` | En mode tension/courant           |
| Aucun        | `FUNC2 "NONe"` | Désactiver le second affichage    |

Contrôle par case à cocher « Affichage secondaire : Fréquence ».

### 3.8 Température (paramètres spécifiques)

| Paramètre   | Commande                     | Interface                |
|-------------|------------------------------|--------------------------|
| Type RTD    | `TEMP:RTD:TYPe`             | Liste : KITS90 / PT100    |
| Unité       | `TEMP:RTD:UNIT`             | Liste : °C / °F / K       |
| Mode affich.| `TEMP:RTD:SHOW`             | TEMP / MEAS / ALL         |

### 3.9 Seuil de continuité

| Paramètre        | Commande            | Interface              |
|------------------|---------------------|------------------------|
| Seuil (Ω)        | `CONT:THRE <value>` | Champ numérique        |

### 3.10 Fonctions mathématiques (CALCulate)

| Fonction  | Commande            | Interface                     |
|-----------|---------------------|-------------------------------|
| Désactivé | `CALC:STAT OFF`     | Bouton « Maths OFF »          |
| Valeur relative | `CALC:FUNC NULL` | Bouton « Rel » + champ offset |
| dB        | `CALC:FUNC DB`      | Bouton « dB » + ref. (Ω)      |
| dBm       | `CALC:FUNC DBM`     | Bouton « dBm » + ref. (Ω)     |
| Moyenne   | `CALC:FUNC AVERage` | Bouton « Moyenne » + stats    |

#### Références dB/dBm
Options : 50, 75, 93, 110, 124, 125, 135, 150, 250, 300, 500, 600, 800, 900, 1000, 1200, 8000 Ω.

#### Statistiques (AVERage)
- Requêtes : `CALC:AVER:ALL?`, `AVERage?`, `MAXimum?`, `MINimum?`
- Affichage : Min, Max, Moyenne, Nombre de mesures
- Bouton « Réinitialiser stats »

### 3.11 Paramètres système

| Paramètre      | Commande            | Interface              |
|----------------|---------------------|------------------------|
| Buzzer         | `SYST:BEEP:STAT`    | Case à cocher ON/OFF   |

### 3.12 Acquisition et export des mesures

| Fonction           | Commandes           | Interface                            |
|--------------------|---------------------|--------------------------------------|
| Mesure unique      | `MEAS?` / `MEAS1?` | Bouton « Mesure »                    |
| Mesure continue    | Timer + `MEAS?`     | Bouton « Mesure continue »           |
| Affichage secondaire | `MEAS2?`         | Intégré à la zone d'affichage        |
| Historique         | —                   | Tableau des N dernières mesures      |
| Export CSV         | —                   | Bouton « Exporter »                  |

### 3.13 Mode enregistrement (logging longue durée)

Mode dédié permettant d'enregistrer des mesures à intervalle régulier sur des durées longues (quelques secondes à plusieurs jours), avec affichage graphique et relecture pour comparaison.

#### Paramètres configurables

| Paramètre           | Description                              | Contraintes                          |
|---------------------|------------------------------------------|--------------------------------------|
| Intervalle          | Période entre deux mesures               | 1 s – 24 h (s, min, h)               |
| Durée               | Durée totale ou illimitée                | Durée fixe (s/min/h/j) ou ∞          |
| Mode de mesure      | Fonction du multimètre utilisée          | Tous les modes (§ 3.2)               |
| Répertoire de sortie| Dossier d'enregistrement                 | Configurable dans config.json        |

#### Format des fichiers horodatés

- **Nom** : `owon_log_YYYY-MM-DD_HH-MM-SS.csv` (date/heure de début d'enregistrement)
- **Contenu** : une ligne d'en-tête + une ligne par mesure

```
timestamp_iso,elapsed_s,value,unit,mode
2025-02-06T14:30:00.000,0,12.345,V,VOLT:DC
2025-02-06T14:30:05.000,5,12.346,V,VOLT:DC
...
```

- **timestamp_iso** : ISO 8601 (date/heure UTC ou locale selon config)
- **elapsed_s** : secondes écoulées depuis le début
- **value** : valeur mesurée (notation scientifique acceptée)
- **unit** : unité (V, A, Ω, Hz, F, °C, etc.)
- **mode** : mode SCPI au moment de la mesure

#### Affichage graphique

- Courbe **valeur = f(temps)** en temps réel pendant l'enregistrement
- Axe X : temps (date/heure ou temps écoulé, sélectionnable)
- Axe Y : valeur avec unité
- Zoom, défilement, grille
- Indicateur d'enregistrement en cours (statut, nb de points, temps restant si durée définie)

#### Relecture et comparaison

- **Ouvrir un fichier** : chargement d'un fichier .csv horodaté existant
- **Affichage** : même graphique que lors de l'enregistrement (courbe rejouée)
- **Comparaison** : possibilité de superposer plusieurs courbes (plusieurs fichiers) sur le même graphique
- **Métadonnées** : affichage des paramètres de la session (mode, intervalle, durée, etc.) si stockés dans le fichier ou un fichier .json associé

#### Interface proposée

- Onglet ou bouton « Mode Enregistrement » dans la fenêtre principale
- Panneau de configuration : intervalle, durée (ou ∞), mode mesure, dossier
- Boutons : [Démarrer] [Arrêter] [Mettre en pause]
- Zone graphique (pyqtgraph ou matplotlib intégré)
- Boutons : [Ouvrir fichier] [Comparer] [Exporter image]



---

## 4. Ergonomie et design de l'interface

### 4.1 Philosophie

L'objectif est de regrouper visuellement les fonctions et de réduire les actions nécessaires par rapport à la face avant du multimètre :

- Pas de menus imbriqués profonds
- Une seule zone pour sélectionner le mode de mesure
- Une zone dédiée pour les plages, visible dès que pertinent
- Paramètres avancés regroupés dans des panneaux repliables ou des onglets

### 4.2 Disposition proposée (layout)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  [Banc de test auto]                 ● Connecté  XDM2041  COM3    [Param.] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─ Modes de mesure ──────────────────────────────────────────────────────┐ │
│  │ [V⎓] [V~] [A⎓] [A~] [Ω] [Ω4W] [Hz] [s] [F] [°C] [⊿] [⚡]               │ │
│  │  Mode actif mis en évidence (bordure/ombre)                             │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌─ Affichage principal ────────────────────────┐ ┌─ Secondaire ─────────┐ │
│  │                                               │ │ [ ] Afficher Hz      │ │
│  │           12.345 V                            │ │                      │ │
│  │                                               │ │   (si activé)        │ │
│  │         [Grand chiffre, fond sombre]          │ │   1.234 kHz          │ │
│  └──────────────────────────────────────────────┘ └──────────────────────┘ │
│                                                                             │
│  ┌─ Plage ───────────────────┐ ┌─ Vitesse ──────┐ ┌─ Math ──────────────┐ │
│  │ (○) Auto  (●) Manuel       │ │ (●) Rapide     │ │ (○) Aucun           │ │
│  │ [5 V ▼]                    │ │ ( ) Moyenne    │ │ ( ) Rel  [0.000]    │ │
│  └────────────────────────────┘ │ ( ) Lente      │ │ ( ) dB  [600Ω▼]     │ │
│                                  └────────────────┘ │ ( ) dBm [600Ω▼]    │ │
│                                                      │ ( ) Moy. [Stats]   │ │
│                                                      └────────────────────┘ │
│  ┌─ Paramètres avancés (repliable) ───────────────────────────────────────┐ │
│  │ Température: [PT100▼] [°C▼] [TEMP▼]  │  Continuité: [50 Ω]  │  [🔊] Buzzer│
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌─ Historique ───────────────────────────────────────────────────────────┐ │
│  │ #1  12.345 V    #2  12.346 V    #3  12.344 V    [Exporter CSV] [Effacer]│
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  [Mesure]  [Mesure continue ●]  [Reset *RST]  [Mode Enregistrement]  [Banc filtre] │
├─────────────────────────────────────────────────────────────────────────────┤
│  Onglet « Mode Enregistrement » : graphique + config intervalle/durée        │
│  Onglet « Banc de test filtre » : caractérisation filtre format Bode,        │
│  balayage fréquence modifiable (f_min, f_max, N points, échelle) — qualif.   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Zones principales

#### Zone 1 : Barre de connexion (en haut)
- Indicateur de connexion (vert/rouge)
- Modèle et port
- Bouton de paramètres (port, débit, etc.) avec possibilité de **sauvegarder la configuration en JSON**

#### Zone 2 : Barre de modes
- Boutons horizontaux pour tous les modes
- Mode actif mis en évidence
- Changement de mode en un clic

#### Zone 3 : Affichage des mesures
- Grande zone pour la mesure principale
- Police type LCD (monospace, grande taille)
- Unité visible et cohérente avec le mode
- Zone secondaire pour Fréquence si activée

#### Zone 4 : Plage et vitesse
- Auto / manuel
- Liste des plages adaptée au mode
- Vitesse de mesure

#### Zone 5 : Fonctions math
- Boutons radio ou onglets pour Rel, dB, dBm, Moyenne
- Champs de réglage selon la fonction choisie

#### Zone 6 : Paramètres avancés
- Panneau repliable
- Paramètres température, continuité, buzzer

#### Zone 7 : Historique et acquisition
- Liste ou tableau des mesures
- Boutons Mesure, Mesure continue, Reset, Export CSV

#### Zone 8 : Mode enregistrement (onglet dédié)
- Panneau de configuration (intervalle, durée, mode mesure, dossier)
- Graphique temps réel valeur = f(temps)
- Boutons Démarrer, Arrêter, Mettre en pause
- Relecture de fichiers horodatés, superposition pour comparaison

#### Zone 9 : Générateur de signaux (commande individuelle)
- Onglet ou panneau pour piloter le FY6900 **individuellement** avec l’ensemble des commandes du protocole : forme d’onde (WMW), fréquence (WMF), amplitude (WMA), offset (WMO), sortie ON/OFF (WMN), etc.
- Paramètres par défaut chargés depuis `config.json` (port, débit ; paramètres du banc filtre réutilisables ou surchargeables).

### 4.4 Codes visuels et accessibilité

| Élément            | Règle                                                     |
|--------------------|-----------------------------------------------------------|
| Mode actif         | Bordure colorée, fond légèrement différent                 |
| Connexion          | Vert (OK), rouge (déconnecté)                             |
| Erreur             | Message court + couleur d'alerte                          |
| Unités             | Toujours affichées à côté des valeurs                     |
| Contraste          | Mode sombre par défaut (type écran multimètre)            |
| Police             | Monospace pour les nombres (ex. Consolas, JetBrains Mono) |

### 4.5 Raccourcis clavier proposés

| Raccourci    | Action                    |
|--------------|---------------------------|
| F5           | Mesure unique             |
| Ctrl+M       | Mesure continue ON/OFF    |
| Ctrl+R       | Reset (*RST)              |
| Ctrl+E       | Export CSV                |
| 1–9          | Sélection rapide de mode (optionnel) |

### 4.6 Options de personnalisation

- Taille de police des mesures (petit / moyen / grand)
- Mode clair / sombre
- Vitesse de rafraîchissement par défaut
- Toutes ces options sont stockées dans `config.json` (voir § 2.4)

---

## 5. Cas d'utilisation prioritaires

1. Mesurer une tension DC en un clic (mode + plage auto).
2. Passer en résistance 4 fils avec plage 5 kΩ en deux clics.
3. Mesurer fréquence avec valeur secondaire (Hz) affichée.
4. Faire une mesure relative (NULL) avec offset défini.
5. Obtenir min/max/moyenne sur une série de mesures.
6. Exporter un historique de mesures en CSV.
7. Changer de plage manuellement pendant une mesure continue.
8. Lancer un enregistrement sur 24 h (température, 1 mesure/min) avec graphique en temps réel.
9. Recharger un fichier horodaté et superposer deux enregistrements pour comparaison.
10. Commander le générateur seul : forme d’onde, fréquence, amplitude, offset, sortie ON/OFF (toutes les commandes du protocole FY6900).
11. Lancer un balayage de réponse en fréquence (banc filtre) pour **caractériser un filtre au format Bode** : générateur FY6900 à Ue fixe, multimètre mesure Us ; **balayage en fréquence modifiable** (f_min, f_max, nombre de points, échelle lin/log, délai de stabilisation) pour une **bonne qualification du filtre** ; tableau et graphique semi-log (gain en dB vs fréquence).

---

## 6. Gestion des erreurs et robustesse

- Timeout série configurable via `config.json` (ex. 2 s)
- Reconnexion après déconnexion physique
- Message clair en cas de commande invalide ou erreur SCPI
- Indicateur de « en cours » lors des requêtes longues

---

## 7. Planning et livrables (suggestion)

| Phase       | Contenu                                  | Priorité |
|------------|-------------------------------------------|----------|
| Phase 1    | Fichier config.json, connexion série, *IDN, modes de mesure | P0       |
| Phase 2    | Affichage mesure, plages, auto/manuel    | P0       |
| Phase 3    | Vitesse, second display, temp/cont       | P1       |
| Phase 4    | Fonctions math (Rel, dB, dBm, Moyenne)   | P1       |
| Phase 5    | Historique, export CSV                   | P1       |
| Phase 5b   | Mode enregistrement : config, fichier CSV, graphique temps réel | P1       |
| Phase 5c   | Relecture fichiers horodatés, comparaison multi-courbes         | P1       |
| Phase 6    | Raccourcis, thèmes, paramètres avancés   | P2       |
| Phase 7    | Banc de test filtre : caractérisation filtre format Bode, balayage modifiable pour qualification — voir [BANC_TEST_FILTRE.md](BANC_TEST_FILTRE.md) | P1       |

---

## 8. Annexe — Commandes SCPI de référence

Résumé des commandes utilisées (voir le manuel pour le détail).

- **Identification** : `*IDN?`, `*RST`
- **Modes** : `CONF:VOLT:DC`, `CONF:VOLT:AC`, `CONF:CURR:DC`, `CONF:CURR:AC`, `CONF:RES`, `CONF:FRES`, `CONF:FREQ`, `CONF:PER`, `CONF:CAP`, `CONF:TEMP:RTD`, `CONF:DIOD`, `CONF:CONT`
- **Plage** : `AUTO`, `RANGE <n>`, `RATE F|M|L`
- **Fonction** : `FUNC?`, `FUNC2 "FREQ"|"NONe"`
- **Math** : `CALC:FUNC NULL|DB|DBM|AVERage`, `CALC:NULL:OFFS`, `CALC:DB:REF`, `CALC:DBM:REF`, `CALC:AVER:ALL?`
- **Mesure** : `MEAS?`, `MEAS1?`, `MEAS2?`
- **Système** : `SYST:LOC`, `SYST:REM`, `SYST:BEEP:STAT`

---

*Document généré à partir du manuel XDM1000 Digital Multimeter Programming Manual (OWON).*
