"""Analyse de sensibilité rétrospective : r physique des plantes Monte-Carlo.

Contexte. Le τ_violation publié (205,8 s) est mesuré sur le MODÈLE NOMINAL du
moniteur (C_BATT = 10 Ah, I_BASE = 0,5 A, u = 3 A, marge de garde 0,02,
éclipse). Les plantes de la campagne tirent C_BATT ∈ [5 ; 9] Ah et
I_BASE ∈ [0,45 ; 0,60] A : leur τ_violation physique est plus court
(≈ 101 à 186 s), et le ratio physique r_plant = τ_armement / τ_violation,plant
peut dépasser 1 — le délai d'armement excède alors le temps dont dispose le
repli sur cette plante. Ce script quantifie cet écart SANS rejouer aucune
campagne :

  - les paramètres de plante sont régénérés par tirage déterministe
    (graine_plante + i, fonction pure de la configuration figée) ;
  - les violations et coûts sont lus dans les fichiers de résultats publiés
    (P2.3 et P3.1) — aucune donnée n'est recalculée ni modifiée.

Définition de τ_violation,plant : même convention que le nominal — départ à la
frontière de garde (seuil brut 0,35 + marge 0,02 = 0,37), action la plus
défavorable persistée (u = U_MAX = 3 A), éclipse (pas de courant de charge),
jusqu'au franchissement du seuil brut. La dynamique SoC en éclipse est
dSoC/dt = −(I_BASE + u) / (C_BATT × 3600), d'où :

    τ_violation,plant = 0,02 × C_BATT / (I_BASE + 3) × 3600   [s]

Sous-populations : r_plant < 0,95 ; 0,95 ≤ r_plant ≤ 1,05 ; r_plant > 1,05
(bande de ±5 % autour de 1, choisie pour l'analyse rétrospective). Comparaison B/D/C dans le
décile des r_plant les plus élevés (30 runs).

Usage :
  python3 analyse_sensibilite_r.py            # écrit resultats_sensibilite_r.json
"""

from __future__ import annotations

import json
import random
import statistics
import sys
from pathlib import Path

RAM_P3 = Path(__file__).resolve().parent
RACINE = RAM_P3.parent
sys.path.insert(0, str(RACINE / "ram_p0"))
sys.path.insert(0, str(RACINE / "ram_p2"))

from campagne_p2 import tirer_parametres_plante  # noqa: E402

MARGE_GARDE = 0.02          # marge de sécurité de C0_SOC_MIN (config figée)
U_PIRE = 3.0                # U_MAX, borne haute du domaine d'action déclaré
BANDE_UNITE = 0.05          # r ∈ [0,95 ; 1,05] compte comme « ≈ 1 »


def tau_violation_plante(p: dict) -> float:
    """Temps de franchissement du seuil brut depuis la frontière de garde,
    action la plus défavorable persistée, éclipse (définition du scénario)."""
    return MARGE_GARDE * p["C_BATT_AH"] / (p["I_BASE"] + U_PIRE) * 3600.0


def sous_population(r: float) -> str:
    if r < 1.0 - BANDE_UNITE:
        return "inferieur"
    if r > 1.0 + BANDE_UNITE:
        return "superieur"
    return "unite"


def analyser_point(nom: str, tau_armement: float, res_par_run: dict,
                   taus: list[float]) -> dict:
    bras_liste = sorted(res_par_run.keys())
    r_plant = [tau_armement / t for t in taus]

    sous = {"inferieur": [], "unite": [], "superieur": []}
    for i, r in enumerate(r_plant):
        sous[sous_population(r)].append(i)

    detail_sous = {}
    for cle, idx in sous.items():
        entree = {"n_runs": len(idx)}
        for bras in bras_liste:
            entree[bras] = {
                "runs_avec_violation": sum(1 for i in idx
                                           if res_par_run[bras][i]["violations"] > 0),
                "taux_repli_moyen": (statistics.mean(res_par_run[bras][i]["taux_repli"]
                                                     for i in idx) if idx else None),
                "livraison_moyenne": (statistics.mean(res_par_run[bras][i]["livraison"]
                                                      for i in idx) if idx else None),
            }
        detail_sous[cle] = entree

    decile = sorted(range(len(r_plant)), key=lambda i: -r_plant[i])[:30]
    detail_decile = {"r_plant_min": min(r_plant[i] for i in decile),
                     "r_plant_max": max(r_plant[i] for i in decile)}
    for bras in bras_liste:
        detail_decile[bras] = {
            "runs_avec_violation": sum(1 for i in decile
                                       if res_par_run[bras][i]["violations"] > 0),
            "taux_repli_moyen": statistics.mean(res_par_run[bras][i]["taux_repli"]
                                                for i in decile),
            "livraison_moyenne": statistics.mean(res_par_run[bras][i]["livraison"]
                                                 for i in decile),
        }

    return {
        "campagne": nom,
        "tau_armement_s": tau_armement,
        "r_plant_min": min(r_plant), "r_plant_max": max(r_plant),
        "sous_populations": detail_sous,
        "decile_r_max": detail_decile,
    }


def main() -> None:
    cfg23 = json.load(open(RACINE / "ram_p2" / "config_p2_3.json"))
    res23 = json.load(open(RACINE / "ram_p2" / "resultats_p2_3.json"))
    res31 = json.load(open(RAM_P3 / "resultats_p3_1.json"))

    n = cfg23["n_runs"]
    plantes = [tirer_parametres_plante(random.Random(cfg23["graine_plante"] + i),
                                       cfg23)
               for i in range(n)]
    taus = [tau_violation_plante(p) for p in plantes]

    # P2.3 et P3.1 partagent graine_plante et bornes : la plante i est
    # identique dans les deux campagnes (vérifié à la lecture des configs).
    points = [("P2.3", cfg23["delai_armement_s"], res23["resultats_par_run"])]
    points += [(f"P3.1 (r_config {p['r']})", p["tau_armement_s"],
                p["resultats_par_run"]) for p in res31["points"]]

    sortie = {
        "definition": {
            "tau_violation_plante_s": "0,02 x C_BATT / (I_BASE + 3) x 3600 — "
                "éclipse, action la plus défavorable persistée, de la "
                "frontière de garde (0,37) au seuil brut (0,35)",
            "tau_violation_nominal_s": tau_violation_plante(
                {"C_BATT_AH": 10.0, "I_BASE": 0.5}),
            "bande_unite": BANDE_UNITE,
            "source": "analyse rétrospective — tirages déterministes de la "
                "config figée + fichiers de résultats publiés ; aucune "
                "campagne rejouée, aucune donnée modifiée",
        },
        "tau_violation_plant_min_s": min(taus),
        "tau_violation_plant_max_s": max(taus),
        "points": [analyser_point(nom, tau, res, taus)
                   for nom, tau, res in points],
    }

    with open(RAM_P3 / "resultats_sensibilite_r.json", "w") as f:
        json.dump(sortie, f, indent=1)

    print(f"τ_violation nominal : {sortie['definition']['tau_violation_nominal_s']:.1f} s")
    print(f"τ_violation plantes : {min(taus):.1f} à {max(taus):.1f} s")
    for pt in sortie["points"]:
        sp = pt["sous_populations"]
        print(f"{pt['campagne']:22s} τ_arm = {pt['tau_armement_s']:5.0f} s  "
              f"r_plant [{pt['r_plant_min']:.2f} ; {pt['r_plant_max']:.2f}]  "
              f"B viol. r<1 : {sp['inferieur']['B:None']['runs_avec_violation']}/{sp['inferieur']['n_runs']}, "
              f"r≈1 : {sp['unite']['B:None']['runs_avec_violation']}/{sp['unite']['n_runs']}, "
              f"r>1 : {sp['superieur']['B:None']['runs_avec_violation']}/{sp['superieur']['n_runs']}")


if __name__ == "__main__":
    main()
