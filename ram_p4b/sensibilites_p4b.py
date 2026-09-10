"""Analyses de sensibilité préenregistrées P4b (§13) — dégradation SEULE.

Deux sensibilités gelées, toujours exécutées (non conditionnelles aux
résultats) :

1. OCV ±0.1 V aux points de table SoC ∈ {0.00 ; 0.02} (incertitude
   déclarée v0.6 du segment quasi vertical) — variantes d'analyse en
   mémoire, mêmes points de design et mêmes graines (CRN) ; la table
   gelée n'est jamais modifiée. Verdict principal toujours calculé sur la
   table gelée.
2. Drapeaux hors domaine (règle symétrique §9/§13) : reclassification sur
   x'_j = x_j − x_j^(flag), où x_j^(flag) = nombre de violations dont le
   minimum survient pendant un épisode hors domaine (outside_at_vmin).

Règle de combinaison GELÉE (§13) — DÉGRADATION SEULE :
- si les conditions V1–V7 changent sous une variante :
  * TRANSITION DETECTED → FRONTIER NOT LOCALIZED (OCV SENSITIVE) /
    (FLAG SENSITIVE) si la frontière disparaît, apparaît ou se déplace ;
  * autre verdict → annotation OCV-SENSITIVE / FLAG-SENSITIVE, verdict
    INCHANGÉ ;
  * si les deux variantes OCV confirment le verdict principal →
    annotation « robuste à l'incertitude OCV locale ».
- Une sensibilité ne peut JAMAIS transformer un verdict autre en
  TRANSITION DETECTED, ni déplacer une frontière : elle ne fait que
  dégrader la certitude. Ce module l'impose structurellement.
"""

from __future__ import annotations

from analyse_p4b import (N_PAR_NIVEAU, classifier_niveau, verdict_p4b)

VERDICT_TRANSITION = "V4"


def _verdict_variante(labels_variante: dict[float, str],
                      n_invalid: int, fraction_flag: float) -> dict | None:
    """Verdict sous la variante. Un run invalide dans une campagne de
    sensibilité invalide CETTE ANALYSE-LÀ (annotation), pas le verdict
    principal (§12, V0)."""
    if n_invalid >= 1:
        return None      # analyse de sensibilité invalide
    return verdict_p4b(labels_variante, n_invalid, fraction_flag)


def combiner_sensibilite(verdict_principal: dict,
                         verdicts_variantes: dict[str, dict | None],
                        etiquette: str) -> dict:
    """Combine le verdict principal avec les verdicts sous variantes.

    verdicts_variantes : {"ocv_plus": verdict|None, "ocv_moins": ...} ou
    {"flags": ...}. etiquette : "OCV" ou "FLAG".

    DÉGRADATION SEULE — garanties structurelles :
    - le code de verdict retourné est TOUJOURS celui du principal, sauf
      déclassement d'un TRANSITION DETECTED en FRONTIER NOT LOCALIZED
      (... SENSITIVE) ;
    - jamais de promotion vers TRANSITION DETECTED ;
    - jamais de déplacement de frontière vers une nouvelle valeur
      (b_star est effacé en cas de déclassement, jamais réécrit).
    """
    code_p = verdict_principal["code"]
    sortie = dict(verdict_principal)
    sortie["sensibilites"] = {}

    degradations = []
    invalides = []
    for nom, vv in verdicts_variantes.items():
        tag = f"{nom}"
        if vv is None:
            invalides.append(nom)
            sortie["sensibilites"][tag] = "analyse invalide (run invalide "
            "technique dans la variante — §12 V0)"
            continue
        meme_code = vv["code"] == code_p
        meme_b = vv.get("b_star") == verdict_principal.get("b_star")
        if meme_code and (code_p != VERDICT_TRANSITION or meme_b):
            sortie["sensibilites"][tag] = "confirme le verdict principal"
        else:
            degradations.append(nom)
            sortie["sensibilites"][tag] = (
                f"modifie les conditions V1–V7 : {code_p} -> {vv['code']}")

    if degradations:
        if code_p == VERDICT_TRANSITION:
            # Déclassement — seule évolution permise du code de verdict.
            sortie["code"] = "V4-SENS"
            sortie["verdict"] = (f"FRONTIER NOT LOCALIZED "
                                 f"({etiquette} SENSITIVE)")
            sortie["b_star"] = None
            sortie["detail"] = (f"frontière disparue, apparue ou déplacée "
                                f"sous {', '.join(degradations)}")
        else:
            # Verdict inchangé + annotation — JAMAIS de promotion.
            sortie["verdict"] = (f"{verdict_principal['verdict']} "
                                 f"[{etiquette}-SENSITIVE]")
            sortie["detail"] = (f"{verdict_principal.get('detail', '')} ; "
                                f"annotation {etiquette}-SENSITIVE "
                                f"({', '.join(degradations)})")
    elif not invalides and verdicts_variantes:
        sortie["verdict"] = (f"{verdict_principal['verdict']} "
                             f"[robuste à l'incertitude {etiquette} locale]"
                             if etiquette == "OCV"
                             else verdict_principal["verdict"])
    return sortie


def sensibilite_drapeaux(x_par_niveau: dict[float, int],
                         x_flag_par_niveau: dict[float, int],
                         verdict_principal: dict,
                         n: int = N_PAR_NIVEAU) -> dict:
    """Règle symétrique pour les drapeaux (§13) : x'_j = x_j − x_j^(flag).

    x_j^(flag) = violations dont le minimum survient hors domaine
    (outside_at_vmin = true). Reclassification, combinaison dégradation
    seule, étiquette FLAG.
    """
    labels_prime = {}
    for rho, x in x_par_niveau.items():
        xf = x_flag_par_niveau.get(rho, 0)
        if not 0 <= xf <= x:
            raise ValueError(f"x_flag hors [0 ; x] au niveau {rho}")
        labels_prime[rho] = classifier_niveau(x - xf, n)
    vv = verdict_p4b(labels_prime)
    return combiner_sensibilite(verdict_principal, {"flags": vv}, "FLAG")


def combiner_sensibilites_ocv(verdict_principal: dict,
                              labels_ocv_plus: dict[float, str] | None,
                              labels_ocv_moins: dict[float, str] | None,
                              n_invalid_plus: int = 0,
                              n_invalid_moins: int = 0,
                              fraction_flag: float = 0.0) -> dict:
    """Sensibilité OCV ±0.1 V (§13) : deux variantes, dégradation seule,
    étiquette OCV. None = variante non exécutée (analysée comme absente)."""
    variantes: dict[str, dict | None] = {}
    if labels_ocv_plus is not None:
        variantes["ocv_plus"] = _verdict_variante(
            labels_ocv_plus, n_invalid_plus, fraction_flag)
    if labels_ocv_moins is not None:
        variantes["ocv_moins"] = _verdict_variante(
            labels_ocv_moins, n_invalid_moins, fraction_flag)
    return combiner_sensibilite(verdict_principal, variantes, "OCV")
