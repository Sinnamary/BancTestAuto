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
| **WMW**  | `WMWxx\n`               | Forme d’onde      | **2 chiffres** (doc FY6900). 0 = sinusoïde (WMW00), 1 = carré, 7 = triangle, 8 = rampe (dent de scie). |
| **WMF**  | `WMF<valeur>\n`        | Fréquence         | Fréquence en **µHz**, **14 chiffres** (zéros à gauche). Ex. 1000 Hz → `WMF00010000000000`. |
| **WMA**  | `WMA<valeur>\n`         | Amplitude crête   | Amplitude en **V**. 3 décimales. Ex. `WMA4.000`, `WMA1.414`. |
| **WMO**  | `WMO<valeur>\n`         | Offset            | Tension de décalage en **V**. 2 décimales. Ex. `WMO0.00`. |
| **WMD**  | `WMD<valeur>\n`         | Rapport cyclique  | Pourcentage 0–100 %. 2 décimales. Ex. `WMD50.00`. Surtout pour carré/triangle. |
| **WMP**  | `WMP<valeur>\n`         | Phase             | Phase en degrés (0–360). 2 décimales. Ex. `WMP90.00`. |
| **WMN**  | `WMN<0\|1>\n`           | Sortie ON/OFF     | **1** = sortie activée, **0** = sortie désactivée. |

---

## Commandes voie 2 (WF)

| Commande | Format envoyé           | Rôle              | Notes |
|----------|-------------------------|-------------------|--------|
| **WFW**  | `WFWxx\n`               | Forme d’onde      | 2 chiffres, même codage que WMW (0 = sinusoïde, 1 = carré, 7 = triangle, 8 = rampe). |
| **WFF**  | `WFF<valeur>\n`          | Fréquence         | Fréquence en **µHz**, 14 chiffres (même format que WMF). |
| **WFA**  | `WFA<valeur>\n`          | Amplitude crête   | Amplitude en **V**, 3 décimales (même format que WMA). |
| **WFO**  | `WFO<valeur>\n`          | Offset            | Offset en **V**, 2 décimales (même format que WMO). |
| **WFD**  | `WFD<valeur>\n`          | Rapport cyclique  | Pourcentage 0–100 % (même format que WMD). |
| **WFP**  | `WFP<valeur>\n`          | Phase             | Phase en degrés 0–360 (même format que WMP). |
| **WFN**  | `WFN<0\|1>\n`            | Sortie ON/OFF     | **1** = sortie voie 2 activée, **0** = désactivée. |

---

## Détails d’implémentation

| Élément     | Détail | Notes |
|-------------|--------|--------|
| Fin de ligne | `\n` (0x0A) | Toutes les commandes se terminent par LF. |
| Réponse appareil | 0x0a après exécution | Lire cette réponse avant d'envoyer la commande suivante. |
| **Fréquence (WMF / WFF)** | µHz, 14 chiffres | Doc FY6900 Rev 1.8 : valeur = freq_Hz × 10⁶. Ex. 1000 Hz → `WMF00010000000000`. |
| **Amplitude (WMA / WFA)** | Décimal, 3 décimales | L’interface affiche l’amplitude **crête à crête** (V pp) et envoie la valeur telle quelle (sans conversion). Ex. `WMA2.828`. |
| **Rapport cyclique (WMD / WFD)** | Pourcentage 0–100, 2 décimales | Ex. `WMD50.00`. |
| **Phase (WMP / WFP)** | Degrés 0–360, 2 décimales | Ex. `WMP90.00`. |
| **Offset (WMO / WFO)**   | Décimal, 2 décimales | Ex. `WMO0.00`, `WFO1.50`. |
| **Forme d’onde (WMW / WFW)** | 2 chiffres | 0 = sinusoïde (WMW00), 1 = carré, 7 = triangle, 8 = rampe / dent de scie (manuel FY6900). |
| **Sortie (WMN / WFN)**   | 0 ou 1 | 0 = OFF, 1 = ON. |

---

## Séquence type (banc filtre)

Pour un point du **banc de test filtre** (voie choisie dans la config, ex. voie 1) :

1. `WMW00` (ou `WFW00` si voie 2) — sinusoïde  
2. `WMA1.414` (ou `WFA1.414`) — amplitude crête (3 décimales)  
3. `WMO0.00` (ou `WFO0.00`) — offset 0 V  
4. `WMF<fréquence en µHz, 14 chiffres>` (ou `WFF<...>`) — ex. 1000 Hz → WMF00010000000000  
5. `WMN1` (ou `WFN1`) — sortie ON  

À la fin du balayage : `WMN0` ou `WFN0` pour couper la sortie.

---

## Succession de commandes

D'après la documentation FY6900 : l'appareil **renvoie 0x0a (LF)** après exécution de chaque commande. Pour une succession de commandes, il faut **lire cette réponse** avant d'envoyer la suivante. L'implémentation (`core/fy6900_protocol.py`) fait donc : envoi → `readline()` (lecture de l'ack) → envoi de la commande suivante.

---

## Référence

- Protocole FeelTech : `docs/FY6900_communication_protocol.pdf`
- Implémentation : `core/fy6900_commands.py`, `core/fy6900_protocol.py`
- Détection automatique : le logiciel envoie `WMW00\n` pour tester si le port répond au protocole FY6900 (`core/device_detection.py`).
