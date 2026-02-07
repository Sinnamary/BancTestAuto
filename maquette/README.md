# Maquette interface — Banc de test automatique

Ce répertoire contient **uniquement l’interface PyQt6** du banc de test, sans logique métier (pas de liaison série, pas de SCPI, pas de protocole FY6900). Il permet de **définir et valider l’ergonomie et le layout** avant d’intégrer l’interface dans le logiciel principal.

---

## Objectif

1. **Développer l’interface** dans `maquette/` avec des données factices.
2. **Valider** la maquette (disposition, onglets, dialogues, thème).
3. **Intégrer** le code validé dans le projet principal en le connectant au `core/` et à la config.

L’arborescence sous `maquette/ui/` **reproduit celle prévue** pour le projet (`ui/main_window.py`, `ui/widgets/`, `ui/views/`, `ui/dialogs/`), afin que l’intégration consiste à déplacer ces fichiers et à brancher les signaux sur la couche métier.

---

## Structure

```
maquette/
├── README.md                 # Ce fichier
├── main_maquette.py          # Point d’entrée (lance uniquement l’interface)
├── ui/
│   ├── __init__.py
│   ├── main_window.py        # QMainWindow, menu, barre connexion, onglets
│   ├── widgets/              # Widgets réutilisables (connexion, affichage, etc.)
│   │   ├── __init__.py
│   │   └── connection_status.py
│   ├── views/                # Contenu de chaque onglet
│   │   ├── __init__.py
│   │   ├── meter_view.py
│   │   ├── generator_view.py
│   │   ├── logging_view.py
│   │   └── filter_test_view.py
│   └── dialogs/
│       ├── __init__.py
│       ├── serial_config_dialog.py
│       └── save_config_dialog.py
└── resources/                # Optionnel : thèmes, icônes pour la maquette
    └── themes/
```

---

## Lancer la maquette

Depuis la racine du projet (avec le même environnement que le logiciel) :

```bash
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
python maquette/main_maquette.py

# Linux / macOS
source .venv/bin/activate
python maquette/main_maquette.py
```

Les dépendances sont celles du projet (`PyQt6` dans `requirements.txt`). Aucun module `core/` ou `config/` n’est importé.

---

## Données factices

- **Barre de connexion :** texte fixe « Multimètre: XDM2041 — COM3 », « Générateur: FY6900 — COM4 » (ou « Non connecté »). Le bouton « Paramètres » ouvre un dialogue sans ouvrir de port.
- **Onglet Multimètre :** valeurs d’affichage simulées (ex. « 12.345 V »), listes de plages en dur, pas d’appel SCPI.
- **Onglet Générateur :** champs éditables, pas d’envoi de commandes.
- **Onglet Enregistrement :** graphique vide ou courbe factice, pas d’écriture CSV.
- **Onglet Banc filtre :** tableau et graphique vides ou avec quelques points factices.

---

## Intégration dans le logiciel principal

Une fois la maquette validée :

1. **Copier** le contenu de `maquette/ui/` vers `BancTestAuto/ui/` (en écrasant ou en fusionnant si des fichiers existent déjà).
2. **Adapter** les imports si le point d’entrée n’est plus `maquette` (ex. `from ui.main_window` au lieu de chemins relatifs à la maquette).
3. **Connecter** les signaux des widgets au `core/` :
   - Barre de connexion → `SerialConnection`, chargement/sauvegarde config.
   - Onglet Multimètre → `Measurement`, `ScpiProtocol`, etc.
   - Onglet Générateur → `Fy6900Protocol`.
   - Onglet Enregistrement → `DataLogger`.
   - Onglet Banc filtre → `FilterTest`.
4. **Remplacer** l’appel dans `main.py` : créer la fenêtre avec `MainWindow` (charger `config.json` au démarrage, connecter les appareils).

Les widgets et vues restent les mêmes ; seules les connexions (signaux/slots, injection des classes métier) sont ajoutées.

---

## Références

- [Conception interface PyQt6](../docs/INTERFACE_PYQT6.md) — détail des widgets et des zones.
- [Guide de développement §3](../docs/DEVELOPPEMENT.md) — arborescence cible du projet et rôles des modules.
