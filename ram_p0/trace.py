"""B5 — Enregistreur de trace de décision (RAM-SPEC-0001 §6, RA-TRC-*).

Formats binaires calqués sur RAM-NOTE-0001 :
  - variante A « résumé »   : 16 octets
  - variante B « standard » : 48 octets
  - variante C « détaillé » : 160 octets

Règles d'architecture :
  - capacité fixée à l'initialisation, jamais réallouée ;
  - un verdict de repli fige une fenêtre de contexte (RA-TRC-006) ;
  - la saturation dégrade la trace, jamais le verdict (RA-RES-004) ;
  - chaque enregistrement perdu est comptabilisé (RA-RES-005) ;
  - version du jeu (RA-IND-004) et de schéma (RA-TRC-005) dans chaque record ;
  - la cause distingue REPLI-enveloppe de REPLI-incertitude (RA-TRC-004).
"""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass, field
from typing import Optional, Sequence

VERSION_SCHEMA = 1

_FMT_A = ">IHHBBHB3s"
_FMT_B = _FMT_A + "6H6B3sIB4sH"
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

GAMMES_DEFAUT = [(0.0, 1.0), (-40.0, 60.0)] + [(0.0, 1.0)] * (NB_GRANDEURS - 2)


def crc16_ccitt(donnees: bytes, crc: int = 0xFFFF) -> int:
    for octet in donnees:
        crc ^= octet << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def _cuc(t_s: float) -> tuple[int, int]:
    """Horodatage type CUC : secondes (4 o) + fraction 1/65536 (2 o)."""
    secondes = int(t_s)
    fraction = int((t_s - secondes) * 65536) & 0xFFFF
    return secondes & 0xFFFFFFFF, fraction


def _q16(x: float, lo: float, hi: float) -> int:
    if x != x:
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
    verdict: int
    cause: int
    mode: int
    indice_contrainte: int
    marge: float
    confiance: float
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
    """Décode un enregistrement C — support du test d'audit à l'aveugle
    (RA-TRC-002, RA-TRC-005)."""
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
    """Tampon anneau à capacité fixe pour la va
