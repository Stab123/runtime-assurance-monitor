"""Campagne P4b — frontière de suffisance de l'enveloppe B face à l'aléa
physique V_pack < 5.0 V. IMPLÉMENTATION DU PROTOCOLE GELÉ.

PRÉENREGISTRÉ (P4B_PREREGISTRATION_v0.1.md, gelé au commit
45e509ee987469598acbf56967fb9e5cdc88a427, tag p4b-preregistration-freeze).
Ce fichier est une implémentation stricte : aucune liberté
d'interprétation résiduelle. Toute modification ultérieure crée une
nouvelle version et un amendement écrit au protocole AVANT reprise
(§14, procédure de divergence).

Facteur expérimental : rho = facteur de scaling résistif (Rs, Rp — jamais
Cp), grille gelée {1.000 ; 1.125 ; … ; 2.000} (§3).

CRN (§7) : pour un bloc j donné, mêmes paramètres de plante (lus depuis le
design gelé — JAMAIS régénérés) et même graine de bruit
seed_graine("NOISE", j) sur les 9 niveaux de rho. Ordre des runs fixe :
bloc-major, rho croissant (§7).

Endpoint (§4) : V_min = min sur k = 0..2699 de V_pack(t_k), évalué sur
l'état (SoC(t_k), Vp(t_k)) avec le courant effectivement appliqué au pas
(u_exec après moniteur, y compris en repli) ; Y = 1{V_min < 5.0} strict,
float64 ; toutes phases ; INVALID_TECHNIQUE tolérance zéro (NaN/Inf,
interruption — aucune substitution de Y).

Moniteur B : INCHANGÉ, importé des modules gelés ram_p0/ram_p2 (aucune
copie) — enveloppe seule : faire_jeu(float("inf"), cfg), k_sigma = 0.0,
comme la campagne P4a gelée. Estimateur : EstimateurEPS gelé (b = 0 en
P4b — la sous-classe biaisée de P4a n'est pas utilisée ; la classe de base
à b ≡ 0 est exactement l'arithmétique gelée, 2 tirages gauss par cycle
dans le même ordre — CRN préservé).

Scénario : lu depuis ram_p4/config_p4a.json GELÉ (source unique, aucune
duplication) : T = 13 500 s, dt = 5.0 s (contrôle 2.5 s), orbite 5 400 s,
lumière (t % 5400) < 3600, payload (t % 5400) ∈ [600 ; 1500) et lumière,
u_payload = 3.0 A, bruit_std = [1e-7 ; 0.1].

EXÉCUTION : la campagne principale sur le design réel est INTERDITE avant
le GO de l'audit externe de pré-exécution. Le point d'entrée CLI exige
--execution-autorisee pour tout run sur le design gelé. Les tests
n'utilisent que des cas synthétiques (jamais un bloc du design).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import socket
import sys
import time
from pathlib import Path

RAM_P4B = Path(__file__).resolve().parent
RAM_P4 = RAM_P4B.parent / "ram_p4"
RAM_P2 = RAM_P4B.parent / "ram_p2"
RAM_P0 = RAM_P4B.parent / "ram_p0"
for p in (str(RAM_P0), str(RAM_P2), str(RAM_P4), str(RAM_P4B)):
    if p not in sys.path:
        sys.path.insert(0, p)

from campagne_p2 import EstimateurEPS, faire_jeu                    # modules gelés
from demo_eps import (PERIODE_ORBITE, DUREE_LUMIERE, U_MIN, U_MAX,  # gelés
                      ModeleEPS, politique_repli_eps)
from moniteur import Moniteur, Verdict                              # gelé
from trace import TamponAnneau                                      # gelé

from graines_p4b import graine_bruit_bloc
from modele_p4b import (PlanteP4b, TablesPhysiques, est_fini,
                        hors_domaine)
from schemas_p4b import valider_run

# --- Constantes gelées du protocole -----------------------------------------
FREEZE_COMMIT = "45e509ee987469598acbf56967fb9e5cdc88a427"
FREEZE_TAG = "p4b-preregistration-freeze"
FREEZE_PARENT = "aba115ff174ee41629f1fda27b6ff826a007622c"
COMMIT_V141 = "2d4ce6a2cecc52778a2f5ebf649e2a128c6a8138"
DOI_V141 = "10.5281/zenodo.22681860"

NIVEAUX_RHO = tuple(1.0 + i * 0.125 for i in range(9))  # exact en binaire
N_BLOCS = 5500
V_MIN_PACK = 5.0
SEUIL_SOC_DESCRIPTEUR = 0.35   # descripteur secondaire §4 (hors verdict)
CYCLE_TEMOIN = 1000            # mécanisme P4a repris (§14)

SHA256_DESIGN = ("20dcb71d9d8bde837f398157882811bc391e94f713e01ec7baedcb42ff"
                 "815a63")

# Paramètres thermiques fixes — repris à l'identique de la campagne P4a
# gelée (axe thermique hors facteur expérimental ; héritage P4a §2).
PARAMS_THERMIQUES_FIXES = {"H": 1.5e-3, "C_TH": 5e-4, "temp0": 20.0}

MODES = ("principal", "dtctrl", "ocv_plus", "ocv_moins")
DELTA_OCV_SENSIBILITE = 0.1    # V — §13 (points SoC {0.00 ; 0.02})


class DesignGeleModifie(Exception):
    """Le fichier de design ne correspond pas à l'empreinte gelée."""


class CampagneInvalideTechnique(Exception):
    """≥ 1 run INVALID_TECHNIQUE : la campagne est ARRÊTÉE immédiatement
    (§12, V0 : « campagne arrêtée, cause documentée, reprise uniquement
    après correction et ré-exécution intégrale avec les mêmes graines —
    jamais de relance partielle »). L'enregistrement fautif est écrit et
    la méta porte le statut INVALID avant l'arrêt."""


class _RunInvalideTechnique(Exception):
    """NaN/Inf détecté — INVALID_TECHNIQUE (§4, tolérance zéro)."""


def charger_design(chemin: Path | None = None) -> list[dict]:
    """Lit les 5 500 points du design GELÉ. Ne génère JAMAIS rien : la
    graine PLANT n'est pas utilisée en campagne (§8) — les points sont lus
    depuis le fichier gelé dont le SHA256 est vérifié."""
    f = chemin or (RAM_P4B / "config_p4b_design.json")
    brut = f.read_bytes()
    sha = hashlib.sha256(brut).hexdigest()
    if sha != SHA256_DESIGN:
        raise DesignGeleModifie(f"design : SHA256 {sha} != gelé {SHA256_DESIGN}")
    points = json.loads(brut.decode("utf-8"))["design_points"]
    if len(points) != N_BLOCS:
        raise DesignGeleModifie(f"{len(points)} points != {N_BLOCS}")
    return points


def charger_scenario(chemin: Path | None = None) -> tuple[dict, str]:
    """Lit les paramètres de scénario depuis la config P4a GELÉE (source
    unique — aucune duplication de constantes). Retourne (cfg, sha256)."""
    f = chemin or (RAM_P4 / "config_p4a.json")
    brut = f.read_bytes()
    src = json.loads(brut.decode("utf-8"))
    cles = ("duree_s", "dt_s", "dt_controle_s", "delai_armement_s",
            "seuil_soc", "seuil_temp", "marge_securite_soc",
            "marge_securite_temp", "u_payload", "fenetre_payload",
            "capacite_tampon", "seuil_incertitude_soc",
            "seuil_incertitude_temp", "k_sigma", "bruit_std")
    cfg = {k: src[k] for k in cles}
    return cfg, hashlib.sha256(brut).hexdigest()


def en_fenetre_payload(t: float, cfg: dict) -> bool:
    """(t % 5400) ∈ [600 ; 1500) ET lumière — identique à campagne_p4a."""
    f = cfg["fenetre_payload"]
    return (t % PERIODE_ORBITE) >= f[0] and (t % PERIODE_ORBITE) < f[1] and \
        (t % PERIODE_ORBITE) < DUREE_LUMIERE


def simuler_p4b(rho: float, params: dict, graine_bruit: int, cfg: dict,
                tables: TablesPhysiques) -> dict:
    """Un run du bras B au niveau rho — implémentation stricte du §4.

    Retourne l'enregistrement JSONL (schéma schemas_p4b). Ne lève jamais
    d'exception métier : toute anomalie technique est convertie en
    invalid_technique = true avec Y = null (tolérance zéro, aucune
    substitution — §4).
    """
    rec: dict = {
        "Y": None, "V_min": None, "t_min": None, "soc_at_vmin": None,
        "Vp_at_vmin": None, "I_batt_at_vmin": None, "I_cell_at_vmin": None,
        "soc_min": None, "violation_silencieuse": None,
        "outside_domain": False, "outside_first_t": None,
        "outside_duration": 0.0, "outside_low": False, "outside_high": False,
        "outside_at_vmin": None,
        "invalid_technique": False, "invalid_reason": None,
        "fallback_fraction": None, "payload_delivery_fraction": None,
        "temoin_bruit": None,
    }
    dt = float(cfg["dt_s"])
    n_cycles = int(cfg["duree_s"] / dt)
    rec["cycles"] = n_cycles
    try:
        rng = random.Random(graine_bruit)
        plante = PlanteP4b(params, rho, tables)
        modele_mon = ModeleEPS()   # modèle nominal gelé du moniteur (P0)
        modele_est = ModeleEPS()   # modèle nominal gelé de l'estimateur
        jeu = faire_jeu(float("inf"), cfg)     # bras B : enveloppe seule
        moniteur = Moniteur(jeu, modele_mon, politique_repli_eps, dt,
                            TamponAnneau(cfg["capacite_tampon"]),
                            U_MIN, U_MAX, k_sigma=0.0)
        estimateur = EstimateurEPS(modele_est, dt, cfg["bruit_std"],
                                   jeu.horizon_pas)

        x_vrai = [params["soc0"], params["temp0"]]
        u_prec = 0.0
        replis = 0
        e_demande = e_livree = 0.0
        v_min = float("inf")
        k_min = -1
        vmin_soc = vmin_vp = vmin_ibatt = vmin_icell = None
        vmin_outside = None
        soc_min = float("inf")

        for k in range(n_cycles):
            t = k * dt   # exact en float64 pour dt ∈ {5.0 ; 2.5} (k·5/2^j)
            lum = (t % PERIODE_ORBITE) < DUREE_LUMIERE
            plante.en_lumiere = lum
            modele_mon.en_lumiere = lum
            modele_est.en_lumiere = lum

            x_est, sig = estimateur.maj(x_vrai, u_prec, rng, 1.0)
            if k == CYCLE_TEMOIN:
                rec["temoin_bruit"] = estimateur.bruit_dernier[0]  # bruit pur

            candidat = cfg["u_payload"] if en_fenetre_payload(t, cfg) else 0.0
            r = moniteur.cycle(t, x_est, sig, True, candidat)
            u_exec = r.action_transmise
            if r.verdict in (Verdict.REPLI, Verdict.INDETERMINE):
                replis += 1

            # --- Endpoint §4 : V_pack(t_k) sur l'état à t_k avec le courant
            # effectivement appliqué à ce pas (y compris en repli, u_exec=0).
            soc_k = x_vrai[0]
            vp_k = plante.vp
            i_batt_k = plante.i_batt(u_exec)
            i_cell_k = plante.i_cell(u_exec)
            v_k = plante.v_pack(soc_k, vp_k, u_exec)
            if not est_fini(soc_k, vp_k, v_k, x_vrai[1]):
                raise _RunInvalideTechnique(
                    f"valeur non finie au pas k={k} (t={t} s)")

            if v_k < v_min:          # strict : premier argmin conservé
                v_min = v_k
                k_min = k
                vmin_soc, vmin_vp = soc_k, vp_k
                vmin_ibatt, vmin_icell = i_batt_k, i_cell_k
                vmin_outside = hors_domaine(soc_k)
            if soc_k < soc_min:
                soc_min = soc_k

            # --- Drapeau hors domaine physique (§9) : l'état n'est JAMAIS
            # saturé ; seules les entrées des tables sont clampées (modèle).
            if hors_domaine(soc_k):
                if not rec["outside_domain"]:
                    rec["outside_domain"] = True
                    rec["outside_first_t"] = t
                rec["outside_duration"] += dt
                if soc_k < 0.0:
                    rec["outside_low"] = True
                if soc_k > 1.0:
                    rec["outside_high"] = True

            # --- Descripteur opérationnel (hors verdict) : énergie payload.
            if en_fenetre_payload(t, cfg):
                e_demande += min(max(candidat, U_MIN), U_MAX) * dt
                e_livree += u_exec * dt

            x_vrai = list(plante.pas(x_vrai, u_exec, dt))
            u_prec = u_exec

        # Run complet ssi k = n_cycles - 1 atteint sans exception (§4).
        rec["Y"] = 1 if v_min < V_MIN_PACK else 0   # inégalité stricte, float64
        rec["V_min"] = v_min
        rec["t_min"] = k_min * dt
        rec["soc_at_vmin"] = vmin_soc
        rec["Vp_at_vmin"] = vmin_vp
        rec["I_batt_at_vmin"] = vmin_ibatt
        rec["I_cell_at_vmin"] = vmin_icell
        rec["outside_at_vmin"] = vmin_outside
        rec["soc_min"] = soc_min
        # Descripteur secondaire préenregistré (§4) : violation silencieuse
        # = Y = 1 ∧ min SoC ≥ 0.35 — descriptif, hors verdict.
        rec["violation_silencieuse"] = bool(
            rec["Y"] == 1 and soc_min >= SEUIL_SOC_DESCRIPTEUR)
        rec["fallback_fraction"] = replis / n_cycles
        rec["payload_delivery_fraction"] = (
            e_livree / e_demande if e_demande > 0 else 1.0)
    except _RunInvalideTechnique as e:
        rec["invalid_technique"] = True
        rec["invalid_reason"] = str(e)
    except Exception as e:  # run interrompu : INVALID_TECHNIQUE (§4)
        rec["invalid_technique"] = True
        rec["invalid_reason"] = f"{type(e).__name__}: {e}"
    return rec


def temoin_bloc(params: dict, graine_bruit: int) -> str:
    """Hash par bloc : paramètres + graine bruit (mécanisme P4a repris, §14)."""
    s = json.dumps({"params": params, "graine_bruit": graine_bruit},
                   sort_keys=True)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def empreintes_code() -> dict:
    """SHA256 de tout le code P4b et des modules gelés importés (§14 —
    mécanisme empreintes_code de P4a, étendu aux dépendances gelées)."""
    out = {}
    for f in sorted(RAM_P4B.glob("*.py")):
        out[f"ram_p4b/{f.name}"] = hashlib.sha256(f.read_bytes()).hexdigest()
    for f in sorted(RAM_P4B.glob("data/*.csv")):
        out[f"ram_p4b/data/{f.name}"] = hashlib.sha256(f.read_bytes()).hexdigest()
    for rel in ("ram_p0/moniteur.py", "ram_p0/demo_eps.py",
                "ram_p0/contraintes.py", "ram_p0/filtre.py", "ram_p0/trace.py",
                "ram_p2/campagne_p2.py", "ram_p2/chemins.py",
                "ram_p4/config_p4a.json"):
        f = RAM_P4B.parent / rel
        out[rel] = hashlib.sha256(f.read_bytes()).hexdigest()
    return out


def meta_provenance(mode: str, sha_scenario: str) -> dict:
    """Champs de provenance pour la future exécution (§14)."""
    versions = {"python": platform.python_version()}
    for mod in ("numpy", "scipy"):
        try:
            versions[mod] = __import__(mod).__version__
        except Exception:
            versions[mod] = None
    return {
        "campagne": "P4b-structural-v1",
        "mode": mode,
        "statut": "CONFIRMATOIRE" if mode == "principal" else "CONTROLE/SENSIBILITE",
        "freeze_commit": FREEZE_COMMIT,
        "freeze_tag": FREEZE_TAG,
        "freeze_parent": FREEZE_PARENT,
        "commit_v1_4_1": COMMIT_V141,
        "doi_v1_4_1": DOI_V141,
        "sha256_design": SHA256_DESIGN,
        "sha256_scenario_p4a": sha_scenario,
        "empreintes_code": empreintes_code(),
        "versions": versions,
        "os": platform.platform(),
        "machine": platform.machine(),
        "hostname": socket.gethostname(),
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def executer(mode: str, debut: int, fin: int, chemin_sortie: Path,
             tables: TablesPhysiques | None = None,
             niveaux_dtctrl_extra: tuple[float, ...] = (),
             points: list[dict] | None = None,
             cfg: dict | None = None) -> dict:
    """Boucle de campagne bloc-major (ordre fixe §7).

    mode = principal : 9 niveaux, dt = 5.0 s ;
    mode = dtctrl    : niveaux {1.000 ; 2.000} (+ niveaux_dtctrl_extra,
                       la paire bornant la frontière si V4 s'applique — §14),
                       dt = 2.5 s, MÊMES graines NOISE (seul dt change) ;
    mode = ocv_plus / ocv_moins : 9 niveaux, variante OCV ±0.1 V en mémoire
                       (§13 — la table gelée sur disque n'est pas modifiée),
                       mêmes points et mêmes graines (CRN).
    """
    if points is None:
        points = charger_design()
    if cfg is None:
        cfg, sha_scenario = charger_scenario()
    else:
        sha_scenario = "fourni-exterieurement (cas synthétique)"
    if tables is None:
        tables = TablesPhysiques.charger()
    if mode == "ocv_plus":
        tables = tables.variante_ocv(+DELTA_OCV_SENSIBILITE)
    elif mode == "ocv_moins":
        tables = tables.variante_ocv(-DELTA_OCV_SENSIBILITE)

    if mode == "dtctrl":
        niveaux = tuple(sorted({NIVEAUX_RHO[0], NIVEAUX_RHO[-1],
                                *niveaux_dtctrl_extra}))
        cfg = dict(cfg, dt_s=cfg["dt_controle_s"])
    else:
        niveaux = NIVEAUX_RHO

    n_runs = 0
    with open(chemin_sortie, "w", encoding="utf-8") as f:
        for j in range(debut, min(fin, len(points))):   # bloc-major (§7)
            p = dict(points[j])
            bloc_id = p.pop("bloc_id")
            params = {**p, **PARAMS_THERMIQUES_FIXES}
            graine = graine_bruit_bloc(bloc_id)          # CRN (§7)
            tb = temoin_bloc(params, graine)
            for rho in niveaux:                          # rho croissant
                rec = simuler_p4b(rho, params, graine, cfg, tables)
                rec.update({
                    "run_id": f"{mode}_rho{rho:.3f}_bloc{bloc_id:05d}",
                    "mode": mode,
                    "bloc_id": bloc_id,
                    "rho": rho,
                    "C_BATT_AH": params["C_BATT_AH"],
                    "I_SUN": params["I_SUN"],
                    "I_BASE": params["I_BASE"],
                    "soc0": params["soc0"],
                    "noise_seed": graine,
                    "dt_s": float(cfg["dt_s"]),
                    "temoin_bloc": tb,
                })
                erreurs = valider_run(rec)
                if erreurs:
                    raise RuntimeError(
                        f"enregistrement non conforme au schéma "
                        f"(bloc {bloc_id}, rho {rho}) : {erreurs}")
                f.write(json.dumps(rec, sort_keys=True) + "\n")
                f.flush()
                n_runs += 1
                if rec["invalid_technique"]:
                    # §12 V0 : campagne ARRÊTÉE, cause documentée. La méta
                    # est écrite avec le statut INVALID avant l'arrêt ; la
                    # reprise exige correction + ré-exécution INTÉGRALE.
                    meta = meta_provenance(mode, sha_scenario)
                    meta["n_runs_avant_arret"] = n_runs
                    meta["statut"] = "INVALID / TECHNICAL FAILURE"
                    meta["cause"] = (f"run {rec['run_id']} : "
                                     f"{rec['invalid_reason']}")
                    meta["fichier_runs"] = chemin_sortie.name
                    with open(chemin_sortie.with_suffix(".meta.json"), "w",
                              encoding="utf-8") as fm:
                        json.dump(meta, fm, indent=1, sort_keys=True)
                    raise CampagneInvalideTechnique(
                        f"V0 — campagne arrêtée au run {rec['run_id']} : "
                        f"{rec['invalid_reason']}")
    meta = meta_provenance(mode, sha_scenario)
    meta["n_runs"] = n_runs
    meta["fichier_runs"] = chemin_sortie.name
    with open(chemin_sortie.with_suffix(".meta.json"), "w",
              encoding="utf-8") as f:
        json.dump(meta, f, indent=1, sort_keys=True)
    return meta


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=MODES)
    ap.add_argument("--debut", type=int, default=0)
    ap.add_argument("--fin", type=int, default=N_BLOCS)
    ap.add_argument("--sortie", type=Path, required=True)
    ap.add_argument("--niveaux-dtctrl-extra", type=float, nargs="*",
                    default=(), help="paire bornant la frontière si V4 (§14)")
    ap.add_argument("--execution-autorisee", action="store_true",
                    help="GO explicite de l'audit externe de pré-exécution. "
                         "SANS ce drapeau, tout run sur le design gelé est "
                         "refusé (le code est livré avant exécution).")
    a = ap.parse_args()
    if not a.execution_autorisee:
        print("REFUS : exécution sur le design gelé interdite sans "
              "--execution-autorisee (audit externe de pré-exécution "
              "préalable — protocole §17/§18).")
        sys.exit(2)
    m = executer(a.mode, a.debut, a.fin, a.sortie,
                 niveaux_dtctrl_extra=tuple(a.niveaux_dtctrl_extra))
    print(f"écrit : {a.sortie} ({m['n_runs']} runs)")
