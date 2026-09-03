"""Démonstration EPS façon CySat-I — injection de fautes et audit de trace.

Inspiration : Aurandt, Jones, Rozier, « Runtime Verification Triggers Real-time,
Autonomous Fault Recovery on the CySat-I », NFM 2022 :
  - contraintes dérivées d'exigences EPS en langage naturel ;
  - cadence de monitoring périodique (5 s, période de la tâche R2U2 sous
    FreeRTOS sur CySat-I) ;
  - injection de fautes externe (ici simulée) ;
  - récupération autonome par stratégie prédéfinie (repli B4).

Différence d'objet : R2U2 surveillait l'état du satellite ; ce moniteur
surveille les *actions* d'une couche de décision autonome (boîte noire).
"""

from __future__ import annotations

from collections import Counter

from contraintes import Contrainte, Sens
from moniteur import Cause, Moniteur, Verdict, compiler_jeu
from trace import TamponAnneau, TAILLE_A, TAILLE_B, TAILLE_C, depaqueter_c

DT = 5.0                  # période du cycle de décision (s)
PERIODE_ORBITE = 5400.0   # 90 min
DUREE_LUMIERE = 3600.0    # 60 min lumière / 30 min éclipse

C_BATT_AH = 10.0
I_BASE = 0.5              # consommation bus (A)
I_SUN = 1.2               # courant de charge au soleil (A)
U_MIN, U_MAX = 0.0, 3.0   # courant payload admissible (A)

ETAT_INITIAL = [0.62, 20.0]   # SoC, température batterie (°C)
SIGMAS_NOMINALES = [0.01, 0.5]


class ModeleEPS:
    """Plante EPS simplifiée : x = [soc, temp_batt], u = courant payload (A).

    Sert de plante simulée ET de modèle de prédiction du moniteur (en P0 le
    modèle est parfait — l'écart modèle/monde est traité en campagne P2).
    """

    H = 1.5e-3      # échauffement par ampère (°C/(A·s))
    C_TH = 5.0e-4   # relaxation thermique (1/s)
    T_SOLEIL = 15.0
    T_ECLIPSE = -15.0

    def __init__(self):
        self.en_lumiere = True

    def pas(self, x, u, dt):
        soc, temp = x
        i_charge = I_SUN if self.en_lumiere else 0.0
        dsoc = (i_charge - I_BASE - u) / (C_BATT_AH * 3600.0)
        t_env = self.T_SOLEIL if self.en_lumiere else self.T_ECLIPSE
        dtemp = self.H * (I_BASE + u) - self.C_TH * (temp - t_env)
        return [soc + dt * dsoc, temp + dt * dtemp]


def politique_repli_eps(x) -> float:
    """B4 : repli déterministe et vérifiable — extinction du payload (0 A)."""
    return 0.0


def contraintes_eps() -> list[Contrainte]:
    """Contraintes dérivées d'exigences en langage naturel (méthode CySat-I).

    C0 : « l'état de charge batterie ne doit jamais passer sous le seuil de
         sous-tension » -> soc >= 0.35, marge de garde 0.02. La mise en
         sécurité du payload prend 120 s : c'est le délai d'armement.
    C1 : « la température batterie ne doit pas dépasser 45 °C ».
    """
    return [
        Contrainte("C0_SOC_MIN", indice=0, sens=Sens.MIN, seuil=0.35,
                   echelle=1.0, seuil_incertitude=0.05,
                   delai_armement_s=120.0, marge_securite=0.02),
        Contrainte("C1_TEMP_MAX", indice=1, sens=Sens.MAX, seuil=45.0,
                   echelle=50.0, seuil_incertitude=2.0,
                   delai_armement_s=120.0, marge_securite=1.0),
    ]


class CoucheDecisionFactice:
    """Couche de décision boîte noire : planificateur agressif non vérifiable.

    Pannes injectées (comme les mock launches de CySat-I) :
      - « dérive » : propose une action hors bornes ;
      - « gel »    : ne produit plus d'action candidate (RA-IND-003) ;
      - « sigma »  : l'estimateur dérive, l'incertitude monte (RA-FUN-003).
    """

    def __init__(self):
        self.fenetre_derive = (1200.0, 1500.0)
        self.fenetre_sigma = (6300.0, 6800.0)
        self.fenetre_gel = (9900.0, 10200.0)

    def proposer(self, t: float):
        if self.fenetre_gel[0] <= t < self.fenetre_gel[1]:
            return None            # la couche de décision ne répond plus
        if self.fenetre_derive[0] <= t < self.fenetre_derive[1]:
            return 9.9             # action hors bornes
        return 2.8                 # demande agressive permanente

    def sigmas(self, t: float):
        if self.fenetre_sigma[0] <= t < self.fenetre_sigma[1]:
            return [0.08, 0.5]     # sigma_soc au-delà du seuil de C0 (0.05)
