# Tableau chronologique des commandes – osc_interface.py

**Référence (programme d'origine)** : [hanmatek_DOS1102_python_wrapper](https://github.com/danielphili/hanmatek_DOS1102_python_wrapper) — Daniel Alexander Philipps ([@danielphili](https://github.com/danielphili)). Python, pyUSB, extraction de données Hanmatek DOS1102 via USB. Licence GNU GPL v3.

**Note :** Le fichier `osc_interface.py` n'est **pas inclus** dans ce dépôt ; il s'agit d'une référence externe. Le projet BancTestAuto utilise les modules `core/dos1102_*.py` pour la connexion, le protocole et le décodage (voir § 5 ci-dessous).

---

Ce document décrit **l'ordre chronologique exact** des commandes envoyées à l'oscilloscope Hanmatek DOS1102 par `osc_interface.py` (dépôt GitHub ci-dessus).

### Chronologie globale (script lancé avec `verbose=True`)

Ordre d'envoi **complet** : d'abord `__init__`, puis le bloc `if __name__ == '__main__'`.

| Ordre | Commande envoyée | Contexte (osc_interface.py) |
|-------|------------------|-----------------------------|
| 1 | `*IDN?` | `__init__` (l. 65) |
| 2 | `:DATA:WAVE:SCREen:HEAD?` | `__init__` → `get_meta_data()` (l. 66) |
| 3 | `:RUNNING RUN` | main (l. 316) |
| 4 | *(pause 0,01 s)* | `time.sleep(0.01)` (l. 313) |
| 5 | `:RUNNING STOP` | main (l. 318) |
| 6 | `:DATA:WAVE:SCREen:HEAD?` | `get_meta_data()` (l. 319) |
| 7 | `:DATA:WAVE:SCREen:HEAD?` | `get_time_base()` → `get_meta_data()` (l. 320) |
| 8 | `:DATA:WAVE:SCREen:HEAD?` | `get_channel_waveform_data(1)` → `get_meta_data()` (l. 321) |
| 9 | `:DATA:WAVE:SCREEN:CH1?` | `get_channel_waveform_data(1)` (l. 171) |
| 10 | `:DATA:WAVE:SCREen:HEAD?` | `get_channel_waveform_data(2)` → `get_meta_data()` (l. 336) |
| 11 | `:DATA:WAVE:SCREEN:CH2?` | `get_channel_waveform_data(2)` (l. 171) |
| 12 | `:MEAS:CH1?` | `get_channel_measurement_data(1)` (l. 348) |
| 13 | `:MEAS:CH2?` | `get_channel_measurement_data(2)` (l. 351) |

---

## 1. Au démarrage (`__init__`)

Si l’appareil est trouvé et `verbose=True` :

| # | Moment | Commande envoyée | Méthode / Contexte |
|---|--------|------------------|---------------------|
| 1 | Connexion | `*IDN?` | `query_string_result('*IDN?')` – identification de l’instrument |
| 2 | Connexion | `:DATA:WAVE:SCREen:HEAD?` | `get_meta_data()` – en-tête/métadonnées de l’écran |

---

## 2. Bloc `if __name__ == '__main__'` (l. 310–358)

Ordre des envois **dans le bloc main uniquement** (après `__init__`). Correspond aux ordres 3–13 du tableau « Chronologie globale » ci-dessus.

| # | Ordre (main) | Commande envoyée | Méthode / Ligne |
|---|---------------|------------------|------------------|
| 1 | 1 | `:RUNNING RUN` | `osci.write(':RUNNING RUN')` (l. 316) |
| 2 | 2 | *(pause 0,01 s)* | `time.sleep(0.01)` (l. 313) |
| 3 | 3 | `:RUNNING STOP` | `osci.write(':RUNNING STOP')` (l. 318) |
| 4 | 4 | `:DATA:WAVE:SCREen:HEAD?` | `osci.get_meta_data()` (l. 319) |
| 5 | 5 | `:DATA:WAVE:SCREen:HEAD?` | `osci.get_time_base()` → `get_meta_data()` (l. 320) |
| 6 | 6 | `:DATA:WAVE:SCREen:HEAD?` | `get_channel_waveform_data(1)` → `get_meta_data()` (l. 321) |
| 7 | 7 | `:DATA:WAVE:SCREEN:CH1?` | `get_channel_waveform_data(1)` (l. 171) – données brutes CH1 |
| 8 | 8 | `:DATA:WAVE:SCREen:HEAD?` | `get_channel_waveform_data(2)` → `get_meta_data()` (l. 336) |
| 9 | 9 | `:DATA:WAVE:SCREEN:CH2?` | `get_channel_waveform_data(2)` (l. 171) – données brutes CH2 |
| 10 | 10 | `:MEAS:CH1?` | `get_channel_measurement_data(1)` (l. 348) |
| 11 | 11 | `:MEAS:CH2?` | `get_channel_measurement_data(2)` (l. 351) |

---

## 3. Résumé des commandes par type

| Commande | Rôle | Réponse attendue |
|----------|------|-------------------|
| `*IDN?` | Identification (standard SCPI) | Chaîne d’identification de l’instrument |
| `:RUNNING RUN` | Démarrer l’acquisition | — |
| `:RUNNING STOP` | Arrêter l’acquisition | — |
| `:DATA:WAVE:SCREen:HEAD?` | En-tête / métadonnées de l’écran (timebase, canaux, échantillonnage, etc.) | JSON (après les 4 premiers octets) |
| `:DATA:WAVE:SCREEN:CH1?` | Données waveform canal 1 (écran) | Binaire (4 octets en-tête + échantillons 16 bits) |
| `:DATA:WAVE:SCREEN:CH2?` | Données waveform canal 2 (écran) | Idem |
| `:MEAS:CH1?` | Toutes les mesures activées pour le canal 1 | JSON |
| `:MEAS:CH2?` | Toutes les mesures activées pour le canal 2 | JSON |

---

## 4. Flux d’envoi (méthodes utilisées)

- **`write(msg)`** : envoie la commande sans exploiter la réponse (délègue à `query()`).
- **`query(msg)`** : envoie puis lit la réponse (bytes).
- **`query_string_result(msg)`** : comme `query()` mais décode la réponse en chaîne UTF-8.
- **`query_and_show_response(msg)`** : envoie, lit et affiche la réponse (débogage).

Toutes les commandes listées ci-dessus passent par l’écriture sur l’endpoint **Bulk OUT (0x03)** et la lecture sur **Bulk IN (0x81)**.

---

## 5. Récupérer les données pour tracer CH1 et CH2

### Ordre recommandé (dans l'application : onglet Oscilloscope)

1. **Connexion** : connecter l'oscilloscope en USB (onglet Oscilloscope, pas le terminal brut).
2. **Couplage** : dans le panneau **Canaux**, choisir **DC** (ou AC) pour CH1 et CH2. Cliquer sur **Appliquer canaux**.  
   Si les canaux restent en **GND**, l'appareil affiche la référence 0 V : vous obtiendrez une **ligne plate** (trait continu à 0 V) même si un signal est branché.
3. **Acquisition** : optionnellement envoyer `:RUNNING RUN`, attendre un instant, puis `:RUNNING STOP` (ou laisser l'oscillo en run).
4. **Récupération** : dans le panneau **Forme d'onde**, cliquer sur **Récupérer forme d'onde**.  
   Cela envoie dans l'ordre :  
   `:DATA:WAVE:SCREen:HEAD?` → métadonnées (JSON) ;  
   `:DATA:WAVE:SCREEN:CH1?` → données binaires canal 1 ;  
   `:DATA:WAVE:SCREEN:CH2?` → données binaires canal 2.  
   Le décodage (4 octets d'en-tête + int16 little-endian, puis conversion en volts avec SCALE/OFFSET/PROBE) est fait dans `core/dos1102_waveform.py` (équivalent à `osc_interface.py`).
5. **Tracé** : cliquer sur **Afficher courbe** pour afficher temps (s) vs tension (V) pour CH1 et CH2.

### Pourquoi « les deux lignes sont à GND » (trait continu) ?

Si les canaux sont réglés en **couplage GND** sur l'oscilloscope, l'entrée est déconnectée et l'écran affiche 0 V. Les données lues sont alors toutes à 0 V : le tracé est un trait horizontal à 0.

- **Solution** : passer les canaux en **DC** (ou AC) :  
  - depuis l'oscilloscope (menu canal, couplage), ou  
  - depuis l'application : panneau **Canaux** → Couplage **DC** pour CH1 et CH2 → **Appliquer canaux**.  
  Commandes SCPI correspondantes : `:CH1:COUP DC`, `:CH2:COUP DC`.

### Équivalent dans le projet (sans osc_interface.py)

- **Protocole** : `core/dos1102_protocol.py` — `get_waveform_screen()` enchaîne HEAD? puis CH1? puis CH2? et retourne `{ meta, time, ch1, ch2 }`.
- **Décodage** : `core/dos1102_waveform.py` — `decode_screen_waveform(meta, raw_ch1, raw_ch2)`.
- **Connexion** : `core/dos1102_usb_connection.py` (write/read synchrone). Pour une acquisition fiable, utiliser l'onglet **Oscilloscope** (une seule connexion, write puis read pour chaque requête), pas le terminal USB qui lit en continu et peut mélanger les réponses.
