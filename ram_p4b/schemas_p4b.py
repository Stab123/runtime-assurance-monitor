"""Schéma des enregistrements JSONL par run — P4b (préenregistrement §14).

« Conservation : résultats bruts par run (JSONL : bloc_id, ρ, paramètres
plante, graine bruit, Y, V_min, t_min, drapeaux, témoin de bruit), logs
d'exécution, config et code hashés — tout conservé, rien d'effacé. »

Ce module est la source unique du schéma : la campagne écrit exactement ces
champs, les tests et le vérificateur valident contre cette liste.

Règles gelées traduites dans le schéma :
- Y ∈ {0, 1} sur un run valide ; Y est null SSI invalid_technique = true
  (une erreur de simulation n'est jamais comptée comme violation ni comme
  non-violation — §4, tolérance zéro, aucune substitution de Y).
- invalid_reason est null sur un run valide, chaîne sinon.
- outside_* : drapeau « hors domaine physique du modèle » (SoC ∉ [0 ; 1]) —
  le run RESTE dans l'analyse (règle d'inclusion §9).
- temoin_bruit : bruit pur au cycle 1000 (mécanisme P4a, CRN §7/§14) ;
  null si le run est invalide avant le cycle 1000 (ou campagne jouet plus
  courte — tests uniquement).
"""

from __future__ import annotations

# (nom, types Python autorisés, nullable)
CHAMPS_RUN: tuple[tuple[str, tuple[type, ...], bool], ...] = (
    # --- identifiant et conditions expérimentales ---------------------------
    ("run_id", (str,), False),
    ("mode", (str,), False),              # principal | dtctrl | ocv_plus | ocv_moins
    ("bloc_id", (int,), False),
    ("rho", (float,), False),
    ("C_BATT_AH", (float,), False),
    ("I_SUN", (float,), False),
    ("I_BASE", (float,), False),
    ("soc0", (float,), False),
    ("noise_seed", (int,), False),
    ("dt_s", (float,), False),
    ("cycles", (int,), False),
    # --- endpoint primaire (§4) ----------------------------------------------
    ("Y", (int,), True),                  # 0/1 ; null SSI invalid_technique
    ("V_min", (float,), True),
    ("t_min", (float,), True),
    ("soc_at_vmin", (float,), True),
    ("Vp_at_vmin", (float,), True),
    ("I_batt_at_vmin", (float,), True),
    ("I_cell_at_vmin", (float,), True),
    # --- descripteur secondaire préenregistré (§4) ----------------------------
    ("soc_min", (float,), True),
    ("violation_silencieuse", (bool,), True),  # Y=1 ∧ min SoC ≥ 0.35
    # --- drapeau hors domaine physique (§9) ----------------------------------
    ("outside_domain", (bool,), False),
    ("outside_first_t", (float,), True),
    ("outside_duration", (float,), False),
    ("outside_low", (bool,), False),      # SoC < 0 rencontré
    ("outside_high", (bool,), False),     # SoC > 1 rencontré
    ("outside_at_vmin", (bool,), True),
    # --- invalidité technique (§4, tolérance zéro) ---------------------------
    ("invalid_technique", (bool,), False),
    ("invalid_reason", (str,), True),
    # --- descripteurs opérationnels (hors verdict) ---------------------------
    ("fallback_fraction", (float,), True),
    ("payload_delivery_fraction", (float,), True),
    # --- témoins déterministes (§14) -----------------------------------------
    ("temoin_bruit", (float,), True),
    ("temoin_bloc", (str,), False),
)

CHAMPS_OBLIGATOIRES = tuple(n for n, _, _ in CHAMPS_RUN)


def valider_run(rec: dict) -> list[str]:
    """Valide un enregistrement JSONL contre le schéma. Retourne la liste
    des erreurs (vide = conforme)."""
    erreurs: list[str] = []
    for nom, types, nullable in CHAMPS_RUN:
        if nom not in rec:
            erreurs.append(f"champ manquant : {nom}")
            continue
        v = rec[nom]
        if v is None:
            if not nullable:
                erreurs.append(f"champ non nullable null : {nom}")
            continue
        # bool est un sous-type de int en Python — distinguer strictement
        if bool in types and type(v) is bool:
            continue
        if type(v) not in types or type(v) is bool and bool not in types:
            erreurs.append(f"type invalide pour {nom} : {type(v).__name__}")
    for nom in rec:
        if nom not in CHAMPS_OBLIGATOIRES:
            erreurs.append(f"champ non prévu par le schéma : {nom}")
    # Cohérences croisées gelées
    if not erreurs:
        if rec["invalid_technique"]:
            if rec["Y"] is not None:
                erreurs.append("run invalide avec Y non null (substitution interdite)")
            if rec["invalid_reason"] is None:
                erreurs.append("run invalide sans invalid_reason")
        else:
            if rec["Y"] not in (0, 1):
                erreurs.append("run valide avec Y hors {0, 1}")
            if rec["invalid_reason"] is not None:
                erreurs.append("run valide avec invalid_reason non null")
            for champ in ("V_min", "t_min", "soc_at_vmin", "Vp_at_vmin",
                          "I_batt_at_vmin", "I_cell_at_vmin", "soc_min",
                          "violation_silencieuse", "outside_at_vmin",
                          "fallback_fraction", "payload_delivery_fraction"):
                if rec[champ] is None:
                    erreurs.append(f"run valide avec {champ} null")
        if rec["outside_domain"] != (rec["outside_first_t"] is not None):
            erreurs.append("outside_domain incohérent avec outside_first_t")
        if not rec["outside_domain"] and rec["outside_duration"] != 0.0:
            erreurs.append("outside_duration non nul sans drapeau")
    return erreurs
