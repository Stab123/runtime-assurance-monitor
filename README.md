# Embedded runtime assurance monitor — prototype and falsification campaign

Executable prototype of an assurance monitor for an autonomous embedded decision layer, with an auditable decision-trace artefact, and a Monte Carlo campaign that **falsifies** the project's differentiating hypothesis.

**Main result: negative.** Hardening on estimation uncertainty (requirement RA-FUN-003) brings nothing in the tested scenario. The safety envelope alone reaches zero violations over 300 draws; every hardening variant costs availability without preventing anything more.

---

## Correction note — September 2026

**Status: re-run in progress.** A code review found two defects. The figures in the Results sections below are the **pre-correction** ones; they will be replaced by the re-run in a single merge commit, and this note updated accordingly. Pre-correction versions remain in the git history.

1. **Temporal off-by-one (RA-FUN-004).** `trajectoire_sure` applied the action for `pas_armement + 1` steps (`k <= pas_armement`): actual persistence was τ_arming + 5 s. Compile time and runtime shared the same convention — no safety hole, arm comparisons unbiased (uniform shift) — but the temporal label was off by one step. Fixed (`k < pas_armement`): persistence is now exactly τ_arming. Regression test added.
2. **Projection below u_min.** For a candidate below u_min whose projection is safe, the filter returned the **upper** bound of the admissible interval instead of u_min — contrary to minimal modification. Latent bug: never reached in the campaigns (candidates ∈ {0; 3} A ⊂ [u_min, u_max]). Fixed (the safe projection is transmitted), tests added on both sides.

Consequences already established (deterministic, checkable without re-run):

- **Formal τ_violation = 205.8 s** on the nominal model (eclipse, u = 3 A, from the SoC guard boundary 0.37 to the raw threshold 0.35; closed form 205.7 s — the thermal constraint is not determining). The τ = 400 s used to define P3's r grid was back-computed from r ≈ 0.3, not derived from the plant dynamics: P3.1's physical r values are **0.68 / 0.83 / 0.92** (P2 at 120 s: 0.58). The P3 result is stated in seconds; the ratio is only given with this formal value.
- **Wall position after correction: compilable up to and including 195 s (residual margin +0.0002), refused from 196 s** — i.e. physical r ≈ 0.95. The wall's physics is unchanged (the correction removes 5 s of persistence and the label now matches reality); the last P3.1 point (190 s, r = 0.92) remains compilable.

All campaigns (P2.2, P2.3, P3 pilot, P3.1) are being re-run with **strictly unchanged** configurations — only the code is fixed. P2.1 is not re-run (historical pilot lost, plan already superseded by P2.2): its pre-correction code bytes are archived under `empreintes/pre_correction/` and the verifier's documented exception is extended accordingly.

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
| **B** | envelope only | **0 %** | **0 / 300** | **6.58 %** | **90.80 %** |
| **D** | + pessimistic 3σ evaluation | 0 % | 0 / 300 | 9.42 % | 85.82 % |
| **C** | + uncertainty threshold (σ = 0.03) | 0 % | 0 / 300 | 18.11 % | 81.52 % |

The violation rate is measured on the **actual plant state**, against the **raw** thresholds — never on the estimated state, never against the switching threshold.

Uncertainty-threshold sweep (arm C):

| σ threshold | 0.005 | 0.008 | 0.010 | 0.015 | 0.020 | 0.030 | 0.050 | 0.080 |
|---|---|---|---|---|---|---|---|---|
| Fallback | 94.4 % | 55.1 % | 37.1 % | 24.1 % | 22.2 % | 18.1 % | 9.59 % | 9.42 % |
| Delivery | 5.0 % | 37.7 % | 51.8 % | 68.0 % | 73.6 % | 81.5 % | 85.8 % | 85.8 % |
| Violations | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

At σ = 0.08, C is identical to D run by run: the threshold never fires. The cost is monotonic, the benefit nil.

**Conclusion.** The pre-registered success criterion required a grid point with a violation rate strictly below control arm B. B is zero; nothing can do better. On both cost metrics, every point is worse than B. RA-FUN-003 is falsified.

**Secondary result.** Arm D shows that pessimistic 3σ evaluation is also dead weight in this scenario: +2.8 points of fallback and −5.0 points of delivery for zero violations avoided. The best configuration in the table is the envelope alone.

Where hardening could pay, compile-time validation refuses the constraint set. Where the set is acceptable, the envelope suffices and hardening can only cost.

---

## P3 — the §7 condition and the compilation wall

§7 made hardening useful only in a regime where fallback authority is marginal relative to time-to-violation (r = τ_arming / τ_violation → 1; P2 sits at r ≈ 0.3). P3 pushes this single lever — the arming delay — with everything else frozen (seeds, plant bounds, margins, thresholds, σ grid, cycles, and compile-time validation on the nominal 10 Ah model).

The pilot (arm B only, N = 30, run **before** freezing the criterion — `ram_p3/resultats_pilote_p3.json`) found two things. First, B stays at **zero violations** across the whole compilable band. Second, beyond τ_arming = 195 s (r ≈ 0.49), RA-FUN-005 validation **rejects the constraint set at compile time**: from the guard boundary, the most adverse action persisted through arming would cross the raw threshold. The regime where hardening could pay is not a hard-to-survive regime — it is **non-deployable by construction**.

The wall is indexed on the action domain (u_max = 3 A, declared in `ram_p0/demo_eps.py`, checked on both bounds at compile time): the result is stated *for this set of bounds*. Here u_payload = u_max — the worst case verified at compile time is exactly the actual load commanded in the payload window.

P3.1 documents the wall with statistical power: r ∈ {0.35; 0.425; 0.475} — the last one flush against the wall —, N = 300, four arms, unchanged σ grid. Configuration frozen and committed before execution (`ram_p3/config_p3_1.json`, two-clause criterion included), executed by `.github/workflows/p3.yml`.

**P3.1 result** (N = 300 per point, CRN 300/300 — `ram_p3/resultats_p3_1.json`): at every point of the compilable band, B stays at **0/300** runs with violation (Wilson [0; 1.3 %]) — including at r = 0.475, the last deployable point. The wall is not an N = 30 artefact. The frozen power criterion decides: P3 is **inconclusive for H4** — there is no deployable regime where B fails, hence none where hardening could pay. Costs rise with r for all monitored arms (B fallback: 10.2 % → 15.6 % → 18.8 %; delivery: 89.0 % → 84.9 %) without the B < D < C ordering ever flipping. Non-regression: arm A reproduces P2.3 bit for bit at every point (6300/6300 identical fields).

### Scope of the result

The exact statement is: **in a regime where the safety envelope already suffices, hardening on uncertainty is not justified.** This is not a general statement.

The control arm is at the ceiling — zero violations. In an experiment where the control fails at nothing, an additional mechanism can only cost. A scenario where the guard margin no longer covers the estimation error might give a different result; building such a scenario *after* seeing these figures would be result fabrication, and was therefore not done.

---

## Declared limitations

**The falsification thresholds were not arbitrated.** The configurations propose a violation ceiling, a fallback ceiling and a delivery floor, marked as requiring operator arbitration. That arbitration did not take place. The conclusion on RA-FUN-003 rests on the comparison with arm B and depends on no absolute ceiling. For information, with 300 runs arm B passes three of the four proposed thresholds and misses the fourth by 0.06 point (delivery 89.94 % at the lower bound against a 90 % floor). The question remains open and needs a satellite operator.

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

**Execution environment of the published campaigns.** P2.1, P2.2 and P2.3 ran in September 2026 in the Linux sandbox of a software agent (CPython 3.12.12, x86-64). The absolute paths `/mnt/agents/output/...` visible in the archived bytes (`empreintes/`) belong to that environment; the executable copies under `ram_p0/` and `ram_p2/` resolve their paths relative to the repository (`ram_p2/chemins.py`) and replay as-is after a clone. A re-run reproduces the results run by run; its `empreintes_code` are identical for the four monitor modules and different for the two pilots, whose paths alone were relativised — fingerprint verification therefore points to `empreintes/`.

The seeds are in the configuration files, the SHA-256 module fingerprints in the results files. Any configuration change creates a new version of the file, never an edit.

---

## Methodological choices

**σ is not circular.** It is computed from measurement residuals — innovations against the nominal model, the very one the monitor uses — and never from plant parameters. A σ derived from the prediction model would have measured nothing.

**The plant/model gap is real and unfavourable to the monitor.** The plant draws its parameters uniformly per run; the monitor keeps the nominal model, which assumes a battery capacity higher than any drawn value. Despite this, the envelope alone misses nothing.

**The control arm is decisive.** Without B, the contribution of RA-FUN-003 would not be attributable. Without D, its cost would remain confounded with that of pessimistic evaluation.

**Code provenance.** Four interaction defects were found by adversarial review while the test suite was entirely green. They were all fixed **before** the first campaign: the monitor-module fingerprints are identical in the P2.1, P2.2 and P2.3 results files; only the campaign pilot differs. No reported result was produced by the defective code. The P2.1 pilot (three arms) was edited in place to become the four-arm version, and the execution environment kept no copy of it: its fingerprint remains verifiable in `resultats_p2_1.json`, and replaying the P2.1 configuration with the four-arm version reproduces arms A, B and C run by run — full rationale in `empreintes/README.md`.

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
