"""Plante P4b — modèle physique GELÉ (P4B_PHASE0_PHYSICAL_BASIS_v0.6 §5, §7.2).

Extension de tension de la plante historique (ram_p2/campagne_p2.PlanteEPS,
inchangée) par un Thevenin d'ordre 1 explicite. Équations gelées :

    I_batt(t) = I_BASE + u_exec(t) - i_charge(t)   (signé ; > 0 = décharge)
    I_cell(t) = I_batt(t) * C_cell / C_BATT        (pack équivalent continu)
    V_pack(t) = N_S * [ OCV(SoC) - I_cell*rho*Rs(SoC) - Vp ]
    dVp/dt    = -Vp / (rho*Rp(SoC)*Cp(SoC)) + I_cell / Cp(SoC)

Règles gelées implémentées ici (aucune liberté d'interprétation) :

- N_S = 2, C_cell = 3.35 Ah ; rho multiplie Rs et Rp UNIQUEMENT — Cp n'est
  PAS scalé (v0.6 §7.2-B).
- Vp est un état dynamique continu, JAMAIS remis à zéro à l'entrée d'une
  fenêtre payload (v0.6 §7.2-E).
- Vp(t0) = rho * Rp(SoC0) * I_BASE * C_cell / C_BATT — convention
  quasi-stationnaire pré-data de l'éclipse pré-run (v0.6 §7.2-E, GELÉ).
- Intégration : Euler explicite, coefficients évalués à t_k — même schéma
  que l'intégrateur SoC gelé de la plante historique
  (soc + dt*dsoc, taux pris au début du pas). Aucune grandeur n'est
  évaluée entre les pas (préenregistrement §4).
- Tables : OCV (HNEI, 51 points, interpolation linéaire) ; Rs, Rp, Cp
  (DTU, 11 points, convention p35, interpolation linéaire).
- Règle hors domaine SoC (v0.6 §7.2-A, GELÉE) : la plante ne sature JAMAIS
  l'état soc ; les entrées des TABLES sont évaluées à la borne la plus
  proche (clamp de la valeur d'entrée, pas de l'état) ; l'événement
  {soc ∉ [0 ; 1]} est tracé par la boucle de campagne (drapeau, premier
  instant, durée cumulée) — voir campagne_p4b.py.
- Extension > 90 % (v0.6 §7.2-B, GELÉE) : Rp(SoC>0.90) = Rp(0.90),
  Cp(SoC>0.90) = Cp(0.90) — clamp ; aucune extrapolation inventée.
  Rs et OCV sont mesurés jusqu'à 100 % : clamp à [0 ; 1] seulement.
- V_min,pack = N_S * 2.5 V = 5.0 V (v0.6 §7.2-D, GELÉ).

Les fichiers de tables sont gelés : leur SHA256 est vérifié au chargement ;
toute modification fait échouer le chargement (la campagne refuse de
tourner sur des tables modifiées).

stdlib uniquement (float64 natif Python) : la plante n'importe ni numpy ni
scipy — réservés à l'analyse (préenregistrement §14).
"""

from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path

RAM_P4B = Path(__file__).resolve().parent

# --- Constantes gelées v0.6 -------------------------------------------------
N_S = 2                      # cellules en série
C_CELL_AH = 3.35             # capacité cellule de référence (Ah)
V_MIN_CELL = 2.5             # V
V_MIN_PACK = N_S * V_MIN_CELL  # 5.0 V — aléa physique gelé
SOC_MAX_RP_CP = 0.90         # clamp Rp/Cp au-delà de 90 % (v0.6 §7.2-B)

# SHA256 des tables gelées (préenregistrement §2 — publiés avant exécution)
SHA256_OCV = "7aa959fc99effefbc995237291217cec1657145051b3fa70cd7678fe0b7154c2"
SHA256_RINT = "330efcd3165f5676f06b9128f723566193cc66fa6844fdddbc1f782015697b93"

# Points de table OCV concernés par la sensibilité ±0.1 V (§13) : SoC 0.00 et 0.02
SOC_SENSIBILITE_OCV = (0.0, 0.02)


class TableGeleeModifiee(Exception):
    """Le SHA256 d'une table chargée ne correspond pas à l'empreinte gelée."""


def _sha256_fichier(chemin: Path) -> str:
    return hashlib.sha256(chemin.read_bytes()).hexdigest()


def _interpolation_lineaire(xs: list[float], ys: list[float], x: float) -> float:
    """Interpolation linéaire entre points de table (règle gelée v0.6 §7.2-A).

    `x` est supposé DÉJÀ clampé dans [xs[0] ; xs[-1]] par l'appelant —
    cette fonction n'extrapole jamais.
    """
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    # Recherche du segment (bisection manuelle — stdlib pur, déterministe)
    lo, hi = 0, len(xs) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if xs[mid] <= x:
            lo = mid
        else:
            hi = mid
    x0, x1 = xs[lo], xs[hi]
    y0, y1 = ys[lo], ys[hi]
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def _clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


class TablesPhysiques:
    """Tables OCV / Thevenin gelées, chargées depuis data/ avec contrôle SHA256.

    Toutes les évaluations clampe la VALEUR D'ENTRÉE de la table (jamais
    l'état SoC de la plante — règle hors domaine gelée) :
      - OCV, Rs : soc_table = clamp(soc, 0.0, 1.0) ;
      - Rp, Cp  : soc_table = clamp(soc, 0.0, 0.90)  (extension > 90 % gelée).
    """

    def __init__(self, soc_ocv: list[float], ocv_v: list[float],
                 soc_rs: list[float], rs_ohm: list[float],
                 soc_rp_cp: list[float], rp_ohm: list[float],
                 cp_f: list[float]):
        self._soc_ocv = soc_ocv
        self._ocv_v = ocv_v
        self._soc_rs = soc_rs          # Rs mesuré jusqu'à SoC = 100 %
        self._rs_ohm = rs_ohm
        self._soc_rp_cp = soc_rp_cp    # Rp/Cp mesurés jusqu'à SoC = 90 %
        self._rp_ohm = rp_ohm
        self._cp_f = cp_f

    # --- chargement ---------------------------------------------------------

    @classmethod
    def charger(cls, repertoire: Path | None = None) -> "TablesPhysiques":
        rep = repertoire or (RAM_P4B / "data")
        f_ocv = rep / "ocv_soc_ncr18650b_hnei.csv"
        f_rint = rep / "rint_soc_nmc_dtu.csv"
        sha_ocv = _sha256_fichier(f_ocv)
        sha_rint = _sha256_fichier(f_rint)
        if sha_ocv != SHA256_OCV:
            raise TableGeleeModifiee(
                f"OCV : SHA256 {sha_ocv} != gelé {SHA256_OCV}")
        if sha_rint != SHA256_RINT:
            raise TableGeleeModifiee(
                f"Rint : SHA256 {sha_rint} != gelé {SHA256_RINT}")

        soc_ocv, ocv_v = [], []
        with open(f_ocv, newline="", encoding="utf-8") as f:
            for row in csv.reader(r for r in f if not r.startswith("#")):
                if row[0].strip() == "soc_pct":
                    continue
                soc_ocv.append(float(row[0]) / 100.0)   # % -> fraction
                ocv_v.append(float(row[1]))

        soc_rs, rs = [], []
        soc_rp_cp, rp, cp = [], [], []
        with open(f_rint, newline="", encoding="utf-8") as f:
            for row in csv.reader(r for r in f if not r.startswith("#")):
                if row[0].strip() == "soc_pct":
                    continue
                s = float(row[0]) / 100.0
                soc_rs.append(s)
                rs.append(float(row[2]) * 1e-3)    # p35 mΩ -> Ω
                if s <= SOC_MAX_RP_CP:
                    # Rp/Cp non mesurés à 100 % (NaN dans la table gelée) :
                    # la règle d'extension > 90 % (clamp gelé) rend le point
                    # 100 % inaccessible pour Rp/Cp — il n'est pas chargé.
                    soc_rp_cp.append(s)
                    rp.append(float(row[4]) * 1e-3)    # p35 mΩ -> Ω
                    cp.append(float(row[6]) * 1e3)     # p35 kF -> F
        return cls(soc_ocv, ocv_v, soc_rs, rs, soc_rp_cp, rp, cp)

    # --- évaluations (entrée clampée, état jamais modifié) -------------------

    def ocv(self, soc: float) -> float:
        return _interpolation_lineaire(
            self._soc_ocv, self._ocv_v, _clamp(soc, 0.0, 1.0))

    def rs(self, soc: float) -> float:
        return _interpolation_lineaire(
            self._soc_rs, self._rs_ohm, _clamp(soc, 0.0, 1.0))

    def rp(self, soc: float) -> float:
        return _interpolation_lineaire(
            self._soc_rp_cp, self._rp_ohm, _clamp(soc, 0.0, SOC_MAX_RP_CP))

    def cp(self, soc: float) -> float:
        return _interpolation_lineaire(
            self._soc_rp_cp, self._cp_f, _clamp(soc, 0.0, SOC_MAX_RP_CP))

    # --- variante de sensibilité OCV (§13) — copie en mémoire UNIQUEMENT ----

    def variante_ocv(self, delta_v: float) -> "TablesPhysiques":
        """OCV'(s) = OCV(s) + delta_v aux points s ∈ {0.00 ; 0.02}.

        Analyse de sensibilité préenregistrée (§13) : la table gelée sur
        disque n'est JAMAIS modifiée ; l'interpolation linéaire est
        inchangée ; les autres points sont intouchés.
        """
        ocv2 = list(self._ocv_v)
        for s_cible in SOC_SENSIBILITE_OCV:
            for i, s in enumerate(self._soc_ocv):
                if s == s_cible:
                    ocv2[i] = ocv2[i] + delta_v
                    break
            else:
                raise ValueError(f"point de table SoC={s_cible} introuvable")
        return TablesPhysiques(list(self._soc_ocv), ocv2, list(self._soc_rs),
                               list(self._rs_ohm), list(self._soc_rp_cp),
                               list(self._rp_ohm), list(self._cp_f))


class PlanteP4b:
    """Plante P4b : dynamique SoC/température IDENTIQUE à PlanteEPS gelée
    (mêmes équations, paramètres par run), étendue de l'état Vp et de la
    tension terminale pack (équations v0.6 §5).

    État : x = [soc, temp] (comme la plante historique) + self.vp (V).
    `en_lumiere` est positionné par la boucle de campagne à chaque pas,
    exactement comme dans le code gelé.
    """

    T_SOLEIL = 15.0
    T_ECLIPSE = -15.0

    def __init__(self, p: dict, rho: float, tables: TablesPhysiques):
        self.p = p
        self.rho = float(rho)
        self.tables = tables
        self.en_lumiere = True
        # Vp(t0) — règle gelée v0.6 §7.2-E : convention quasi-stationnaire
        # de l'éclipse pré-run (u = 0, i_charge = 0), évaluée à SoC0 :
        #   Vp(t0) = rho * Rp(SoC0) * I_BASE * C_cell / C_BATT
        soc0 = p["soc0"]
        i_cell0 = p["I_BASE"] * C_CELL_AH / p["C_BATT_AH"]
        self.vp = self.rho * self.tables.rp(soc0) * i_cell0

    # --- courants (convention signée gelée : I_batt > 0 = décharge) ----------

    def i_charge(self) -> float:
        return self.p["I_SUN"] if self.en_lumiere else 0.0

    def i_batt(self, u_exec: float) -> float:
        """I_batt = I_BASE + u_exec - i_charge  (gelé v0.6 §5)."""
        return self.p["I_BASE"] + u_exec - self.i_charge()

    def i_cell(self, u_exec: float) -> float:
        """I_cell = I_batt * C_cell / C_BATT  (pack équivalent continu)."""
        return self.i_batt(u_exec) * C_CELL_AH / self.p["C_BATT_AH"]

    # --- tension terminale (endpoint §4 : état à t_k, courant à t_k) ---------

    def v_pack(self, soc: float, vp: float, u_exec: float) -> float:
        """V_pack = N_S * [ OCV(SoC) - I_cell*rho*Rs(SoC) - Vp ]  (gelé).

        Évalué sur l'état (soc, vp) au temps t_k avec le courant
        effectivement appliqué à ce pas (u_exec après moniteur).
        """
        ic = self.i_cell(u_exec)
        return N_S * (self.tables.ocv(soc)
                      - ic * self.rho * self.tables.rs(soc)
                      - vp)

    def dvp(self, soc: float, vp: float, i_cell: float) -> float:
        """dVp/dt = -Vp / (rho*Rp(SoC)*Cp(SoC)) + I_cell / Cp(SoC)  (gelé).

        rho multiplie Rp UNIQUEMENT — Cp n'est PAS scalé (v0.6 §7.2-B).
        Coefficients évalués à SoC = SoC(t_k) (Euler explicite, règle D1).
        """
        rp = self.tables.rp(soc)
        cp = self.tables.cp(soc)
        return -vp / (self.rho * rp * cp) + i_cell / cp

    # --- propagation (Euler explicite, coefficients à t_k) -------------------

    def pas(self, x: list[float], u_exec: float, dt: float) -> list[float]:
        """Un pas d'intégration. Retourne le nouvel x = [soc, temp] et met
        à jour self.vp. Schéma IDENTIQUE à la plante gelée pour soc/temp
        (Euler explicite, taux au début du pas) ; même schéma pour Vp :

            dVp/dt = -Vp / (rho*Rp(SoC)*Cp(SoC)) + I_cell / Cp(SoC)

        avec SoC = SoC(t_k) et I_cell = I_cell(t_k). Vp n'est jamais remis
        à zéro ici ni ailleurs (mémoire continue, v0.6 §7.2-E).
        """
        soc, temp = x
        i_chg = self.i_charge()
        i_batt = self.p["I_BASE"] + u_exec - i_chg
        i_cell = i_batt * C_CELL_AH / self.p["C_BATT_AH"]

        # Dynamique SoC — IDENTIQUE à ram_p2/campagne_p2.PlanteEPS.pas :
        #   dsoc = (i_charge - I_BASE - u) / (C_BATT_AH * 3600)
        # (= -I_batt / (C_BATT·3600), convention gelée). AUCUNE saturation.
        dsoc = (i_chg - self.p["I_BASE"] - u_exec) / (self.p["C_BATT_AH"] * 3600.0)
        t_env = self.T_SOLEIL if self.en_lumiere else self.T_ECLIPSE
        dtemp = (self.p["H"] * (self.p["I_BASE"] + u_exec)
                 - self.p["C_TH"] * (temp - t_env))

        # Dynamique Vp — Euler explicite, coefficients à t_k (règle D1).
        self.vp = self.vp + dt * self.dvp(soc, self.vp, i_cell)

        return [soc + dt * dsoc, temp + dt * dtemp]


def hors_domaine(soc: float) -> bool:
    """Drapeau « hors domaine physique du modèle » : SoC(t) ∉ [0 ; 1]."""
    return soc < 0.0 or soc > 1.0


def est_fini(*valeurs: float) -> bool:
    """Contrôle de finitude (INVALID_TECHNIQUE, tolérance zéro — §4)."""
    return all(math.isfinite(v) for v in valeurs)
