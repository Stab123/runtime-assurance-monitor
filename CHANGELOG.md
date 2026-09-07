# Changelog

All notable changes to this repository are documented here.

## [v1.4.1] — 2026-09-10

Patch release — documentation metadata only. Includes the post-v1.4
CITATION.cff clarification (« docs: clarify CITATION.cff safety claim »):
the citation abstract now states « zero observed violations in the tested
campaigns » and no longer cites an aggregate run/configuration count, which
was unnecessary in a citation and risked an ambiguous total. No other
change relative to v1.4 — code, configurations, data and results identical.

## [v1.4] — 2026-09-10

Documentation cleanup release — no change to code, configurations, data or
results. P2/P2.3 remains strictly frozen (bit-for-bit identical; fingerprint
chain CONFORME, 23/23 tests green).

Final P3.1 terminology and interpretation cleanup (README EN/FR,
`ram_p3/README.md`, `paper/README.md`, and paper v5 FR/EN — PDFs
regenerated):

- canonical « P3.1 — corrected interpretation » section in the root README;
- operational-cost ordering stated as **B < D ≤ C** — C and D coincide at
  some uncertainty-threshold settings (notably σ = 0.08), so the strict
  ordering B < D < C was too strong;
- dominance claims replaced by the equal-observed-safety formulation: B, C
  and D all show zero observed violations in the tested configurations;
  under this equal observed safety outcome, B achieves the lowest fallback
  rate and the highest mission delivery;
- 0.68 / 0.83 / 0.92 named **corrected nominal ratios r_nominal** everywhere
  in the current documentation (« physical r values » removed); the per-run
  Monte Carlo ratios remain named r_plant;
- the 190 s point described as the **last tested P3.1 grid point**, not the
  compile-time limit: 195 s is the last compilable arming delay under the
  declared nominal model and constraint set; 196 s is rejected;
- safety claims uniformly stated as « zero observed violations in 300
  runs », with the 95 % Wilson upper bound ≈ 1.3 % where needed;
- `ram_p3/analyse_sensibilite_r.py`: comment-only change (« choisie a
  priori » → « choisie pour l'analyse rétrospective »); the regenerated
  results JSON is byte-identical — no threshold, calculation or result
  modified.

Historical entries (v1.0–v1.3) and pre-registered configurations keep their
original wording intentionally.

## [v1.3] — 2026-09-09

P3/P3.1 interpretation release — no change to code, configurations, data or
results. P2 remains strictly frozen (bit-for-bit identical).

- **Paper v5** (`paper/`, FR/EN — scientifically identical). Changes from v4:
  - the nominal-model vs real-plant distinction is stated explicitly, with
    the sentence: « The 205.8 s value is derived from the nominal monitor
    model and should not be interpreted as the physical time-to-violation of
    every Monte Carlo plant realization. »;
  - the compile-time wall formulation is tightened: « Under the declared
    nominal monitor model, action bounds and constraint set, compile-time
    validation rejects configurations beyond the identified arming-delay
    boundary. » — still not a general physical impossibility;
  - the sensitivity analysis now reports **all three metrics** (violations,
    fallback, delivery) per r_plant subpopulation: in the most constraining
    decile (τ_arming = 190 s, r_plant 1.73–1.88), arm A violates 14/30 runs
    while B keeps zero observed violation with 21.6 % fallback and 81.9 %
    delivery, against 24.3 % / 73.3 % for D and worse for every C threshold
    (up to 99.6 % / 0.4 %). B dominates exactly where r_plant > 1;
  - the decision **not** to launch a retuned P3.2 campaign is substantiated:
    selecting margins, plant bounds or a scenario after the fact to force a
    B transition would fabricate the desired outcome; the frozen H4
    criterion stands (P3.1 inconclusive for H4) and any new campaign
    requires a new pre-registered protocol;
  - defect no. 8 (`dt_s`) is clarified: P3.1 imports the same frozen
    campaign module as P2.3 (`ram_p2/campagne_p2.py`, unmodified — the
    bit-for-bit non-regression rests on this identity), so the defect covers
    P3 executions identically; `dt_s` = 5.0 s = `DT` in `config_p3_1.json`
    as in every frozen configuration — zero numerical impact, documented,
    not fixed.
- **Terminology clarification** (documentation only): the operational-cost
  ordering is B < D ≤ C, since C and D coincide for some
  uncertainty-threshold settings (notably σ = 0.08). The values
  0.68 / 0.83 / 0.92 are corrected nominal ratios r_nominal (nominal
  monitor-model τ_violation = 205.8 s), not plant-physical ratios — the
  per-run Monte Carlo ratios remain named r_plant. The 190 s point is the
  last tested P3.1 grid point, not the compile-time limit: 195 s is the
  last compilable arming delay under the declared nominal model and
  constraint set; 196 s is rejected.
- **READMEs** (EN/FR, `ram_p3/README.md`, `paper/README.md`) carry the same
  corrections, definitions and numbers as the paper.
- No campaign re-run, no scenario retuned, no data modified. The sensitivity
  JSON (`ram_p3/resultats_sensibilite_r.json`) already contained the
  per-subpopulation fallback/delivery metrics; only the reporting is new.

## [v1.2] — 2026-09-09

Scope-correction release — no change to code, configurations, data or results.

- **Eighth defect documented (dt_s).** The September 2026 review also found
  that the campaign layer (`ram_p2/campagne_p2.py`) read the `DT` constant
  from `demo_eps.py` instead of the configuration's declared `dt_s` — a
  configuration value ignored. Both equal 5.0 s in every frozen configuration,
  so the numerical impact is **zero** (verified by bit-for-bit non-regression
  against the published results). By decision, the P2 code is kept intact as a
  frozen scientific artefact: the defect is **documented, not fixed**. The
  unified accounting becomes: four interaction + three code + one
  documentation defect — eight in total (README EN/FR, paper §6 and Table 5).
- **Paper v4** (`paper/`, FR/EN). Changes from v3:
  - the 205.8 s τ_violation is explicitly tied to the monitor's **nominal
    model** (C_BATT = 10 Ah, I_BASE = 0.5 A, u = 3 A, margin 0.02) — not
    presented as the physical time-to-violation of the Monte Carlo plants
    (C_BATT ∈ [5; 9] Ah, I_BASE ∈ [0.45; 0.60] A);
  - new retrospective sensitivity analysis (`ram_p3/analyse_sensibilite_r.py`,
    `ram_p3/resultats_sensibilite_r.json`): per-run τ_violation,plant computed
    from the frozen deterministic draws — 100.9 to 185.6 s; r_plant exceeds 1
    for 50/300 runs in P2 and 292/300 at τ_arming = 190 s (up to 1.88); arm B
    remains at zero observed violation in every subpopulation, including the
    top r_plant decile (where arm A violates in 14/30 runs); the B < D < C
    cost ordering is unchanged. No campaign re-run, no data modified;
  - the compile-time wall is now stated conditionally: under the declared
    nominal monitor model and action bounds (u_max = 3 A), validation rejects
    constraint sets beyond the identified arming-delay boundary — not a
    general physical impossibility;
  - the historical r labels (400 s reference: 0.35 / 0.425 / 0.475) are
    distinguished from the **corrected r_nominal** (0.68 / 0.83 / 0.92);
  - P3.1 stated as **inconclusive for H4** per its frozen criterion; Wilson
    wording made uniform (« no violations observed in 300 runs; 95 % Wilson
    upper bound ≈ 1.3 % »);
  - defect count updated to eight (abstract, contributions, §6, Table 5).
- No new campaign was run and no scenario was retuned: this release only
  narrows the scope of statements and adds retrospective analysis.

## [v1.1] — 2026-09-09

Paper v3 release — no change to code, data or results.

- `paper/`: added version 3 of the preprint (FR/EN). Changes from v2:
  post-correction figures throughout (Table 4, Table 5, §5.2); the ratio r is
  now measured — formal τ_violation = 205.8 s, physical r = 0.58 in P2,
  0.68 / 0.83 / 0.92 in P3.1, compile-time wall at 195 s (refused from 196 s,
  r ≈ 0.95); new Section 5.4 (campaign P3.1, Table 6, Figure 4) with the arm-B
  costs per point (fallback 10.18 → 15.60 → 18.77 %; delivery 89.05 → 86.47 →
  84.91 %); §3.3 worst case recomputed (0.3583 at 120 s); §6 and Table 5
  extended with the three September 2026 defects (unified accounting: four
  interaction + two code + one documentation defect, seven in total); §4.5
  notes the missed 90 % delivery floor (89.95 % CI lower bound); §4.6 now
  points to Zenodo and Software Heritage (annotated, unsigned tags included)
  instead of the author's word; version banner on page 1.
- Figure renumbering: demonstration scenario = Figure 2 (unchanged), P2.3 bar
  charts = Figure 3, P3.1 curves = Figure 4.
- `figures/faire_figures.py`: now bilingual (EN/FR); regenerates Figures 3
  and 4 of the paper in both languages.
- The v2 PDFs remain in `paper/`, marked *superseded* (banner on page 1);
  they are replaced by v3 as the version of record.
- Closes the known issue of v1.0.1: the archived zip of this release contains
  the bannered v2 PDFs alongside v3.

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
- **Known issue:** the Zenodo archive of v1.0.1
  ([10.5281/zenodo.22553128](https://doi.org/10.5281/zenodo.22553128)) was cut
  before the SUPERSEDED banner was applied to the v2 PDFs (commit `8f5e07b7`);
  the `paper/` PDFs in that archived zip therefore lack the banner. Corrected
  from v1.1 onwards (bannered PDFs, or replacement by v3).

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

**Defect accounting.** The count used across the README, this changelog and the
paper (§6) is: four interaction defects found and fixed before the first
campaign, plus the three defects above (two code, one documentation) — seven in
total.

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
