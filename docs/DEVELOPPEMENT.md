# Guide de développement — Banc de test automatique

**Dernière mise à jour :** 6 février 2025

Le développement s’effectue en **petits fichiers**, avec des **classes distinctes pour chaque appareil de mesure** (multimètre OWON, générateur FY6900). Ces classes sont **appelées pour piloter le banc de test** (ex. caractérisation filtre) : le module banc n’orchestre que les appels aux classes d’appareils, sans dupliquer leur logique.

---

## 1. Environnement virtuel Python

### 1.1 Emplacement

L'environnement virtuel se trouve dans le dossier **`.venv`** à la racine du projet :

```
BancTestAuto/
└── .venv/           # Environnement virtuel (ignoré par Git)
```

### 1.2 Activation

**Windows (PowerShell) :**
```powershell
cd c:\pa\CursorAI\BancTestAuto
.\.venv\Scripts\Activate.ps1
```

**Windows (CMD) :**
```cmd
cd c:\pa\CursorAI\BancTestAuto
.venv\Scripts\activate.bat
```

**Linux / macOS :**
```bash
cd /chemin/vers/BancTestAuto
source .venv/bin/activate
```

### 1.3 Vérification

```bash
python --version    # Python 3.13.x
pip --version      # pip 25.x
```

### 1.4 Création (si nécessaire)

```powershell
cd c:\pa\CursorAI\BancTestAuto
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 1.5 Dépendances

Les paquets sont listés dans `requirements.txt`. Installation :

```bash
pip install -r requirements.txt
```

Paquets prévus pour le projet :
- `PyQt6` — interface graphique
- `pyserial` — liaison série
- `pyqtgraph` ou `matplotlib` — graphiques (mode enregistrement)

---

## 2. Git local

### 2.1 Dépôt

- **Emplacement :** `c:\pa\CursorAI\BancTestAuto`
- **Type :** dépôt Git local (pas de remote configuré par défaut)
- **Branche par défaut :** `master`

### 2.2 Commandes utiles

```bash
# Statut
git status

# Ajouter des fichiers
git add .
git add <fichier>

# Commit
git commit -m "Message descriptif"

# Historique
git log --oneline

# Vérifier la configuration
git config --list --local
```

### 2.3 Premier commit (déjà effectué)

Commit initial : `Initial commit - Banc de test automatique`

### 2.4 Fichiers suivis / ignorés

Le fichier `.gitignore` exclut notamment :
- `.venv/` — environnement virtuel
- `__pycache__/` — cache Python
- `.idea/`, `.vscode/` — config IDE
- `*.log` — fichiers de log

---

## 3. Arborescence du projet

### 3.1 Structure actuelle

```
BancTestAuto/
├── .git/                    # Dépôt Git (interne)
├── .gitignore               # Fichiers ignorés par Git
├── .venv/                   # Environnement virtuel Python (ignoré)
├── config/
│   └── config.json          # Config par défaut : multimètre, générateur, banc filtre
├── docs/
│   ├── BANC_TEST_FILTRE.md  # Caractérisation filtre format Bode, balayage modifiable
│   ├── CAHIER_DES_CHARGES.md # Spécifications complètes du projet
│   ├── DEVELOPPEMENT.md     # Ce fichier — guide développeur
│   ├── FY6900_communication_protocol.pdf
│   └── XDM1000_Digital_Multimeter_Programming_Manual.pdf
├── requirements.txt         # Dépendances Python
└── README.md
```

### 3.2 Structure cible — Arborescence complète (décomposition maximale)

L’objectif est **petits fichiers** et **classes facilement réutilisables** : un fichier = une responsabilité, une classe (ou un petit groupe cohérent) par fichier. Si un module dépasse ~200 lignes, le découper en sous-modules.

```
BancTestAuto/
├── main.py
│
├── core/                          # Logique métier, protocoles, orchestration
│   ├── __init__.py
│   ├── serial_connection.py       # Classe SerialConnection : un port, buffers, log échanges
│   ├── scpi_protocol.py           # Classe ScpiProtocol : envoi/réception SCPI (utilise SerialConnection)
│   ├── scpi_commands.py           # Constantes et chaînes SCPI (CONF:VOLT:DC, MEAS?, etc.)
│   ├── measurement.py             # Classe Measurement : logique mesures OWON (utilise ScpiProtocol)
│   ├── owon_ranges.py              # Plages par mode (listes, valeurs SCPI) — données réutilisables
│   ├── fy6900_protocol.py         # Classe Fy6900Protocol : commandes WMW, WMF, WMA, WMN (utilise SerialConnection)
│   ├── fy6900_commands.py         # Format des commandes FY6900 (WMF 14 chiffres, etc.) — helpers
│   ├── data_logger.py             # Classe DataLogger : enregistrement CSV horodaté
│   ├── filter_test.py             # Classe FilterTest : orchestration banc filtre (appelle Measurement + Fy6900Protocol)
│   ├── filter_sweep.py            # Génération liste de fréquences (log/lin), pas de balayage
│   └── bode_calc.py               # Calculs gain linéaire, gain dB (20*log10) — réutilisable sans UI
│
├── config/
│   ├── __init__.py
│   ├── settings.py                # Chargement / sauvegarde config (config.json), valeurs par défaut
│   └── config.json                # Fichier de configuration (valeurs par défaut)
│
├── ui/                            # Interface PyQt6
│   ├── __init__.py
│   ├── main_window.py             # Fenêtre principale : onglets, barre outil, orchestration des vues
│   │
│   ├── widgets/                   # Widgets réutilisables (un fichier = une classe ou un petit groupe)
│   │   ├── __init__.py
│   │   ├── measurement_display.py # Affichage principal type LCD (valeur + unité)
│   │   ├── mode_button.py         # Bouton de mode (V⎓, V~, Ω, etc.) — réutilisable
│   │   ├── mode_bar.py            # Barre de boutons de mode (compose plusieurs ModeButton)
│   │   ├── range_selector.py      # Sélecteur plage : Auto / Manuel + liste déroulante
│   │   ├── rate_selector.py       # Vitesse mesure : Rapide / Moyen / Lent (boutons radio ou liste)
│   │   ├── math_panel.py          # Panneau fonctions math : Rel, dB, dBm, Moyenne + champs
│   │   ├── history_table.py       # Tableau des N dernières mesures + Export CSV
│   │   ├── connection_status.py   # Indicateur connexion (vert/rouge) + modèle + port
│   │   ├── secondary_display.py   # Affichage secondaire (ex. fréquence Hz)
│   │   └── advanced_params.py     # Panneau repliable : température, continuité, buzzer
│   │
│   ├── dialogs/
│   │   ├── __init__.py
│   │   ├── serial_config_dialog.py # Dialogue port, débit, timeouts (multimètre ou générateur)
│   │   └── save_config_dialog.py  # Sauvegarde configuration JSON (fichier, « Enregistrer sous »)
│   │
│   ├── views/                     # Vues composites (assemblent des widgets)
│   │   ├── __init__.py
│   │   ├── meter_view.py          # Vue principale multimètre (modes, affichage, plage, maths, historique)
│   │   ├── generator_view.py      # Vue générateur FY6900 (forme, fréquence, amplitude, offset, ON/OFF)
│   │   ├── logging_view.py        # Vue mode enregistrement : config, graphique temps réel, Démarrer/Arrêter
│   │   ├── filter_test_view.py    # Vue banc filtre : config balayage + tableau + graphique Bode
│   │   ├── filter_config_panel.py # Panneau config balayage (f_min, f_max, N points, échelle, délai, Ue)
│   │   ├── filter_results_table.py# Tableau résultats : f | Us | Us/Ue | Gain (dB)
│   │   └── bode_plot_widget.py    # Widget graphique Bode (semi-log, gain dB vs fréquence) — réutilisable
│   │
│   └── (optionnel) mixins/
│       └── __init__.py            # Mixins UI si besoin (ex. ExportMixin pour CSV)
│
├── resources/                     # Ressources statiques
│   ├── icons/                    # Icônes (modes, connexion, etc.)
│   └── themes/                   # Feuilles de style (dark, light)
│
├── docs/
│   ├── BANC_TEST_FILTRE.md
│   ├── CAHIER_DES_CHARGES.md
│   ├── DEVELOPPEMENT.md
│   ├── FY6900_communication_protocol.pdf
│   └── XDM1000_Digital_Multimeter_Programming_Manual.pdf
│
├── .gitignore
├── .venv/                         # (ignoré)
├── requirements.txt
└── README.md
```

### 3.3 Rôle des modules (référence rapide)

| Fichier | Rôle principal | Réutilisable par |
|---------|----------------|------------------|
| **core/serial_connection.py** | Une liaison série (port, buffers, log). Pas de protocole. | ScpiProtocol, Fy6900Protocol |
| **core/scpi_protocol.py** | Envoi/réception SCPI (write/read). Dépend de SerialConnection. | Measurement, toute commande OWON |
| **core/scpi_commands.py** | Constantes SCPI (chaînes). Aucune I/O. | scpi_protocol, measurement, UI (libellés) |
| **core/measurement.py** | Logique mesures (mode, plage, MEAS?). Utilise ScpiProtocol. | meter_view, filter_test |
| **core/owon_ranges.py** | Données plages par mode (listes, valeurs SCPI). | measurement, range_selector |
| **core/fy6900_protocol.py** | Protocole FY6900 (WMW, WMF, WMA, WMN). Utilise SerialConnection. | generator_view, filter_test |
| **core/fy6900_commands.py** | Format commandes (ex. WMF 14 chiffres). Aucune I/O. | fy6900_protocol |
| **core/data_logger.py** | Écriture CSV horodaté (timestamp, value, unit, mode). | logging_view |
| **core/filter_test.py** | Orchestration : balayage, réglage FY6900, mesure OWON, calcul gain. | filter_test_view |
| **core/filter_sweep.py** | Génération liste f[] (log/lin). Pur calcul. | filter_test |
| **core/bode_calc.py** | Gain linéaire, gain dB. Pur calcul. | filter_test, bode_plot_widget |
| **config/settings.py** | Charger/sauver config.json, appliquer défauts. | main_window, toute vue |
| **ui/main_window.py** | Fenêtre principale, onglets (multimètre, générateur, logging, banc filtre). | main.py |
| **ui/widgets/measurement_display.py** | Affichage valeur + unité (style LCD). | meter_view, logging_view |
| **ui/widgets/mode_button.py** | Un bouton de mode (état actif/inactif). | mode_bar |
| **ui/widgets/mode_bar.py** | Barre de boutons de mode (compose ModeButton). | meter_view |
| **ui/widgets/range_selector.py** | Auto/Manuel + liste plages. | meter_view |
| **ui/widgets/rate_selector.py** | Rapide / Moyen / Lent. | meter_view |
| **ui/widgets/math_panel.py** | Rel, dB, dBm, Moyenne + champs. | meter_view |
| **ui/widgets/history_table.py** | Tableau mesures + Export CSV. | meter_view |
| **ui/widgets/connection_status.py** | Indicateur connexion + port. | main_window |
| **ui/widgets/secondary_display.py** | Affichage secondaire (Hz). | meter_view |
| **ui/widgets/advanced_params.py** | Panneau repliable (temp, continuité, buzzer). | meter_view |
| **ui/dialogs/serial_config_dialog.py** | Config port série (port, débit, timeouts). | main_window, meter_view |
| **ui/dialogs/save_config_dialog.py** | Sauvegarde config JSON (chemin, « Enregistrer sous »). | main_window |
| **ui/views/meter_view.py** | Vue complète multimètre (compose widgets). | main_window |
| **ui/views/generator_view.py** | Vue complète générateur FY6900. | main_window |
| **ui/views/logging_view.py** | Vue enregistrement (config + graphique + contrôles). | main_window |
| **ui/views/filter_test_view.py** | Vue banc filtre (config + tableau + Bode). | main_window |
| **ui/views/filter_config_panel.py** | Panneau f_min, f_max, N, échelle, délai, Ue. | filter_test_view |
| **ui/views/filter_results_table.py** | Tableau f | Us | Us/Ue | Gain dB. | filter_test_view |
| **ui/views/bode_plot_widget.py** | Graphique Bode semi-log (réutilisable). | filter_test_view, export image |

### 3.4 Principes de développement — petits fichiers et classes par appareil

Le développement se fait en **petits fichiers**, avec des **classes distinctes pour chaque appareil de mesure** :

- **Une classe dédiée par appareil** : une (ou quelques) classe(s) par type d’équipement (multimètre OWON, générateur FY6900), dans des fichiers séparés. Chaque classe encapsule le protocole et les commandes de l’appareil.
- **Ces classes sont appelées pour piloter le banc de test** : le module de banc de test (ex. `filter_test.py`) **utilise** les classes multimètre et générateur ; il ne duplique pas la logique de communication. Il orchestre les deux appareils (balayage en fréquence, mesures, calculs) en s’appuyant sur leurs API.
- **Avantages** : code lisible, testable unitairement par appareil, réutilisation (commande individuelle dans l’UI + pilotage du banc).

**Exemple de chaîne d’appel :**
- `filter_test.py` (banc filtre) reçoit la config (f_min, f_max, etc.), crée ou reçoit les instances **Measurement** (ScpiProtocol) et **Fy6900Protocol**, puis les **appelle** pour régler la fréquence, lancer une mesure, etc.
- Les vues UI (multimètre seul, générateur seul, banc filtre) s’appuient sur les mêmes classes d’appareils.

---

### 3.5 Liaisons série par classe, buffers, logging et threads

Les **liaisons série sont programmées par classe** (une classe dédiée par port, ex. `SerialConnection`), avec les points suivants.

- **Une classe par liaison** : chaque port série est géré par une instance d'une classe dédiée (même classe, instanciée par port). Pas d'accès direct au port dans les couches protocole (SCPI, FY6900).
- **Paramètres JSON et paramètres par défaut** : chaque liaison série de chaque appareil a ses paramètres dans le fichier JSON (`serial_multimeter`, `serial_generator`). Les classes reprennent ces paramètres à l'initialisation ; elles définissent aussi des paramètres par défaut (dans le code). Si une clé manque dans le JSON, la valeur par défaut de la classe est utilisée. **Le logiciel doit permettre de sauvegarder un JSON** : enregistrement de la configuration complète (bouton ou menu dédié, fichier par défaut `config/config.json`, option « Enregistrer sous » possible). Voir cahier des charges § 2.7.
- **Buffers** : prévoir des tampons d'entrée et de sortie (taille adaptée au débit et aux trames) pour découpler lecture/écriture et traitement, et limiter les pertes de données.
- **Possibilité d'arrêter de logger les échanges** : une option (configurable dans `config.json`, clés `serial_multimeter.log_exchanges` et `serial_generator.log_exchanges`, et/ou dans l'interface) permet d'activer ou désactiver l'enregistrement des trames envoyées et reçues. Quand le log est désactivé, aucun tracé des échanges ; quand il est activé, les échanges peuvent être écrits vers un fichier ou une fenêtre de debug. À désactiver en production pour éviter surcharge et fuites d'informations.

**Utilisation de threads — recommandation :** l'**usage de threads est optimal** pour les I/O série avec PyQt6 :

- Les opérations série (read/write) sont **bloquantes**. Si elles s'exécutent dans le thread de l'interface, l'UI se fige pendant les échanges et les timeouts.
- **Solution recommandée** : exécuter les I/O série dans un **thread dédié** (ex. **QThread** ou worker PyQt6). Le worker ouvre le port, lit et écrit ; il communique avec le thread principal via **signaux/slots** (données reçues, erreur, état de connexion). La classe série peut vivre dans le thread worker ou être appelée depuis celui-ci.
- **Bénéfices** : interface restant réactive, pas de blocage pendant les timeouts, mesure continue et banc de test fluides. Voir aussi cahier des charges § 2.5 et 2.6.

---

## 4. Lancer le projet

Une fois le point d’entrée `main.py` créé à la racine du projet :

```bash
.\.venv\Scripts\Activate.ps1
python main.py
```

---

## 5. Références

| Document | Rôle |
|----------|------|
| **Cahier des charges** (`CAHIER_DES_CHARGES.md`) | Spécifications fonctionnelles, structure cible, ergonomie, config détaillée |
| **Banc de test filtre** (`BANC_TEST_FILTRE.md`) | Caractérisation filtre format Bode, balayage modifiable pour qualification |
| **Manuel SCPI OWON** (`XDM1000_Digital_Multimeter_Programming_Manual.pdf`) | Commandes SCPI du multimètre |
| **Manuel FY6900** (`FY6900_communication_protocol.pdf`) | Protocole FeelTech générateur |
| **Configuration** (`config/config.json`) | Paramètres par défaut ; **le logiciel doit permettre de sauvegarder un JSON** (configuration complète vers ce fichier ou un autre) |
