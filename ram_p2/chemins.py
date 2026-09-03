"""Résolution des chemins du dépôt — aucun chemin absolu dans le code.

RACINE est le répertoire parent de ram_p2/, quel que soit l'endroit où le
dépôt est cloné et depuis quel répertoire la campagne est lancée. C'est la
condition pour que la campagne soit rejouable par un tiers.
"""

from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
RAM_P0 = RACINE / "ram_p0"
RAM_P2 = RACINE / "ram_p2"

MODULES_EMPREINTE = [
    RAM_P0 / "moniteur.py",
    RAM_P0 / "filtre.py",
    RAM_P0 / "trace.py",
    RAM_P0 / "contraintes.py",
    RAM_P2 / "campagne_p2.py",
]

# Pour l'exécuteur parallèle P2.3, qui ajoute son propre module à la liste.
MODULES_EMPREINTE_P2_3 = MODULES_EMPREINTE + [RAM_P2 / "executer_p2_3.py"]
