# Rapport de métriques de code

Application regroupant :

- **Tailles** : nombre de fichiers, tailles par extension et par dossier
- **Métriques Radon** : LOC, SLOC, complexité cyclomatique (CC), indice de maintenabilité (MI) par fichier et par fonction/classe
- **Cohésion** (optionnel) : si le package `cohesion` est installé, tentative d’intégration des scores de cohésion par classe
- **Rapport HTML** : index récapitulatif + une page par fichier Python (style htmlcov)

## Usage

Depuis la racine du projet (recommandé) :

```bash
python run_metrics.py
```

Ou directement depuis tools :

```bash
python tools/run_metrics_report.py
```

Options :

- `-o DIR`, `--output DIR` : dossier de sortie du rapport (défaut : `tools/code_metrics_report`)
- `--no-cohesion` : ne pas lancer l’analyse de cohésion
- `--no-html` : affichage terminal uniquement (pas de génération HTML)

## Dépendances

- **Requis** : `pip install radon`
- **Optionnel** (cohésion) : `pip install cohesion`

## Sortie

- **Terminal** : résumé par extension, par dossier, puis pour chaque fichier Python : MI, CC max, LOC
- **HTML** : `tools/code_metrics_report/index.html` + une page par fichier `.py` avec détail des blocs (fonctions, méthodes, classes) et complexité

Pour ouvrir le rapport : ouvrir `tools/code_metrics_report/index.html` dans un navigateur, ou lancer depuis la racine :

```bash
python serve_metrics.py
```

(Le serveur écoute sur le port 8766 pour ne pas conflit avec `serve_htmlcov.py` qui utilise 8765.)
