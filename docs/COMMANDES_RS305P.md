# Alimentation Rockseed RS305P — Commandes implémentées

Référence du **protocole Modbus RTU** utilisé par le logiciel Banc de test automatique pour piloter l'alimentation stabilisée Rockseed RS305P. Protocole : liaison série 9600 baud, 8 bits de données, pas de parité, 1 bit d'arrêt. Le logiciel utilise uniquement les **codes fonction 03** (lecture) et **06** (écriture).

---

## Paramètres série

| Paramètre | Valeur |
|-----------|--------|
| Débit | 9600 baud |
| Bits de données | 8 |
| Parité | Aucune (N) |
| Bits d'arrêt | 1 |
| Adresse esclave | 1 (typique, configurable 1–250) |

---

## Structure de trame Modbus RTU

| Champ | Octets | Description |
|-------|--------|-------------|
| Adresse esclave | 1 | Adresse de l'alimentation (1–250). |
| Code fonction | 1 | **03** = lecture registres, **06** = écriture registre. |
| Données | N | Adresse registre, longueur ou valeur selon la fonction. |
| CRC | 2 | CRC-16 Modbus (polynôme A001), octet bas puis octet haut. |

Les registres sont sur 16 bits ; octet haut en premier, octet bas ensuite.

---

## Registres utilisés

| N° | Nom | Adresse (hex) | Plage | Décimale | R/W | Rôle |
|----|-----|---------------|-------|----------|-----|------|
| 0 | ON/OFF | 0001H | 0 ou 1 | 0 | r/w | Sortie ON (1) ou OFF (0). |
| 5 | U (tension affichée) | 0010H | 0–65535 | 2 | r | Tension mesurée en V. Valeur = tension × 100. |
| 6 | I (courant affiché) | 0011H | 0–65535 | 3 | r | Courant mesuré en A. Valeur = courant × 1000. |
| 9 | SetU | 0030H | 0–65535 | 2 | r/w | Tension cible en V. Valeur = tension × 100. |
| 10 | SetI | 0031H | 0–65535 | 3 | r/w | Courant cible en A. Valeur = courant × 1000. |

---

## Code fonction 03 — Lecture de registres

**Requête** (exemple : lire 1 registre à l'adresse 0x0010) :

| Octets | Valeur | Signification |
|--------|--------|---------------|
| 1 | 01 | Adresse esclave |
| 1 | 03 | Code fonction |
| 2 | 00 10 | Adresse de départ (registre 0x0010) |
| 2 | 00 01 | Nombre de registres à lire |
| 2 | XX XX | CRC |

**Réponse** : adresse, fonction, longueur (octets), données (2 octets par registre), CRC.

---

## Code fonction 06 — Écriture d'un registre

**Requête** (exemple : écrire 3000 dans le registre 0x0030 pour 30,00 V) :

| Octets | Valeur | Signification |
|--------|--------|---------------|
| 1 | 01 | Adresse esclave |
| 1 | 06 | Code fonction |
| 2 | 00 30 | Adresse registre (SetU) |
| 2 | 0B B8 | Donnée (3000 = 30,00 V) |
| 2 | XX XX | CRC |

**Réponse** : écho de la requête (confirmation).

---

## Conversion des valeurs

| Grandeur | Formule | Exemple |
|----------|---------|---------|
| Tension (V) | physique = registre / 100 | 3000 → 30,00 V |
| Courant (A) | physique = registre / 1000 | 500 → 0,500 A |
| ON/OFF | 0 = OFF, 1 = ON | — |

---

## Autres registres (doc Modbus)

| N° | Nom | Adresse | R/W | Notes |
|----|-----|---------|-----|-------|
| 1 | Statut protections | 0002H | r | OVP, OCP, OPP, OTP, SCP (bits). |
| 12 | OVP (sur-tension) | 0020H | r/w | Seuil protection tension. |
| 13 | OCP (sur-courant) | 0021H | r/w | Seuil protection courant. |
| 14 | OPP (sur-puissance) | 0022H–0023H | r/w | 32 bits. |
| 15 | Adresse Modbus | 9999H | r/w | Adresse esclave (1–250). |

---

## Séquence type (préréglage)

Pour appliquer un préréglage (ex. 5 V, 0,5 A, sortie OFF) :

1. FC 06, registre 0x0030, valeur 500 — tension 5,00 V  
2. FC 06, registre 0x0031, valeur 500 — courant 0,500 A  
3. FC 06, registre 0x0001, valeur 0 — sortie OFF  

Pour activer la sortie : FC 06, registre 0x0001, valeur 1.

---

## Référence

- Documentation Modbus : `docs/Modbus.pdf`
- Implémentation : `core/rs305p_protocol.py`
- Interface : `ui/views/power_supply_view.py`
- Connexion gérée dans l'onglet Alimentation (aucun paramètre dans config.json).
