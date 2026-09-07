# paper/ — preprints

## Status: v2 superseded

Both PDFs in this directory are **version 2** of the paper, **superseded**
(banner on page 1). They predate the September 2026 code correction and the
post-correction re-run. All qualitative conclusions are unchanged, but four
points of the v2 text are stale:

1. **The ratio r (§7).** v2 states the §7 condition qualitatively — hardening
   can only pay where fallback authority is marginal relative to
   time-to-violation. That regime has since been measured (P3/P3.1): with the
   formal τ_violation = 205.8 s, the physical r values are 0.68 / 0.83 / 0.92,
   and the marginal regime turns out to be **non-deployable** (next point).
2. **The wall.** v2 §3.3 quotes the pre-correction compile-time check
   (« 120 s passes with a worst-case SoC of 0.3575; 300 s is rejected »). After
   the off-by-one fix, the wall sits at **195 s** (compilable with a residual
   margin of +0.0002, refused from 196 s) and the end-of-arming worst case
   moved accordingly.
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

A **v3** is in preparation with the post-correction figures and the Zenodo
DOI. Until then, the data and code of record are this repository at tag
`v1.0-p3.1`, archived at
[10.5281/zenodo.22552148](https://doi.org/10.5281/zenodo.22552148)
(concept DOI: [10.5281/zenodo.22552147](https://doi.org/10.5281/zenodo.22552147)).
Full correction protocol: [CHANGELOG.md](../CHANGELOG.md), entry v1.0-p3.1.

## Files

- `QUAND_L_ENVELOPE_SUFFIT_v2_FR_superseded.pdf` — version 2, français (originale)
- `WHEN_THE_ENVELOPE_SUFFICES_v2_EN_superseded.pdf` — version 2, English (translation)

Figures 2 and 3 can be regenerated from the published result files with
[`figures/faire_figures.py`](../figures/faire_figures.py).
