# paper/ — preprints

## Status: v4 current

The current version of the paper is **version 4** (September 2026). Changes
from v3: the 205.8 s τ_violation is explicitly tied to the monitor's **nominal
model** (C_BATT = 10 Ah, I_BASE = 0.5 A, u = 3 A, margin 0.02); a new
retrospective sensitivity analysis covers the Monte Carlo plants' physical
τ_violation (100.9–185.6 s; r_plant exceeds 1 for part of the runs — result
unchanged); the compile-time wall's scope is conditioned on the declared
nominal model and action bounds (not a general physical impossibility); the
historical r labels (400 s reference) are distinguished from the **corrected
r_nominal**; and an eighth defect (configuration `dt_s` ignored by the
campaign layer, zero numerical impact, P2 code kept intact) is documented in
Section 6:

- `QUAND_L_ENVELOPE_SUFFIT_v4_FR.pdf` — version 4, français (originale)
- `WHEN_THE_ENVELOPE_SUFFICES_v4_EN.pdf` — version 4, English (translation)

Version 3 (`*_v3_*.pdf`) is kept for the record; version 2
(`*_v2_*_superseded.pdf`) carries a SUPERSEDED banner on page 1.

The **v2** PDFs predate the September 2026 code correction and the
post-correction re-run. All qualitative conclusions are unchanged;
four points of the v2 text are stale:

1. **The ratio r (§7).** v2 states the §7 condition qualitatively — hardening
   can only pay where fallback authority is marginal relative to
   time-to-violation. That regime has since been measured (P3/P3.1): with the
   formal τ_violation = 205.8 s, the physical r values are 0.68 / 0.83 / 0.92,
   and the marginal regime turns out to be **non-deployable** (next point).
2. **The wall.** v2 §3.3 quotes the pre-correction compile-time check
   (« 120 s passes with a worst-case SoC of 0.3575; 300 s is rejected »). After
   the off-by-one fix, the wall sits at **195 s** (compilable with a residual
   margin of +0.0002, refused from 196 s) and the end-of-arming worst case is
   0.3583 at 120 s.
3. **Table 4 (P2.3).** The printed fallback and delivery figures are the
   pre-correction ones; the re-run shifts them by at most 0.04 point
   (violation counts are identical). Current values: B fallback 6.57 % /
   delivery 90.81 %; D 9.43 % / 85.83 %; C(σ = 0.03) 18.11 % / 81.52 %.
4. **The defect count (§6).** v2 reports four interaction defects and states
   that « no reported number was produced by the defective code ». The
   September 2026 review found **two further code defects** (plus one stale
   documentation table) — and unlike the first four, the published results
   *had* been produced by the affected code, which is why every campaign was
   re-run with unchanged configurations.

Figure numbering changed between v2 and v3: the demonstration scenario is now
Figure 2, the P2.3 bar charts are Figure 3, and the new P3.1 curves are
Figure 4. Figures 3 and 4 can be regenerated from the published result files
with [`figures/faire_figures.py`](../figures/faire_figures.py).

Archived at Zenodo (concept DOI, always resolves to the latest version):
[10.5281/zenodo.22552147](https://doi.org/10.5281/zenodo.22552147).
Full correction protocol: [CHANGELOG.md](../CHANGELOG.md), entries v1.0-p3.1
and v1.1.
