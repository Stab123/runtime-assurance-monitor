"""Pilote de puissance P3 — localisation de la transition du bras B.

Exécuté AVANT le figeage du critère de P3.1 (voir config_pilote_p3.json).

Un seul levier : delai_armement_s = r x tau_violation_s. Tout le reste est
figé (config P2.3 reprise à l'identique). Bras B uniquement ; seul le taux
de violation de B est imprimé — pas de bras C, pas de grille sigma, pas de
métrique de coût. Les champs repli/livraison que simuler() calcule
structurellement sont écartés : ils ne sont ni imprimés ni stockés.

Si le jeu de contraintes est refusé à la compilation (RA-FUN-005, modèle
nominal), le point est rapporté comme tel : c'est une donnée du régime,
pas un échec du pilote.

Le code de campagne (ram_p2/campagne_p2.py) est importé SANS modification :
mêmes fonctions simuler/tirer_parametres_plante, mêmes graines. Au point
r = 0,3 (delai_armement_s = 120 s, valeur P2), les runs de ce pilote sont
donc les runs 0..29 du bras B de P2.3, bit à bit (vérifié à l'étape 4).

Usage : python3 pilote_p3.py [config] [sortie]
"""

from __future__ import annotations

import json
import math
import random
import sys
import time
from multiprocessing import Pool
from pathlib import Path

RAM_P3 = Path(__file__).resolve().parent
RACINE = RAM_P3.parent
sys.path.insert(0, str(RACINE / "ram_p0"))
sys.path.insert(0, str(RACINE / "ram_p2"))

from campagne_p2 import (faire_jeu, simuler, tirer_parametres_plante,  # noqa: E402
                         empreinte_fichiers)

MODULES_EMPREINTE = [
    RACINE / "ram_p0" / "moniteur.py",
    RACINE / "ram_p0" / "filtre.py",
    RACINE / "ram_p0" / "trace.py",
    RACINE / "ram_p0" / "contraintes.py",
    RACINE / "ram_p2" / "campagne_p2.py",
    RAM_P3 / "pilote_p3.py",
]


def compilable(r: float, cfg: dict) -> bool:
    """Le jeu compile-t-il avec ce délai d'armement ? (RA-FUN-005, modèle
    nominal — inchangé, c'est le point du protocole.)"""
    c = dict(cfg)
    c["delai_armement_s"] = r * cfg["tau_violation_s"]
    try:
        faire_jeu(math.inf, c)
        return True
    except Exception:
        return False


def un_run(args):
    """Un run du bras B au point r. Seules les données de violation sont
    conservées (protocole : rien d'autre n'est regardé)."""
    r, i, cfg = args
    c = dict(cfg)
    c["delai_armement_s"] = r * cfg["tau_violation_s"]
    params = tirer_parametres_plante(random.Random(cfg["graine_plante"] + i), c)
    res = simuler("B", math.inf, params, cfg["graine_bruit"] + i, c)
    return r, i, {"cycles": res["cycles"], "violations": res["violations"],
                  "taux_violation": res["taux_violation"]}


def main(chemin_config=str(RAM_P3 / "config_pilote_p3.json"),
         chemin_sortie=str(RAM_P3 / "resultats_pilote_p3.json")):
    with open(chemin_config) as f:
        cfg = json.load(f)

    grille = sorted(set(cfg["grille_r_prescrite"] + cfg["grille_r_densifiee"]))
    n_runs = cfg["n_runs"]
    t0 = time.time()

    # Statut de compilation par point (déterministe, modèle nominal) —
    # établi avant tout run, indépendamment des tirages.
    statuts = {r: compilable(r, cfg) for r in grille}

    entete = []
    entete.append(f"Pilote de puissance {cfg.get('version_config', '?')} — "
                  f"bras B seul, N={n_runs} — exécuté avant figeage du critère")
    entete.append(f"tau_violation de référence : {cfg['tau_violation_s']:.0f} s "
                  f"(r = 0,3 en P2 avec delai_armement 120 s)")
    entete.append(f"{'r':>6} {'tau_arm (s)':>11}  statut / taux de violation de B")
    print("\n".join(entete), flush=True)
    lignes = []
    resultats = {}
    for r in grille:
        tau = r * cfg["tau_violation_s"]
        if not statuts[r]:
            ligne = (f"{r:6.3f} {tau:11.0f}  jeu REFUSÉ à la compilation "
                     f"(RA-FUN-005) — pas de donnée en vol")
            print(ligne, flush=True)
            lignes.append(ligne)
            resultats[f"{r}"] = {"statut": "refuse_compilation"}
            continue
        rs = [None] * n_runs
        with Pool(2) as pool:
            for _, i, res in pool.imap_unordered(
                    un_run, [(r, i, cfg) for i in range(n_runs)]):
                rs[i] = res
        k = sum(1 for x in rs if x["violations"] > 0)
        taux = sum(x["taux_violation"] for x in rs) / len(rs)
        ligne = (f"{r:6.3f} {tau:11.0f}  taux_viol B = {taux:.4%} "
                 f"({k}/{n_runs} runs avec violation)")
        print(ligne, flush=True)
        lignes.append(ligne)
        resultats[f"{r}"] = {"statut": "execute", "n_runs": n_runs,
                             "runs_avec_violation": k,
                             "taux_violation_moyen": taux,
                             "par_run": rs}
    duree = time.time() - t0
    lignes.append(f"Durée de calcul : {duree:.0f} s")
    print(lignes[-1], flush=True)
    sortie = "\n".join(entete + lignes)

    with open(chemin_sortie, "w") as f:
        json.dump({"config": cfg,
                   "empreintes_code": empreinte_fichiers(
                       [str(c) for c in MODULES_EMPREINTE]),
                   "resultats": resultats,
                   "tableau": sortie}, f, indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:])
