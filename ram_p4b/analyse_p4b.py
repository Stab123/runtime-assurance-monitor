"""Analyse statistique P4b — règles GELÉES du préenregistrement §5, §6,
§9, §10, §11, §12. Aucune liberté d'interprétation.

- IC de Wilson bilatéral 99.4444 % (z = 2.7729212946086634), formule
  standard centrée (§5) ;
- classification d'un niveau : SUFFICIENT ⟺ borne sup ≤ 0.01 ;
  INSUFFICIENT ⟺ borne inf ≥ 0.05 ; INTERMEDIATE sinon (§5) — implémentée
  DEUX façons (bornes ET seuils entiers x ≤ 34 / x ≥ 320, §6) dont
  l'équivalence sur x = 0..5500 est vérifiée par les tests ;
- frontière : existence ssi S ≠ ∅, I ≠ ∅, max(S) < min(I) ; localisation
  b* ∈ (max(S) ; min(I)] ; aucune interpolation ; annotation LOW
  RESOLUTION si min(I) − max(S) > 0.250 (§10) ;
- monotonie testée, jamais imposée : inversion dure ⟺ ∃ j < k : ρ_j ∈ I
  ∧ ρ_k ∈ S (§11) ;
- verdicts V0–V7 évalués DANS L'ORDRE, premier cas qui matche (§12).

stdlib + math uniquement côté décision (déterminisme) ; numpy/scipy ne
sont pas requis par ce module.
"""

from __future__ import annotations

import math

# --- Constantes gelées (§3, §5, §6) ------------------------------------------
Z_WILSON = 2.7729212946086634        # IC bilatéral 99.4444 % (α = 1/360)
N_PAR_NIVEAU = 5500
EPS_S = 0.01
EPS_F = 0.05
SEUIL_X_SUFFICIENT = 34              # SUFFICIENT ⟺ x ≤ 34 (§6)
SEUIL_X_INSUFFICIENT = 320           # INSUFFICIENT ⟺ x ≥ 320 (§6)
NIVEAUX_RHO = tuple(1.0 + i * 0.125 for i in range(9))
GARDE_FOU_FLAG = 0.25                # V0b : fraction flaggée > 25 % STRICT (§9)
PAS_GRILLE = 0.125
SEUIL_LOW_RESOLUTION = 0.250         # annotation si largeur > 0.250 (§10)

SUFFICIENT, INSUFFICIENT, INTERMEDIATE = "S", "I", "M"


def wilson_ic(x: int, n: int, z: float = Z_WILSON) -> tuple[float, float]:
    """IC de Wilson bilatéral 99.4444 % — formule standard centrée (§5) :

        centre = (p̂ + z²/2N) / (1 + z²/N)
        demi   = z·sqrt(p̂(1−p̂)/N + z²/4N²) / (1 + z²/N)
    """
    if n <= 0:
        raise ValueError("n doit être > 0")
    if not 0 <= x <= n:
        raise ValueError("x hors [0 ; n]")
    p = x / n
    d = 1.0 + z * z / n
    c = p + z * z / (2.0 * n)
    m = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n))
    return (c - m) / d, (c + m) / d


def classifier_niveau_bornes(x: int, n: int = N_PAR_NIVEAU) -> str:
    """Classification par les BORNES de l'IC (formulation primaire §5)."""
    lo, hi = wilson_ic(x, n)
    if hi <= EPS_S:
        return SUFFICIENT
    if lo >= EPS_F:
        return INSUFFICIENT
    return INTERMEDIATE


def classifier_niveau_seuils(x: int, n: int = N_PAR_NIVEAU) -> str:
    """Classification par les SEUILS ENTIERS gelés (§6) : x ≤ 34 → S ;
    x ≥ 320 → I ; sinon M. Valide uniquement pour n = 5 500."""
    if n != N_PAR_NIVEAU:
        raise ValueError("seuils entiers gelés valables pour N = 5500 seulement")
    if x <= SEUIL_X_SUFFICIENT:
        return SUFFICIENT
    if x >= SEUIL_X_INSUFFICIENT:
        return INSUFFICIENT
    return INTERMEDIATE


def verifier_equivalence_seuils(n: int = N_PAR_NIVEAU) -> bool:
    """Les deux méthodes (bornes §5 / seuils entiers §6) doivent être
    équivalentes pour TOUT x ∈ [0 ; 5500] — contrôle exhaustif."""
    return all(classifier_niveau_bornes(x, n) == classifier_niveau_seuils(x, n)
               for x in range(n + 1))


def classifier_niveau(x: int, n: int = N_PAR_NIVEAU) -> str:
    """Classification canonique d'un niveau (bornes, §5)."""
    return classifier_niveau_bornes(x, n)


# --- Frontière et monotonie (§10, §11) ---------------------------------------

def inversion_dure(labels: dict[float, str]) -> bool:
    """∃ j < k : ρ_j ∈ I ∧ ρ_k ∈ S — détection déterministe sur les
    LABELS, pas sur les p̂ (§11)."""
    niveaux = sorted(labels)
    vu_insuffisant = False
    for rho in niveaux:
        if labels[rho] == INSUFFICIENT:
            vu_insuffisant = True
        elif labels[rho] == SUFFICIENT and vu_insuffisant:
            return True
    return False


def frontiere(labels: dict[float, str]) -> dict:
    """Frontière au sens du protocole (§10). Hypothèse : pas d'inversion
    dure (vérifiée par l'appelant — sinon b* = null, §11)."""
    s = sorted(r for r, lab in labels.items() if lab == SUFFICIENT)
    i = sorted(r for r, lab in labels.items() if lab == INSUFFICIENT)
    if s and i and max(s) < min(i):
        largeur = min(i) - max(s)
        return {"existe": True, "borne_inf": max(s), "borne_sup": min(i),
                "largeur": largeur,
                "low_resolution": largeur > SEUIL_LOW_RESOLUTION}
    return {"existe": False, "borne_inf": None, "borne_sup": None,
            "largeur": None, "low_resolution": False,
            "borne_b_superieure": max(s) if s else None,   # b* > max(S) (V5)
            "borne_b_inferieure": min(i) if i else None}   # b* < min(I) (V6)


# --- Règle de décision V0–V7 (§12) — ordre strict, premier match -------------

VERDICTS = {
    "V0": "INVALID / TECHNICAL FAILURE",
    "V0b": "INCONCLUSIVE (MODEL LIMIT)",
    "V1": "SUFFICIENT OVER TESTED DOMAIN",
    "V2": "INSUFFICIENT AT BASELINE",
    "V3": "FRONTIER NOT LOCALIZED (NON-MONOTONE)",
    "V4": "TRANSITION DETECTED",
    "V5": "FRONTIER NOT LOCALIZED (b* > max(S))",
    "V6": "FRONTIER NOT LOCALIZED (b* < min(I))",
    "V7": "INCONCLUSIVE",
}


def verdict_p4b(labels: dict[float, str], n_invalid_technique: int = 0,
                fraction_flag: float = 0.0) -> dict:
    """Règle de décision déterministe (§12), évaluée DANS L'ORDRE.

    labels : {rho: "S"/"I"/"M"} sur les 9 niveaux (campagnes valides).
    n_invalid_technique : runs INVALID_TECHNIQUE de la campagne
    PRINCIPALE (§4/V0 — zéro tolérance : ≥ 1 → V0).
    fraction_flag : fraction de runs flaggés hors domaine (§9/V0b —
    déclenchement STRICTEMENT au-delà de 25 %).
    """
    if set(labels) != set(NIVEAUX_RHO):
        raise ValueError("labels doivent couvrir exactement les 9 niveaux gelés")
    if any(lab not in (SUFFICIENT, INSUFFICIENT, INTERMEDIATE)
           for lab in labels.values()):
        raise ValueError("label hors {S, I, M}")

    s = sorted(r for r, lab in labels.items() if lab == SUFFICIENT)
    i = sorted(r for r, lab in labels.items() if lab == INSUFFICIENT)

    # V0 — INVALID_TECHNIQUE dans la campagne principale (§4).
    if n_invalid_technique >= 1:
        return {"code": "V0", "verdict": VERDICTS["V0"], "b_star": None,
                "low_resolution": False, "inversion_dure": None,
                "detail": f"{n_invalid_technique} run(s) INVALID_TECHNIQUE"}
    # V0b — garde-fou hors domaine : fraction > 25 % STRICT (§9).
    if fraction_flag > GARDE_FOU_FLAG:
        return {"code": "V0b", "verdict": VERDICTS["V0b"], "b_star": None,
                "low_resolution": False, "inversion_dure": None,
                "detail": f"fraction flaggée {fraction_flag:.6f} > 0.25"}
    # V1 — les 9 niveaux ∈ S.
    if len(s) == len(NIVEAUX_RHO):
        return {"code": "V1", "verdict": VERDICTS["V1"], "b_star": None,
                "low_resolution": False, "inversion_dure": False,
                "detail": "9/9 niveaux SUFFICIENT"}
    # V2 — ρ = 1.000 ∈ I.
    if labels[NIVEAUX_RHO[0]] == INSUFFICIENT:
        return {"code": "V2", "verdict": VERDICTS["V2"], "b_star": None,
                "low_resolution": False,
                "inversion_dure": inversion_dure(labels),
                "detail": "niveau de base ρ = 1.000 INSUFFICIENT"}
    # V3 — inversion dure (§11).
    if inversion_dure(labels):
        return {"code": "V3", "verdict": VERDICTS["V3"], "b_star": None,
                "low_resolution": False, "inversion_dure": True,
                "detail": "∃ j < k : ρ_j ∈ I ∧ ρ_k ∈ S"}
    f = frontiere(labels)
    # V4 — transition certifiée aux deux bornes.
    if f["existe"]:
        b = {"code": "V4", "verdict": VERDICTS["V4"],
             "b_star": (f["borne_inf"], f["borne_sup"]),
             "low_resolution": f["low_resolution"], "inversion_dure": False,
             "detail": f"b* ∈ ({f['borne_inf']:.3f} ; {f['borne_sup']:.3f}]"}
        if f["low_resolution"]:
            b["verdict"] += " — LOW RESOLUTION"
        return b
    # V5 — S ≠ ∅, I = ∅, non V1 : borne b* > max(S).
    if s and not i:
        return {"code": "V5", "verdict": VERDICTS["V5"],
                "b_star": (max(s), None), "low_resolution": False,
                "inversion_dure": False,
                "detail": f"b* > {max(s):.3f} — transition éventuelle au-delà "
                          f"de la région certifiée, non démontrée"}
    # V6 — S = ∅, I ≠ ∅ (non V2, donc ρ = 1.000 ∈ M) : borne b* < min(I).
    if i:
        return {"code": "V6", "verdict": VERDICTS["V6"],
                "b_star": (None, min(i)), "low_resolution": False,
                "inversion_dure": False,
                "detail": f"b* < {min(i):.3f} — aucune région suffisante "
                          f"certifiée"}
    # V7 — S = ∅ ∧ I = ∅.
    return {"code": "V7", "verdict": VERDICTS["V7"], "b_star": None,
            "low_resolution": False, "inversion_dure": False,
            "detail": "puissance insuffisante pour trancher dans la zone "
                      "intermédiaire"}


def labels_depuis_comptages(x_par_niveau: dict[float, int],
                            n: int = N_PAR_NIVEAU) -> dict[float, str]:
    """Comptages de violations → labels S/I/M (classification canonique)."""
    return {rho: classifier_niveau(x, n) for rho, x in x_par_niveau.items()}


def fraction_flaggee(runs: list[dict]) -> float:
    """Fraction de runs flaggés hors domaine sur les runs VALIDES de la
    campagne principale (§9)."""
    valides = [r for r in runs if not r["invalid_technique"]]
    if not valides:
        return 0.0
    return sum(1 for r in valides if r["outside_domain"]) / len(valides)
