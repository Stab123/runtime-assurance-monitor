# paper/ — preprints

## Status: v3 current

The current version of the paper is **version 3** (September 2026), with the
post-correction figures, the P3.1 campaign (Section 5.4) and the measured
ratio r (formal τ_violation = 205.8 s; physical r = 0.58 in P2, 0.68 / 0.83 /
0.92 in P3.1, wall at r ≈ 0.95):

- `QUAND_L_ENVELOPE_SUFFIT_v3_FR.pdf` — version 3, français (originale)
- `WHEN_THE_ENVELOPE_SUFFICES_v3_EN.pdf` — version 3, English (translation)

The two **v2** PDFs (`*_v2_*_superseded.pdf`) are kept for the record, with a
SUPERSEDED banner on page 1. They predate the September 2026 code correction
and the post-correction re-run. All qualitative conclusions are unchanged;
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
