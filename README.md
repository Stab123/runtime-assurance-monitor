# Embedded runtime assurance monitor — prototype and falsification campaign

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22552147.svg)](https://doi.org/10.5281/zenodo.22552147)
[![tests](https://github.com/Stab123/runtime-assurance-monitor/actions/workflows/tests.yml/badge.svg)](https://github.com/Stab123/runtime-assurance-monitor/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Executable prototype of an assurance monitor for an autonomous embedded decision layer, with an auditable decision-trace artefact, and a Monte Carlo campaign that **falsifies** the project's differentiating hypothesis.

**Main result: negative.** Hardening on estimation uncertainty (requirement RA-FUN-003) brings nothing in the tested scenario. The safety envelope alone reaches zero observed violations over 300 draws; every hardening variant costs availability without preventing anything more.

---

## Correction note — September 2026

**Status: re-run complete.** A code review found two code defects (a temporal off-by-one in the fallback persistence, and a latent projection bug never reached by the campaigns) plus one stale documentation table. All campaigns (P2.2, P2.3, P3 pilot, P3.1) were re-run on GitHub Actions with **strictly unchanged** configurations: violation counts are unchanged, fallback and delivery shifted by at most 0.04 point, the wall moved by exactly one pilot grid point as the fix predicted, and every figure below is the post-correction one. **All qualitative conclusions are unchanged.** Full protocol, numbers and consequences: [CHANGELOG.md](CHANGELOG.md) (entry v1.0-p3.1).

---

## Context

*Runtime assurance* wraps a decision layer that cannot be statically verified — planner, learned policy, adaptive controller — behind a verified monitor that authorizes, modifies or blocks each action. The pattern is established: Simplex architecture (Seto et al. 1998), ASTM F3269, and on the control side Wabersich & Zeilinger's *predictive safety filter*. On the embedded runtime-verification side, R2U2 flew on a CubeSat (CySat-I), on the ISS (Robonaut2) and on a JAXA mission.

This repository reinvents none of these elements. It explores two points the literature does not address:

1. **an auditable decision-trace artefact** — reconstructing after the mission what the monitor knew, what it refused, and which constraint flipped the verdict, without access to the decision layer's internal state;
2. **estimation uncertainty as a first-order trigger** for fallback, independently of the nominal value.

Point 2 is the one the campaign falsifies.

---

## Results — P2.3 campaign

Four arms, same draws (*common random numbers*), 300 runs per point, 2700 cycles of 5 s per run.

| Arm | Configuration | Violations | Runs with violation | Fallback rate | Mission delivery |
|---|---|---|---|---|---|
| **A** | no monitor | 2.53 % | 68 / 300 | 0 % | 100 % |
| **B** | envelope only | **0 %** | **0 / 300** | **6.57 %** | **90.81 %** |
| **D** | + pessimistic 3σ evaluation | 0 % | 0 / 300 | 9.43 % | 85.83 % |
| **C** | + uncertainty threshold (σ = 0.03) | 0 % | 0 / 300 | 18.11 % | 81.52 % |

The violation rate is measured on the **actual plant state**, against the **raw** thresholds — never on the estimated state, never against the switching threshold.

Uncertainty-threshold sweep (arm C):

| σ threshold | 0.005 | 0.008 | 0.010 | 0.015 | 0.020 | 0.030 | 0.050 | 0.080 |
|---|---|---|---|---|---|---|---|---|
| Fallback | 94.89 % | 59.10 % | 40.20 % | 24.98 % | 22.63 % | 18.11 % | 9.60 % | 9.43 % |
| Delivery | 4.54 % | 31.91 % | 48.00 % | 67.34 % | 74.13 % | 81.52 % | 85.82 % | 85.83 % |
| Violations | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

At σ = 0.08, C is identical to D run by run: the threshold never fires. The cost is monotonic, the benefit nil.

**Conclusion.** The pre-registered success criterion required a grid point with a violation rate strictly below control arm B. B is zero; nothing can do better. On both cost metrics, every point is worse than B. RA-FUN-003 is falsified.

**Secondary result.** Arm D shows that pessimistic 3σ evaluation is also dead weight in this scenario: +2.9 points of fallback and −5.0 points of delivery for zero observed violations avoided. The best configuration in the table is the envelope alone.

Where hardening could pay, compile-time validation refuses the constraint set. Where the set is acceptable, the envelope suffices and hardening can only cost.

---

## P3 — the §7 condition and the compilation wall

§7 made hardening useful only in a regime where fallback authority is marginal relative to time-to-violation (r = τ_arming / τ_violation → 1; with the formal τ_violation = 205.8 s of the correction note, P2 at 120 s sits at r_nominal = 0.58). P3 pushes this single lever — the arming delay — with everything else frozen (seeds, plant bounds, margins, thresholds, σ grid, cycles, and compile-time validation on the nominal 10 Ah model).

The pilot (arm B only, N = 30, run **before** freezing the criterion — `ram_p3/resultats_pilote_p3.json`) found two things. First, B stays at **zero observed violations** across the whole compilable band — including at 195 s, which the pre-correction code still refused (the off-by-one made it apply 200 s; the fix moved the wall by exactly one grid point, as predicted). Second, beyond τ_arming = 195 s (r_nominal ≈ 0.95), RA-FUN-005 validation **rejects the constraint set at compile time**: from the guard boundary, the most adverse action persisted through arming would cross the raw threshold (compilable at 195 s with a residual margin of +0.0002, refused from 196 s; the pilot's next grid point, 240 s, is refused). The regime where hardening could pay is not a hard-to-survive regime — it is **non-deployable within the declared framework**: under the declared nominal monitor model, action bounds and constraint set, compile-time validation rejects configurations beyond the identified arming-delay boundary — the wall depends on the nominal model (C_BATT = 10 Ah), the declared action bounds (u_max = 3 A), the safety margins and the constraint set; it is not a general physical impossibility.

The wall is indexed on the action domain (u_max = 3 A, declared in `ram_p0/demo_eps.py`, checked on both bounds at compile time): the result is stated *for this set of bounds*. Here u_payload = u_max — the worst case verified at compile time is exactly the actual load commanded in the payload window.

### P3.1 — corrected interpretation

The arming delays of 140, 170 and 190 s correspond to the corrected nominal ratios:

- r_nominal = 0.68 at 140 s
- r_nominal = 0.83 at 170 s
- r_nominal = 0.92 at 190 s

These values use a nominal time-to-violation of approximately 205.8 s.

The value 205.8 s is derived from the nominal monitor model (C_BATT = 10 Ah, I_BASE = 0.5 A, u = 3 A, SoC margin = 0.02). It must not be interpreted as the physical time-to-violation of every Monte Carlo plant realization.

Across the sampled plant population, the retrospectively calculated plant-specific time-to-violation ranges from approximately 100.92 s to 185.58 s. Therefore, r_plant can exceed 1.

The 190 s point is the last tested P3.1 grid point. It is not the compile-time limit. Under the declared nominal model, action bounds, margins and constraint set, 195 s is still accepted by compile-time validation, while 196 s is rejected.

B, C and D all have zero observed violations in the tested P3.1 configurations. With the same observed safety result, B has the lowest fallback rate and the highest mission delivery.

The operational-cost ordering is:

B < D ≤ C

At some uncertainty thresholds, C and D are identical.

Results for B:

- 140 s: 0/300 runs with an observed violation; fallback = 10.18%; mission delivery = 89.05%.
- 170 s: 0/300 runs with an observed violation; fallback = 15.60%; mission delivery = 86.47%.
- 190 s: 0/300 runs with an observed violation; fallback = 18.77%; mission delivery = 84.91%.

Zero observed violations does not mean that the true probability of violation is zero. With 0 observed violations in 300 runs, the upper bound of the 95% Wilson confidence interval is approximately 1.3%.

At the 190 s point, 292 of the 300 sampled plants have r_plant > 1.05.

In the 30 runs with the highest r_plant values, approximately 1.73 to 1.88:

- A: 14/30 runs with an observed violation
- B: 0/30 runs with an observed violation
- B fallback = 21.63%
- B mission delivery = 81.85%
- D: 0/30 runs with an observed violation
- D fallback = 24.34%
- D mission delivery = 73.33%

The r_plant sensitivity analysis is retrospective. It does not modify or rerun the frozen P3.1 campaign.

Because B never exhibited a strictly positive observed violation rate at any tested P3.1 point, the pre-registered informativeness criterion for testing H4 was not met.

P3.1 therefore remains formally inconclusive for H4.

Within the tested regime, however, C and D prevented no additional observed violation relative to B while producing higher operational costs.

No post-hoc P3.2 campaign was introduced to force a transition. Any future campaign testing different assumptions must be defined under a new pre-registered protocol before execution.

(N = 300 per point, CRN 300/300, four arms, unchanged σ grid — `ram_p3/config_p3_1.json` frozen and committed before execution, `ram_p3/resultats_p3_1.json`; the frozen configuration keeps the historical r labels indexed on a 400 s reference constant — 0.35 / 0.425 / 0.475 — the executed delays are 140 / 170 / 190 s. Retrospective sensitivity analysis: `ram_p3/analyse_sensibilite_r.py`. Non-regression: arm A reproduces P2.3 bit for bit at every point, 6300/6300 identical fields.)

### Scope of the result

The exact statement is: **in a regime where the safety envelope already suffices, hardening on uncertainty is not justified.** This is not a general statement.

The control arm is at the ceiling — zero observed violations. In an experiment where the control fails at nothing, an additional mechanism can only cost. A scenario where the guard margin no longer covers the estimation error might give a different result; building such a scenario *after* seeing these figures would be result fabrication, and was therefore not done.

---

## Declared limitations

**The falsification thresholds were not arbitrated.** The configurations propose a violation ceiling, a fallback ceiling and a delivery floor, marked as requiring operator arbitration. That arbitration did not take place. The conclusion on RA-FUN-003 rests on the comparison with arm B and depends on no absolute ceiling. For information, with 300 runs arm B passes three of the four proposed thresholds and misses the fourth by 0.05 point (delivery 89.95 % at the lower bound against a 90 % floor). The question remains open and needs a satellite operator.

**The prototype is not flight code.** Python, dynamic allocation: the requirements of statically bounded memory and worst-case execution time cannot be demonstrated here. The action is scalar and exploits a monotonicity assumption specific to the tested model; the vector case requires the full quadratic formulation. Uncertainty is assumed constant over the prediction horizon.

**A single use case.** The monitor's genericity — black-box decision layer, versioned constraint set — is a design property, not a demonstrated one.

---

## Contents

```
ram_p0/
  contraintes.py       constraint-set types (versioned, per-constraint uncertainty thresholds)
  filtre.py            predictive safety filter, scalar specialisation of W&Z
  moniteur.py          verdicts, fallback latching, set compilation, liveness signal
  trace.py             recorder: 16/48/160-byte formats, frozen ring buffer, CRC, decoder
  demo_eps.py          CySat-I-style EPS scenario, fault injection
  test_moniteur.py     tests, each tied to a requirement
ram_p2/
  chemins.py           repository path resolution
  campagne_p2.py       Monte Carlo campaign, four arms (relative paths)
  executer_p2_3.py     per-run parallel execution (relative paths)
  config_p2_1.json     frozen P2.1 configuration   resultats_p2_1.json
  config_p2_2.json     frozen P2.2 configuration   resultats_p2_2.json
  config_p2_3.json     frozen P2.3 configuration   resultats_p2_3.json
ram_p3/
  pilote_p3.py         power pilot, arm B only, before freezing
  executer_p3_1.py     P3.1 parallel execution and partial merging
  config_pilote_p3.json, config_p3_1.json (frozen before execution)
  resultats_pilote_p3.json, partiel_r*.json, resultats_p3_1.json
empreintes/            exact bytes that produced the published results —
                       for verification, never execution
                       (see empreintes/README.md)
verifier_empreintes.py compares module by module the SHA-256 fingerprints
                       embedded in the results against the empreintes/ bytes
.github/workflows/tests.yml
                       on every push: pytest ram_p0/test_moniteur.py,
                       then verifier_empreintes.py
.github/workflows/p3.yml
                       manual trigger: runs P3.1, one job per r point
.github/workflows/rejeu.yml
                       manual trigger: the September 2026 re-runs
                       (P2.2, P2.3, P3 pilot), unchanged configurations
figures/
  faire_figures.py     regenerates Figures 2 and 3 of the paper from
                       the published result files (figures_2_3.png)
docs/
  exigences.md         requirements traceability (RA-* → mechanism → test)
  README_fr.md         French translation of this README (English is
                       authoritative)
paper/                 the v2 preprint (FR/EN), superseded — v3 in preparation
CITATION.cff           citation metadata (Zenodo concept DOI)
CHANGELOG.md           correction protocol and release history
```

All three campaigns are preserved. P2.1 had an experimental-design flaw — arm C varied two things at once — fixed in P2.2 by adding arm D and extending the grid. P2.3 raises N from 32 to 300 with no other change. Shared points reproduce identically, checked as a non-regression.

---

## Reproduction

```bash
python3 -m pytest ram_p0/test_moniteur.py -q
python3 ram_p0/demo_eps.py
python3 verifier_empreintes.py
python3 ram_p2/executer_p2_3.py ram_p2/config_p2_2.json resultats_rejeu.json 4
```

Python 3.10+, standard library only.

**Execution environment of the published campaigns.** P2.1, P2.2 and P2.3 originally ran in the Linux sandbox of a software agent (CPython 3.12.12, x86-64). The absolute paths `/mnt/agents/output/...` visible in the original archived bytes (`empreintes/campagne_p2.py`, `empreintes/executer_p2_3.py`) belong to that environment; the executable copies under `ram_p0/` and `ram_p2/` resolve their paths relative to the repository (`ram_p2/chemins.py`) and replay as-is after a clone. The September 2026 re-runs (P2.2, P2.3, P3) ran on GitHub Actions runners with those relative-path copies: they reproduce the original results run by run (violations identical, fallback/delivery within 0.04 point — the off-by-one fix shortens persistence by exactly one step), and their `empreintes_code` are archived under `empreintes/campagne_p2_rejeu.py` and `empreintes/executer_p2_3_rejeu.py`. A re-run reproduces the results run by run; its `empreintes_code` are identical for the four monitor modules and different for the two pilots, whose paths alone were relativised — fingerprint verification therefore points to `empreintes/`.

The seeds are in the configuration files, the SHA-256 module fingerprints in the results files. Any configuration change creates a new version of the file, never an edit.

---

## Methodological choices

**σ is not circular.** It is computed from measurement residuals — innovations against the nominal model, the very one the monitor uses — and never from plant parameters. A σ derived from the prediction model would have measured nothing.

**The plant/model gap is real and unfavourable to the monitor.** The plant draws its parameters uniformly per run; the monitor keeps the nominal model, which assumes a battery capacity higher than any drawn value. Despite this, the envelope alone misses nothing.

**The control arm is decisive.** Without B, the contribution of RA-FUN-003 would not be attributable. Without D, its cost would remain confounded with that of pessimistic evaluation.

**Code provenance.** The defect accounting used everywhere in this repository (README, CHANGELOG, paper §6) is: **four interaction defects + three code defects + one documentation defect** — eight in total. The four interaction defects were found by adversarial review while the test suite was entirely green, and were all fixed **before** the first campaign: the monitor-module fingerprints are identical in the P2.1, P2.2 and P2.3 results files; only the campaign pilot differs. No reported result was produced by that defective code. The next three defects — two in the code, one stale documentation table — were found later (September 2026 correction note at the top): the published results had been produced by the affected code, so all campaigns were re-run with unchanged configurations — every qualitative conclusion held. The eighth defect — the campaign layer reading the `DT` constant from `demo_eps.py` instead of the configuration's declared `dt_s` — was found in the same September 2026 review; both equal 5.0 s in every frozen configuration (P2.3 and P3.1 alike), so the numerical impact is **zero** (verified by bit-for-bit non-regression against the published results). P3.1 imports that same campaign module without modification — its bit-for-bit non-regression against P2.3 rests on this identity — so the defect covers P3 executions identically, and the P2/P3 code is kept intact as a frozen scientific artefact: the defect is documented, not fixed. The P2.1 pilot (three arms) was edited in place to become the four-arm version, and the execution environment kept no copy of it: its fingerprint remains verifiable in `resultats_p2_1.json`, and replaying the P2.1 configuration with the four-arm version reproduces arms A, B and C run by run — full rationale in `empreintes/README.md`.

**Pre-registration and archiving.** Every campaign configuration was committed before its execution — the git history carries the config-before-results order for P2.1, P2.2, P2.3 and P3.1. That history is now timestamped in two independent, non-rewritable archives: Zenodo (concept DOI [10.5281/zenodo.22552147](https://doi.org/10.5281/zenodo.22552147), one version DOI per release) and [Software Heritage](https://archive.softwareheritage.org/), which preserves the full git graph. The release tags are annotated but not GPG-signed; timestamping and integrity are covered by these two archives.

---

## References

- K. P. Wabersich, M. N. Zeilinger, *A predictive safety filter for learning-based control of constrained nonlinear dynamical systems*, Automatica 129:109597, 2021 — arXiv:1812.05506
- A. Aurandt, P. H. Jones, K. Y. Rozier, *Runtime Verification Triggers Real-time, Autonomous Fault Recovery on the CySat-I*, NASA Formal Methods 2022
- D. Seto, B. Krogh, L. Sha, A. Chutinan, *The Simplex architecture for safe on-line control system upgrades*, ACC 1998
- ECSS-E-ST-70-11C Rev.1 (15 October 2025), *Space segment operability*
- ECSS-E-ST-70-41C, *Telemetry and telecommand packet utilization*

---

## License

MIT.
