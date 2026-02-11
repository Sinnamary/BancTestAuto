# Aide — Banc de test automatique

Bienvenue dans l’aide du **Banc de test automatique**. Cette application permet de piloter un **multimètre OWON** (XDM1041/XDM2041) et un **générateur de signaux FeelTech FY6900** et une **alimentation Rockseed RS305P**, de configurer des mesures, d’enregistrer des données et de caractériser un filtre au format Bode.

---

## Sommaire

1. [Démarrage rapide](#démarrage-rapide)
2. [Connexion des équipements](#connexion-des-équipements)
3. [Onglet Multimètre](#onglet-multimètre)
4. [Onglet Générateur](#onglet-générateur)
5. [Onglet Enregistrement](#onglet-enregistrement)
6. [Onglet Banc filtre](#onglet-banc-filtre)
7. [Onglet Alimentation](#onglet-alimentation)
8. [Onglet Terminal série](#onglet-terminal-série)
9. [Configuration et thème](#configuration-et-thème)
10. [Raccourcis clavier](#raccourcis-clavier)
11. [Fichiers et export](#fichiers-et-export)
12. [Dépannage](#dépannage)

---

## Démarrage rapide

1. **Branchez** le multimètre et le générateur en USB (ports COM sous Windows, `/dev/ttyUSBx` sous Linux).
2. Lancez l’application : `python main.py` (après activation du venv et `pip install -r requirements.txt`).
3. Ouvrez le menu **Outils → Détecter les équipements** (ou cliquez sur **Détecter** dans la barre de connexion) pour identifier automatiquement les ports du multimètre et du générateur.
4. **Aucun port n'est ouvert au démarrage** : cliquez sur **Détecter** puis **Connecter tout** pour connecter le multimètre et le générateur. Une fois les pastilles **vertes**, vous pouvez utiliser chaque onglet (Multimètre, Générateur, Enregistrement, Banc filtre, Alimentation, Terminal série).

**Prérequis :** Python 3.10+, PyQt6, pyserial. Voir `requirements.txt`.

---

## Connexion des équipements

### Barre de connexion

En haut de la fenêtre, **quatre pastilles** indiquent (Multimètre, Générateur, Alimentation, Oscilloscope) l’état de connexion :

- **Vert** : équipement détecté et connecté (modèle et port affichés).
- **Rouge** : non connecté ou non détecté.

**Boutons** : **Détecter** (en premier, mis en avant) lance la détection des 4 équipements ; **Connecter tout** relit la config et ouvre les connexions ; **Déconnecter tout** ferme toutes les connexions. Il n'y a plus de bouton Paramètres : les ports se modifient via `config.json` ou Fichier → Ouvrir config.

### Détection automatique

- **Menu : Outils → Détecter les équipements** (ou bouton Détecter).
- L’application parcourt les ports COM disponibles et envoie des commandes de test :
  - **Multimètre OWON** : commande SCPI `*IDN?` ; si la réponse contient « OWON » ou « XDM », le port est retenu.
  - **Générateur FY6900** : test du protocole FeelTech ; si la réponse est cohérente, le port est retenu.
- Les champs **Port multimètre** et **Port générateur** dans la configuration sont alors mis à jour. Pensez à **sauvegarder la configuration** (Fichier → Sauvegarder config) pour conserver les ports au prochain lancement.

### Configuration série

Les ports et débits sont dans **`config/config.json`**. Pour modifier :

- **Port** : COM3, COM4, etc. (Windows) ou /dev/ttyUSB0, etc. (Linux).
- **Débit** : 9600 pour l’OWON (ou 115200 selon modèle), 115200 pour le FY6900.
- **Timeouts** : lecture et écriture (en secondes).

Les changements sont pris en compte après validation. Enregistrez la config pour les conserver.

---

## Onglet Multimètre

Vue principale pour piloter le **multimètre OWON** : modes de mesure, plage, vitesse, affichage, fonctions math, historique.

### Modes de mesure

Sélectionnez le mode avec les boutons : **V⎓** (tension DC), **V~** (tension AC), **A⎓** (courant DC), **A~** (courant AC), **Ω** (résistance 2 fils), **Ω 4W** (résistance 4 fils), **Hz**, **s** (période), **F** (capacité), **°C** (température RTD), **Diode**, **Continuité**. Un seul mode est actif à la fois.

### Plage et vitesse

- **Plage** : **Auto** (recommandé) ou **Manuel** avec choix de la plage dans la liste (adaptée au mode).
- **Vitesse** : **Rapide**, **Moyenne** ou **Lente** (influence la précision et le temps de mesure).

### Mesure unique et mesure continue

- **Mesure** (ou **F5**) : une mesure immédiate ; la valeur s’affiche dans la zone principale.
- **Mesure continue** (ou **Ctrl+M**) : rafraîchissement périodique selon l’intervalle défini dans la configuration (ex. 500 ms). Utilisez à nouveau **Ctrl+M** pour arrêter.

### Reset

Le bouton **Reset (*RST)** (ou **Ctrl+R**) envoie la commande SCPI `*RST` et remet le multimètre à ses valeurs par défaut.

### Affichage secondaire

En mode tension ou courant, une case **Afficher Hz** permet d’afficher la fréquence (mesure secondaire) en plus de la valeur principale.

### Fonctions mathématiques

- **Aucun** : valeur brute.
- **Rel** : valeur relative (offset réglable).
- **dB** / **dBm** : avec référence en Ω (liste prédéfinie).
- **Moyenne** : statistiques (min, max, moyenne, nombre) avec bouton pour réinitialiser les stats.

### Historique et export

Les dernières mesures apparaissent dans un **tableau**. Le bouton **Exporter CSV** (ou **Ctrl+E**) enregistre l’historique dans un fichier CSV.

---

## Onglet Générateur

Pilotage du **générateur FeelTech FY6900** : choix de la **voie (1 ou 2)**, forme d’onde (Sinusoïde, Triangle, Carré, Dent de scie — codes FY6900 : 0, 7, 1, 8 ; format WMWxx 2 chiffres), fréquence (envoyée en µHz, 14 chiffres), amplitude, offset, rapport cyclique, phase, sortie ON/OFF. Le logiciel lit la réponse (0x0a) après chaque commande avant la suivante. Valeurs par défaut dans `config.json`. Voir [Commandes FY6900](COMMANDES_FY6900.md).

---

## Onglet Terminal série

L'onglet **n'a pas de connexion propre** : il utilise la connexion d'un équipement **déjà connecté** via la barre (Connecter tout). Choisissez l'équipement dans la liste déroulante (Multimètre, Générateur, Alimentation, Oscilloscope) : seuls les équipements connectés sont proposés. Envoi et réception se font sur la connexion de l'équipement sélectionné. Cases à cocher **CR** et **LF** pour la fin de chaîne. Tous les échanges TX/RX sont enregistrés dans le fichier **`serial_AAAA-MM-JJ_HH-MM-SS.log`** (dossier `logs/`), avec l'équipement indiqué une fois au changement de sélection.

---

## Onglet Enregistrement

Mode **enregistrement longue durée** des mesures du multimètre uniquement.

- **Configuration** : intervalle entre deux mesures (ex. 5 s), durée totale ou illimitée, mode de mesure, dossier de sortie (par défaut `./logs`).
- **Fichiers** : CSV horodatés (timestamp, valeur, unité, mode). Nom du type `owon_log_AAAA-MM-JJ_HH-MM-SS.csv`.
- **Graphique** : courbe **valeur = f(temps)** en temps réel pendant l’enregistrement.
- **Relecture** : chargement d’un fichier CSV existant pour afficher la courbe.
- **Comparaison** : superposition de plusieurs courbes (plusieurs fichiers) sur le même graphique.

Boutons : **Démarrer**, **Arrêter**, **Mettre en pause**, **Charger un fichier**, **Comparer**, **Exporter image**.

---

## Onglet Banc filtre

Caractérisation d’un **filtre au format Bode** (réponse en fréquence).

- **Principe** : le générateur FY6900 envoie une sinusoïde à tension fixe (Ue) sur l’entrée du filtre ; le multimètre mesure la tension de sortie (Us). Le logiciel balaie les fréquences et calcule le gain (Us/Ue) en dB.
- **Configuration** : voie du générateur (1 ou 2), **f_min**, **f_max**, nombre de points, échelle **lin** ou **log**, délai de stabilisation (ms), tension Ue (V RMS).
- **Résultats** : tableau (fréquence, Us, gain linéaire, gain dB) et **graphique Bode** (gain dB vs fréquence, axe fréquentiel lin ou log). Export CSV et export du graphique possible.

Au démarrage d’un balayage, la configuration générateur (forme d’onde, amplitude, offset) est appliquée depuis `config.json` pour un état reproductible.

---

## Onglet Alimentation

Pilotage de l'**alimentation stabilisée Rockseed RS305P** (protocole Modbus RTU). L'onglet **utilise la connexion déjà établie** par la barre (bouton **Connecter tout**) : aucun bloc « Connexion série » dans l'onglet. Le port est défini dans `config.json` (section `serial_power_supply`) et est affecté par la détection.

### Paramètres et sortie

- **Tension (V)** et **Courant (A)** : spinboxes pour définir les valeurs cibles (0–30 V, 0–5 A). Cliquez sur **Appliquer** pour envoyer à l'alimentation.
- **Préréglages** : boutons rapides **3,3 V**, **5 V**, **9 V**, **12 V** (chaque bouton règle 0,5 A et met la sortie OFF).
- **Sortie ON/OFF** : active ou coupe la sortie de l'alimentation.

### Valeurs mesurées

- **Rafraîchir** : lit la tension et le courant affichés par l'alimentation pour mettre à jour l'affichage.

Voir [Commandes RS305P](COMMANDES_RS305P.md) pour le détail du protocole Modbus.

---

## Configuration et thème

### Fichier de configuration

Tous les réglages sont centralisés dans **`config/config.json`** (ports série, mesure, affichage, logging, générateur, banc filtre). L’application charge ce fichier au démarrage.

- **Fichier → Ouvrir config...** : charger un autre fichier JSON.
- **Fichier → Sauvegarder config** : enregistrer dans `config/config.json`.
- **Fichier → Enregistrer config sous...** : enregistrer dans un autre fichier.
- **Fichier → Voir config JSON (lecture seule)** : afficher le contenu actuel sans le modifier.

### Thème d’affichage

- **Configuration → Thème → Clair** ou **Foncé** : changement immédiat de l’apparence.
- Pour **conserver** le thème au prochain lancement : après avoir choisi Clair ou Foncé, faites **Fichier → Sauvegarder config**. La valeur est stockée dans `display.theme` (`"light"` ou `"dark"`). Fichiers de style : `resources/themes/light.qss` et `dark.qss`.

### Police d'affichage

La police de l'interface (menus, libellés, graphique Bode) est définie dans **`config.json`** sous **`display.font_family`** (ex. `"Segoe UI"`, `"Arial"`). Par défaut : `"Segoe UI"` (recommandé sous Windows). Pour changer : éditez le fichier puis **Fichier → Sauvegarder config** ; le changement s'applique au prochain lancement.

### Niveau de log

**Configuration → Niveau de log** : DEBUG, INFO, WARNING, ERROR. Utile pour le dépannage. Pensez à sauvegarder la config pour conserver le niveau.

---

## Raccourcis clavier

| Raccourci | Action |
|-----------|--------|
| **F1** | Aide (manuel utilisateur avec recherche) |
| **F5** | Mesure unique (onglet Multimètre) |
| **Ctrl+M** | Mesure continue ON/OFF (onglet Multimètre) |
| **Ctrl+R** | Reset *RST (onglet Multimètre) |
| **Ctrl+E** | Export CSV (onglet Multimètre, historique) |

Les raccourcis agissent sur l’onglet **Multimètre** lorsqu’il est actif.

---

## Fichiers et export

- **Configuration** : JSON (config.json ou « Enregistrer sous »).
- **Historique multimètre** : CSV (Export CSV).
- **Enregistrement** : CSV horodatés dans le dossier configuré (ex. `./logs`).
- **Banc filtre** : CSV des points (f, Us, gain) et export du graphique Bode.

Tous les exports CSV et graphiques sont adaptés à une utilisation ultérieure (tableur, rapport, impression).

---

## Dépannage

### Les pastilles restent rouges

- Vérifiez que les câbles USB sont bien branchés et que les appareils sont sous tension.
- Lancez **Outils → Détecter les équipements** (ou **Détecter**). Si aucun port n’est trouvé, vérifiez les pilotes (Windows : Gestionnaire de périphériques ; Linux : droits sur `/dev/ttyUSBx`).
- Vérifiez dans `config.json` (ou **Fichier → Voir config JSON**) que les ports et débits correspondent au matériel (OWON souvent 115200, FY6900 115200, RS305P 9600).

### Erreur SCPI ou timeout

- Augmentez le **timeout** dans les sections série de `config.json` si nécessaire.
- Vérifiez qu’aucun autre logiciel n’utilise le même port COM.
- En cas de mesure très lente, passez en vitesse **Rapide** ou réduisez l’intervalle de rafraîchissement dans la config.

### Le générateur ne répond pas

- FY6900 utilise le débit **115200** et la fin de ligne **LF** (0x0a). Vérifiez la configuration série.
- Assurez-vous que le bon port a été affecté après la détection.

### Où sont les logs ?

- **`logs/app_AAAA-MM-JJ_HH-MM-SS.log`** : log général de l'application (démarrage, détection, connexions, erreurs). Créé au lancement.
- **`logs/serial_AAAA-MM-JJ_HH-MM-SS.log`** : log **uniquement** des échanges de l'onglet **Terminal série** (TX/RX), avec l'équipement connecté indiqué une fois au changement de sélection. Créé au premier choix d'équipement ou premier envoi/réception dans le terminal.
- Le chemin des logs est configurable dans `config.json` (section `logging.output_dir`). Le niveau (DEBUG, INFO, etc.) se règle dans **Configuration → Niveau de log**.

### Documentation complète

- **Cahier des charges** : `docs/CAHIER_DES_CHARGES.md`
- **Banc de test filtre** : `docs/BANC_TEST_FILTRE.md`
- **Guide de développement** : `docs/DEVELOPPEMENT.md`
- **Commandes RS305P** : `docs/COMMANDES_RS305P.md`
- **README** : `README.md` à la racine du projet

---

*Banc de test automatique — Aide intégrée. Pour toute question sur le matériel, consulter les manuels OWON (XDM1000), FeelTech (FY6900) et Rockseed (RS305P Modbus).*
