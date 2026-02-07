# Banc de test automatique

Application PyQt6 pour **commander individuellement** le multimètre OWON XDM et le générateur de signaux FeelTech FY6900, avec **l’ensemble des commandes implantées dans le matériel**. Configuration par défaut dans `config/config.json`. Le **banc de test filtre** permet de **caractériser un filtre au format Bode** (réponse en fréquence) avec un **balayage en fréquence modifiable** pour une **bonne qualification du filtre**.

## Fonctionnalités

- **Multimètre OWON** : pilotage individuel via SCPI (toutes les commandes : modes, plages, vitesse, fonctions math, etc.) — config par défaut dans `config.json`
- **Générateur FY6900** : pilotage individuel (forme d’onde, fréquence, amplitude, offset, sortie ON/OFF, etc.) — config par défaut dans `config.json`
- **Banc de test filtre** : caractérisation d’un filtre au format Bode ; balayage modifiable (f_min, f_max, N points, échelle, délai) pour qualifier le filtre ; tableau et courbe gain (dB) vs fréquence
- **Mode enregistrement** : logging longue durée avec graphique temps réel
- **Export** : CSV, graphiques semi-log pour impression
- **Sauvegarde JSON** : le logiciel permet de sauvegarder la configuration en fichier JSON (`config/config.json` ou autre)

## Démarrage rapide

```bash
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## Documentation

| Document | Description |
|----------|-------------|
| [Cahier des charges](docs/CAHIER_DES_CHARGES.md) | Spécifications complètes |
| [Guide de développement](docs/DEVELOPPEMENT.md) | Environnement, Git, arborescence |
| [Banc de test filtre](docs/BANC_TEST_FILTRE.md) | Caractérisation filtre format Bode, balayage modifiable, qualification |

## Matériel

- Multimètre OWON XDM1041/XDM2041 (SCPI)
- Générateur FeelTech FY6900 (optionnel, banc filtre)
