"""Vérification indépendante des empreintes de code embarquées dans les résultats.

Recalcule les empreintes SHA-256 (16 premiers caractères hexadécimaux) des
octets d'archive présents dans empreintes/ — les fichiers exacts ayant produit
les résultats — et les compare, module par module, aux empreintes embarquées
dans chaque fichier de résultats (ram_p2/resultats_p2_*.json,
ram_p3/resultats_pilote_p3.json, puis ram_p3/resultats_p3_1.json).

Usage :  python3 verifier_empreintes.py
         (à lancer depuis la racine du dépôt cloné, n'importe quel répertoire
         courant convient : les chemins sont résolus relativement à ce script)

La sortie affiche pour chaque campagne et chaque module l'empreinte calculée
et l'empreinte attendue côte à côte : le verdict ne demande pas de faire
confiance au script, la table se relit d'elle-même.

Verdict attendu : tous les modules IDENTIQUE, stables entre P2.2, P2.3 et P3
(code corrigé de septembre 2026). Deux exceptions documentées :

1. campagne_p2.py de P2.1 porte l'empreinte de l'ancien pilote à trois bras
   (0dad3d6d5bfe9f55), édité en place et perdu — la version quatre bras
   d'empreintes/ le remplace (motif complet dans empreintes/README.md) ;
2. P2.1, historique, n'a pas été rejouée après la correction de septembre
   2026 (off-by-one RA-FUN-004 + projection sous u_min) : ses empreintes
   moniteur.py et filtre.py pointent sur les octets pré-correction, archivés
   sous empreintes/pre_correction/. P2.2, P2.3 et P3 ont été rejouées avec
   le code corrigé, configurations strictement inchangées.
"""

import hashlib
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
EMPREINTES = RACINE / "empreintes"

# Octets d'archive dans empreintes/ — jamais la copie exécutable de ram_p0/
# et ram_p2/ (chemins relativisés, donc octets différents pour les pilotes).
MODULES = [
    "moniteur.py",
    "filtre.py",
    "trace.py",
    "contraintes.py",
    "campagne_p2.py",
    "executer_p2_3.py",
    "pilote_p3.py",
    "executer_p3_1.py",
    "campagne_p2_rejeu.py",
    "executer_p2_3_rejeu.py",
    "pre_correction/moniteur.py",
    "pre_correction/filtre.py",
]

# Les campagnes rejouées (septembre 2026 : P2.2, P2.3, P3) ont tourné avec
# les copies REJOUABLES (chemins relativisés) de campagne_p2.py et
# executer_p2_3.py : octets différents des archives d'origine à chemins
# absolus, sémantique inchangée (prouvé par non-régression bit à bit :
# bras A de P3.1 == bras A de P2.3, 6300/6300 champs identiques ; pilote P3
# à r = 0,3 == bras B de P2.3, 90/90 champs identiques — voir ram_p3/README.md).
ALIAS_REJEU = {"campagne_p2.py": "campagne_p2_rejeu.py",
               "executer_p2_3.py": "executer_p2_3_rejeu.py"}

# P2.1 (historique, non rejouée) : moniteur.py et filtre.py pré-correction.
ALIAS_PRE_CORRECTION = {"moniteur.py": "pre_correction/moniteur.py",
                        "filtre.py": "pre_correction/filtre.py"}

RESULTATS = [
    "ram_p2/resultats_p2_1.json",
    "ram_p2/resultats_p2_2.json",
    "ram_p2/resultats_p2_3.json",
    "ram_p3/resultats_pilote_p3.json",
    "ram_p3/resultats_p3_1.json",
]

# Empreinte du pilote P2.1 (3 bras), perdu — voir empreintes/README.md.
EMPREINTE_PILOTE_P2_1 = "0dad3d6d5bfe9f55"


def empreinte(chemin: Path) -> str:
    return hashlib.sha256(chemin.read_bytes()).hexdigest()[:16]


def main() -> int:
    locales = {}
    for nom in MODULES:
        p = EMPREINTES / nom
        locales[nom] = empreinte(p) if p.exists() else None

    tout_ok = True
    for res in RESULTATS:
        p = RACINE / res
        if not p.exists():
            print(f"{res} : absent")
            tout_ok = False
            continue
        embarquees = json.loads(p.read_text())["empreintes_code"]
        print(f"== {res} ==")
        for nom, ref in embarquees.items():
            nom_archive = nom
            note = ""
            if "p2_1" in res and nom in ALIAS_PRE_CORRECTION:
                nom_archive = ALIAS_PRE_CORRECTION[nom]
                note = " (pré-correction, archivé)"
            elif "p2_1" not in res and nom in ALIAS_REJEU:
                nom_archive = ALIAS_REJEU[nom]
                note = " (copie rejouable)"
            loc = locales.get(nom_archive)
            ok = loc == ref
            if not ok and nom == "campagne_p2.py" and "p2_1" in res \
                    and ref == EMPREINTE_PILOTE_P2_1:
                # Pilote historique à trois bras, perdu (édité en place) :
                # la version quatre bras d'empreintes/ le remplace.
                print(f"  {nom:20s} attendue={ref}  archive={loc}  "
                      f"pilote P2.1 (3 bras), remplacé par la version "
                      f"4 bras — attendu (empreintes/README.md)")
                continue
            tout_ok &= ok
            print(f"  {nom:20s} attendue={ref}  archive={loc}  "
                  f"{'IDENTIQUE' if ok else 'DIFFÈRE'}{note}")

    # Stabilité des modules du moniteur sur les campagnes rejouées (code
    # corrigé) — P2.1, pré-correction, est vérifiée séparément ci-dessus.
    modules_moniteur = ["moniteur.py", "filtre.py", "trace.py", "contraintes.py"]
    series = {m: set() for m in modules_moniteur}
    for res in RESULTATS:
        if "p2_1" in res:
            continue
        p = RACINE / res
        if p.exists():
            emb = json.loads(p.read_text())["empreintes_code"]
            for m in modules_moniteur:
                series[m].add(emb.get(m))
    stables = all(len(s) == 1 for s in series.values())
    print("----")
    print("Empreintes des modules du moniteur stables entre P2.2, P2.3 et P3 "
          "(code corrigé) :", "OUI" if stables else "NON")
    print("P2.1 : vérifiée contre les octets pré-correction archivés "
          "(empreintes/pre_correction/).")
    print("VERDICT GLOBAL :", "CONFORME" if (tout_ok and stables) else "ÉCART DÉTECTÉ")
    return 0 if (tout_ok and stables) else 1


if __name__ == "__main__":
    sys.exit(main())
