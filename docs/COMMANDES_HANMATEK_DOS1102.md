# Oscilloscope HANMATEK DOS1102 — Commandes SCPI

Référence des **commandes SCPI** utilisables pour piloter l’oscilloscope HANMATEK DOS1102 (série DSO, liaison USB virtuelle série). Ces commandes ont été identifiées par reverse‑engineering et par rapprochement avec le manuel **DSO2000 Series SCPI Programmers Manual** (Hantek).

---

## Identification et liaison

- **Liaison** :  
  - **Série (COM)** : port COM virtuel, débit typique **115200** ou **9600** bauds (pilote CDC/série).  
  - **USB (WinUSB/PyUSB)** : connexion directe USB sans port COM. Pilote **WinUSB** (ex. installé via [Zadig](https://zadig.akeo.ie/)), backend **libusb** et **PyUSB** (`pip install pyusb`). Dans l’onglet Oscilloscope, choisir le mode **USB (WinUSB/PyUSB)**, cliquer sur **Rafraîchir USB**, sélectionner le périphérique dans la liste puis **Connexion**.
- **Terminaison** : les commandes doivent se terminer par un **retour à la ligne** (`\n`). Ne pas envoyer `\` + `n` en clair (échapper correctement en code).
- **Test au terminal série** : dans l’onglet **Terminal série**, sélectionner **Oscilloscope** puis envoyer une commande par ligne (ex. `*IDN?`, `:CH1:COUP AC`, `:HOR:SCAL 10ms`). Les échanges sont enregistrés dans `logs/serial_*.log`.
- **Identification et réinitialisation** :

| Commande | Rôle | Notes |
|----------|------|--------|
| `*IDN?` | Identification | Réponse type fabricant, modèle, numéro de série (si supporté). |
| `*RST` | Réinitialisation | Remet l'appareil dans un état par défaut. |

---

## Commandes documentées (forum NI / essais)

Syntaxe observée sur DOS1102 (certaines variantes utilisent `CH1`/`CH2` au lieu de `CHANnel1`/`CHANnel2`).

### Acquisition

| Commande | Rôle | Notes |
|----------|------|--------|
| `:ACQ:MODE SAMP` | Mode d’acquisition : échantillonnage | |
| `:ACQ:MODE PEAK` | Mode peak (détection de pics) | |
| `:ACQ:MODE AVE` | Mode moyenne | |

### Canaux (voies)

| Commande | Rôle | Notes |
|----------|------|--------|
| `:CH1:COUP DC` | Couplage voie 1 : DC | |
| `:CH1:COUP AC` | Couplage voie 1 : AC | |
| `:CH1:COUP GND` | Couplage voie 1 : GND | |
| `:CH2:COUP DC` / `AC` / `GND` | Couplage voie 2 | Idem pour CH2. |
| `:CH<n>:SCAL <valeur>` | Échelle verticale (amplitude, V/div) | n = 1 ou 2. **Format avec unité** : `100mV`, `500mV`, `1V`, `2V`, `5V`, etc. Ex. `:CH1:SCAL 100mV`. |
| `:CH<n>:POS <valeur>` | Position verticale (div) | |
| `:CH<n>:OFFS <valeur>` | Offset vertical (V) | |
| `:CH<n>:PROBE 1X` / `10X` / `100X` / `1000X` | Rapport de sonde | |
| `:CH<n>:INV OFF` / `ON` | Inversion de voie | |

### Base de temps (horizontal)

Le DOS1102 attend la base de temps **avec unité**. **Pour les ms** : uniquement `1.0ms`, `2.0ms` et `5.0ms` avec un zéro ; les autres sans : `10ms`, `20ms`, `50ms`, etc. ns/us sans `.0` : `500ns`, `2us`. Secondes : `1.0s`.

| Commande | Rôle | Notes |
|----------|------|--------|
| `:HOR:OFFS <valeur>` | Offset horizontal | Position du trigger. |
| `:HOR:SCAL <valeur>` | Échelle horizontale (temps/div) | **Format ms** : `1.0ms`, `2.0ms`, `5.0ms` avec zéro ; `10ms`, `20ms`, `50ms` sans. ns/us : `500ns`, `2us`. Ex. `:HOR:SCAL 2.0ms`, `:HOR:SCAL 10ms`. |

### Trigger

| Commande | Rôle | Notes |
|----------|------|--------|
| `:TRIG EDGE` | Trigger type edge | |
| `:TRIG VIDEO` | Trigger type vidéo | |
| `:TRIG:TYPE SING` | Mode single | |
| `:TRIG:TYPE ALT` | Mode alternate | |

*(Source et niveau du trigger à confirmer selon modèle ; voir manuel DSO2000 pour `:TRIGger:EDGe:SOURce`, `:TRIGger:EDGe:LEVel`, etc.)*

### Mesures (requêtes)

| Commande | Rôle | Notes |
|----------|------|--------|
| `:MEAS?` | Requête mesure (général) | Retourne la valeur courante selon mesure affichée |
| `:MEAS:CH1:PERiod?` | Période voie 1 | |
| `:MEAS:CH1:FREQuency?` | Fréquence voie 1 | |
| `:MEAS:CH1:AVERage?` | Moyenne voie 1 | |
| `:MEAS:CH1:PKPK?` | Crête à crête voie 1 | |
| `:MEAS:CH1:MAX?` | Maximum voie 1 | |
| `:MEAS:CH1:MIN?` | Minimum voie 1 | |
| `:MEAS:CH1:VTOP?` | Sommet voie 1 | |
| `:MEAS:CH1:VBASe?` | Base voie 1 | |
| `:MEAS:CH1:VAMP?` | Amplitude voie 1 | |
| `:MEAS:CH1:TRUERMS?` | RMS vrai voie 1 | |
| `:MEAS:CH1:RTime?` | Temps de montée | |
| `:MEAS:CH1:FTime?` | Temps de descente | |
| `:MEAS:CH1:PWIDth?` | Largeur d’impulsion positive | |
| `:MEAS:CH1:NWIDth?` | Largeur d’impulsion négative | |
| `:MEAS:CH2:...` | Mêmes types pour la voie 2 | |

*(Liste partielle ; d’autres types sont documentés dans le forum : SQUARESUM, VPRESHOOT, PREShoot, PDUTy, NDUTy, RDELay, FDELay, CYCRms, WORKPERIOD, RISEPHASEDELAY, PPULSENUM, NPULSENUM, RISINGEDGENUM, FALLINGEDGENUM, AREA, CYCLEAREA.)*

---

### Mesures inter-canal (différence de phase entre les deux voies)

Pour un **diagramme de Bode phase** (φ en degrés en fonction de la fréquence) :

| Mesure (sur CH2) | Commande typique | Rôle |
|------------------|------------------|------|
| Délai phase montée | `:MEAS:CH2:RISEPHASEDELAY?` | Sur le DOS1102, la réponse est **directement en degrés** (ex. `RP : 26.352°`). |
| Délai montée | `:MEAS:CH2:RDELay?` | Délai en secondes (variante) |
| Délai descente | `:MEAS:CH2:FDELay?` | Délai en secondes |

Si la commande renvoie un délai en secondes plutôt qu’en degrés, utiliser : φ (°) = (délai / période) × 360, avec la période lue via `:MEAS:CH1:PERiod?` ou `:MEAS:CH2:PERiod?`.

L'application propose **« Toutes les mesures »** (par voie CH1, CH2, ou inter-canal) pour récupérer en une fois toutes les valeurs nécessaires au Bode phase.

### Récupération des données de courbe (forme d'onde)

Pour **afficher les signaux** (courbes CH1/CH2 en fonction du temps), l'application utilise l'API Hanmatek/OWON (référence : [hanmatek_DOS1102_python_wrapper](https://github.com/danielphili/hanmatek_DOS1102_python_wrapper)) :

| Commande | Rôle |
|----------|------|
| `:DATA:WAVE:SCREen:HEAD?` | Méta-données (4 octets puis JSON : échelles, offset, sample rate, DATALEN, etc.) |
| `:DATA:WAVE:SCREEN:CH1?` | Données brutes canal 1 : 4 octets + int16 signé (little-endian) par point |
| `:DATA:WAVE:SCREEN:CH2?` | Données brutes canal 2 : idem |

Formule de conversion en tension (V) : `voltage = scale * (adc_val - offset*8.25) / 410` (scale inclut le facteur de sonde). L'onglet Oscilloscope **« Récupérer forme d'onde »** envoie HEAD? puis CH1?/CH2?, décode les binaires et affiche **« Afficher courbe »** (temps en s, CH1/CH2 en V).

*Ancienne commande (selon modèle) :* `:WAV:DATA:ALL?` / `:WAVeform:DATA:ALL?` (ASCII ou bloc SCPI).

---

## Référence manuel DSO2000 (Hantek)

Le **DSO2000 Series SCPI Programmers Manual** (Hantek) décrit une syntaxe plus complète avec les sous-systèmes :

- **CHANnel** : `:CHANnel<n>:COUPling`, `:CHANnel<n>:SCALe`, `:CHANnel<n>:OFFSet`, `:CHANnel<n>:PROBe`, etc.
- **TIMebase** : `:TIMebase:SCALe`, `:TIMebase:POSition`, etc.
- **ACQuire** : `:ACQuire:TYPE` (NORMal, PEAK, AVERage), `:ACQuire:POINts`, etc.
- **TRIGger** : `:TRIGger:EDGe:SOURce`, `:TRIGger:EDGe:LEVel`, `:TRIGger:EDGe:SLOPe`, etc.
- **MEASure** : `:MEASure:CHANnel:ITEM`, `:MEASure:ADISplay?`, etc.
- **WAVeform** : `:WAVeform:DATA:ALL?` pour récupérer les données de courbe.

Sur le DOS1102, la syntaxe courte (`:CH1:`, `:ACQ:MODE`) peut être acceptée ; en cas de doute, essayer la forme longue du manuel DSO2000.

---

## Implémentation dans BancTestAuto

- **Commandes** : `core/dos1102_commands.py` (constantes SCPI, `WAVEFORM_HEAD`, `WAVEFORM_SCREEN_CH(ch)`, `MEAS_TYPES_PER_CHANNEL`, etc.)
- **Protocole** : `core/dos1102_protocol.py` — envoi/réception sur `SerialConnection` ou `Dos1102UsbConnection` ; `waveform_meta_data()`, `waveform_screen_raw(ch, n_points)`, **`get_waveform_screen()`** (HEAD? + CH1?/CH2? → meta, time, ch1, ch2) ; `meas_all_per_channel(ch)`, `meas_all_inter_channel()` pour Bode phase
- **Parsing forme d'onde** : `core/dos1102_waveform.py` — `decode_screen_channel()`, `time_base_from_meta()`, `decode_screen_waveform()` pour le binaire Hanmatek/OWON
- **Vue** : `ui/oscilloscope/` — onglet Oscilloscope : connexion, acquisition, trigger, mesures, **forme d'onde** (récupération via `get_waveform_screen()` + affichage courbe CH1/CH2 en V vs temps en s)

---

## Références

- Forum NI : [Communication with oscilloscope Hanmatek DOS 1102](https://forums.ni.com/t5/Instrument-Control-GPIB-Serial/Communication-with-oscilloscope-Hanmatek-DOS-1102/td-p/4231411) (commandes trouvées par essais).
- Hantek : *DSO2000 Series SCPI Programmers Manual* (PDF sur hantek.com).
- Hanmatek : [Manuels](https://hanmatek.com/pages/manuals-center).
