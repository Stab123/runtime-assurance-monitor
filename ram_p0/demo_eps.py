"""Démonstration EPS façon CySat-I — injection de fautes et audit de trace.

Inspiration : Aurandt, Jones, Rozier, « Runtime Verification Triggers Real-time,
Autonomous Fault Recovery on the CySat-I », NFM 2022 :
  - contraintes dérivées d'exigences EPS en langage naturel ;
  - cadence de monitoring périodique (ici 5 s, la période de la tâche R2U2
    sous FreeRTOS sur CySat-I) ;
  - injection de fautes externe (ici simulée : dérive capteur, gel de la
    couche de décision, action hors bornes) ;
  - récupération autonome par stratégie prédéfinie (ici : repli B4).

La différence d'objet : R2U2 surveillait l'état du satellite ; ce moniteur
surveille les *actions* d'une couche de décision autonome (boîte noire),
conformément à RAM-SPEC-0001.
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

    Sert à la fois de plante simulée et de modèle de prédiction du moniteur
    (en P0, le modèle est parfait — l'écart modèle/monde est un sujet de P1,
    à couvrir par le gonflement d'incertitude).
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
    """Contraintes dérivées d'exigences en langage naturel (méthode CySat-I) :

    C0 : « l'état de charge batterie ne doit jamais passer sous le seuil de
         sous-tension » -> soc >= 0.35, avec marge de garde 0.02. La mise en
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
        return list(SIGMAS_NOMINALES)


NOMS_VERDICT = ["AUTORISE", "MODIFIE", "REPLI", "INDETERMINE"]
NOMS_CAUSE = ["AUCUNE", "VIOLATION_ENVELOPPE", "INCERTITUDE", "TIMEOUT_ACTION",
              "ENTREES_INVALIDES", "REPLI_VERROUILLE"]
NOMS_CONTRAINTES = {0: "C0_SOC_MIN", 1: "C1_TEMP_MAX", 255: "-"}


def faire_moniteur(capacite_tampon: int = 3600, **kw) -> tuple[Moniteur, ModeleEPS]:
    modele = ModeleEPS()
    modele.en_lumiere = False  # compilation au pire cas : éclipse
    jeu = compiler_jeu(1, contraintes_eps(), modele, politique_repli_eps, DT,
                       etat_nominal=[0.6, 20.0], bornes_action=(U_MIN, U_MAX))
    tampon = TamponAnneau(capacite_tampon)
    moniteur = Moniteur(jeu, modele, politique_repli_eps, DT, tampon,
                        U_MIN, U_MAX, **kw)
    return moniteur, modele


def executer(duree_s: float = 13500.0, afficher: bool = True):
    """2,5 orbites avec injection de fautes. La plante applique l'action
    *transmise* par le moniteur (IF-3) — jamais l'action candidate brute."""
    plante = ModeleEPS()
    moniteur, modele_mon = faire_moniteur()
    decideur = CoucheDecisionFactice()

    etat = list(ETAT_INITIAL)
    resultats = []
    t = 0.0
    while t < duree_s:
        en_lumiere = (t % PERIODE_ORBITE) < DUREE_LUMIERE
        plante.en_lumiere = en_lumiere
        modele_mon.en_lumiere = en_lumiere
        r = moniteur.cycle(t, etat, decideur.sigmas(t), True, decideur.proposer(t))
        resultats.append(r)
        etat = list(plante.pas(etat, r.action_transmise, DT))
        t += DT

    if afficher:
        _afficher_bilan(resultats, moniteur, duree_s)
    return resultats, moniteur


def _afficher_bilan(resultats, moniteur: Moniteur, duree_s: float) -> None:
    n = len(resultats)
    compteur = Counter((r.verdict.name, r.cause.name) for r in resultats)
    print("=" * 72)
    print(f"DÉMO EPS — {n} cycles de {DT:.0f} s ({duree_s / 3600:.1f} h simulées)")
    print("=" * 72)
    print("\nVerdicts émis (exactement un par cycle, RA-FUN-001) :")
    for (verdict, cause), nb in sorted(compteur.items()):
        print(f"  {verdict:<12} / {cause:<20} : {nb:>5}")

    print("\nJournal IF-4 (notifications vers le FDIR bord) :")
    for t, msg in moniteur.notifications[:8]:
        print(f"  t={t:>8.0f} s  {msg}")
    if len(moniteur.notifications) > 8:
        print(f"  ... ({len(moniteur.notifications)} notifications au total)")

    tampon = moniteur._tampon
    print(f"\nTrace (B5) : {tampon.occupation} enregistrements variante C "
          f"({tampon.occupation * TAILLE_C / 1e6:.1f} Mo), pertes = {tampon.pertes}")
    print(f"Formats : A={TAILLE_A} o, B={TAILLE_B} o, C={TAILLE_C} o "
          f"(RAM-NOTE-0001)")

    gele = tampon.extraire_gele()
    if gele:
        print(f"\nFenêtre figée extraite (RA-TRC-006) : {len(gele)} enregistrements")
        print("Audit à l'aveugle — reconstruction depuis la seule trace (§7) :")
        non_nominaux = [b for _, b in gele]
        for blob in non_nominaux[:6]:
            d = depaqueter_c(blob)
            idx = d["indice_contrainte"]
            # La marge lue est celle de la contrainte déterminante — c'est le
            # champ qui porte la valeur d'audit (RAM-SPEC-0001 §6).
            marge_det = (f"{d['marges'][idx]:+.3f}" if 0 <= idx < len(d["marges"])
                         else "-")
            print(
                f"  seq={d['seq']:>5} t={d['t_s']:>7.0f}s "
                f"{NOMS_VERDICT[d['verdict']]:<11}/{NOMS_CAUSE[d['cause']]:<20} "
                f"contrainte={NOMS_CONTRAINTES.get(idx, '?'):<10} "
                f"marge_det={marge_det} "
                f"u_cand={d['action_candidate'][0]:.2f}A -> u_exec={d['action_transmise'][0]:.2f}A "
                f"conf={d['confiance']:.2f}"
            )


if __name__ == "__main__":
    executer()
