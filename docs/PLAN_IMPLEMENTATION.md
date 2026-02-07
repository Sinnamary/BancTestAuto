# Plan d'implémentation par phase — Banc de test automatique

**Référence :** analyse documentation vs code (février 2025).  
**Objectif :** compléter l'application pour être conforme au [README](../README.md) et au [cahier des charges](CAHIER_DES_CHARGES.md).

---

## Vue d'ensemble des phases

| Phase | Intitulé | Priorité | Dépendances |
|-------|----------|----------|-------------|
| **1** | Raccourcis clavier et ressources | Haute | Aucune |
| **2** | Vue Multimètre — modes, plage, vitesse, mesure continue, reset | Haute | Phase 1 optionnelle |
| **3** | Vue Multimètre — fonctions math et paramètres avancés | Moyenne | Phase 2 |
| **4** | Mode enregistrement — graphique et relecture | Moyenne | Aucune (DataLogger existant) |
| **5** | Finalisation et optionnels | Basse | Phases 1–4 |

---

## Phase 1 — Raccourcis clavier et ressources

**Durée estimée :** 0,5–1 jour  
**Fichiers concernés :** `main.py` ou `ui/main_window.py`, nouveau dossier `resources/`, éventuellement `config/settings.py` pour thème.

### 1.1 Raccourcis clavier

- **Fichier :** `ui/main_window.py` (ou délégation à l’onglet actif).
- **Actions :**
  - **F5** → Mesure unique (focus sur onglet Multimètre : déclencher le clic « Mesure » ou appeler `MeterView`).
  - **Ctrl+M** → Mesure continue ON/OFF (toggle).
  - **Ctrl+R** → Reset (*RST) (multimètre).
  - **Ctrl+E** → Export CSV (historique multimètre ou vue active).
- **Implémentation :** `QShortcut` dans `MainWindow` ; si l’onglet actif est « Multimètre », les raccourcis appellent des slots/signaux exposés par `MeterView` (ex. `trigger_measure()`, `toggle_continuous()`, `trigger_reset()`, `trigger_export_csv()`).

### 1.2 Dossier resources et thème

- **Créer :** `resources/`, `resources/themes/`.
- **Fichiers :**
  - `resources/themes/dark.qss` (ou style sombre intégré dans une seule feuille).
  - Optionnel : `resources/themes/light.qss`.
- **Application du thème :** au démarrage dans `main.py` ou `MainWindow.__init__`, lire `config["display"]["theme"]` et charger le QSS correspondant via `QApplication.setStyleSheet()` ou `main_win.setStyleSheet()`.
- **Optionnel :** `resources/icons/` (icônes pour modes, connexion, etc.) — peut être reporté en Phase 5.

**Livrables Phase 1 :**
- [x] Raccourcis F5, Ctrl+M, Ctrl+R, Ctrl+E opérationnels.
- [x] Dossier `resources/themes/` créé, thème sombre appliqué par défaut.
- [x] README / doc : raccourcis déjà documentés ; aucune mise à jour obligatoire.

---

## Phase 2 — Vue Multimètre : modes, plage, vitesse, mesure continue, reset

**Durée estimée :** 2–3 jours  
**Fichiers concernés :** `core/measurement.py`, `core/scpi_protocol.py`, `ui/views/meter_view.py`. Référence : [CAHIER_DES_CHARGES § 3.2–3.6](CAHIER_DES_CHARGES.md), [INTERFACE_PYQT6 § 3](INTERFACE_PYQT6.md).

### 2.1 Extension du core (Measurement + ScpiProtocol)

- **measurement.py :**
  - Méthodes par mode : `set_voltage_dc()`, `set_voltage_ac()`, `set_current_dc()`, `set_current_ac()`, `set_resistance()`, `set_resistance_4w()`, `set_frequency()`, `set_period()`, `set_capacitance()`, `set_temperature_rtd()`, `set_diode()`, `set_continuity()` (chaque méthode envoie la commande CONF correspondante via `scpi_protocol`).
  - `set_auto_range(on: bool)`.
  - `set_range(value)` (plage manuelle selon le mode — voir `scpi_commands` / manuel OWON).
  - `set_rate(fast|medium|slow)` → RATE F / M / L.
  - `reset()` → *RST.
  - `get_current_mode()` ou équivalent (pour afficher l’unité côté UI).
- **scpi_protocol.py :** exposer les appels nécessaires (ex. `conf_voltage_dc()`, `rate_f()`, `auto()`, `range_val()`, `rst()`) en s’appuyant sur `scpi_commands.py` (déjà fourni).

### 2.2 Unité selon le mode

- Dans `meter_view.py`, le worker de mesure (ou le slot qui reçoit le résultat) doit déduire l’unité (V, A, Ω, Hz, s, F, °C, etc.) du **mode courant**.
- **Options :** soit `Measurement.get_unit_for_current_mode()` qui retourne une chaîne, soit un mapping mode → unité dans la vue. Corriger le `# TODO: selon le mode` dans `MeasureWorker` / `_on_measure_result`.

### 2.3 Connexion des contrôles dans MeterView

- **Modes :** connecter chaque bouton de la barre de modes (V⎓, V~, A⎓, A~, Ω, Ω 4W, Hz, s, F, °C, Diode, Continuité) à la méthode `Measurement` correspondante. Un seul mode actif (déjà `QButtonGroup`).
- **Plage :** connecter Auto/Manuel et le `QComboBox` de plage à `set_auto_range` / `set_range` ; remplir le combo selon le mode (liste de plages par mode — éventuellement dans `scpi_commands` ou `measurement`).
- **Vitesse :** connecter les 3 boutons Rapide / Moyenne / Lente à `set_rate(...)`.
- **Mesure continue :** timer (QTimer) + appel périodique à `read_value()` (et mise à jour affichage + historique). Bouton toggle pour démarrer/arrêter. Respecter `config["measurement"]["refresh_interval_ms"]`.
- **Reset :** bouton « Reset (*RST) » connecté à `measurement.reset()`.

### 2.4 Exposition des actions pour les raccourcis (Phase 1)

- Si les raccourcis sont gérés dans `MainWindow`, `MeterView` doit exposer des slots publics ou des signaux : par ex. `trigger_measure()`, `toggle_continuous_measure()`, `trigger_reset()`, `trigger_export_csv()`, appelables depuis la fenêtre principale lorsque l’onglet « Multimètre » est actif.

**Livrables Phase 2 :**
- [x] Tous les modes de mesure configurables depuis l’interface et reflétés en SCPI.
- [x] Plage (Auto/Manuel) et vitesse (Rapide/Moyenne/Lente) connectées.
- [x] Unité affichée cohérente avec le mode (plus de TODO).
- [x] Mesure continue opérationnelle (timer + MEAS?).
- [x] Reset (*RST) opérationnel.
- [x] Raccourcis Phase 1 pleinement fonctionnels sur l’onglet Multimètre.

---

## Phase 3 — Vue Multimètre : fonctions math et paramètres avancés

**Durée estimée :** 1,5–2 jours  
**Fichiers concernés :** `core/measurement.py`, `core/scpi_protocol.py`, `core/scpi_commands.py`, `ui/views/meter_view.py`. Référence : CDC § 3.7–3.11, INTERFACE_PYQT6 § 3.5–3.6.

### 3.1 Fonctions math (CALCulate)

- **Core :** dans `ScpiProtocol` / `Measurement`, ajouter : `calc_off()`, `calc_rel(offset)`, `calc_db()`, `calc_dbm()`, `calc_average()` ; requêtes pour stats : `calc_average_all()`, `maximum()`, `minimum()`, etc. (voir CDC § 3.10).
- **UI :** 
  - Cinq options (Aucun, Rel, dB, dBm, Moyenne) déjà en place ; les connecter aux commandes CALC.
  - Rel : ajouter un champ (QDoubleSpinBox ou QLineEdit) pour l’offset, connecté à `calc_rel(offset)`.
  - dB / dBm : ajouter un `QComboBox` pour la référence (Ω) : 50, 75, 600, etc. (liste CDC).
  - Moyenne : zone stats (Min, Max, Moyenne, N) avec `QLabel` + bouton « Réinitialiser stats » ; rafraîchir via requêtes SCPI.

### 3.2 Affichage secondaire (Hz)

- Case « Afficher Hz » déjà présente ; connecter à `FUNC2 "FREQ"` / `FUNC2 "NONe"` et, en mesure continue ou sur mesure unique, récupérer `MEAS2?` pour remplir le label secondaire.

### 3.3 Paramètres avancés (panneau repliable)

- **Température :** type RTD (KITS90 / PT100), unité (°C / °F / K), mode affichage (TEMP / MEAS / ALL) — `QComboBox` et commandes SCPI § 3.8.
- **Continuité :** seuil en Ω — `QDoubleSpinBox` + `CONT:THRE <value>`.
- **Buzzer :** case à cocher ON/OFF — `SYST:BEEP:STAT`.
- **UI :** un `QGroupBox` repliable (ou bouton « Afficher / Masquer ») contenant ces contrôles, comme décrit dans INTERFACE_PYQT6 § 3.6.

**Livrables Phase 3 :**
- [x] Rel, dB, dBm, Moyenne opérationnels avec champs associés et stats.
- [x] Affichage secondaire (Hz) connecté (FUNC2 + MEAS2?).
- [x] Panneau « Paramètres avancés » (température, continuité, buzzer) ajouté et connecté.

---

## Phase 4 — Mode enregistrement : graphique temps réel et relecture

**Durée estimée :** 2–3 jours  
**Fichiers concernés :** `ui/views/logging_view.py`, éventuellement `core/data_logger.py` (callbacks). Dépendance : `pyqtgraph` ou `matplotlib` (voir `requirements.txt`). Référence : CDC § 3.13.

### 4.1 Graphique temps réel

- Remplacer le placeholder (QFrame) par un widget de courbe (recommandation : `pyqtgraph` pour intégration PyQt6 et performances).
- À chaque point enregistré (callback du `DataLogger`), ajouter le point (temps écoulé ou timestamp, valeur) à la série et mettre à jour le graphique.
- Configurer axe X (temps), axe Y (valeur + unité), titre.

### 4.2 Relecture de fichiers CSV

- Bouton « Charger un fichier CSV » (ou « Relecture ») : `QFileDialog`, choix d’un CSV horodaté produit par l’application.
- Parser le CSV (timestamp, valeur, unité, mode) et afficher la courbe dans le même widget ou un second graphique (onglet ou panneau dédié « Relecture »).

### 4.3 Comparaison de plusieurs courbes

- Possibilité de charger plusieurs fichiers et de superposer les courbes (couleurs différentes, légende). Stocker en mémoire les séries (liste de listes (t, value)) et les tracer sur le même graphique avec des styles distincts.

**Livrables Phase 4 :**
- [ ] Graphique temps réel opérationnel pendant l’enregistrement.
- [ ] Relecture d’un fichier CSV et affichage de la courbe.
- [ ] Comparaison d’au moins deux courbes (superposition avec légende ou labels).

---

## Phase 5 — Finalisation et optionnels

**Durée estimée :** 0,5–1 jour (optionnel)

### 5.1 Icônes

- Créer `resources/icons/` et ajouter des icônes pour : modes de mesure (optionnel), indicateurs de connexion, actions (mesure, export). Les utiliser dans la barre de connexion et/ou les boutons de mode si souhaité.

### 5.2 Thème clair

- **Implémenté :** fichier `resources/themes/light.qss` ; menu **Configuration → Thème → Clair / Foncé** (bascule immédiate). La valeur est stockée dans `display.theme` ; **Fichier → Sauvegarder config** pour conserver au prochain lancement. Voir README § Thème d’affichage.

### 5.3 Module owon_ranges.py (optionnel)

- Extraire les plages par mode (tension DC/AC, courant, résistance, capacité, etc.) dans un module dédié `core/owon_ranges.py` pour faciliter la maintenance et le remplissage des listes de plage dans l’UI. Réutilisé par `measurement` et `meter_view`.

### 5.4 Tests et documentation

- Ajouter ou compléter les tests unitaires pour les nouvelles méthodes de `Measurement` et les commandes SCPI utilisées.
- Mettre à jour le README si de nouvelles entrées (ex. raccourcis) n’y figuraient pas déjà ; vérifier que DEVELOPPEMENT.md et CAHIER_DES_CHARGES restent cohérents.

**Livrables Phase 5 :**
- [ ] (Optionnel) Icônes en place.
- [x] Thème clair sélectionnable (menu Configuration → Thème ; sauvegarde via Fichier → Sauvegarder config).
- [ ] (Optionnel) `owon_ranges.py` créé et utilisé.
- [ ] Tests et doc à jour si nécessaire.

---

## Ordre recommandé et jalons

1. **Phase 1** — à faire en premier : gain rapide (raccourcis + thème), pas de dépendance.
2. **Phase 2** — cœur métier multimètre : indispensable pour un usage « complet » du multimètre depuis l’UI.
3. **Phase 3** — peut suivre Phase 2 immédiatement ou après un jalon de recette sur Phase 2.
4. **Phase 4** — peut être menée en parallèle de la Phase 3 (équipe ou tâches distinctes), car elle ne dépend que du `DataLogger` existant.
5. **Phase 5** — en fin de projet ou par itérations (icônes, thème clair, plages, tests).

**Jalons suggérés :**
- **J1** : Phase 1 terminée → application utilisable avec raccourcis et thème.
- **J2** : Phase 2 terminée → multimètre pleinement pilotable (modes, plage, vitesse, continue, reset).
- **J3** : Phases 3 et 4 terminées → conformité fonctionnelle avec le cahier des charges (math, avancés, enregistrement avec graphique et relecture).
- **J4** : Phase 5 (optionnels) selon besoin.

---

## Références

- [Cahier des charges](CAHIER_DES_CHARGES.md) — § 2 (architecture), § 3 (spécification fonctionnelle), § 2.7 (config).
- [Conception interface PyQt6](INTERFACE_PYQT6.md) — structure des vues et widgets.
- [Guide de développement](DEVELOPPEMENT.md) — arborescence et rôles des modules.
- [Banc de test filtre](BANC_TEST_FILTRE.md) — déjà implémenté ; pas de phase dédiée ici.
