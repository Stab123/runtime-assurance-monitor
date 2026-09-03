"""Campagne Monte Carlo P2 — falsification du durcissement (RAM-SPEC-0001 §7).

Question : le durcissement (enveloppe + incertitude de premier ordre, H4)
produit-il un régime utile, ou un taux de repli inacceptable ?

Quatre bras, mêmes tirages (common random numbers) :
  A — sans moniteur : la couche de décision commande directement la plante ;
  B — enveloppe seule : k_sigma = 0, seuil d'incertitude infini ;
  C — moniteur complet : k_sigma = 3, seuil = point de grille ;
  D — pessimisme seul (ajout P2.2) : k_sigma = 3, seuil infini. En P2.1,
      C - B confondait deux effets ; D les décompose : B -> D -> C.

Non-circularité de sigma — le point critique :
  sigma est calculé par EstimateurEPS à partir des RÉSIDUS DE MESURE
  (innovations), jamais des paramètres du modèle de prédiction. La plante tire
  ses paramètres dans des bornes propres ; le modèle du moniteur reste le
  nominal. L'écart modèle/monde n'atteint sigma que via les mesures.

Comparabilité : pour un run donné, les paramètres de plante sont tirés une
seule fois (graine_plante + i) et le bruit est re-généré à l'identique dans
chaque bras (graine_bruit + i). Un témoin est vérifié identique entre bras.

Usage : python3 campagne_p2.py [config] [sortie]
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

from chemins import MODULES_EMPREINTE, RAM_P0, RAM_P2

sys.path.insert(0, str(RAM_P0))

from contraintes import Contrainte, Sens
from demo_eps import (DT, PERIODE_ORBITE, DUREE_LUMIERE, U_MIN, U_MAX,
                      ModeleEPS, politique_repli_eps)
from moniteur import Moniteur, Verdict, compiler_jeu
from trace import TamponAnneau


class PlanteEPS:
    """L'écart paramétrique plante/modèle est ce que la campagne mesure.
    Le moniteur ne connaît que le modèle nominal de P0."""

    T_SOLEIL = 15.0
    T_ECLIPSE = -15.0

    def __init__(self, p: dict):
        self.p = p
        self.en_lumiere = True

    def pas(self, x, u, dt):
        soc, temp = x
        i_charge = self.p["I_SUN"] if self.en_lumiere else 0.0
        dsoc = (i_charge - self.p["I_BASE"] - u) / (self.p["C_BATT_AH"] * 3600.0)
        t_env = self.T_SOLEIL if self.en_lumiere else self.T_ECLIPSE
        dtemp = self.p["H"] * (self.p["I_BASE"] + u) - self.p["C_TH"] * (temp - t_env)
        return [soc + dt * dsoc, temp + dt * dtemp]


def tirer_parametres_plante(rng: random.Random, cfg: dict) -> dict:
    """Tirage uniforme : choix le moins informatif — aucune queue inventée."""
    b = cfg["bornes_plante"]
    return {
        "C_BATT_AH": rng.uniform(*b["C_BATT_AH"]),
        "I_SUN": rng.uniform(*b["I_SUN"]),
        "I_BASE": rng.uniform(*b["I_BASE"]),
        "H": rng.uniform(*b["H"]),
        "C_TH": rng.uniform(*b["C_TH"]),
        "soc0": rng.uniform(*b["soc0"]),
        "temp0": rng.uniform(*b["temp0"]),
    }


class EstimateurEPS:
    """Correction proportionnelle + statistiques d'innovation (EWMA).

    sigma = écart-type des innovations + |biais moyen| x horizon_moniteur

    Le premier terme couvre le bruit de mesure ; le second propage sur
    l'horizon le biais systématique estimé (dérive modèle/monde).
    """

    def __init__(self, modele_nominal, dt, bruit_std, horizon_pas,
                 alpha=0.5, beta=0.02):
        self._m = modele_nominal
        self._dt = dt
        self._bruit_std = list(bruit_std)
        self._horizon = horizon_pas
        self._alpha = alpha
        self._beta = beta
        self.x = None
        self._var = [s * s for s in bruit_std]
        self._biais = [0.0, 0.0]
        self.z_dernier = None

    def maj(self, x_vrai, u_applique, rng: random.Random, facteur_bruit: float):
        # La mesure — seule entrée de l'estimateur. Deux tirages par cycle,
        # dans le même ordre, dans tous les bras (comparabilité CRN).
        eps = [rng.gauss(0.0, self._bruit_std[i] * facteur_bruit)
               for i in range(2)]
        z = [x_vrai[i] + eps[i] for i in range(2)]
        self.z_dernier = z
        # Le tirage brut sert de témoin CRN : il ne dépend que de la graine et
        # du nombre d'appels, pas de l'état (qui diverge entre bras — c'est
        # l'objet de l'expérience). Stocké avant tout calcul : le reconstruire
        # par soustraction serait faux en virgule flottante.
        self.bruit_dernier = eps
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


def faire_jeu(seuil_inc_soc: float, cfg: dict):
    modele = ModeleEPS()
    modele.en_lumiere = False
    contraintes = [
        Contrainte("C0_SOC_MIN", 0, Sens.MIN, cfg["seuil_soc"], 1.0,
                   seuil_inc_soc, cfg["delai_armement_s"],
                   cfg["marge_securite_soc"]),
        Contrainte("C1_TEMP_MAX", 1, Sens.MAX, cfg["seuil_temp"], 50.0,
                   cfg["seuil_incertitude_temp"], cfg["delai_armement_s"],
                   cfg["marge_securite_temp"]),
    ]
    return compiler_jeu(1, contraintes, modele, politique_repli_eps, DT,
                        etat_nominal=[0.6, 20.0],
                        bornes_action=(U_MIN, U_MAX))


def en_fenetre_payload(t: float, cfg: dict) -> bool:
    t_orb = t % PERIODE_ORBITE
    return cfg["fenetre_payload"][0] <= t_orb < cfg["fenetre_payload"][1]


def simuler(bras: str, seuil_inc_soc: float, params: dict,
            graine_bruit: int, cfg: dict) -> dict:
    rng = random.Random(graine_bruit)
    plante = PlanteEPS(params)
    modele_mon = ModeleEPS()     # modèle nominal de prédiction
    modele_est = ModeleEPS()     # modèle nominal de propagation (estimateur)
    k_sigma = 0.0 if bras == "B" else cfg["k_sigma"]
    moniteur = None
    horizon = 36
    if bras != "A":
        jeu = faire_jeu(seuil_inc_soc, cfg)
        horizon = jeu.horizon_pas
        moniteur = Moniteur(jeu, modele_mon, politique_repli_eps, DT,
                            TamponAnneau(cfg["capacite_tampon"]),
                            U_MIN, U_MAX, k_sigma=k_sigma)
    estimateur = EstimateurEPS(modele_est, DT, cfg["bruit_std"], horizon)

    x_vrai = [params["soc0"], params["temp0"]]
    u_prec = 0.0
    n_cycles = int(cfg["duree_s"] / DT)
    violations = replis = 0
    e_demande = e_livree = 0.0
    temoin = None
    t = 0.0
    for k in range(n_cycles):
        lum = (t % PERIODE_ORBITE) < DUREE_LUMIERE
        plante.en_lumiere = lum
        modele_mon.en_lumiere = lum
        modele_est.en_lumiere = lum
        degrade = cfg["fenetre_degradation"][0] <= t < cfg["fenetre_degradation"][1]
        facteur = cfg["facteur_degradation"] if degrade else 1.0

        x_est, sig = estimateur.maj(x_vrai, u_prec, rng, facteur)
        if k == cfg["cycle_temoin"]:
            temoin = estimateur.bruit_dernier[0]  # bruit pur — identique entre bras

        candidat = cfg["u_payload"] if en_fenetre_payload(t, cfg) else 0.0
        if bras == "A":
            u_exec = min(max(candidat, U_MIN), U_MAX)
            replis += 0
        else:
            r = moniteur.cycle(t, x_est, sig, True, candidat)
            u_exec = r.action_transmise
            if r.verdict in (Verdict.REPLI, Verdict.INDETERMINE):
                replis += 1

        # Métriques sur l'état VRAI, contre les seuils BRUTS.
        if x_vrai[0] < cfg["seuil_soc"] or x_vrai[1] > cfg["seuil_temp"]:
            violations += 1
        if en_fenetre_payload(t, cfg):
            e_demande += min(max(candidat, U_MIN), U_MAX) * DT
            e_livree += u_exec * DT

        x_vrai = list(plante.pas(x_vrai, u_exec, DT))
        u_prec = u_exec
        t += DT

    return {
        "cycles": n_cycles,
        "violations": violations,
        "replis": replis,
        "taux_violation": violations / n_cycles,
        "taux_repli": replis / n_cycles,
        "livraison": e_livree / e_demande if e_demande > 0 else 1.0,
        "temoin": temoin,
    }


def _t_975(df: int) -> float:
    try:
        from scipy.stats import t as loi_t
        return float(loi_t.ppf(0.975, df))
    except Exception:
        return 2.04 if df >= 30 else 2.09


def ic_moyenne(valeurs: list[float]) -> tuple[float, float, float]:
    n = len(valeurs)
    m = statistics.fmean(valeurs)
    if n < 2:
        return m, m, m
    e = statistics.stdev(valeurs) / math.sqrt(n) * _t_975(n - 1)
    return m, m - e, m + e


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 1.0
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - m) / d, (c + m) / d


def empreinte_fichiers(chemins) -> dict:
    """Empreintes SHA-256 tronquées, indexées par nom de fichier."""
    out = {}
    for c in chemins:
        c = Path(c)
        out[c.name] = hashlib.sha256(c.read_bytes()).hexdigest()[:16]
    return out


def main(chemin_config=None, chemin_sortie=None):
    chemin_config = Path(chemin_config or RAM_P2 / "config_p2_3.json")
    chemin_sortie = Path(chemin_sortie or RAM_P2 / "resultats_p2_3.json")
    with open(chemin_config) as f:
        cfg = json.load(f)

    grille = cfg["grille_seuil_incertitude_soc"]
    n_runs = cfg["n_runs"]
    resultats = defaultdict(list)
    crn_echecs = 0
    t0 = time.time()

    for i in range(n_runs):
        params = tirer_parametres_plante(random.Random(cfg["graine_plante"] + i), cfg)
        temoins = set()
        for bras in ("A", "B", "C", "D"):
            for seuil in (grille if bras == "C" else [None]):
                seuil_eff = seuil if bras == "C" else (
                    math.nan if bras == "A" else math.inf)
                r = simuler(bras, seuil_eff, params,
                            cfg["graine_bruit"] + i, cfg)
                temoins.add(r["temoin"])
                if bras == "C":
                    resultats[("C", seuil)].append(r)
                else:
                    resultats[(bras, None)].append(r)
        if len(temoins) != 1:
            crn_echecs += 1

    duree = time.time() - t0

    lignes = []
    lignes.append(f"Campagne {cfg.get('version_config', '?')} — "
                  f"{n_runs} runs par point")
    lignes.append(f"CRN : {n_runs - crn_echecs}/{n_runs} runs avec temoin identique "
                  f"sur les quatre bras ({'OK' if crn_echecs == 0 else 'ECHEC'})")
    lignes.append(f"Duree de calcul : {duree:.0f} s")
    entete = (f"{'bras':<4} {'seuil_sig_soc':>13} {'N':>3} "
              f"{'taux_viol (IC95)':>22} {'runs_viol [Wilson]':>22} "
              f"{'taux_repli (IC95)':>22} {'livraison (IC95)':>22}")
    lignes.append(entete)
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
            f"{cle[0]:<4} {seuil_txt:>13} {n:>3} "
            f"{v:>8.4%} [{v_lo:.4%},{v_hi:.4%}] "
