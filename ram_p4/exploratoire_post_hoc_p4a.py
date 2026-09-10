"""POST-HOC / EXPLORATOIRE — emboîtement et signature physique des blocs
défaillants de P4a. Ce script N'EST PAS préenregistré : il a été écrit APRÈS
le verdict D gelé, ne sert qu'à la description, et ne peut modifier ni le
verdict ni aucun seuil. Aucun fichier gelé n'est lu en écriture.

Entrée : resultats_p4a_principal.json (données confirmatoires gelées).
Sortie : exploratoire_post_hoc_p4a_resultats.json (annexe descriptive).
"""
import json, statistics as st, os

RAM_P4 = os.path.dirname(os.path.abspath(__file__))
runs = json.load(open(os.path.join(RAM_P4, "resultats_p4a_principal.json")))["runs"]


def defaillants(b):
    return {r["bloc_id"] for r in runs if abs(r["biais"] - b) < 1e-9 and r["Y"] == 1}


d002, d005, d010 = defaillants(0.02), defaillants(0.05), defaillants(0.10)

emboitement = {
    "n_defaillants": {"0.02": len(d002), "0.05": len(d005), "0.10": len(d010)},
    "D002_dans_D005": d002 <= d005,
    "D005_dans_D010": d005 <= d010,
    "D005_egal_D010": d005 == d010,
    "blocs_D005": sorted(d005),
}

b0 = {r["bloc_id"]: r for r in runs if abs(r["biais"]) < 1e-9}


def marge_r2(p):
    return 3600 * p["I_SUN"] - 5400 * p["I_BASE"] - 0.5 * (3 * 900)


def marge_r1(p):
    return p["I_SUN"] - 1.5 * p["I_BASE"]


FACTEURS = {
    "C_BATT_AH": lambda p: p["C_BATT_AH"],
    "I_SUN": lambda p: p["I_SUN"],
    "I_BASE": lambda p: p["I_BASE"],
    "soc0": lambda p: p["soc0"],
    "marge_R2": marge_r2,
    "marge_R1": marge_r1,
    "marge_min_b0": None,  # champ run, pas params
}


def desc(groupe):
    out = {"n": len(groupe)}
    for nom, f in FACTEURS.items():
        vals = [b0[j]["marge_min"] if f is None else f(b0[j]["params_plante"])
                for j in groupe]
        out[nom] = {"min": min(vals), "mediane": st.median(vals), "max": max(vals)}
    return out


non_def = [j for j in range(500) if j not in d005]
signature = {"defaillants": desc(sorted(d005)), "non_defaillants": desc(non_def)}

# épinglage au garde-fou : marge_min(0) ≈ 0.02 = guard
epingles = [j for j in range(500) if b0[j]["marge_min"] <= 0.025]
signature["epingles_guard_n"] = len(epingles)
signature["epingles_guard_non_defaillants"] = sorted(j for j in epingles if j not in d005)

resultats = {
    "statut": "POST-HOC / EXPLORATOIRE — aucune valeur confirmatoire, verdict D inchangé",
    "emboitement": emboitement,
    "signature_physique": signature,
}
chemin = os.path.join(RAM_P4, "exploratoire_post_hoc_p4a_resultats.json")
json.dump(resultats, open(chemin, "w"), indent=1)
print(json.dumps(emboitement, indent=1))
print("écrit :", chemin)
