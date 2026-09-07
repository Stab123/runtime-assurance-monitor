# Changelog

All notable changes to this repository are documented here.

## [v1.0.1] — 2026-09-07

Documentation and archival release — no change to code, data or results.

- Added `CITATION.cff` with the Zenodo concept DOI
  ([10.5281/zenodo.22552147](https://doi.org/10.5281/zenodo.22552147)).
- Added DOI and CI badges to the README; the September 2026 correction note is
  reduced to a summary (full detail below under v1.0-p3.1).
- Added `docs/exigences.md`: requirements traceability table (RA-* → mechanism →
  test).
- Added `figures/faire_figures.py`: regenerates Figures 2 and 3 of the paper from
  the published result files.
- Added `paper/`: the v2 preprint (FR/EN), marked *superseded* pending v3.
- Added French translation of the README under `docs/README_fr.md`.
- Repository topics and description set.

## [v1.0-p3.1] — 2026-09-07

Post-correction re-run release. Archived on Zenodo:
[10.5281/zenodo.22552148](https://doi.org/10.5281/zenodo.22552148).

### Defects fixed (September 2026 review)

1. **Temporal off-by-one (RA-FUN-004).** `trajectoire_sure` applied the action for
   `pas_armement + 1` steps (`k <= pas_armement`): actual persistence was
   τ_arming + 5 s. Compile time and runtime shared the same convention — no safety
   hole, arm comparisons unbiased (uniform shift) — but the temporal label was off
   by one step. Fixed (`k < pas_armement`): persistence is now exactly τ_arming.
   Regression test added.
2. **Projection below u_min.** For a candidate below u_min whose projection is
   safe, the filter returned the **upper** bound of the admissible interval
   instead of u_min — contrary to minimal modification. Latent bug: never reached
   in the campaigns (candidates ∈ {0; 3} A ⊂ [u_min, u_max]). Fixed (the safe
   projection is transmitted); tests added on both sides.
3. **Documentation defect found during the re-run.** The σ-sweep table of the
   README had quoted stale draft values since the first commit, inconsistent with
   `resultats_p2_3.json` (old and new alike). It now quotes the campaign file.
   The published data were never affected.

### Re-run protocol

All campaigns (P2.2, P2.3, P3 pilot, P3.1) were re-run on GitHub Actions
(`.github/workflows/rejeu.yml`) with **strictly unchanged** configurations — only
the code was fixed. P2.1 was not re-run (historical pilot lost, plan already
superseded by P2.2): its pre-correction code bytes are archived under
`empreintes/pre_correction/` and the verifier's documented exception is extended
accordingly. The re-run workflow used replayable copies of the campaign scripts
(`empreintes/campagne_p2_rejeu.py`, `empreintes/executer_p2_3_rejeu.py`,
relativized paths, byte-identical logic); results were then merged back under the
canonical file names.

### Outcome of the re-run

- Violation counts unchanged everywhere (arm A: 68/300; arms B, C, D: 0/300 at
  every point).
- Fallback and delivery shifted by at most 0.04 point on P2.3.
- The σ-sweep effect direction is unchanged; magnitude reduced (+2.9 points of
  fallback and −5.0 points of delivery at σ = 0.03, was +7.9 / −9.7).
- The wall moved by exactly one pilot grid point, as the fix predicted:
  compilable up to and including 195 s (residual margin +0.0002), refused from
  196 s.
- P3.1: identical shape; fallback costs at τ_arming ∈ {140; 170; 190} s are
  10.18 % → 15.60 % → 18.77 % (was 10.7 % → 14.4 % → 17.4 %).
- Both non-regressions re-verified on the new data (6300/6300 and 90/90
  identical fields).
- Formal τ_violation = 205.8 s on the nominal model; physical r values of the
  P3.1 grid are 0.68 / 0.83 / 0.92 (P2 at 120 s: 0.58).

**All qualitative conclusions are unchanged.** The main result remains negative.
