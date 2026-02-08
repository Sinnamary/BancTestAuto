# Multimètre OWON XDM — Commandes implémentées

Référence des **commandes SCPI** utilisées par le logiciel Banc de test automatique pour piloter le multimètre OWON (XDM1041 / XDM2041). Protocole : liaison série, débit typique 9600 ou 115200 selon modèle.

---

## Identification et système

| Commande | Rôle | Notes |
|----------|------|--------|
| `*IDN?` | Identification de l’appareil | Réponse type : fabricant, modèle, numéro de série. Utilisée pour la détection automatique des ports. |
| `*RST` | Réinitialisation | Remet l’appareil dans un état par défaut. Raccourci **Ctrl+R** dans l’interface. |
| `SYST:LOC` | Mode local | Reprend le contrôle du panneau frontal. |
| `SYST:REM` | Mode distant | Contrôle par le logiciel. |
| `SYST:BEEP:STAT` | État du buzzer | — |
| `SYST:BEEP:STAT?` | Requête état buzzer | — |
| `SYST:BEEP:STAT ON` | Buzzer activé | Son sur continuité / diode. |
| `SYST:BEEP:STAT OFF` | Buzzer désactivé | Désactive le bip. |

---

## Modes de mesure (CONFigure)

| Commande | Rôle | Notes |
|----------|------|--------|
| `CONF:VOLT:DC` | Tension continue (V⎓) | Mode tension DC. |
| `CONF:VOLT:AC` | Tension alternative (V~) | Mode tension AC. Utilisé pour le banc filtre (mesure Us). |
| `CONF:CURR:DC` | Courant continu (A⎓) | — |
| `CONF:CURR:AC` | Courant alternatif (A~) | — |
| `CONF:RES` | Résistance 2 fils (Ω) | — |
| `CONF:FRES` | Résistance 4 fils (Ω 4W) | — |
| `CONF:FREQ` | Fréquence (Hz) | — |
| `CONF:PER` | Période (s) | — |
| `CONF:CAP` | Capacité (F) | — |
| `CONF:TEMP:RTD` | Température RTD (°C) | Sonde RTD. |
| `CONF:DIOD` | Test diode (⊿) | — |
| `CONF:CONT` | Continuité (⚡) | — |

---

## Plage et vitesse

| Commande | Rôle | Notes |
|----------|------|--------|
| `AUTO` | Plage automatique | Sélection automatique du calibre. |
| `AUTO?` | Requête état auto | — |
| `RANGE <valeur>` | Plage manuelle | Valeur selon le mode (ex. `5`, `500E-3`, `5E3`). |
| `RATE F` | Vitesse rapide | Mesure plus rapide, moins de stabilité. |
| `RATE M` | Vitesse moyenne | Compromis vitesse / précision. |
| `RATE L` | Vitesse lente | Meilleure précision, mesure plus lente. |

---

## Mesure et affichage secondaire

| Commande | Rôle | Notes |
|----------|------|--------|
| `MEAS?` | Mesure immédiate (voie principale) | Retourne la valeur courante. **F5** ou bouton Mesure. |
| `MEAS1?` | Mesure voie 1 | — |
| `MEAS2?` | Mesure affichage secondaire | Utilisé pour afficher la fréquence (Hz) en mode tension/courant. |
| `FUNC?` | Requête fonction actuelle | — |
| `FUNC2 "FREQ"` | Afficher la fréquence en secondaire | Affiche la fréquence en Hz sur le second écran. |
| `FUNC2 "NONe"` | Désactiver l’affichage secondaire | — |

---

## Fonctions math (CALCulate)

| Commande | Rôle | Notes |
|----------|------|--------|
| `CALC:STAT OFF` | Désactiver les fonctions math | — |
| `CALC:FUNC NULL` | Mode Rel (offset) | Mesure relative à une référence. |
| `CALC:NULL:OFFS <valeur>` | Définir l’offset Rel | Valeur de référence (ex. 1.5). |
| `CALC:FUNC DB` | Mode dB | Gain en dB. |
| `CALC:DB:REF <ohm>` | Référence dB (résistance Ω) | Ex. 600 Ω. |
| `CALC:FUNC DBM` | Mode dBm | Puissance en dBm. |
| `CALC:DBM:REF <ohm>` | Référence dBm (résistance Ω) | Ex. 50 Ω. |
| `CALC:FUNC AVERage` | Moyenne avec statistiques | Min, max, moyenne. |
| `CALC:AVER:ALL?` | Réinitialise et retourne les stats | — |
| `AVerage?` | Valeur moyenne | — |
| `MAXimum?` | Valeur max | — |
| `MINimum?` | Valeur min | — |

---

## Température RTD

| Commande | Rôle | Notes |
|----------|------|--------|
| `TEMP:RTD:TYPE KITS90` | Type de sonde KITS90 | — |
| `TEMP:RTD:TYPE PT100` | Type de sonde PT100 | — |
| `TEMP:RTD:UNIT CEL` | Unité °C | — |
| `TEMP:RTD:UNIT FAR` | Unité °F | — |
| `TEMP:RTD:UNIT K` | Unité K | — |
| `TEMP:RTD:SHOW TEMP` | Afficher température | — |
| `TEMP:RTD:SHOW MEAS` | Afficher mesure brute | — |
| `TEMP:RTD:SHOW ALL` | Afficher tout | — |

---

## Continuité

| Commande | Rôle | Notes |
|----------|------|--------|
| `CONT:THRE <valeur>` | Seuil de continuité (Ω) | Ex. 10. Au-dessous, le multimètre considère le circuit fermé. |

---

## Référence

- Manuel de programmation : `docs/XDM1000_Digital_Multimeter_Programming_Manual.pdf`
- Implémentation : `core/scpi_commands.py`, `core/scpi_protocol.py`, `core/measurement.py`
