# Plan de développement — Banc filtre avec oscilloscope

**Version :** 1.0  
**Date :** 11 février 2026  
**Contexte :** Le multimètre n’est pas adapté à la mesure de la valeur efficace au-delà de ~2 kHz. Le banc filtre doit utiliser l’oscilloscope (Hanmatek DOS1102) pour Ue (canal 1), Us (canal 2) et la phase, avec une bande passante adaptée.

**Documents associés :**
- [Cahier des charges Visualisation Bode](CAHIER_DES_CHARGES_VISUALISATION_BODE.md)
- [Banc de test de filtre](BANC_TEST_FILTRE.md)
- [Évolution 4 équipements](EVOLUTION_4_EQUIPEMENTS.md)

---

## État d’avancement global

| Phase | Intitulé | Statut | Date |
|-------|----------|--------|------|
| 1 | Réorganisation des onglets | Fait | 11 fév. 2026 |
| 2 | Source de mesure : oscilloscope dans le core | Fait | 11 fév. 2026 |
| 3 | UI Banc filtre et orchestration | Fait | 11 fév. 2026 |
| 4 | Format CSV et visualisation Bode | À faire | — |
| 5 | Courbe de Bode phase (optionnel) | À faire | — |
| 6 | Nettoyage et documentation | À faire | — |

*Mettre à jour la colonne « Statut » (À faire / En cours / Fait) et « Date » au fil de l’avancement.*

---

## Phase 1 — Réorganisation des onglets

**Objectif :** Placer l’onglet Oscilloscope juste avant Banc filtre pour refléter la chaîne Générateur → Oscilloscope → Banc filtre.

**Ordre actuel :**  
Multimètre, Générateur, Enregistrement, Banc filtre, Calcul filtre, Alimentation, Terminal série, Oscilloscope.

**Ordre cible :**
1. Multimètre  
2. Générateur  
3. **Oscilloscope**  
4. **Banc filtre**  
5. Calcul filtre  
6. Enregistrement  
7. Alimentation  
8. Terminal série  

**Tâches :**
- [x] Modifier l’ordre des `addTab` dans `maquette/ui/main_window.py`
- [x] Reporter le même ordre dans `ui/main_window.py`
- [x] Mettre à jour `docs/INTERFACE_PYQT6.md` (liste des onglets)
- [x] Mettre à jour `docs/AIDE.md` (liste des onglets)

**Statut :** Fait (11 fév. 2026)

---

## Phase 2 — Source de mesure : oscilloscope dans le core

**Objectif :** Le banc filtre peut s’appuyer sur l’oscilloscope au lieu du multimètre pour la mesure (Ue, Us, phase).

**Tâches :**
- [x] Introduire une abstraction « source de mesure » (ex. interface ou type union : multimètre / oscilloscope)
- [x] Implémenter la lecture oscilloscope : Ue (canal 1, RMS), Us (canal 2), phase (Ch2 vs Ch1) via protocole Hanmatek DOS1102
- [x] Étendre `BodePoint` (`core/filter_test.py`) avec un champ optionnel `phase_deg`
- [x] Adapter `FilterTest` pour accepter soit `Measurement` (multimètre), soit une source oscilloscope
- [x] Ajouter dans la config (ex. `filter_test` / `banc_filtre`) : source (Multimètre / Oscilloscope), canaux Ue/Us si oscillo (ex. Ch1=Ue, Ch2=Us)

**Statut :** Fait (11 fév. 2026). Fichiers : `core/bode_measure_source.py` (Protocol `BodeMeasureSource`, `MultimeterBodeAdapter`, `OscilloscopeBodeSource`), `core/filter_test.py` (BodePoint.phase_deg, FilterTest avec measure_source), config `filter_test.measure_source` / `oscillo_channel_ue` / `oscillo_channel_us`, bridge utilise `MultimeterBodeAdapter`.

---

## Phase 3 — UI Banc filtre et orchestration

**Objectif :** Choix de la source de mesure dans l’onglet Banc filtre et exécution du balayage via l’oscilloscope.

**Tâches :**
- [x] Dans `FilterTestView` : sélecteur « Source de mesure » (Multimètre / Oscilloscope), avec indication « Multimètre limité < 2 kHz »
- [x] Lorsque « Oscilloscope » : rappel des canaux (Ch1=Ue, Ch2=Us), pas de dépendance au panneau multimètre pour le sweep
- [x] Brancher l’orchestration : `FilterTest` reçoit la source choisie (multimètre ou oscilloscope) ; connexion oscilloscope via la barre (déjà connecté)
- [x] Vérifier que Détecter / Connecter tout inclut l’oscilloscope pour le banc filtre

**Statut :** Fait (11 fév. 2026). `SwitchableBodeMeasureSource` dans le bridge ; sélecteur dans FilterTestView ; `set_measure_source_kind` avant démarrage ; persistance `measure_source` dans config (Fichier → Sauvegarder config). Détecter / Connecter tout gère déjà les 4 équipements dont l’oscilloscope.

---

## Phase 4 — Format CSV et visualisation Bode (CDC Bode)

**Objectif :** CSV compatible ancien format + colonnes optionnelles (Ue, phase) ; visualisation Bode à jour.

**Tâches :**
- [ ] Conserver colonnes existantes : `f_Hz` ; `Us_V` ; `Us_Ue` ; `Gain_dB`
- [ ] Ajouter colonnes optionnelles : `Ue_V`, `Phase_deg` (lorsque l’acquisition est faite via oscilloscope)
- [ ] Viewer Bode (Fichier → Ouvrir CSV Banc filtre) : détection des colonnes par en-tête ; si `Phase_deg` présent, le charger pour usage ultérieur (Phase 5)
- [ ] Mettre à jour le cahier des charges [CAHIER_DES_CHARGES_VISUALISATION_BODE.md](CAHIER_DES_CHARGES_VISUALISATION_BODE.md) : structure des données (§ 3) avec colonnes optionnelles, mention acquisition possible via oscilloscope

**Statut :** À faire

---

## Phase 5 — Courbe de Bode phase (optionnel, P2)

**Objectif :** Afficher la phase en plus du gain (diagramme de Bode phase).

**Tâches :**
- [ ] Étendre le cahier des charges Bode : exigence optionnelle « Courbe phase (deg) vs fréquence » (axe X log), quadrillage, option de recherche de phase cible (ex. -45°)
- [ ] Dans le viewer Bode : onglet ou second graphique « Phase » utilisant la colonne `Phase_deg` si présente dans le CSV

**Statut :** À faire

---

## Phase 6 — Nettoyage et documentation

**Objectif :** Clarifier le rôle du multimètre pour le banc filtre et documenter l’ensemble.

**Tâches :**
- [ ] Déprécier ou documenter la limite « Multimètre < 2 kHz » pour le banc filtre ; recommander l’oscilloscope par défaut
- [ ] Mettre à jour [BANC_TEST_FILTRE.md](BANC_TEST_FILTRE.md) : schéma avec oscilloscope (Ch1=Ue, Ch2=Us), protocole de mesure (RMS + phase), référence au CDC Bode pour le format CSV et la visualisation
- [ ] Mettre à jour [AIDE.md](AIDE.md) et [README.md](../README.md) si besoin (procédure banc filtre, équipements requis)

**Statut :** À faire

---

## Historique des mises à jour

| Date | Modification |
|------|--------------|
| 11 février 2026 | Création du plan (Phases 1 à 6). Phase 1 (réorganisation des onglets) réalisée : ordre Multimètre, Générateur, Oscilloscope, Banc filtre, Calcul filtre, Enregistrement, Alimentation, Terminal série ; maquette + ui + INTERFACE_PYQT6.md + AIDE.md mis à jour. |
| 11 février 2026 | Phase 2 (source de mesure oscilloscope dans le core) réalisée : `core/bode_measure_source.py` (BodeMeasureSource, MultimeterBodeAdapter, OscilloscopeBodeSource), BodePoint.phase_deg, FilterTest(measure_source), config filter_test.measure_source / oscillo_channel_ue|us, bridge + maquette utilisent MultimeterBodeAdapter. |
| 11 février 2026 | Phase 3 (UI Banc filtre et orchestration) réalisée : SwitchableBodeMeasureSource, bridge construit la source switchable et _make_oscilloscope_bode_source ; FilterTestView avec combo « Source de mesure » (Multimètre &lt; 2 kHz / Oscilloscope Ch1=Ue Ch2=Us), set_measure_source_kind avant balayage, message si oscillo non connecté ; persistance measure_source dans _update_config_from_views + Sauvegarder config. |
