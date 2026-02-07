# Banc de test de filtre — Spécifications

**Version :** 1.0  
**Date :** 6 février 2025  
**Références :** FY6900_communication_protocol.pdf, XDM1000_Digital_Multimeter_Programming_Manual.pdf

---

## 1. Reformulation du besoin

### 1.1 Objectif

Le **banc de test filtre** permet de **caractériser un filtre au format Bode** (réponse en fréquence). Il fournit :

- Un **balayage en fréquence entièrement modifiable** (f_min, f_max, N points, échelle, délai, Ue) ; valeurs par défaut dans `config.json`, ajustables pour une **bonne qualification du filtre** (passe-bas, coupure, etc.).
- Un **tableau de résultats** : fréquence (Hz) | Us (V) | Us/Ue | 20×log₁₀(Us/Ue) [dB]
- Un **graphique au format Bode** (semi-log) : gain en dB vs fréquence, pour analyse et export
- Une **impression** possible sur papier semi-log

Ce mode orchestre FY6900 et OWON ; chaque appareil reste **commandable individuellement** avec toutes les commandes du matériel (voir cahier des charges).

### 1.2 Schéma fonctionnel

```
┌─────────────────────┐      ┌─────────────┐      ┌─────────────────┐
│  Générateur FY6900  │      │   FILTRE    │      │  Multimètre     │
│  (FeelTech)         │─────▶│   À TESTER  │─────▶│  OWON XDM       │
│  Ue = 1 V RMS       │      │             │      │  mesure Us      │
│  sinusoïde          │      │  entrée     │      │  tension AC     │
└─────────────────────┘      │  sortie     │      └─────────────────┘
         │                   └─────────────┘               │
         │                                                  │
         └──────────────────┬───────────────────────────────┘
                            │
                     ┌──────▼──────┐
                     │   PC        │
                     │  Application│
                     │  PyQt6      │
                     └─────────────┘
```

- **Ue** : tension d’entrée du filtre = 1 V RMS (fixe, imposée par le générateur)
- **Us** : tension de sortie du filtre (mesurée par le multimètre en AC)
- **Gain** : Us/Ue (linéaire) ou 20×log₁₀(Us/Ue) (dB)

### 1.3 Hypothèses

- Générateur FY6900 (FeelTech) : sortie sinusoïdale, amplitude réglable pour obtenir 1 V RMS à l’entrée du filtre
- Multimètre OWON : mode tension AC, mesure RMS
- Pour un signal sinusoïdal : **amplitude crête = Ueff × √2** → 1 V RMS ≈ 1,414 V crête → WMA1.414

---

## 2. Protocole générateur FY6900 (FeelTech)

### 2.1 Communication

| Paramètre     | Valeur    |
|---------------|-----------|
| Débit         | 115200 bps |
| Fin de commande | 0x0a (LF) |
| Réponse       | 0x0a après exécution |

### 2.2 Commandes nécessaires pour le banc filtre

| Commande | Format | Description | Exemple |
|----------|--------|-------------|---------|
| **WMW**  | WMWxx + 0x0a | Forme d’onde canal principal | WMW0 = sinusoïde |
| **WMF**  | WMFxxxxxxxxxxxxxx + 0x0a | Fréquence (14 chiffres, unité µHz) | WMF1000000000 = 100 Hz |
| **WMA**  | WMAxx.xx + 0x0a | Amplitude crête (V) | WMA1.414 = 1 V RMS |
| **WMO**  | WMOxx.xx + 0x0a | Offset (V) | WMO0 = 0 V |
| **WMN**  | WMNx + 0x0a | Sortie ON/OFF | WMN1 = ON, WMN0 = OFF |

### 2.3 Conversion fréquence → commande WMF

Fréquence en Hz → valeur en µHz (14 chiffres) :

| f (Hz) | Valeur WMF |
|--------|------------|
| 10     | WMF00010000000 |
| 100    | WMF00100000000 |
| 1000   | WMF01000000000 |
| 10 000 | WMF10000000000 |

Formule : `valeur = int(f * 1_000_000)` formatée sur 14 chiffres avec zéros à gauche.

### 2.4 Séquence type pour une mesure

**Au démarrage du balayage**, le logiciel applique d’abord la configuration connue (depuis config.json), puis à chaque point :

1. WMW0 — sinusoïde (ou valeur depuis `generator.waveform`)
2. WMA &lt;amplitude_crête&gt; — ex. 1,414 V pour 1 V RMS (depuis `filter_test.ue_rms` ou `generator.amplitude_v_peak`)
3. WMO0 — offset 0 V (depuis `generator.offset_v`)
4. WMF&lt;freq&gt; — fréquence de test (balayage)
5. WMN1 — sortie ON
6. Attendre stabilisation (ex. 100–500 ms, `filter_test.settling_ms`)
7. Lancer mesure multimètre (Us)
8. (Optionnel) WMN0 — sortie OFF entre deux fréquences

---

## 3. Protocole multimètre OWON (SCPI)

### 3.1 Commandes utilisées

| Commande | Description |
|----------|-------------|
| `CONF:VOLT:AC` | Mode tension AC |
| `AUTO` | Plage automatique |
| `MEAS?` ou `MEAS1?` | Mesure tension (V RMS) |
| `FUNC?` | Vérifier le mode |

### 3.2 Mode de mesure

Tension AC (RMS) sur la sortie du filtre.

---

## 4. Logique de mesure et calculs

### 4.1 Paramètres du balayage (modifiables pour une bonne qualification)

Pour **qualifier correctement le filtre** (pente de coupure, résonance, bande passante, etc.), tous les paramètres du balayage sont **modifiables** dans l'interface ; les valeurs par défaut viennent de `config.json` (section `filter_test`) et peuvent être adaptées à chaque filtre :

| Paramètre | Description | Valeurs typiques | Rôle pour la qualification |
|-----------|-------------|------------------|-----------------------------|
| **Voie générateur** | Voie du FY6900 utilisée pour le balayage | 1 ou 2 | Choisir la sortie du générateur (FY6900 a deux voies) |
| f_min     | Fréquence minimale (Hz) | 10, 20, 50 | Adapter à la plage utile du filtre |
| f_max     | Fréquence maximale (Hz) | 100 kHz, 1 MHz | Couvrir la bande passante ou la coupure |
| N_points  | Nombre de points | 20–100 | Résolution du tracé Bode (plus de points = courbe plus lisse) |
| Échelle   | Linéaire ou logarithmique | Log recommandé | Log pour Bode classique, lin pour zoom sur une bande |
| Temps stabilisation | Délai après changement de fréquence (ms) | 100–500 | Limiter les erreurs de mesure à chaque pas |
| Ue        | Tension d’entrée effective (V RMS) | 1,0 (fixe) | Niveau d'excitation du filtre |

### 4.2 Échelle logarithmique des fréquences

Pour un balayage log entre f_min et f_max avec N points :

```
f[i] = f_min × (f_max / f_min)^(i / (N-1))   pour i = 0, 1, ..., N-1
```

### 4.3 Calculs

- **Us/Ue** : gain linéaire (Ue = 1 V)
- **20×log₁₀(Us/Ue)** : gain en dB (limite à −∞ si Us = 0)

---

## 5. Tableau de résultats

| Colonne | Unité | Description |
|---------|-------|-------------|
| f       | Hz    | Fréquence |
| Us      | V     | Tension de sortie mesurée (RMS) |
| Us/Ue   | —     | Gain linéaire |
| Gain dB | dB    | 20×log₁₀(Us/Ue) |

### 5.1 Exemple

| f (Hz) | Us (V) | Us/Ue | Gain (dB) |
|--------|--------|-------|-----------|
| 10     | 0.998  | 0.998 | −0.02     |
| 100    | 0.995  | 0.995 | −0.04     |
| 1000   | 0.707  | 0.707 | −3.01     |
| 10000  | 0.100  | 0.100 | −20.0     |

---

## 6. Graphique semi-logarithmique

### 6.1 Axes (point de vue mathématique)

- **Axe des abscisses (X)** : **fréquence f (Hz)** — **toujours en échelle logarithmique** (log f ou log₁₀ f). C’est le cas standard pour un diagramme de Bode.
- **Axe des ordonnées (Y)** :
  - **Si l’on affiche le gain linéaire Us/Ue** : échelle **linéaire** (on trace Us/Ue tel quel).
  - **Si l’on affiche le gain en dB** : on trace **20×log₁₀(Us/Ue)** ; la grandeur portée en Y est alors **logarithmique** (log du gain linéaire). L’axe Y est en général gradué linéairement en dB (−40 dB, −20 dB, 0 dB, etc.), ce qui correspond à une représentation logarithmique du gain Us/Ue.

En résumé : **fréquence toujours en log** ; **Us/Ue en linéaire** (échelle linéaire) ou **en dB** (représentation logarithmique du gain).

### 6.2 Courbe de Bode

- **20×log(Us/Ue) en dB** en fonction de **log(f)** : courbe de Bode en gain (format classique).
- Format semi-log : abscisse en log (fréquence), ordonnée soit linéaire (Us/Ue), soit en dB (logarithmique du gain).

### 6.3 Export pour impression

- **CSV** : tableau complet (f, Us, Us/Ue, Gain dB)
- **Image** (PNG, PDF) : courbe semi-log, prête à imprimer
- **Papier semi-log** : mise en page compatible avec papier 3 ou 4 décades

---

## 7. Architecture d’implémentation

### 7.1 Nouveaux modules

| Module | Rôle |
|--------|------|
| `core/fy6900_protocol.py` | Protocole FY6900 (WMW, WMF, WMA, WMN, etc.) |
| `core/filter_test.py` | Orchestration : balayage fréquence, mesures, calculs |
| `ui/filter_test_view.py` | Interface : config, tableau, graphique, export |

### 7.2 Connexions série

- **Port 1** : multimètre OWON (SCPI, ex. 9600 ou 115200 bauds)
- **Port 2** : générateur FY6900 (115200 bauds, obligatoire)

Les liaisons série sont gérées **par classe** (une instance par port), avec buffers et option de log des échanges (voir cahier des charges § 2.5). Les I/O série sont exécutées dans un **thread dédié** (ex. QThread) pour garder l’interface réactive (cahier des charges § 2.6, DEVELOPPEMENT.md § 3.4).

### 7.3 Dépendances et principe d’appel

- **Classes distinctes par appareil** : chaque appareil de mesure est piloté par sa propre classe (fichiers séparés). Ces classes sont **appelées** par le module banc pour piloter le banc de test.
- Réutiliser `SerialConnection` pour les deux ports.
- Réutiliser la classe dédiée OWON (`ScpiProtocol` / couche mesure) pour le multimètre.
- Classe dédiée FeelTech (`Fy6900Protocol` ou équivalent) pour le générateur.
- **`filter_test.py`** : n’implémente pas les protocoles ; il **appelle** les classes multimètre et générateur pour orchestrer le balayage en fréquence, les mesures et les calculs (gain, Bode).

### 7.4 Structure proposée

```
core/
├── serial_connection.py
├── scpi_protocol.py        # OWON
├── fy6900_protocol.py      # FeelTech FY6900 (NOUVEAU)
├── measurement.py
├── data_logger.py
└── filter_test.py          # Banc filtre (NOUVEAU)

ui/
├── filter_test_view.py     # Vue banc filtre (NOUVEAU)
└── ...
```

---

## 8. Configuration (config.json)

### 8.1 Liaisons série et banc filtre

Chaque liaison série a ses paramètres dans le JSON : **`serial_multimeter`** (multimètre) et **`serial_generator`** (générateur FY6900). Les classes reprennent ces paramètres à l’initialisation et définissent des paramètres par défaut si une clé manque. Le banc filtre utilise la section **`filter_test`** pour le balayage (f_min, f_max, n_points, etc.) et les classes générateur/multimètre utilisent respectivement `serial_generator` et `serial_multimeter` pour la connexion. La section **`generator`** définit les **paramètres par défaut du générateur** (forme d’onde, fréquence, amplitude crête, offset), utilisés par l’onglet Générateur et par le banc filtre.

### 8.2 Configuration initiale connue (banc filtre)

**Le banc de test filtre part toujours d’une configuration connue, et non de la configuration précédente de l’équipement.** Au démarrage d’un balayage, le logiciel :

1. **Applique** sur le générateur la configuration définie dans `config.json` : forme d’onde (ex. sinusoïde depuis `generator.waveform`), amplitude crête (déduite de `filter_test.ue_rms` : Ueff × √2), offset (`generator.offset_v`), voie (`filter_test.generator_channel`).
2. Puis effectue le balayage en fréquence (f_min → f_max) en réglant la fréquence à chaque pas.

Ainsi, le résultat ne dépend pas de l’état dans lequel le générateur était laissé après une utilisation précédente (onglet Générateur ou autre).

Exemple (structure complète dans le cahier des charges § 2.7) :

```json
{
  "generator": {
    "default_channel": 1,
    "waveform": 0,
    "frequency_hz": 1000,
    "amplitude_v_peak": 1.414,
    "offset_v": 0
  },
  "serial_generator": {
    "port": "COM4",
    "baudrate": 115200,
    "timeout": 2,
    "write_timeout": 2,
    "log_exchanges": false
  },
  "filter_test": {
    "generator_channel": 1,
    "f_min_hz": 10,
    "f_max_hz": 100000,
    "n_points": 50,
    "scale": "log",
    "settling_ms": 200,
    "ue_rms": 1.0
  }
}
```

---

## 9. Interface utilisateur

### 9.1 Onglet « Banc de test filtre »

- **Zone config (balayage modifiable)** : **voie générateur (Voie 1 / Voie 2)**, f_min, f_max, N_points, échelle (lin/log), délai de stabilisation, Ue — tous modifiables pour **qualifier correctement le filtre** (coupure, pente, bande passante). Valeurs par défaut depuis `config.json`, modifiables à la volée.
- **Connexions** : port générateur, port multimètre (paramètres existants ou dédiés)
- **Boutons** : [Démarrer balayage] [Arrêter] [Exporter CSV] [Exporter graphique]
- **Tableau** : f | Us | Us/Ue | Gain (dB)
- **Graphique** : courbe de Bode (semi-log) temps réel — gain en dB vs fréquence
- **Barre de progression** : avancement du balayage

### 9.2 Intégration

- Nouvel onglet à côté de « Mode Enregistrement » et « Mesure »
- Ou mode dédié accessible depuis le menu

---

## 10. Planning suggéré

| Phase | Contenu |
|-------|---------|
| 1 | Module `fy6900_protocol.py` (WMW, WMF, WMA, WMN) |
| 2 | Module `filter_test.py` (balayage, mesures, calculs) |
| 3 | Vue `filter_test_view.py` (config, tableau, graphique) |
| 4 | Export CSV et image semi-log |
| 5 | Tests avec filtre réel |

---

## 11. Annexes

### 11.1 Référence rapide FY6900

- Document : `docs/FY6900_communication_protocol.pdf`
- WMW0 = sinusoïde
- WMF : 14 chiffres, unité µHz (1 Hz = 1 000 000 µHz)
- WMA : amplitude crête en V (1 V RMS ≈ WMA1.414)

### 11.2 Référence OWON

- Document : `docs/XDM1000_Digital_Multimeter_Programming_Manual.pdf`
- `CONF:VOLT:AC` + `MEAS?` pour tension AC RMS

---

## 12. Évolutions possibles — Mieux caractériser le filtre

Les fonctionnalités suivantes permettraient d’obtenir une **meilleure approche des caractéristiques du filtre** avec le matériel actuel (OWON + FY6900) ou en évolution.

### 12.1 Avec le matériel actuel (gain uniquement)

| Fonctionnalité | Description | Bénéfice |
|----------------|-------------|----------|
| **Fréquence(s) de coupure à −3 dB** | Détection automatique des points où Gain = −3 dB (interpolation entre points si besoin). Affichage fc pour passe-bas / passe-haut, fc1/fc2 pour passe-bande. | Qualification directe de la bande passante et des coupures. |
| **Pente de coupure (roll-off)** | Estimation de la pente en dB/décade dans la zone de transition (régression sur les points entre −1 et −25 dB par exemple). Afficher ex. « −20 dB/déc » (ordre 1), « −40 dB/déc » (ordre 2). | Donne une idée de l’ordre du filtre et de la raideur de la coupure. |
| **Moyenne par fréquence** | À chaque fréquence du balayage, effectuer N mesures (ex. 3 à 5), afficher la moyenne (et optionnellement l’écart-type). | Réduction du bruit et courbe de Bode plus stable. |
| **Seuil de bruit / plancher** | Seuil minimal Us (ou gain dB) en dessous duquel la mesure est considérée comme bruit (multimètre). Option : ne pas tracer ou marquer ces points, ou afficher une zone « bruit ». | Évite de surinterpréter la queue de courbe quand le filtre atténue fortement. |
| **Zoom / balayage ciblé** | Après un premier balayage, permettre de définir une plage [f_min_zoom, f_max_zoom] et relancer un balayage avec plus de points (ex. 100) en échelle lin ou log. | Meilleure résolution autour de fc ou d’un pic de résonance. |
| **Résumé « Caractéristiques »** | Panneau affichant : fc (−3 dB), pente (dB/déc), gain max (dB), bande passante à −3 dB (pour passe-bande). Rempli automatiquement après le balayage. | Synthèse lisible sans interprétation manuelle. |
| **Courbe de référence / comparaison** | Superposition d’une courbe théorique (ex. 1er ordre avec fc choisi, 2e ordre Butterworth) ou chargement d’un CSV de référence pour comparer deux filtres ou deux mesures. | Vérification par rapport à un modèle ou à un filtre de référence. |
| **Sauvegarde / chargement de courbes** | Sauvegarder le résultat (f, Us, gain dB) en JSON/CSV avec métadonnées (date, paramètres du balayage). Recharger pour comparaison ou rapport. | Traçabilité et comparaison avant/après. |
| **Rapport exportable** | Génération d’un rapport (PDF ou HTML) : graphique Bode, tableau résumé, fc, pente, paramètres du balayage. | Documentation de qualification. |

### 12.2 Indicateurs de qualité (toujours avec matériel actuel)

| Indicateur | Description |
|------------|-------------|
| **Stabilité par point** | Si moyenne de N mesures : afficher écart-type ou incertitude par fréquence (optionnel dans le tableau ou en tooltip). |
| **Cohérence Ue** | Vérification périodique de Ue (mesure sur entrée du filtre si possible, ou rappel de la valeur configurée) pour s’assurer que le niveau d’excitation est constant. |

### 12.3 Évolutions nécessitant des mesures supplémentaires (phase, etc.)

| Fonctionnalité | Description | Limite actuelle |
|----------------|-------------|------------------|
| **Phase (déphasage φ)** | Courbe de Bode phase : φ(f) en degrés ou radians. Nécessite mesure de phase (décalage temporel ou analyseur). | Le multimètre RMS seul ne donne pas la phase ; il faudrait un oscillo 2 voies ou un analyseur. |
| **Délai de groupe** | −dφ/dω pour analyser la linéarité de phase. | Dépend de la mesure de phase. |
| **Courbe de Bode complète** | Gain + phase sur un même écran (format Bode classique). | Phase non disponible avec OWON seul. |

### 12.4 Priorisation suggérée

- **Priorité haute (qualification immédiate)** : fréquence de coupure −3 dB, pente en dB/décade, résumé « Caractéristiques », moyenne par fréquence.
- **Priorité moyenne** : zoom / balayage ciblé, courbe de référence ou comparaison, seuil bruit, sauvegarde/chargement courbes.
- **Priorité plus basse** : rapport PDF/HTML, indicateurs de stabilité détaillés ; phase/délai de groupe en cas d’évolution du matériel.
