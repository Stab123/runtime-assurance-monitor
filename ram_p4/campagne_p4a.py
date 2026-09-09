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

Implementation exacte (amendement pre-data, commit d'audit) : la sous-classe
EstimateurEPSBiaisee forme explicitement z = x_vrai + nu (2 tirages gauss par
cycle, meme ordre — CRN preserve), puis z' = (clip(z_SoC + b, 0, 1), z_temp),
et applique ensuite l'arithmetique de mise a jour de l'estimateur fige,
reprise a l'identique. Equivalence bit a bit avec l'estimateur fige verifiee
a b = 0, clamp inerte (controle mecanique pre-commit). n_saturation compte
les activations du clamp.

Endpoint primaire : Y depend UNIQUEMENT de SoC_vrai < seuil_soc. Les
depassements thermiques sont enregistres separement (diagnostic), jamais
dans Y (amendement pre-data).

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


class EstimateurEPSBiaisee(EstimateurEPS):
    """Estimateur fige + injection exacte du pre-enregistrement §6.

    z = x_vrai + nu est forme explicitement (2 tirages gauss par cycle, dans
    le meme ordre que l'estimateur fige — le temoin CRN bruit_dernier reste
    le bruit pur, comparable entre niveaux). Puis z' = (clip(z_SoC + b, 0, 1),
    z_temp). L'arithmetique de mise a jour (prediction, innovation, alpha,
    EWMA variance/biais, sigma) est reprise a l'identique de la classe figee.
    """

    def __init__(self, *args, biais_soc: float = 0.0, **kw):
        super().__init__(*args, **kw)
        self._biais_inj = biais_soc
        self.n_saturation = 0

    def maj(self, x_vrai, u_applique, rng, facteur_bruit: float):
        eps = [rng.gauss(0.0, self._bruit_std[i] * facteur_bruit)
               for i in range(2)]
        z = [x_vrai[i] + eps[i] for i in range(2)]
        self.z_dernier = z
        self.bruit_dernier = eps          # bruit pur — temoin CRN
        # --- injection APRES le bruit : z' = clip(z + b) -------------------
        zb0 = z[0] + self._biais_inj
        if zb0 > 1.0 or zb0 < 0.0:
            self.n_saturation += 1
        z = [min(max(zb0, 0.0), 1.0), z[1]]
        # --- arithmetique figee, inchangee ---------------------------------
        if self.x is None:
            self.x = list(z)
            return list(self.x), list(self._bruit_std)
        x_pred = list(self._m.pas(self.x, u_applique, self._dt))
        innov = [z[i] - x_pred[i] for i in range(2)]
        self.x = [x_pred[i] + self._alpha * innov[i] for i in range(2)]
        b = self._beta
        self._var = [(1 - b) * self._var[i] + b * innov[i] ** 2 for i in range(2)]
        self._biais = [(1 - b) * self._biais[i] + b * innov[i] for i in range(2)]
        sigma = [math.sqrt(self._var[i]) + abs(self._biais[i]) * self._horizon
                 for i in range(2)]
        return list(self.x), sigma


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
    estimateur = EstimateurEPSBiaisee(modele_est, dt, cfg["bruit_std"],
                                      jeu.horizon_pas, biais_soc=biais_soc)

    x_vrai = [params["soc0"], params["temp0"]]
    u_prec = 0.0
    n_cycles = int(cfg["duree_s"] / dt)
    violations = violations_temp = replis = 0
    e_demande = e_livree = 0.0
    marge_min = float("inf")
    t_premiere_violation = None
    err_somme = err_max = 0.0
    temoin_bruit = None
    t = 0.0
    for k in range(n_cycles):
        lum = (t % PERIODE_ORBITE) < DUREE_LUMIERE
        plante.en_lumiere = lum
        modele_mon.en_lumiere = lum
        modele_est.en_lumiere = lum

        # facteur 1.0 : pas de fenetre de degradation en P4a. L'injection du
        # biais a lieu DANS l'estimateur, apres formation de z = x_vrai + nu.
        x_est, sig = estimateur.maj(x_vrai, u_prec, rng, 1.0)
        if k == CYCLE_TEMOIN:
            temoin_bruit = estimateur.bruit_dernier[0]   # bruit pur (CRN)

        candidat = cfg["u_payload"] if en_fenetre_payload(t, cfg) else 0.0
        r = moniteur.cycle(t, x_est, sig, True, candidat)
        u_exec = r.action_transmise
        if r.verdict in (Verdict.REPLI, Verdict.INDETERMINE):
            replis += 1

        # --- Endpoint primaire : SoC VRAI contre seuil BRUT, uniquement ----
        if x_vrai[0] < cfg["seuil_soc"]:
            violations += 1
            if t_premiere_violation is None:
                t_premiere_violation = t
        # Diagnostic thermique separe — n'entre JAMAIS dans Y (axe exclu).
        if x_vrai[1] > cfg["seuil_temp"]:
            violations_temp += 1
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
        "violations_temp_cycles_diagnostic": violations_temp,
        "t_premiere_violation_s": t_premiere_violation,
        "marge_min": marge_min,
        "replis": replis,
        "taux_repli": replis / n_cycles,
        "livraison": e_livree / e_demande if e_demande > 0 else 1.0,
        "err_est_soc_moyenne": err_somme / n_cycles,
        "err_est_soc_max": err_max,
        "n_saturation": estimateur.n_saturation,
        "temoin_bruit": temoin_bruit,
    }


def temoin_bloc(params: dict, graine_bruit: int) -> str:
    s = json.dumps({"params": params, "graine_bruit": graine_bruit},
                   sort_keys=True)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def empreintes_code() -> dict:
    out = {}
    for f in sorted(RAM_P4.glob("*.py")):
        out[f.name] = hashlib.sha256(f.read_bytes()).hexdigest()
    return out


def executer(mode: str, cfg: dict, debut: int, fin: int,
             chemin_config: str, commit_sha: str) -> dict:
    """Boucle de campagne. mode in {principal, reseed, dtctrl, pilote}.

    DTCTRL (amendement pre-data) : MEMES 500 blocs et MEMES graines NOISE que
    le principal pour les niveaux +0.02/+0.05 — seul DT change (5 -> 2.5 s) ;
    la classification est donc directement comparable (N identique des deux
    cotes), et l'effet du DT est isole de tout effet plante/bruit."""
    points = cfg["design_points"]
    niveaux = cfg["niveaux_biais"]
    if mode == "dtctrl":
        niveaux = [n for n in niveaux if n in (0.02, 0.05)]
        cfg = dict(cfg, dt_s=cfg["dt_controle_s"])
    elif mode == "pilote":
        niveaux = [0.0, 0.10]
    label_bruit = {"principal": "NOISE", "reseed": "RESEED",
                   "dtctrl": "NOISE", "pilote": "PILOT"}[mode]

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
    import platform
    versions = {"python": platform.python_version()}
    for mod in ("numpy", "scipy", "statsmodels"):
        try:
            versions[mod] = __import__(mod).__version__
        except Exception:
            versions[mod] = None
    return {
        "meta": {
            "campagne": cfg["version_campagne"],
            "mode": mode,
            "statut": "CONFIRMATOIRE" if mode == "principal" else "CONTROLE",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "hash_code": empreintes_code(),
            "hash_config": hashlib.sha256(
                open(chemin_config, "rb").read()).hexdigest(),
            "commit_git": commit_sha,
            "versions": versions,
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
    ap.add_argument("--commit-sha", required=True,
                    help="SHA du HEAD Git au moment de l'execution (traced)")
    a = ap.parse_args()
    cfg = json.load(open(a.config))
    sortie = a.sortie or str(RAM_P4 / f"resultats_p4a_{a.mode}.json")
    json.dump(executer(a.mode, cfg, a.debut, a.fin, a.config, a.commit_sha),
              open(sortie, "w"))
    print(f"ecrit : {sortie}")
