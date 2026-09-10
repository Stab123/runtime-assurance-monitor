"""Contrôles préenregistrés P4b (§14) — implémentation stricte.

1. RE-RUN DÉTERMINISTE : la campagne principale complète est ré-exécutée
   une seconde fois avec les mêmes graines. Exigence : vecteurs Y et V_min
   BIT À BIT identiques sur la même plateforme ; tolérance
   cross-plateforme : Y identique ET écart relatif V_min < 1e-12. Toute
   divergence → INVALID / TECHNICAL FAILURE (V0).
2. CONTRÔLE DU PAS DE TEMPS : campagne dt = 2.5 s, mêmes points et MÊMES
   graines NOISE (convention P4a-dtctrl : seul dt change), sur ρ = 1.000,
   ρ = 2.000, et — si V4 s'applique — les deux niveaux bornant la
   frontière (max(S), min(I)). Critère : labels S/I/M identiques à ceux
   du principal pour ces niveaux. Toute différence qui change le verdict
   → INCONCLUSIVE (NUMERICAL SENSITIVITY) ; différence sans effet sur le
   verdict → annotation rapportée.
3. TÉMOIN CRN : hash par bloc (paramètres + graine bruit) et bruit pur au
   pas 1 000 identiques entre les 9 niveaux d'un même bloc.

Ces fonctions comparent des résultats DÉJÀ PRODUITS ; elles n'exécutent
aucune simulation.
"""

from __future__ import annotations

import struct

TOLERANCE_RELATIVE_VMIN_CROSS_PLATEFORME = 1e-12

VERDICT_DT_DIVERGENT = "INCONCLUSIVE (NUMERICAL SENSITIVITY)"


def _bits(v: float) -> bytes:
    return struct.pack("<d", v)


def comparer_rerun(runs_a: list[dict], runs_b: list[dict],
                   meme_plateforme: bool = True) -> dict:
    """Compare deux exécutions de la MÊME campagne (mêmes graines).

    runs_* : enregistrements JSONL triés à l'identique (ordre des runs fixe
    §7 — l'appariement est positionnel sur run_id).
    """
    if len(runs_a) != len(runs_b):
        return {"identique": False,
                "detail": f"cardinaux différents : {len(runs_a)} vs {len(runs_b)}"}
    divergences = []
    for a, b in zip(runs_a, runs_b):
        if a["run_id"] != b["run_id"]:
            divergences.append((a["run_id"], b["run_id"], "run_id"))
            continue
        if a["Y"] != b["Y"]:
            divergences.append((a["run_id"], "Y", a["Y"], b["Y"]))
            continue
        if a["V_min"] is None:      # run invalide : Y null des deux côtés
            continue
        if meme_plateforme:
            if _bits(a["V_min"]) != _bits(b["V_min"]):
                divergences.append((a["run_id"], "V_min bits",
                                    a["V_min"], b["V_min"]))
        else:
            ref = abs(a["V_min"])
            ecart = abs(a["V_min"] - b["V_min"])
            if ecart > TOLERANCE_RELATIVE_VMIN_CROSS_PLATEFORME * max(ref, 1.0):
                divergences.append((a["run_id"], "V_min rel",
                                    a["V_min"], b["V_min"]))
    return {"identique": not divergences, "n_runs": len(runs_a),
            "divergences": divergences,
            "critere": "bit à bit" if meme_plateforme
                       else f"Y identique + écart relatif V_min < "
                            f"{TOLERANCE_RELATIVE_VMIN_CROSS_PLATEFORME:.0e}"}


def comparer_dtctrl(labels_principal: dict[float, str],
                    labels_dt: dict[float, str],
                    niveaux_controles: tuple[float, ...],
                    verdict_principal: str,
                    verdict_sous_dt: str) -> dict:
    """Contrôle du pas de temps (§14, contrôle 2).

    niveaux_controles : (1.000, 2.000) + paire bornant la frontière si V4.
    Retourne le statut du contrôle et l'effet sur le verdict.
    """
    comparaisons = {}
    differences = []
    for rho in niveaux_controles:
        lp = labels_principal.get(rho)
        ld = labels_dt.get(rho)
        comparaisons[rho] = {"principal": lp, "dt_2_5": ld,
                             "identique": lp == ld}
        if lp != ld:
            differences.append(rho)
    if not differences:
        return {"statut": "CONFORME", "differences": {},
                "effet_verdict": "aucun", "comparaisons": comparaisons}
    if verdict_sous_dt != verdict_principal:
        return {"statut": "DIVERGENT", "differences": differences,
                "effet_verdict": VERDICT_DT_DIVERGENT,
                "comparaisons": comparaisons}
    return {"statut": "DIFFERENCE_SANS_EFFET", "differences": differences,
            "effet_verdict": "annotation rapportée — verdict inchangé",
            "comparaisons": comparaisons}


def verifier_temoins_crn(runs: list[dict]) -> dict:
    """Témoin CRN (§14, contrôle 3) : pour chaque bloc, les 9 niveaux de ρ
    partagent la même graine NOISE — le témoin de bruit pur au pas 1 000
    et le hash de bloc doivent être identiques entre niveaux."""
    par_bloc: dict[int, list[dict]] = {}
    for r in runs:
        par_bloc.setdefault(r["bloc_id"], []).append(r)
    blocs_ok = 0
    anomalies = []
    for bloc_id, rs in sorted(par_bloc.items()):
        temoins = {r["temoin_bruit"] for r in rs}
        hashes = {r["temoin_bloc"] for r in rs}
        if None in temoins:
            anomalies.append((bloc_id, "témoin absent (run invalide avant "
                                       "le pas 1000 ou campagne tronquée)"))
        elif len(temoins) != 1:
            anomalies.append((bloc_id, "témoins de bruit divergents"))
        elif len(hashes) != 1:
            anomalies.append((bloc_id, "hash de bloc divergents"))
        else:
            blocs_ok += 1
    return {"blocs_ok": blocs_ok, "n_blocs": len(par_bloc),
            "anomalies": anomalies,
            "conforme": not anomalies}
