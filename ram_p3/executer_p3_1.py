"""P3.1 — exécution parallèle de la campagne sur la bande compilable.

Le code de campagne (ram_p2/campagne_p2.py) est importé SANS modification :
mêmes fonctions (simuler, tirer_parametres_plante, ic_moyenne, wilson),
mêmes graines, mêmes tirages. Un seul levier : delai_armement_s =
r x tau_violation_s, par point de la grille r de la config P3.1. La
parallélisation porte uniquement sur les runs, indépendants par construction
(paramètres de plante de graine_plante + i, bruit de graine_bruit + i, sans
état partagé) ; l'ordre des résultats est préservé (imap ordonné).

Non-régression bit à bit (étape 4 du protocole) : le bras A ne compile
aucun jeu de contraintes, il ne dépend donc pas de r — à chaque point, ses
300 runs doivent reproduire le bras A de P2.3 bit à bit. (Le harnais a par
ailleurs été validé : pilote P3 à r = 0,3 ↔ bras B de P2.3, 90/90 champs
identiques sur les 30 runs communs.)

Usage :
  python3 executer_p3_1.py <config> <sortie> [r|tous] [n_processus]
      Exécute un point de la grille r (ex. 0.475) ou tous (« tous »).
      La sortie d'un point seul est un résultat partiel.
  python3 executer_p3_1.py --fusionne <config> <sortie> <partiel1.json> ...
      Fusionne les résultats partiels (un par point r) en resultats_p3_1.json
      et régénère le tableau complet.
"""

from __future__ import annotations

import json
import math
import random
import sys
import time
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

RAM_P3 = Path(__file__).resolve().parent
RACINE = RAM_P3.parent
sys.path.insert(0, str(RACINE / "ram_p0"))
sys.path.insert(0, str(RACINE / "ram_p2"))

from campagne_p2 import (empreinte_fichiers, ic_moyenne, simuler,  # noqa: E402
                         tirer_parametres_plante, wilson)

MODULES_EMPREINTE = [
    RACINE / "ram_p0" / "moniteur.py",
    RACINE / "ram_p0" / "filtre.py",
    RACINE / "ram_p0" / "trace.py",
    RACINE / "ram_p0" / "contraintes.py",
    RACINE / "ram_p2" / "campagne_p2.py",
    RAM_P3 / "executer_p3_1.py",
]


def cfg_point(cfg: dict, r: float) -> dict:
    """La config P2.3 figée, avec UN levier déplacé : le délai d'armement."""
    c = dict(cfg)
    c["delai_armement_s"] = r * cfg["tau_violation_s"]
    return c


def un_run(args):
    """Un run complet à un point r : les quatre bras, tous les seuils sigma."""
    r, i, cfg = args
    c = cfg_point(cfg, r)
    params = tirer_parametres_plante(random.Random(cfg["graine_plante"] + i), c)
    grille_sigma = cfg["grille_seuil_incertitude_soc"]
    temoins = set()
    res = {}
    for bras in ("A", "B", "C", "D"):
        for seuil in (grille_sigma if bras == "C" else [None]):
            seuil_eff = seuil if bras == "C" else (
                math.nan if bras == "A" else math.inf)
            rr = simuler(bras, seuil_eff, params, cfg["graine_bruit"] + i, c)
            temoins.add(rr["temoin"])
            res[(bras, seuil)] = rr
    return r, i, res, len(temoins) == 1


def executer_point(r: float, cfg: dict, n_proc: int) -> dict:
    """Tous les runs d'un point r. Retourne le dictionnaire de résultats
    partiels (par run), prêt à être écrit ou fusionné."""
    n_runs = cfg["n_runs"]
    resultats: dict[tuple[str, object], list] = defaultdict(list)
    crn_ok = 0
    t0 = time.time()
    with Pool(n_proc) as pool:
        for _, i, res, ok in pool.imap(
                un_run, [(r, i, cfg) for i in range(n_runs)]):
            crn_ok += int(ok)
            for cle, rr in res.items():
                resultats[cle].append(rr)
            if (i + 1) % 25 == 0:
                print(f"  r={r} — {i + 1}/{n_runs} runs "
                      f"({time.time() - t0:.0f} s)", flush=True)
    return {
        "r": r,
        "tau_armement_s": r * cfg["tau_violation_s"],
        "n_runs": n_runs,
        "crn_runs_ok": crn_ok,
        "duree_s": round(time.time() - t0),
        "resultats_par_run": {
            f"{bras}:{seuil}": rs for (bras, seuil), rs in resultats.items()
        },
    }


def tableau_point(partiel: dict, cfg: dict) -> list[str]:
    """Le tableau d'un point r, même formatage que P2.3."""
    grille_sigma = cfg["grille_seuil_incertitude_soc"]
    resultats = {cle: partiel["resultats_par_run"][f"{cle[0]}:{cle[1]}"]
                 for cle in [("A", None), ("B", None), ("D", None)]
                 + [("C", s) for s in grille_sigma]}
    lignes = []
    lignes.append(f"--- point r = {partiel['r']} "
                  f"(tau_arm = {partiel['tau_armement_s']:.0f} s) — "
                  f"N = {partiel['n_runs']}, CRN "
                  f"{partiel['crn_runs_ok']}/{partiel['n_runs']} ---")
    lignes.append(f"{'bras':<4} {'seuil_σ_soc':>11} {'N':>3} "
                  f"{'taux_viol (IC95)':>22} {'runs_viol [Wilson]':>22} "
                  f"{'taux_repli (IC95)':>22} {'livraison (IC95)':>22}")
    for cle, rs in resultats.items():
        n = len(rs)
        v, v_lo, v_hi = ic_moyenne([x["taux_violation"] for x in rs])
        k_viol = sum(1 for x in rs if x["violations"] > 0)
        w_lo, w_hi = wilson(k_viol, n)
        rp, rp_lo, rp_hi = ic_moyenne([x["taux_repli"] for x in rs])
        lv, lv_lo, lv_hi = ic_moyenne([x["livraison"] for x in rs])
        seuil_txt = "-" if cle[1] is None else f"{cle[1]:.3f}"
        lignes.append(
            f"{cle[0]:<4} {seuil_txt:>11} {n:>3} "
            f"{v:>8.4%} [{v_lo:.4%},{v_hi:.4%}] "
            f"{k_viol:>3}/{n} [{w_lo:.3f},{w_hi:.3f}] "
            f"{rp:>9.4%} [{rp_lo:.4%},{rp_hi:.4%}] "
            f"{lv:>9.4%} [{lv_lo:.4%},{lv_hi:.4%}]"
        )
    return lignes


def main():
    if sys.argv[1] == "--fusionne":
        fusionner(sys.argv[2], sys.argv[3], sys.argv[4:])
        return
    chemin_config, chemin_sortie = sys.argv[1], sys.argv[2]
    cible = sys.argv[3] if len(sys.argv) > 3 else "tous"
    n_proc = int(sys.argv[4]) if len(sys.argv) > 4 else 2
    with open(chemin_config) as f:
        cfg = json.load(f)

    points = cfg["grille_r"] if cible == "tous" else [float(cible)]
    partiels = []
    for r in points:
        print(f"Exécution du point r = {r} "
              f"(tau_arm = {r * cfg['tau_violation_s']:.0f} s)", flush=True)
        partiels.append(executer_point(r, cfg, n_proc))
        for ligne in tableau_point(partiels[-1], cfg):
            print(ligne, flush=True)

    brut = {
        "config": cfg,
        "empreintes_code": empreinte_fichiers(
            [str(c) for c in MODULES_EMPREINTE]),
        "points": partiels,
    }
    with open(chemin_sortie, "w") as f:
        json.dump(brut, f, indent=1, default=str)
    print(f"Écrit : {chemin_sortie}", flush=True)


def fusionner(chemin_config: str, chemin_sortie: str, partiels: list[str]):
    """Assemble les résultats partiels (un par point r) en resultats final.

    Déterministe : les listes par run sont déjà dans l'ordre des graines
    (imap ordonné à l'exécution). Vérifie la cohérence des empreintes et de
    la config entre partiels avant de fusionner."""
    with open(chemin_config) as f:
        cfg = json.load(f)
    docs = []
    for p in partiels:
        with open(p) as f:
            docs.append(json.load(f))
    refs = {json.dumps(d["empreintes_code"], sort_keys=True) for d in docs}
    if len(refs) != 1:
        raise SystemExit("Partiels incohérents : empreintes_code diffèrent")
    points = [p for d in docs for p in d["points"]]
    if sorted(p["r"] for p in points) != sorted(cfg["grille_r"]):
        raise SystemExit("Partiels incohérents : la grille r n'est pas couverte")

    lignes = [f"Campagne {cfg.get('version_config', '?')} — "
              f"{cfg['n_runs']} runs par point, grille r = {cfg['grille_r']}"]
    for p in sorted(points, key=lambda x: x["r"]):
        lignes.extend(tableau_point(p, cfg))
    sortie = "\n".join(lignes)
    print(sortie)

    brut = {
        "config": cfg,
        "empreintes_code": docs[0]["empreintes_code"],
        "crn_runs_ok": sum(p["crn_runs_ok"] for p in points),
        "points": points,
        "tableau": sortie,
    }
    with open(chemin_sortie, "w") as f:
        json.dump(brut, f, indent=1, default=str)
    print(f"Écrit : {chemin_sortie}")


if __name__ == "__main__":
    main()
