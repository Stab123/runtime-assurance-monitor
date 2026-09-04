"""P2.3 — exécution parallèle de la campagne de falsification.

Le code de campagne (campagne_p2.py) est INCHANGÉ : même sémantique, mêmes
tirages, mêmes fonctions (simuler, tirer_parametres_plante, ic_moyenne,
wilson). La parallélisation porte uniquement sur les runs, indépendants par
construction : paramètres de plante tirés de graine_plante + i, bruit de
graine_bruit + i, sans état partagé. L'ordre des résultats est préservé
(imap ordonné), donc les listes par point de grille sont identiques à une
exécution série.

Validation du pilote : relancé avec n_runs=32 sur la config P2.2, il doit
reproduire resultats_p2_2.json bit à bit (tous champs de tous les runs).

Usage : python3 executer_p2_3.py <config> <sortie> [n_processus]
"""

from __future__ import annotations

import json
import math
import random
import sys
import time
from collections import defaultdict
from multiprocessing import Pool

sys.path.insert(0, "/mnt/agents/output/ram_p0")
sys.path.insert(0, "/mnt/agents/output/ram_p2")

from campagne_p2 import (empreinte_fichiers, ic_moyenne, simuler,
                         tirer_parametres_plante, wilson)


def un_run(args):
    """Un run complet : les quatre bras, tous les points de grille."""
    i, cfg = args
    params = tirer_parametres_plante(random.Random(cfg["graine_plante"] + i), cfg)
    grille = cfg["grille_seuil_incertitude_soc"]
    temoins = set()
    res = {}
    for bras in ("A", "B", "C", "D"):
        for seuil in (grille if bras == "C" else [None]):
            seuil_eff = seuil if bras == "C" else (
                math.nan if bras == "A" else math.inf)
            r = simuler(bras, seuil_eff, params, cfg["graine_bruit"] + i, cfg)
            temoins.add(r["temoin"])
            res[(bras, seuil)] = r
    return i, res, len(temoins) == 1


def main(chemin_config: str, chemin_sortie: str, n_proc: int = 2):
    with open(chemin_config) as f:
        cfg = json.load(f)
    grille = cfg["grille_seuil_incertitude_soc"]
    n_runs = cfg["n_runs"]
    resultats: dict[tuple[str, object], list] = defaultdict(list)
    crn_ok = 0
    t0 = time.time()

    with Pool(n_proc) as pool:
        for i, res, ok in pool.imap(un_run, [(i, cfg) for i in range(n_runs)]):
            crn_ok += int(ok)
            for cle, r in res.items():
                resultats[cle].append(r)
            if (i + 1) % 25 == 0:
                print(f"  ... {i + 1}/{n_runs} runs ({time.time() - t0:.0f} s)",
                      flush=True)

    duree = time.time() - t0

    lignes = []
    lignes.append(f"Campagne {cfg.get('version_config', '?')} — "
                  f"{n_runs} runs par point (exécution parallèle, {n_proc} processus)")
    lignes.append(f"CRN : {crn_ok}/{n_runs} runs avec témoin identique "
                  f"sur les quatre bras ({'OK' if crn_ok == n_runs else 'ÉCHEC'})")
    lignes.append(f"Durée de calcul : {duree:.0f} s")
    lignes.append(f"{'bras':<4} {'seuil_σ_soc':>11} {'N':>3} "
                  f"{'taux_viol (IC95)':>22} {'runs_viol [Wilson]':>22} "
                  f"{'taux_repli (IC95)':>22} {'livraison (IC95)':>22}")
    cles = [("A", None), ("B", None), ("D", None)] + [("C", s) for s in grille]
    for cle in cles:
        rs = resultats[cle]
        n = len(rs)
        v, v_lo, v_hi = ic_moyenne([r["taux_violation"] for r in rs])
        k_viol = sum(1 for r in rs if r["violations"] > 0)
        w_lo, w_hi = wilson(k_viol, n)
        rp, rp_lo, rp_hi = ic_moyenne([r["taux_repli"] for r in rs])
        lv, lv_lo, lv_hi = ic_moyenne([r["livraison"] for r in rs])
        seuil_txt = "-" if cle[1] is None else f"{cle[1]:.3f}"
        lignes.append(
            f"{cle[0]:<4} {seuil_txt:>11} {n:>3} "
            f"{v:>8.4%} [{v_lo:.4%},{v_hi:.4%}] "
            f"{k_viol:>3}/{n} [{w_lo:.3f},{w_hi:.3f}] "
            f"{rp:>9.4%} [{rp_lo:.4%},{rp_hi:.4%}] "
            f"{lv:>9.4%} [{lv_lo:.4%},{lv_hi:.4%}]"
        )
    sortie = "\n".join(lignes)
    print(sortie)

    brut = {
        "config": cfg,
        "empreintes_code": empreinte_fichiers([
            "/mnt/agents/output/ram_p0/moniteur.py",
            "/mnt/agents/output/ram_p0/filtre.py",
            "/mnt/agents/output/ram_p0/trace.py",
            "/mnt/agents/output/ram_p0/contraintes.py",
            "/mnt/agents/output/ram_p2/campagne_p2.py",
            "/mnt/agents/output/ram_p2/executer_p2_3.py",
        ]),
        "crn_runs_ok": crn_ok,
        "resultats_par_run": {
            f"{bras}:{seuil}": rs for (bras, seuil), rs in resultats.items()
        },
        "tableau": sortie,
    }
    with open(chemin_sortie, "w") as f:
        json.dump(brut, f, indent=1, default=str)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 2)
