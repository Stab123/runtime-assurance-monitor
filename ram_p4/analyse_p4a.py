"""Analyse P4a — script unique, strictement conforme au pre-enregistrement.

Produit : classes S/T/F par niveau, test de tendance (logistique, SE
cluster-robust par bloc), frontiere b* (isotonique + regles de plateau),
IC bootstrap 2000 par blocs de nuisance, controles RESEED (homogeneite) et
DTCTRL, verdicts globaux A-E automatiques. Aucune decision humaine.

Entrees : resultats_p4a_principal.json (+ _reseed.json, _dtctrl.json).
Sortie : analyse_p4a_resultats.json + resume markdown sur stdout.
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

RAM_P4 = Path(__file__).resolve().parent
sys.path.insert(0, str(RAM_P4))
from graines_p4 import seed_graine

EPS_S = 0.01
EPS_F = 0.05
Z = 1.959963985130054  # quantile 0.975 — Wilson 95 % bilateral
NIVEAUX_POSITIFS = [0.0, 0.01, 0.02, 0.05, 0.10]
N_BOOT = 2000
LARGEUR_MAX_IC_BSTAR = 0.02
ALPHA_TENDANCE = 0.05
ALPHA_BONFERRONI = 0.05 / 9
SEUIL_EXCLUSION = 0.02  # >2 % de runs invalides -> niveau INCONCLUSIVE
PROP_MIN_BOOT_DEFINI = 0.95  # A exige b* défini dans >= 95 % des répliques


def wilson(x: int, n: int) -> tuple[float, float]:
    if n == 0:
        return 0.0, 1.0
    p = x / n
    d = 1 + Z * Z / n
    c = p + Z * Z / (2 * n)
    m = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n))
    return (c - m) / d, (c + m) / d


def classe(x: int, n: int) -> str:
    lo, hi = wilson(x, n)
    if hi < EPS_S:
        return "S"
    if lo > EPS_F:
        return "F"
    return "T"


def invariant_ok(run: dict) -> bool:
    """Invariants logiciels pre-enregistres (jamais bases sur le resultat)."""
    for cle in ("marge_min", "err_est_soc_moyenne", "livraison"):
        v = run.get(cle)
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return False
    soc0 = run["params_plante"]["soc0"]
    if not (-0.5 <= soc0 <= 1.5):
        return False
    return True


def pava(y: list[float]) -> list[float]:
    """Pool-Adjacent-Violators, non decroissant, poids egaux."""
    m = list(y)
    w = [1] * len(m)
    i = 0
    while i < len(m) - 1:
        if m[i] > m[i + 1] + 1e-12:
            m[i] = (m[i] * w[i] + m[i + 1] * w[i + 1]) / (w[i] + w[i + 1])
            w[i] += w[i + 1]
            del m[i + 1]
            del w[i + 1]
            i = max(i - 1, 0)
        else:
            i += 1
    out = []
    for val, wt in zip(m, w):
        out.extend([val] * wt)
    return out


def b_etoile(p_iso: list[float], niveaux: list[float]) -> float | None:
    """b* = plus petite valeur positive b telle que p_iso(b) >= EPS_F.

    Regles de plateau pre-enregistrees :
    - interpolation lineaire uniquement si p_iso(b_i) < EPS_F < p_iso(b_{i+1}) ;
    - egalite ou plateau couvrant EPS_F : bord gauche du plateau ;
    - p_iso(0.01) >= EPS_F : frontiere censuree a gauche -> retourne 0.01
      (rapporte comme « b* <= 0.01 », pas d'interpolation entre 0 et 0.01) ;
    - aucun niveau >= EPS_F : None (voies B/D).
    """
    for i, b in enumerate(niveaux):
        if b <= 0.0:
            continue
        if p_iso[i] >= EPS_F:
            if i == 0 or niveaux[i - 1] <= 0.0:
                return b                      # censure a gauche
            if p_iso[i - 1] < EPS_F - 1e-15:
                b0, b1 = niveaux[i - 1], b
                p0, p1 = p_iso[i - 1], p_iso[i]
                return b0 + (EPS_F - p0) * (b1 - b0) / (p1 - p0)
            return b                          # bord gauche du plateau
    return None


def charger(nom: str) -> dict:
    p = RAM_P4 / nom
    return json.load(open(p)) if p.exists() else {"runs": []}


def par_niveau(runs: list[dict]) -> dict:
    out = {}
    for r in runs:
        out.setdefault(round(r["biais"], 6), []).append(r)
    return out


def test_tendance(groupes: dict) -> tuple[float | None, float | None]:
    """Regression logistique p ~ b (niveaux >= 0), SE cluster-robust par bloc.
    Retourne (pente, p unilaterale H1: pente > 0).
    REGLE PRE-ENREGISTREE : si tous les Y des niveaux positifs sont identiques,
    la pente est NON ESTIMABLE (separation complete) -> (None, None) ; aucun
    test de tendance n'est interprete. Cela n'empeche pas la voie B si ses
    autres criteres sont satisfaits."""
    import numpy as np
    import statsmodels.api as sm
    X, y, g = [], [], []
    for b in NIVEAUX_POSITIFS:
        for r in groupes.get(b, []):
            X.append([1.0, b])
            y.append(r["Y"])
            g.append(r["bloc_id"])
    if len(set(y)) <= 1:
        return None, None
    m = sm.GLM(np.array(y), np.array(X), family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": np.array(g)})
    pente = float(m.params[1])
    p_uni = float(m.pvalues[1]) / 2.0 if pente > 0 else 1.0 - float(m.pvalues[1]) / 2.0
    return pente, p_uni


def bootstrap_bstar(groupes: dict) -> tuple[float | None, float | None, float, float | None]:
    """Bootstrap par blocs de nuisance (jamais niveau par niveau)."""
    rng = random.Random(seed_graine("BOOTSTRAP", 0))
    blocs = sorted({r["bloc_id"] for b in NIVEAUX_POSITIFS for r in groupes.get(b, [])})
    est = []
    for rep in range(N_BOOT):
        echan = [blocs[rng.randrange(len(blocs))] for _ in blocs]
        ph = []
        for b in NIVEAUX_POSITIFS:
            tab = {r["bloc_id"]: r["Y"] for r in groupes.get(b, [])}
            ys = [tab[j] for j in echan if j in tab]
            ph.append(sum(ys) / len(ys))
        b0 = b_etoile(pava(ph), NIVEAUX_POSITIFS)
        if b0 is not None:
            est.append(b0)
    if len(est) < 50:
        return None, None, len(est) / N_BOOT, None
    est.sort()
    lo = est[int(0.025 * len(est))]
    hi = est[min(int(0.975 * len(est)), len(est) - 1)]
    return lo, hi, len(est) / N_BOOT, hi - lo


def homogeneite(g_main: dict, g_re: dict) -> dict:
    """Test z bilateral de deux proportions (variance poolée) par niveau."""
    from scipy.stats import norm
    res = {}
    for b, runs_m in g_main.items():
        runs_r = g_re.get(b, [])
        if not runs_r:
            continue
        x1, n1 = sum(r["Y"] for r in runs_m), len(runs_m)
        x2, n2 = sum(r["Y"] for r in runs_r), len(runs_r)
        p = (x1 + x2) / (n1 + n2)
        if p in (0.0, 1.0):
            # p = 0 exige x1 = x2 = 0 ; p = 1 exige deux taux de 100 % :
            # dans les deux cas les proportions sont IDENTIQUES — concordant.
            res[b] = {"p_value": 1.0, "discordant": False}
            continue
        z = (x1 / n1 - x2 / n2) / math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
        pv = 2 * (1 - norm.cdf(abs(z)))
        res[b] = {"p_value": pv, "discordant": pv < ALPHA_BONFERRONI}
    return res


def main():
    principal = [r for r in charger("resultats_p4a_principal.json")["runs"]]
    reseed = [r for r in charger("resultats_p4a_reseed.json")["runs"]]
    dtctrl = [r for r in charger("resultats_p4a_dtctrl.json")["runs"]]

    # --- exclusions par invariant (log d'audit) ------------------------------
    valides, exclus = [], []
    for r in principal:
        (valides if invariant_ok(r) else exclus).append(r)
    g = par_niveau(valides)

    # --- S/T/F par niveau ----------------------------------------------------
    classes = {}
    for b, runs in sorted(g.items()):
        n = len(runs)
        x = sum(r["Y"] for r in runs)
        n_excl = sum(1 for r in exclus if round(r["biais"], 6) == b)
        lo, hi = wilson(x, n)
        cl = classe(x, n)
        if n_excl / max(n + n_excl, 1) > SEUIL_EXCLUSION:
            cl = "INCONCLUSIVE"
        classes[b] = {"x": x, "n": n, "ic": [lo, hi], "classe": cl,
                      "exclus": n_excl}

    # --- tendance (niveaux >= 0) ---------------------------------------------
    pente, p_tendance = test_tendance(g)

    # --- frontiere b* + bootstrap par blocs ----------------------------------
    ph = [sum(r["Y"] for r in g.get(b, [])) / max(len(g.get(b, [])), 1)
          for b in NIVEAUX_POSITIFS]
    p_iso = pava(ph)
    bs = b_etoile(p_iso, NIVEAUX_POSITIFS)
    blo, bhi, prop_def, largeur = bootstrap_bstar(g)

    # --- controles RESEED / DTCTRL -------------------------------------------
    hom = homogeneite(g, par_niveau(reseed)) if reseed else {}
    pente_r = None
    if reseed:
        pente_r, _ = test_tendance(par_niveau(reseed))
    dt_concordant = None
    if dtctrl:
        gd = par_niveau(dtctrl)
        dt_concordant = all(
            classe(sum(r["Y"] for r in gd.get(b, [])), len(gd.get(b, [])))
            == classes.get(b, {}).get("classe")
            for b in (0.02, 0.05) if b in classes)

    # --- verdict global automatique ------------------------------------------
    cls = {b: c["classe"] for b, c in classes.items()}
    pos = {b: c for b, c in cls.items() if b >= 0}
    n_S = sum(1 for c in pos.values() if c == "S")
    n_F = sum(1 for c in pos.values() if c == "F")
    discordance_determinante = any(
        h["discordant"] for b, h in hom.items()
        if cls.get(b) == "F" or n_F == 0)
    direction_rompue = (pente_r is not None and pente is not None
                        and pente > 0 and pente_r <= 0)
    # pente NON ESTIMABLE (tous Y identiques) -> tendance_signif = False ;
    # n'empeche ni B ni D, seulement A et la voie « monotone ».
    tendance_signif = (p_tendance is not None
                       and p_tendance < ALPHA_TENDANCE)

    if discordance_determinante or direction_rompue:
        verdict = "D"
    elif dt_concordant is False:
        verdict = "E"
    elif n_S >= 1 and n_F >= 1 and tendance_signif and \
            bs is not None and largeur is not None and \
            largeur <= LARGEUR_MAX_IC_BSTAR and \
            prop_def >= PROP_MIN_BOOT_DEFINI:
        verdict = "A"
    elif n_F == 0 and all(c == "S" for c in pos.values()):
        verdict = "B"
    elif n_F >= 1 and not tendance_signif:
        verdict = "C"
    else:
        verdict = "D"

    bilan = {
        "classes": classes, "pente": pente, "p_tendance": p_tendance,
        "p_iso": dict(zip(NIVEAUX_POSITIFS, p_iso)),
        "b_etoile": bs, "ic_b_etoile": [blo, bhi],
        "proportion_boot_defini": prop_def, "largeur_ic": largeur,
        "homogeneite_reseed": hom, "pente_reseed": pente_r,
        "dtctrl_concordant": dt_concordant,
        "exclusions_audit": [r["run_id"] for r in exclus],
        "verdict_global": verdict,
    }
    json.dump(bilan, open(RAM_P4 / "analyse_p4a_resultats.json", "w"), indent=1)
    print(json.dumps({k: bilan[k] for k in
                      ("classes", "b_etoile", "largeur_ic", "verdict_global")},
                     indent=1))


if __name__ == "__main__":
    main()
