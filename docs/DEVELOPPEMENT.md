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

### 3.2 Structure cible

→ **Voir cahier des charges, § 2.2 (Structure de l'application)** et § 2.3 (Principes de modularité).

La structure détaillée (fichiers, rôles des modules) est définie dans le cahier des charges pour éviter la redondance.

### 3.3 Principes de développement — petits fichiers et classes par appareil

Le développement se fait en **petits fichiers**, avec des **classes distinctes pour chaque appareil de mesure** :

- **Une classe dédiée par appareil** : une (ou quelques) classe(s) par type d’équipement (multimètre OWON, générateur FY6900), dans des fichiers séparés. Chaque classe encapsule le protocole et les commandes de l’appareil.
- **Ces classes sont appelées pour piloter le banc de test** : le module de banc de test (ex. `filter_test.py`) **utilise** les classes multimètre et générateur ; il ne duplique pas la logique de communication. Il orchestre les deux appareils (balayage en fréquence, mesures, calculs) en s’appuyant sur leurs API.
- **Avantages** : code lisible, testable unitairement par appareil, réutilisation (commande individuelle dans l’UI + pilotage du banc).

**Exemple de chaîne d’appel :**
- `filter_test.py` (banc filtre) reçoit la config (f_min, f_max, etc.), crée ou reçoit les instances des classes **OwonMeter** (ou `ScpiProtocol` + `Measurement`) et **Fy6900Generator** (ou `Fy6900Protocol`), puis les **appelle** pour régler la fréquence, lancer une mesure, etc.
- Les vues UI (multimètre seul, générateur seul, banc filtre) s’appuient sur les mêmes classes d’appareils.

---

### 3.4 Liaisons série par classe, buffers, logging et threads

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
