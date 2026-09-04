"""B5 — Enregistreur de trace de décision (RAM-SPEC-0001 §6, RA-TRC-*).

Formats binaires calqués sur RAM-NOTE-0001 :
  - variante A « résumé »   : 16 octets
  - variante B « standard » : 48 octets
  - variante C « détaillé » : 160 octets

Règles d'architecture implémentées :
  - capacité fixée à l'initialisation, jamais réallouée (préparation de
    RA-RES-001/002 — la démonstration formelle reste à faire au portage) ;
  - un verdict non nominal fige une fenêtre de contexte dans le tampon anneau
    (RA-TRC-006 de RAM-NOTE-0001 §8) ;
  - la saturation dégrade la trace, jamais le verdict (RA-RES-004) ;
  - chaque enregistrement perdu est comptabilisé (RA-RES-005) ;
  - chaque enregistrement porte la version du jeu de contraintes (RA-IND-004)
    et la version de schéma (RA-TRC-005) ;
  - la cause distingue REPLI-enveloppe de REPLI-incertitude (RA-TRC-004).
"""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass, field
from typing import Optional, Sequence

VERSION_SCHEMA = 1

# ---------------------------------------------------------------------------
# Formats binaires (big-endian, sans alignement). Tailles garanties par
# assertion à l'import : toute dérive de format casse le chargement du module.
# ---------------------------------------------------------------------------

# A (16 o) : CUC(4+2) version(2) champs_de_bits(1) contrainte(1) marge_q16(2)
#            confiance_u8(1) empreinte_candidate(3)
_FMT_A = ">IHHBBHB3s"

# B (48 o) : A + état 6xq16(12) + incertitudes 6xu8(6) + empreinte_transmise(3)
#            + séquence(4) + schéma(1) + réservé(4) + CRC16(2)
_FMT_B = _FMT_A + "6H6B3sIB4sH"

# C (160 o) : en-tête + état 6xf32(24) + incertitudes 6xf32(24)
#             + marges 16xi16(32) + actions candidate/transmise 4xf32(16+16)
#             + empreintes(3+3) + schéma(1) + réservé + CRC16(2)
_FMT_C_CORPS = ">IHHBBfI6f6f16h4f4f3s3sB"
_RESERVE_C = 160 - 2 - struct.calcsize(_FMT_C_CORPS)
_FMT_C = _FMT_C_CORPS + f"{_RESERVE_C}sH"

TAILLE_A = struct.calcsize(_FMT_A)
TAILLE_B = struct.calcsize(_FMT_B)
TAILLE_C = struct.calcsize(_FMT_C)
assert TAILLE_A == 16, TAILLE_A
assert TAILLE_B == 48, TAILLE_B
assert TAILLE_C == 160, TAILLE_C

NB_GRANDEURS = 6
NB_CONTRAINTES_TRACE = 16
NB_AXES_ACTION = 4

# Gammes de quantification par défaut : (SoC, température batterie), le reste
# est une réserve sans signification physique.
GAMMES_DEFAUT = [(0.0, 1.0), (-40.0, 60.0)] + [(0.0, 1.0)] * (NB_GRANDEURS - 2)


def crc16_ccitt(donnees: bytes, crc: int = 0xFFFF) -> int:
    for octet in donnees:
        crc ^= octet << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def _cuc(t_s: float) -> tuple[int, int]:
    """Horodatage type CUC : secondes grossières (4 o) + fraction 1/65536 (2 o)."""
    secondes = int(t_s)
    fraction = int((t_s - secondes) * 65536) & 0xFFFF
    return secondes & 0xFFFFFFFF, fraction


def _q16(x: float, lo: float, hi: float) -> int:
    if x != x:  # NaN -> 0
        return 0
    x = min(max(x, lo), hi)
    return int((x - lo) / (hi - lo) * 65535) & 0xFFFF


def _q16_marge(m: float) -> int:
    return _q16(m, -1.0, 1.0)


def _u8(x: float, hi: float) -> int:
    if x != x:
        return 0
    return int(min(max(x / hi, 0.0), 1.0) * 255) & 0xFF


def _pad(seq: Sequence[float], n: int, remplissage: float = math.nan) -> list[float]:
    out = list(seq[:n])
    out.extend([remplissage] * (n - len(out)))
    return out


@dataclass
class Enregistrement:
    """Contenu logique d'un enregistrement de trace (RAM-SPEC-0001 §6)."""

    t_s: float
    seq: int
    version_jeu: int
    verdict: int                       # 0 AUTORISE, 1 MODIFIE, 2 REPLI, 3 INDETERMINE
    cause: int                         # voir moniteur.Cause
    mode: int                          # 0 NOMINAL, 1 REPLI
    indice_contrainte: int             # 255 = aucune (contrainte déterminante)
    marge: float                       # normalisée dans [-1, 1], NaN si sans objet
    confiance: float                   # agrégat dans [0, 1]
    empreinte_candidate: bytes = b"\x00\x00\x00"
    empreinte_transmise: bytes = b"\x00\x00\x00"
    etat: Sequence[float] = field(default_factory=list)
    incertitudes: Sequence[float] = field(default_factory=list)
    marges: Sequence[float] = field(default_factory=list)
    action_candidate: Sequence[float] = field(default_factory=list)
    action_transmise: Sequence[float] = field(default_factory=list)

    def _champs_bits(self) -> int:
        return (self.verdict & 0x3) | ((self.cause & 0x7) << 2) | ((self.mode & 0x1) << 5)

    def paquet_a(self) -> bytes:
        s, f = _cuc(self.t_s)
        return struct.pack(
            _FMT_A, s, f, self.version_jeu & 0xFFFF, self._champs_bits(),
            self.indice_contrainte & 0xFF, _q16_marge(self.marge),
            _u8(self.confiance, 1.0), self.empreinte_candidate[:3].ljust(3, b"\x00"),
        )

    def paquet_b(self, gammes=GAMMES_DEFAUT) -> bytes:
        s, f = _cuc(self.t_s)
        etat_q = [_q16(v, *gammes[i]) for i, v in enumerate(_pad(self.etat, NB_GRANDEURS))]
        inc_q = [_u8(v, 1.0) for v in _pad(self.incertitudes, NB_GRANDEURS, 0.0)]
        corps = struct.pack(
            _FMT_A, s, f, self.version_jeu & 0xFFFF, self._champs_bits(),
            self.indice_contrainte & 0xFF, _q16_marge(self.marge),
            _u8(self.confiance, 1.0), self.empreinte_candidate[:3].ljust(3, b"\x00"),
        ) + struct.pack(
            ">6H6B3sIB4s", *etat_q, *inc_q,
            self.empreinte_transmise[:3].ljust(3, b"\x00"),
            self.seq & 0xFFFFFFFF, VERSION_SCHEMA, b"\x00" * 4,
        )
        return corps + struct.pack(">H", crc16_ccitt(corps))

    def paquet_c(self) -> bytes:
        s, f = _cuc(self.t_s)
        corps = struct.pack(
            _FMT_C_CORPS, s, f, self.version_jeu & 0xFFFF, self._champs_bits(),
            self.indice_contrainte & 0xFF,
            self.confiance if self.confiance == self.confiance else 0.0,
            self.seq & 0xFFFFFFFF,
            *_pad(self.etat, NB_GRANDEURS),
            *_pad(self.incertitudes, NB_GRANDEURS, 0.0),
            *[0 if m != m else int(min(max(m, -1.0), 1.0) * 32767)
              for m in _pad(self.marges, NB_CONTRAINTES_TRACE)],
            *_pad(self.action_candidate, NB_AXES_ACTION),
            *_pad(self.action_transmise, NB_AXES_ACTION),
            self.empreinte_candidate[:3].ljust(3, b"\x00"),
            self.empreinte_transmise[:3].ljust(3, b"\x00"),
            VERSION_SCHEMA,
        ) + b"\x00" * _RESERVE_C
        return corps + struct.pack(">H", crc16_ccitt(corps))


def depaqueter_c(blob: bytes) -> dict:
    """Décode un enregistrement variante C — support du « test d'audit à
    l'aveugle » (RAM-SPEC-0001 §7) : reconstituer le raisonnement sans accès
    à l'état interne de la couche de décision (RA-TRC-002)."""
    assert len(blob) == TAILLE_C
    corps, crc = blob[:-2], struct.unpack(">H", blob[-2:])[0]
    if crc16_ccitt(corps) != crc:
        raise ValueError("CRC invalide : enregistrement corrompu")
    champs = struct.unpack(_FMT_C_CORPS, corps[: struct.calcsize(_FMT_C_CORPS)])
    (s, f, version, bits, idx, confiance, seq) = champs[:7]
    etat = champs[7:13]
    incertitudes = champs[13:19]
    marges = [m / 32767 for m in champs[19:35]]
    return {
        "t_s": s + f / 65536.0,
        "seq": seq,
        "version_jeu": version,
        "verdict": bits & 0x3,
        "cause": (bits >> 2) & 0x7,
        "mode": (bits >> 5) & 0x1,
        "indice_contrainte": idx,
        "confiance": confiance,
        "etat": list(etat),
        "incertitudes": list(incertitudes),
        "marges": marges,
        "action_candidate": list(champs[35:39]),
        "action_transmise": list(champs[39:43]),
        "empreinte_candidate": champs[43],
        "empreinte_transmise": champs[44],
        "version_schema": champs[45],
    }


class TamponAnneau:
    """Tampon anneau à capacité fixe pour la variante C (RAM-NOTE-0001 §7.2).

    Politique de saturation : un emplacement figé (fenêtre de contexte d'un
    verdict non nominal) n'est jamais écrasé ; l'enregistrement entrant est
    perdu et comptabilisé. La trace se dégrade, le verdict n'est jamais
    bloqué (RA-RES-004), les pertes sont comptées (RA-RES-005).
    """

    def __init__(self, capacite: int):
        if capacite < 2:
            raise ValueError("capacité minimale : 2 enregistrements")
        self._cases: list[Optional[tuple[int, float, bytes, bool]]] = [None] * capacite
        self._prochain = 0
        self.capacite = capacite
        self.pertes = 0
        self._gel_debut: Optional[int] = None
        self._gel_fin: Optional[int] = None

    def ecrire(self, seq: int, t_s: float, blob: bytes) -> bool:
        """Écrit un enregistrement. Renvoie False si perdu (case figée)."""
        gele = (
            self._gel_debut is not None
            and self._gel_debut <= seq <= self._gel_fin
        )
        case = self._cases[self._prochain]
        if case is not None and case[3]:
            # Case figée : l'enregistrement entrant est perdu (compté,
            # RA-RES-005), mais la tête avance — sinon tout ce qui suit serait
            # perdu tant que le gel n'est pas extrait.
            self.pertes += 1
            self._prochain = (self._prochain + 1) % self.capacite
            return False
        self._cases[self._prochain] = (seq, t_s, blob, gele)
        self._prochain = (self._prochain + 1) % self.capacite
        return True

    def figer(self, seq_evenement: int, n_pre: int, n_post: int) -> None:
        """Fige la fenêtre [événement - n_pre, événement + n_post] (RA-TRC-006)."""
        debut, fin = seq_evenement - n_pre, seq_evenement + n_post
        if self._gel_debut is None:
            self._gel_debut, self._gel_fin = debut, fin
        else:
            self._gel_debut = min(self._gel_debut, debut)
            self._gel_fin = max(self._gel_fin, fin)
        for i, case in enumerate(self._cases):
            if case is not None and not case[3] and self._gel_debut <= case[0] <= self._gel_fin:
                self._cases[i] = (case[0], case[1], case[2], True)

    def extraire_gele(self) -> list[tuple[int, bytes]]:
        """Extraction sur demande (type ST[15]) : renvoie et défige la fenêtre."""
        if self._gel_debut is None:
            return []
        out = []
        for i, case in enumerate(self._cases):
            if case is not None and case[3] and self._gel_debut <= case[0] <= self._gel_fin:
                out.append((case[0], case[2]))
                self._cases[i] = (case[0], case[1], case[2], False)
        self._gel_debut = self._gel_fin = None
        out.sort(key=lambda e: e[0])
        return out

    def extraire_plage(self, t0: float, t1: float) -> list[tuple[int, bytes]]:
        """Lecture non destructive d'une plage temporelle (extraction sol)."""
        out = [c for c in self._cases if c is not None and t0 <= c[1] <= t1]
        out.sort(key=lambda c: c[0])
        return [(c[0], c[2]) for c in out]

    @property
    def occupation(self) -> int:
        return sum(1 for c in self._cases if c is not None)
