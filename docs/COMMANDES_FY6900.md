# Générateur FeelTech FY6900 — Commandes implémentées

Référence des **commandes série** utilisées par le logiciel Banc de test automatique pour piloter le générateur de signaux FeelTech FY6900. Protocole : liaison série, débit 115200, fin de ligne `LF` (0x0A). Le générateur dispose de **deux voies** ; chaque voie a son propre jeu de commandes (préfixe **WM** = voie 1, **WF** = voie 2).

---

## Convention des préfixes

| Préfixe | Voie   | Rôle                          |
|---------|--------|-------------------------------|
| **WM**  | Voie 1 | Canal principal (main wave)   |
| **WF**  | Voie 2 | Canal auxiliaire (auxiliary)  |

Le logiciel envoie les commandes correspondant à la **voie sélectionnée** dans l’interface (onglet Générateur) ou à la voie configurée pour le banc filtre.

---

## Commandes voie 1 (WM)

| Commande | Format envoyé           | Rôle              | Notes |
|----------|-------------------------|-------------------|--------|
| **WMW**  | `WMW<n>\n`              | Forme d’onde      | `n` = type. **0** = sinusoïde, 1 = triangle, 2 = carré, etc. (voir manuel). |
| **WMF**  | `WMF<valeur>\n`        | Fréquence         | Fréquence en **Hz avec 6 décimales**. Ex. `WMF12345678.901234`. |
| **WMA**  | `WMA<valeur>\n`         | Amplitude crête   | Amplitude en **V** (crête à crête ou crête selon modèle). 2 décimales. Ex. `WMA5.00`. |
| **WMO**  | `WMO<valeur>\n`         | Offset            | Tension de décalage en **V**. 2 décimales. Ex. `WMO0.00`. |
| **WMN**  | `WMN<0\|1>\n`           | Sortie ON/OFF     | **1** = sortie activée, **0** = sortie désactivée. |

---

## Commandes voie 2 (WF)

| Commande | Format envoyé           | Rôle              | Notes |
|----------|-------------------------|-------------------|--------|
| **WFW**  | `WFW<n>\n`              | Forme d’onde      | Même codage que WMW (0 = sinusoïde, etc.). |
| **WFF**  | `WFF<valeur>\n`          | Fréquence         | Fréquence en **Hz avec 6 décimales** (même format que WMF). |
| **WFA**  | `WFA<valeur>\n`          | Amplitude crête   | Amplitude en **V**, 2 décimales (même format que WMA). |
| **WFO**  | `WFO<valeur>\n`          | Offset            | Offset en **V**, 2 décimales (même format que WMO). |
| **WFN**  | `WFN<0\|1>\n`            | Sortie ON/OFF     | **1** = sortie voie 2 activée, **0** = désactivée. |

---

## Détails d’implémentation

| Élément     | Détail | Notes |
|-------------|--------|--------|
| Fin de ligne | `\n` (0x0A) | Toutes les commandes se terminent par LF. |
| **Fréquence (WMF / WFF)** | Hz, 6 décimales | Ex. 1000 Hz → `WMF1000.000000`, 12345678.901234 Hz → `WMF12345678.901234`. |
| **Amplitude (WMA / WFA)** | Décimal, 2 décimales | Ex. `WMA5.00`, `WFA3.50`. |
| **Offset (WMO / WFO)**   | Décimal, 2 décimales | Ex. `WMO0.00`, `WFO1.50`. |
| **Forme d’onde (WMW / WFW)** | Entier | 0 = sinusoïde, 1 = triangle, 2 = carré, 3 = dent de scie (codes selon manuel FY6900). |
| **Sortie (WMN / WFN)**   | 0 ou 1 | 0 = OFF, 1 = ON. |

---

## Séquence type (banc filtre)

Pour un point du **banc de test filtre** (voie choisie dans la config, ex. voie 1) :

1. `WMW0` (ou `WFW0` si voie 2) — sinusoïde  
2. `WMA1.41` (ou `WFA1.41`) — amplitude crête (2 décimales)  
3. `WMO0.00` (ou `WFO0.00`) — offset 0 V  
4. `WMF<fréquence µHz>` (ou `WFF<...>`) — fréquence du point  
5. `WMN1` (ou `WFN1`) — sortie ON  

À la fin du balayage : `WMN0` ou `WFN0` pour couper la sortie.

---

## Référence

- Protocole FeelTech : `docs/FY6900_communication_protocol.pdf`
- Implémentation : `core/fy6900_commands.py`, `core/fy6900_protocol.py`
- Détection automatique : le logiciel envoie `WMW0\n` pour tester si le port répond au protocole FY6900 (`core/device_detection.py`).
