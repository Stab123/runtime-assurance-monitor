"""Vérificateur d'implémentation P4b — contrôles statiques et mécaniques
exécutables AVANT l'audit externe de pré-exécution.

Ce script NE PRODUIT AUCUN RÉSULTAT SCIENTIFIQUE : il n'exécute jamais la
plante sur un bloc du design gelé. Il vérifie :

  V-1  fichiers gelés inchangés (SHA256 vs empreintes du freeze) ;
  V-2  constantes du code = protocole gelé (grille, N, z, seuils, εS/εF) ;
  V-3  équivalence exhaustive bornes Wilson §5 ⟷ seuils entiers §6
       (x = 0..5500) ;
  V-4  exhaustivité de la règle de décision : les 3^9 = 19 683
       combinaisons de labels S/I/M donnent chacune exactement un verdict
       V1–V7 (partition complète, §12) ;
  V-5  tables gelées chargeables (SHA256 internes) et variantes OCV en
       mémoire seule ;
  V-6  design gelé lisible et conforme (SHA256, 5 500 points) — LECTURE
       SEULE, aucun bloc n'est exécuté ;
  V-7  dérivation de graines : source unique (module gelé), labels
       restreints à PLANT/NOISE ;
  V-8  provenance : commit/tag de freeze dans le code = freeze réel.

Usage : python3 verifier_implementation_p4b.py
Sortie : 0 si tous les contrôles passent, 1 sinon.
"""

from __future__ import annotations

import hashlib
import itertools
import sys
from pathlib import Path

RAM_P4B = Path(__file__).resolve().parent
RACINE = RAM_P4B.parent
for p in (RAM_P4B, RACINE / "ram_p0", RACINE / "ram_p2", RACINE / "ram_p4"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import analyse_p4b as an
import campagne_p4b as camp
import graines_p4b
from modele_p4b import TablesPhysiques

ECHECS: list[str] = []


def controle(nom: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'OK ' if ok else 'ÉCHEC'}] {nom}" + (f" — {detail}" if detail else ""))
    if not ok:
        ECHECS.append(nom)


def main() -> int:
    print("=" * 72)
    print("VÉRIFICATEUR D'IMPLÉMENTATION P4b — pré-exécution, aucun résultat")
    print("=" * 72)

    # V-1 Fichiers gelés inchangés
    print("\nV-1. Intégrité des fichiers gelés (freeze "
          + camp.FREEZE_COMMIT[:12] + ")")
    sys.path.insert(0, str(RAM_P4B / "tests"))
    from test_gel_p4b import FICHIERS_GELES, MODULES_HISTORIQUES_GELES
    for rel, sha in {**FICHIERS_GELES, **MODULES_HISTORIQUES_GELES}.items():
        reel = hashlib.sha256((RACINE / rel).read_bytes()).hexdigest()
        controle(f"{rel}", reel == sha)

    # V-2 Constantes = protocole gelé
    print("\nV-2. Constantes du protocole")
    controle("grille ρ = 9 niveaux, pas 0.125",
             an.NIVEAUX_RHO == tuple(1.0 + i * 0.125 for i in range(9)))
    controle("N = 5 500", an.N_PAR_NIVEAU == 5500 == camp.N_BLOCS)
    controle("z = 2.7729212946086634", an.Z_WILSON == 2.7729212946086634)
    controle("εS = 0.01, εF = 0.05", an.EPS_S == 0.01 and an.EPS_F == 0.05)
    controle("seuils entiers 34 / 320",
             an.SEUIL_X_SUFFICIENT == 34 and an.SEUIL_X_INSUFFICIENT == 320)
    controle("garde-fou drapeaux 25 % strict", an.GARDE_FOU_FLAG == 0.25)
    controle("LOW RESOLUTION > 0.250 strict",
             an.SEUIL_LOW_RESOLUTION == 0.250)

    # V-3 Équivalence des deux méthodes de classification
    print("\nV-3. Équivalence bornes Wilson §5 ⟷ seuils entiers §6 "
          "(exhaustif, x = 0..5500)")
    controle("équivalence sur 5 501 comptages",
             an.verifier_equivalence_seuils())

    # V-4 Partition de la règle de décision
    print("\nV-4. Exhaustivité V1–V7 sur les 3^9 = 19 683 labels synthétiques")
    tous = True
    for combo in itertools.product("SIM", repeat=9):
        lab = {rho: combo[i] for i, rho in enumerate(an.NIVEAUX_RHO)}
        v = an.verdict_p4b(lab)
        if v["code"] not in {"V1", "V2", "V3", "V4", "V5", "V6", "V7"}:
            tous = False
            break
    controle("19 683 combinaisons → exactement un verdict V1–V7", tous)

    # V-5 Tables gelées
    print("\nV-5. Tables physiques")
    try:
        t = TablesPhysiques.charger()
        controle("chargement avec SHA256 gelés", True)
        vp = t.variante_ocv(+0.1)
        controle("variante OCV en mémoire (originale intacte)",
                 vp.ocv(0.0) == t.ocv(0.0) + 0.1
                 and t.ocv(0.0) == 2.834)
    except Exception as e:
        controle("chargement avec SHA256 gelés", False, str(e))

    # V-6 Design gelé — LECTURE SEULE (aucun bloc exécuté)
    print("\nV-6. Design gelé (lecture seule — aucun bloc exécuté)")
    try:
        pts = camp.charger_design()
        controle("5 500 points, SHA256 gelé", len(pts) == 5500)
        ids = [p["bloc_id"] for p in pts]
        controle("bloc_id = 0..5499 sans trou", ids == list(range(5500)))
    except Exception as e:
        controle("5 500 points, SHA256 gelé", False, str(e))

    # V-7 Graines
    print("\nV-7. Dérivation des graines")
    from verifier_design_p4b import seed_graine as seed_gele
    controle("source unique (module gelé)",
             graines_p4b.seed_graine is seed_gele)
    controle("labels restreints à PLANT/NOISE",
             graines_p4b.LABELS == ("PLANT", "NOISE"))

    # V-8 Provenance
    print("\nV-8. Provenance")
    controle("commit de freeze dans le code",
             camp.FREEZE_COMMIT == "45e509ee987469598acbf56967fb9e5cdc88a427")
    controle("tag de freeze dans le code",
             camp.FREEZE_TAG == "p4b-preregistration-freeze")
    controle("parent du freeze",
             camp.FREEZE_PARENT == "aba115ff174ee41629f1fda27b6ff826a007622c")

    print("\n" + "=" * 72)
    if ECHECS:
        print(f"VERDICT : NOT READY — {len(ECHECS)} contrôle(s) en échec :")
        for e in ECHECS:
            print(f"  - {e}")
        return 1
    print("VERDICT : TOUS LES CONTRÔLES MÉCANIQUES PASSENT")
    print("(aucun run scientifique exécuté — implémentation seule)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
