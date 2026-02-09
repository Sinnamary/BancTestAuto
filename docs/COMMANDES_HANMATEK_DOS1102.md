# Oscilloscope HANMATEK DOS1102 — Commandes SCPI

Référence des **commandes SCPI** utilisables pour piloter l’oscilloscope HANMATEK DOS1102 (série DSO, liaison USB virtuelle série). Ces commandes ont été identifiées par reverse‑engineering et par rapprochement avec le manuel **DSO2000 Series SCPI Programmers Manual** (Hantek).

---

## Identification et liaison

- **Liaison** :  
  - **Série (COM)** : port COM virtuel, débit typique **115200** ou **9600** bauds (pilote CDC/série).  
  - **USB (WinUSB/PyUSB)** : connexion directe USB sans port COM. Pilote **WinUSB** (ex. installé via [Zadig](https://zadig.akeo.ie/)), backend **libusb** et **PyUSB** (`pip install pyusb`). Dans l’onglet Oscilloscope, choisir le mode **USB (WinUSB/PyUSB)**, cliquer sur **Rafraîchir USB**, sélectionner le périphérique dans la liste puis **Connexion**.
- **Terminaison** : les commandes doivent se terminer par un **retour à la ligne** (`\n`). Ne pas envoyer `\` + `n` en clair (échapper correctement en code).
- **Identification** : `*IDN?` — réponse type fabricant, modèle, numéro de série (si supporté).

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
| `:CH2:COUP DC` | Couplage voie 2 : DC | |
| `:CH2:COUP AC` | Couplage voie 2 : AC | |
| `:CH2:COUP GND` | Couplage voie 2 : GND | |
| `:CH1:SCA <valeur>` | Échelle verticale voie 1 (V/div) | |
| `:CH2:SCA <valeur>` | Échelle verticale voie 2 | |
| `:CH1:POS <valeur>` | Position verticale voie 1 | |
| `:CH2:POS <valeur>` | Position verticale voie 2 | |
| `:CH1:OFFS <valeur>` | Offset vertical voie 1 | |
| `:CH2:OFFS <valeur>` | Offset vertical voie 2 | |
| `:CH1:PROBE 1X` | Sonde voie 1 : 1X | |
| `:CH1:PROBE 10X` | Sonde voie 1 : 10X | |
| `:CH1:PROBE 100X` | Sonde voie 1 : 100X | |
| `:CH1:PROBE 1000X` | Sonde voie 1 : 1000X | |
| `:CH2:PROBE 1X` / `10X` / `100X` / `1000X` | Idem voie 2 | |
| `:CH1:INV OFF` | Inversion voie 1 désactivée | |
| `:CH1:INV ON` | Inversion voie 1 activée | |
| `:CH2:INV OFF` / `ON` | Idem voie 2 | |

### Base de temps (horizontal)

| Commande | Rôle | Notes |
|----------|------|--------|
| `:HOR:OFFS <valeur>` | Offset horizontal (position du trigger) | |
| `:HOR:SCAL <valeur>` | Échelle horizontale (temps/div, ex. s ou ms) | |

### Trigger

| Commande | Rôle | Notes |
|----------|------|--------|
| `:TRIG EDGE` | Trigger type edge | |
| `:TRIG VIDEO` | Trigger type vidéo | |
| `:TRIG:TYPE SING` | Mode single | |
| `:TRIG:TYPE ALT` | Mode alternate | |

*(Source source et niveau du trigger à confirmer selon modèle ; voir manuel DSO2000 pour `:TRIGger:EDGe:SOURce`, `:TRIGger:EDGe:LEVel`, etc.)*

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

- **Commandes** : `core/dos1102_commands.py`
- **Protocole** : `core/dos1102_protocol.py` (envoi/réception sur `SerialConnection`)
- **Vue** : `ui/views/oscilloscope_view.py` (onglet Oscilloscope)

---

## Références

- Forum NI : [Communication with oscilloscope Hanmatek DOS 1102](https://forums.ni.com/t5/Instrument-Control-GPIB-Serial/Communication-with-oscilloscope-Hanmatek-DOS-1102/td-p/4231411) (commandes trouvées par essais).
- Hantek : *DSO2000 Series SCPI Programmers Manual* (PDF sur hantek.com).
- Hanmatek : [Manuels](https://hanmatek.com/pages/manuals-center).
