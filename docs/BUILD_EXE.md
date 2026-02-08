# Créer l'exécutable Windows

L'application peut être distribuée sous forme d'un **exécutable unique** (.exe) grâce à PyInstaller. Le fichier `config.json` et le dossier `logs/` seront créés à côté de l'exécutable au premier lancement.

---

## Prérequis

- **Python 3.10+** avec l'environnement virtuel du projet activé
- Dépendances installées : `pip install -r requirements.txt`
- **PyInstaller** : `pip install pyinstaller`

---

## Génération de l'exécutable

À la racine du projet :

```powershell
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
pip install pyinstaller
pyinstaller BancTestAuto.spec
```

L'exécutable est produit dans le dossier **`dist/`** :

```
dist/
└── BancTestAuto.exe
```

---

## Premier lancement

1. Copiez `BancTestAuto.exe` (et éventuellement tout le dossier `dist/`) où vous voulez.
2. Lancez `BancTestAuto.exe`.
3. Au premier lancement, un fichier **`config.json`** est créé dans le même répertoire que l'exe (si vous enregistrez la configuration). Le dossier **`logs/`** est créé au même endroit pour les journaux d'application.
4. Utilisez **Outils → Détecter les équipements** pour identifier les ports du multimètre et du générateur, puis **Fichier → Sauvegarder config** pour enregistrer les ports.

---

## Fichiers inclus dans l'exécutable

- Thèmes (dark.qss, light.qss)
- Aide intégrée (AIDE.md, F1)
- Configuration par défaut (structure du config.json ; le fichier utilisé à l’exécution est à côté de l’exe)

---

## Dépannage

- **Antivirus** : certains antivirus peuvent bloquer un .exe généré par PyInstaller. Ajoutez une exception si nécessaire.
- **Erreur « Module not found »** : ajoutez le module manquant dans la section `hiddenimports` du fichier `BancTestAuto.spec`, puis relancez `pyinstaller BancTestAuto.spec`.
- **Config ou thème introuvable** : lancez l’exe depuis son propre répertoire (ne pas déplacer uniquement le .exe sans son dossier si vous utilisez un build « onedir » ; avec le spec fourni, un seul fichier .exe est généré).
