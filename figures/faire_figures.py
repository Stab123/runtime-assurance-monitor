#!/usr/bin/env python3
"""Regenerate Figures 2 and 3 of the paper from the published result files.

No data is hard-coded: every number is recomputed from the per-run records of
the campaign files. Requires matplotlib (pip install matplotlib).

Usage (from the repository root):

    python3 figures/faire_figures.py

Reads:

    ram_p2/resultats_p2_3.json   P2.3 campaign, 300 runs per point
    ram_p3/resultats_p3_1.json   P3.1 campaign, 300 runs per point

Writes:

    figures/figure_2.png  P2.3 — fallback and delivery per arm (A, B, D, C)
    figures/figure_3.png  P3.1 — cost of hardening vs arming delay
"""

import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SORTIE = os.path.join(RACINE, "figures")


def charger(chemin_relatif):
    with open(os.path.join(RACINE, chemin_relatif), encoding="utf-8") as f:
        return json.load(f)


def moyennes_par_bras(resultats_par_run):
    """Mean fallback rate, delivery and runs with violation, per arm key."""
    agregat = {}
    for cle, runs in resultats_par_run.items():
        n = len(runs)
        agregat[cle] = {
            "n": n,
            "taux_repli": 100.0 * sum(r["taux_repli"] for r in runs) / n,
            "livraison": 100.0 * sum(r["livraison"] for r in runs) / n,
            "runs_avec_violation": sum(1 for r in runs if r["violations"] > 0),
        }
    return agregat


def figure_2(p23):
    """P2.3: the safety envelope alone reaches zero violations; hardening only
    costs availability."""
    agregat = moyennes_par_bras(p23["resultats_par_run"])
    bras = [("A:None", "A\nno monitor"), ("B:None", "B\nenvelope"),
            ("D:None", "D\n+3σ eval."), ("C:0.03", "C\n+σ thresh.")]
    etiquettes = [e for _, e in bras]
    repli = [agregat[k]["taux_repli"] for k, _ in bras]
    livraison = [agregat[k]["livraison"] for k, _ in bras]
    violations = [agregat[k]["runs_avec_violation"] for k, _ in bras]

    fig, (g1, g2) = plt.subplots(1, 2, figsize=(11, 4.2))
    couleurs = ["#b0b0b0", "#2e7d32", "#ef6c00", "#c62828"]

    b1 = g1.bar(etiquettes, repli, color=couleurs)
    g1.set_ylabel("Fallback rate (%)")
    g1.set_title("(a) Fallback rate — the cost")
    for rect, v in zip(b1, repli):
        g1.annotate(f"{v:.2f}", (rect.get_x() + rect.get_width() / 2, v),
                    ha="center", va="bottom", fontsize=9)

    b2 = g2.bar(etiquettes, livraison, color=couleurs)
    g2.set_ylabel("Mission delivery (%)")
    g2.set_ylim(0, 105)
    g2.set_title("(b) Mission delivery — what remains")
    for rect, v, nv in zip(b2, livraison, violations):
        g2.annotate(f"{v:.2f}", (rect.get_x() + rect.get_width() / 2, v),
                    ha="center", va="bottom", fontsize=9)
        g2.annotate(f"{nv}/300 runs\nwith violation",
                    (rect.get_x() + rect.get_width() / 2, 4),
                    ha="center", va="bottom", fontsize=8, color="white")

    fig.suptitle("P2.3 campaign — 300 runs per arm, common random numbers "
                 "(post-correction re-run)")
    fig.tight_layout()
    chemin = os.path.join(SORTIE, "figure_2.png")
    fig.savefig(chemin, dpi=150)
    plt.close(fig)
    return chemin


def figure_3(p31):
    """P3.1: cost of hardening vs arming delay tau_arming (seconds)."""
    taus = sorted({p["tau_armement_s"] for p in p31["points"]})
    series = {}
    for point in p31["points"]:
        agregat = moyennes_par_bras(point["resultats_par_run"])
        for cle in agregat:
            series.setdefault(cle, {})[point["tau_armement_s"]] = agregat[cle]

    bras = [("B:None", "B — envelope only", "#2e7d32", "o"),
            ("D:None", "D — + 3σ evaluation", "#ef6c00", "s"),
            ("C:0.03", "C — + σ threshold (0.03)", "#c62828", "^")]

    fig, (g1, g2) = plt.subplots(1, 2, figsize=(11, 4.2))
    for cle, etiquette, couleur, marqueur in bras:
        xs = [t for t in taus if t in series.get(cle, {})]
        g1.plot(xs, [series[cle][t]["taux_repli"] for t in xs],
                marker=marqueur, color=couleur, label=etiquette)
        g2.plot(xs, [series[cle][t]["livraison"] for t in xs],
                marker=marqueur, color=couleur, label=etiquette)

    g1.set_xlabel("Arming delay τ_arming (s)")
    g1.set_ylabel("Fallback rate (%)")
    g1.set_title("(a) Fallback rate")
    g1.legend(fontsize=8)
    g1.grid(alpha=0.3)
    g2.set_xlabel("Arming delay τ_arming (s)")
    g2.set_ylabel("Mission delivery (%)")
    g2.set_title("(b) Mission delivery")
    g2.legend(fontsize=8)
    g2.grid(alpha=0.3)

    fig.suptitle("P3.1 campaign — 300 runs per point, common random numbers "
                 "(post-correction re-run)")
    fig.tight_layout()
    chemin = os.path.join(SORTIE, "figure_3.png")
    fig.savefig(chemin, dpi=150)
    plt.close(fig)
    return chemin


def main():
    os.makedirs(SORTIE, exist_ok=True)
    p23 = charger(os.path.join("ram_p2", "resultats_p2_3.json"))
    p31 = charger(os.path.join("ram_p3", "resultats_p3_1.json"))
    for chemin in (figure_2(p23), figure_3(p31)):
        print("écrit :", os.path.relpath(chemin, RACINE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
