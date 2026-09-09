"""Campagne P4a — frontiere de suffisance de l'enveloppe B (bras B seul).

PRE-ENREGISTRE (PRE_REGISTRATION_P4A.md) — ce fichier est fige au commit de
gel AVANT toute execution confirmatoire. Toute modification ulterieure cree
une nouvelle version et une nouvelle preinscription.

Facteur scientifique : b = biais SoC persistant signe (b > 0 = surestimation).
Chaine d'injection exacte :

    PLANTE -> MESURE z = x_vrai + nu (iid, echelle instrumentale)
           -> BIAIS z' = (z_SoC + b, z_temp)
           -> ESTIMATEUR (algorithme fige, non modifie)
           -> MONITEUR (enveloppe seule : k_sigma = 0, seuil d'incertitude infini)

Implementation : le biais est additif et commute avec le bruit ; passer
x_mes = [clamp(x_vrai[0] + b), x_vrai[1]] a l'estimateur fige (qui ajoute nu
lui-meme) produit exactement z' = z + b. clamp = saturation [0;1] sur le SoC
biaise (comptee par run : n_saturation ; quasi-inerte dans D_physique).

CRN : pour un bloc j donne, memes parametres de plante et meme graine de bruit
sur les 9 niveaux de biais. Temoin par run : SHA-256(parametres, graine bruit)
+ bruit pur au cycle 1000 (independant de l'etat, donc du biais).

Le dt est lu depuis cfg["dt_s"] (le defaut historique #8 de ram_p2 n'est PAS
herite : ce module n'importe pas DT pour la duree de pas).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

RAM_P4 = Path(__file__).resolve().parent
RAM_P2 = RAM_P4.parent / "ram_p2"
RAM_P0 = RAM_P4.parent / "ram_p0"
sys.path.insert(0, str(RAM_P0))
sys.path.insert(0, str(RAM_P2))
sys.path.insert(0, str(RAM_P4))

from campagne_p2 import PlanteEPS, EstimateurEPS, faire_jeu          # modules figes
from demo_eps import (PERIODE_ORBITE, DUREE_LUMIERE, U_MIN, U_MAX,
                      ModeleEPS, politique_repli_eps)
from moniteur import Moniteur, Verdict
from trace import TamponAnneau
from graines_p4 import seed_graine

# Parametres thermiques fixes (axe thermique exclu de P4a — Phase 2, L2) :
# valeurs nominales des constantes de classe du modele fige.
PARAMS_THERMIQUES_FIXES = {"H": 1.5e-3, "C_TH": 5e-4, "temp0": 20.0}

CYCLE_TEMOIN = 1000


def en_fenetre_payload(t: float, cfg: dict) -> bool:
    f = cfg["fenetre_payload"]
    return (t % PERIODE_ORBITE) >= f[0] and (t % PERIODE_ORBITE) < f[1] and \
        (t % PERIODE_ORBITE) < DUREE_LUMIERE


def simuler_p4(biais_soc: float, params: dict, graine_bruit: int,
               cfg: dict) -> dict:
    """Un run du bras B avec biais SoC persistant injecte sur la mesure."""
    import random
    rng = random.Random(graine_bruit)
    dt = float(cfg["dt_s"])
    plante = PlanteEPS(params)
    modele_mon = ModeleEPS()
    modele_est = ModeleEPS()
    jeu = faire_jeu(float("inf"), cfg)          # k_sigma=0, seuil=inf : bras B
    moniteur = Moniteur(jeu, modele_mon, politique_repli_eps, dt,
                        TamponAnneau(cfg["capacite_tampon"]),
                        U_MIN, U_MAX, k_sigma=0.0)
    estimateur = EstimateurEPS(modele_est, dt, cfg["bruit_std"],
                               jeu.horizon_pas)

    x_vrai = [params["soc0"], params["temp0"]]
    u_prec = 0.0
    n_cycles = int(cfg["duree_s"] / dt)
    violations = replis = 0
    e_demande = e_livree = 0.0
    marge_min = float("inf")
    t_premiere_violation = None
    err_somme = err_max = 0.0
    n_saturation = 0
    temoin_bruit = None
    t = 0.0
    for k in range(n_cycles):
        lum = (t % PERIODE_ORBITE) < DUREE_LUMIERE
        plante.en_lumiere = lum
        modele_mon.en_lumiere = lum
        modele_est.en_lumiere = lum

        # --- BIAIS : z' = z + b sur le canal SoC, saturation [0;1] ---------
        z_soc_biaise = x_vrai[0] + biais_soc
        if z_soc_biaise > 1.0 or z_soc_biaise < 0.0:
            n_saturation += 1
        z_soc_biaise = min(max(z_soc_biaise, 0.0), 1.0)
        x_mes = [z_soc_biaise, x_vrai[1]]

        # facteur 1.0 : pas de fenetre de degradation en P4a
        x_est, sig = estimateur.maj(x_mes, u_prec, rng, 1.0)
        if k == CYCLE_TEMOIN:
            temoin_bruit = estimateur.bruit_dernier[0]   # bruit pur (CRN)

        candidat = cfg["u_payload"] if en_fenetre_payload(t, cfg) else 0.0
        r = moniteur.cycle(t, x_est, sig, True, candidat)
        u_exec = r.action_transmise
        if r.verdict in (Verdict.REPLI, Verdict.INDETERMINE):
            replis += 1

        # --- Metriques sur l'etat VRAI, seuils BRUTS (convention figee) ----
        if x_vrai[0] < cfg["seuil_soc"] or x_vrai[1] > cfg["seuil_temp"]:
            violations += 1
            if t_premiere_violation is None:
                t_premiere_violation = t
        marge_min = min(marge_min, x_vrai[0] - cfg["seuil_soc"])
        err = x_est[0] - x_vrai[0]
        err_somme += err
        err_max = max(err_max, abs(err))
        if en_fenetre_payload(t, cfg):
            e_demande += min(max(candidat, U_MIN), U_MAX) * dt
            e_livree += u_exec * dt

        x_vrai = list(plante.pas(x_vrai, u_exec, dt))
        u_prec = u_exec
        t += dt

    return {
        "cycles": n_cycles,
        "Y": 1 if violations > 0 else 0,
        "violations_cycles": violations,
        "t_premiere_violation_s": t_premiere_violation,
        "marge_min": marge_min,
        "replis": replis,
        "taux_repli": replis / n_cycles,
        "livraison": e_livree / e_demande if e_demande > 0 else 1.0,
        "err_est_soc_moyenne": err_somme / n_cycles,
        "err_est_soc_max": err_max,
        "n_saturation": n_saturation,
        "temoin_bruit": temoin_bruit,
    }


def temoin_bloc(params: dict, graine_bruit: int) -> str:
    s = json.dumps({"params": params, "graine_bruit": graine_bruit},
                   sort_keys=True)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def executer(mode: str, cfg: dict, debut: int, fin: int) -> dict:
    """Boucle de campagne. mode in {principal, reseed, dtctrl, pilote}."""
    points = cfg["design_points"]
    niveaux = cfg["niveaux_biais"]
    if mode == "dtctrl":
        niveaux = [n for n in niveaux if n in (0.02, 0.05)]
        cfg = dict(cfg, dt_s=cfg["dt_controle_s"])
    elif mode == "pilote":
        niveaux = [0.0, 0.10]
    label_bruit = {"principal": "NOISE", "reseed": "RESEED",
                   "dtctrl": "DTCTRL", "pilote": "PILOT"}[mode]

    runs = []
    for j in range(debut, min(fin, len(points))):
        p = dict(points[j])
        bloc_id = p.pop("bloc_id")
        params = {**p, **PARAMS_THERMIQUES_FIXES}
        graine_bruit = seed_graine(label_bruit, bloc_id)
        for b in niveaux:
            t0 = time.time()
            res = simuler_p4(b, params, graine_bruit, cfg)
            runs.append({
                "run_id": f"{mode}_b{b:+.2f}_bloc{bloc_id:03d}",
                "mode": mode,
                "biais": b,
                "bloc_id": bloc_id,
                "params_plante": params,
                "graine_bruit": graine_bruit,
                "temoin_bloc": temoin_bloc(params, graine_bruit),
                **res,
                "duree_calcul_s": round(time.time() - t0, 3),
            })
    return {
        "meta": {
            "campagne": cfg["version_campagne"],
            "mode": mode,
            "statut": "CONFIRMATOIRE" if mode == "principal" else "CONTROLE",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
        "runs": runs,
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["principal", "reseed", "dtctrl", "pilote"])
    ap.add_argument("--debut", type=int, default=0)
    ap.add_argument("--fin", type=int, default=500)
    ap.add_argument("--config", default=str(RAM_P4 / "config_p4a.json"))
    ap.add_argument("--sortie", default=None)
    a = ap.parse_args()
    cfg = json.load(open(a.config))
    sortie = a.sortie or str(RAM_P4 / f"resultats_p4a_{a.mode}.json")
    json.dump(executer(a.mode, cfg, a.debut, a.fin), open(sortie, "w"))
    print(f"ecrit : {sortie}")
