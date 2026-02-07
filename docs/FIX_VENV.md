# Corriger le venv (erreur « Fatal error in launcher »)

Si `pip install -r requirements.txt` affiche :

```text
Fatal error in launcher: Unable to create process using '"…\\.venv\\Scripts\\python.exe" ...': Le fichier spécifié est introuvable.
```

c’est que le `.venv` a été créé ou copié depuis un autre projet : les launchers `pip.exe` / `python.exe` pointent encore vers l’ancien chemin. Il faut **recréer** l’environnement virtuel dans BancTestAuto.

## Étapes (PowerShell, à la racine du projet)

1. **Désactiver** le venv (optionnel) : `deactivate`

2. **Supprimer** l’ancien `.venv` :
   ```powershell
   Remove-Item -Recurse -Force .venv
   ```

3. **Créer** un nouveau venv (sans pip si `ensurepip` pose problème) :
   ```powershell
   py -m venv .venv --without-pip
   ```
   Si besoin : `python -m venv .venv --without-pip`

4. **Installer pip** dans le venv :
   ```powershell
   .\.venv\Scripts\python.exe -m ensurepip --upgrade
   ```

5. **Activer** le venv :
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

6. **Installer les dépendances** (préférer `python -m pip` pour éviter le launcher) :
   ```powershell
   python -m pip install -r requirements.txt
   ```

Ensuite `python main.py` et `pytest` utilisent bien le Python de `BancTestAuto\.venv`. Si `pip install ...` échoue encore, utiliser systématiquement **`python -m pip install ...`**.
