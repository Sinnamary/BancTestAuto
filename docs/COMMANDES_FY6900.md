# Générateur FeelTech FY6900 — Commandes implémentées

Référence des **commandes série** utilisées par le logiciel Banc de test automatique pour piloter le générateur de signaux FeelTech FY6900. Protocole : liaison série, débit 115200, fin de ligne `LF` (0x0A). Le logiciel permet de choisir la **voie (1 ou 2)** dans l’interface ; les commandes ci‑dessous s’appliquent au canal configuré (voir manuel FY6900 pour le préfixe éventuel de canal).

---

## Commandes principales

| Commande | Format envoyé | Rôle | Notes |
|----------|----------------|------|--------|
| **WMW** | `WMW<n>\n` | Forme d’onde | `n` = type de forme. **0** = sinusoïde. Autres codes selon manuel (carré, triangle, etc.). |
| **WMF** | `WMF<14 chiffres>\n` | Fréquence | Fréquence en **µHz** sur 14 chiffres. Ex. 100 Hz → `WMF00100000000`. Le logiciel convertit Hz → µHz. |
| **WMA** | `WMA<valeur>\n` | Amplitude crête | Amplitude en **V crête**. Ex. 1,414 V crête ≈ 1 V RMS sinusoïdal. 3 décimales. |
| **WMO** | `WMO<valeur>\n` | Offset | Tension de décalage en **V**. 2 décimales. |
| **WMN** | `WMN<0|1>\n` | Sortie ON/OFF | **1** = sortie activée, **0** = sortie désactivée. Coupe ou active la sortie du générateur. |

---

## Détails d’implémentation

| Élément | Détail | Notes |
|--------|--------|--------|
| Fin de ligne | `\n` (LF) | Toutes les commandes se terminent par 0x0A. |
| WMF | 14 chiffres, unité µHz | Valeur bornée entre 0 et 99999999999999. 100 Hz → 100 000 000 µHz. |
| WMA | Décimal, 3 décimales | Ex. `WMA1.414` pour environ 1 V RMS. |
| WMO | Décimal, 2 décimales | Ex. `WMO0.00`. |
| Voie 1 / 2 | Choix dans l’interface | Paramètre `generator_channel` (1 ou 2) ; selon modèle FY6900, les commandes peuvent cibler le canal courant ou un préfixe peut être requis (voir manuel). |

---

## Séquence type (banc filtre)

Pour un point du **banc de test filtre**, le logiciel envoie la séquence suivante (sinusoïde 1 V RMS, fréquence donnée, sortie ON) :

1. `WMW0` — sinusoïde  
2. `WMA1.414` — 1 V crête (≈ 1 V RMS)  
3. `WMO0.00` — offset 0 V  
4. `WMF<fréquence en µHz>` — fréquence du point  
5. `WMN1` — sortie ON  

À la fin du balayage : `WMN0` pour couper la sortie.

---

## Référence

- Protocole FeelTech : `docs/FY6900_communication_protocol.pdf`
- Implémentation : `core/fy6900_commands.py`, `core/fy6900_protocol.py`
- Détection automatique : le logiciel envoie `WMW0\n` pour tester si le port répond au protocole FY6900 (`core/device_detection.py`).
