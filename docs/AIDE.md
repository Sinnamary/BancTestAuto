# Aide — Banc de test automatique

Bienvenue dans l’aide du **Banc de test automatique**. Cette application permet de piloter un **multimètre OWON** (XDM1041/XDM2041) et un **générateur FeelTech FY6900**, une **alimentation Rockseed RS305P** et un **oscilloscope Hanmatek DOS1102**, de configurer des mesures, d’enregistrer des données, de caractériser un filtre au format Bode et de calculer les composants de filtres (RC, RLC, Pont de Wien, etc.).

---

## Sommaire

1. [Démarrage rapide](#démarrage-rapide)
2. [Connexion des équipements](#connexion-des-équipements)
3. [Onglet Multimètre](#onglet-multimètre)
4. [Onglet Générateur](#onglet-générateur)
5. [Onglet Oscilloscope](#onglet-oscilloscope)
6. [Onglet Banc filtre](#onglet-banc-filtre)
7. [Onglet Calcul filtre](#onglet-calcul-filtre)
8. [Onglet Enregistrement](#onglet-enregistrement)
9. [Onglet Alimentation](#onglet-alimentation)
10. [Onglet Terminal série](#onglet-terminal-série)
11. [Configuration et thème](#configuration-et-thème)
12. [Raccourcis clavier](#raccourcis-clavier)
13. [Fichiers et export](#fichiers-et-export)
14. [Dépannage](#dépannage)

---

## Démarrage rapide

1. **Branchez** le multimètre et le générateur en USB (ports COM sous Windows, `/dev/ttyUSBx` sous Linux).
2. Lancez l’application : `python main.py` (après activation du venv et `pip install -r requirements.txt`).
3. Ouvrez le menu **Outils → Détecter les équipements** (ou cliquez sur **Détecter** dans la barre de connexion) pour identifier automatiquement les ports du multimètre et du générateur.
4. **Aucun port n'est ouvert au démarrage** : cliquez sur **Détecter** puis **Connecter tout** pour connecter le multimètre et le générateur. Une fois les pastilles **vertes**, vous pouvez utiliser chaque onglet (Multimètre, Générateur, Oscilloscope, Banc filtre, Calcul filtre, Enregistrement, Alimentation, Terminal série).

**Prérequis :** Python 3.10+, PyQt6, pyserial. Voir `requirements.txt`.

---

## Connexion des équipements

### Barre de connexion

En haut de la fenêtre, **quatre pastilles** indiquent (Multimètre, Générateur, Alimentation, Oscilloscope) l’état de connexion :

- **Vert** : équipement détecté et connecté (modèle et port affichés).
- **Rouge** : non connecté ou non détecté.

**Boutons** : **Détecter** lance la détection des 4 équipements ; **Connecter tout** relit la config et ouvre les connexions ; **Déconnecter tout** ferme toutes les connexions. Les ports et la configuration série se modifient via `config.json` ou **Fichier → Ouvrir config...**.

### Détection automatique

- **Menu : Outils → Détecter les équipements** (ou bouton Détecter).
- L’application parcourt les ports COM et les périphériques USB :
  - **Multimètre OWON** : commande SCPI `*IDN?` ; si la réponse contient « OWON » ou « XDM », le port est retenu.
  - **Générateur FY6900** : test du protocole FeelTech ; si la réponse est cohérente, le port est retenu.
  - **Alimentation RS305P** : test Modbus RTU ; le port est retenu si l’appareil répond.
  - **Oscilloscope DOS1102** : détection sur port COM ou en USB (WinUSB/PyUSB, VID/PID dans `config.json`).
- Les champs de configuration (ports, oscilloscope USB, etc.) sont mis à jour. Pensez à **Sauvegarder config** (Fichier → Sauvegarder config) pour conserver les réglages au prochain lancement.

### Configuration série

Les ports et débits sont dans **`config/config.json`**. Pour modifier :

Éditez le fichier ou **Fichier → Ouvrir config...** puis **Sauvegarder config**.
- Débits typiques : OWON 115200, FY6900 115200, RS305P 9600.  l’OWON (ou 115200 selon modèle), 115200 pour le FY6900.
Après détection : **Sauvegarder config** pour écrire les ports trouvés dans `config.json`.

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

## Onglet Oscilloscope

Pilotage de l’**oscilloscope Hanmatek DOS1102**. L’onglet **utilise la connexion déjà établie** par la barre (bouton **Connecter tout**) : aucun bloc « Connexion série » dédié dans l’onglet. L’oscilloscope peut être connecté en **série (port COM)** ou en **USB (WinUSB/PyUSB)** ; en mode USB, utilisez **Rafraîchir USB** puis sélectionnez le périphérique dans la liste.

- **Canaux** : couplage (DC, AC, GND), échelle (V/div), position, offset, sonde (1X, 10X…), inversion.
- **Acquisition / Trigger** : mode d’acquisition, type de trigger, réglages.
- **Mesures** : requêtes par canal (fréquence, période, RMS, crête à crête, etc.) ou inter-canal (déphasage pour Bode).
- **Forme d’onde** : récupération des courbes (HEAD?, CH1?/CH2?) et affichage tension vs temps.

Voir [Commandes Hanmatek DOS1102](COMMANDES_HANMATEK_DOS1102.md) pour le détail des commandes SCPI.

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

- **Principe** : le générateur FY6900 envoie une sinusoïde à tension fixe (Ue) sur l’entrée du filtre ; la tension de sortie (Us) est mesurée par le **multimètre** ou par l’**oscilloscope**, au choix. Le logiciel balaie les fréquences et calcule le gain (Us/Ue) en dB (et éventuellement la phase en degrés si l’oscilloscope est utilisé).
- **Choix de l’instrument** : le banc filtre peut utiliser soit le **multimètre OWON**, soit l’**oscilloscope Hanmatek DOS1102**. Avec le multimètre, la bande passante utile pour la mesure RMS est limitée ; le multimètre ne permet pas de mesurer la **phase**, donc seul le gain (courbe Bode gain) est disponible. Avec l’oscilloscope, la bande passante en fréquence est de **100 MHz** et le logiciel peut enregistrer la **phase** (Ch1 = Ue, Ch2 = Us) pour tracer le **diagramme Bode complet** (gain + phase). Voir [Cahier des charges visualisation Bode](CAHIER_DES_CHARGES_VISUALISATION_BODE.md).
- **Configuration** : voie du générateur (1 ou 2), **f_min**, **f_max**, nombre de points, échelle **lin** ou **log**, délai de stabilisation (ms), tension Ue (V RMS). En mode oscilloscope, le paramètre **phase_skip_below_scale_ch2_mv** (dans `config.json`, section `filter_test`) définit le calibre CH2 en mV/div en dessous duquel la phase n'est pas relevée (défaut 20 : au-delà de 20 mV/div la colonne Phase reste vide, signal trop altéré).
- **Résultats** : tableau (fréquence, Us, gain linéaire, gain dB ; et phase en ° si oscilloscope) et **graphique Bode** (gain dB vs fréquence ; avec phase si le CSV contient `Phase_deg`). Export CSV et export du graphique possible.

Au démarrage d’un balayage, la configuration générateur (forme d’onde, amplitude, offset) est appliquée depuis `config.json` pour un état reproductible.

---

## Onglet Calcul filtre

Onglet **calcul de composants** pour les filtres électroniques : à partir des valeurs de **R**, **L**, **C** (et paramètres spécifiques), le logiciel calcule les **fréquences de coupure** et paramètres associés.

- **Types de filtres** : RC passe-bas, CR passe-haut, Pont de Wien, RLC (résonance, facteur de qualité), Double T.
- **Unités** : résistance (Ω, kΩ, MΩ), inductance (pH à H), capacité (pF à F).
- **Schémas** : un schéma par type de filtre (SVG) pour visualiser le montage.
- **Paramètres avancés** : par exemple Pont de Wien avec R1, R2, C1, C2 distincts.

Les formules utilisent le module `core/filter_calculator.py` et les utilitaires Bode (`core/bode_utils.py`). Utile pour dimensionner un filtre avant de le caractériser avec l’onglet **Banc filtre**.

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

- **Fichier → Ouvrir config...** : charger un fichier de configuration JSON.
- **Fichier → Ouvrir CSV Banc filtre...** : ouvrir un fichier CSV de courbe Bode (banc filtre) dans le visualiseur dédié (courbes, fréquence de coupure, export).
- **Configuration** : JSON (config.json ou « Enregistrer sous »).
- **Historique multimètre** : CSV (Export CSV, onglet Multimètre).
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
- **Commandes OWON (multimètre)** : `docs/COMMANDES_OWON.md`
- **Commandes FY6900 (générateur)** : `docs/COMMANDES_FY6900.md`
- **Commandes RS305P (alimentation)** : `docs/COMMANDES_RS305P.md`
- **Commandes Hanmatek DOS1102 (oscilloscope)** : `docs/COMMANDES_HANMATEK_DOS1102.md`
- **README** : `README.md` à la racine du projet

---

*Banc de test automatique — Aide intégrée. Pour toute question sur le matériel, consulter les manuels OWON (XDM1000), FeelTech (FY6900) et Rockseed (RS305P Modbus).*
