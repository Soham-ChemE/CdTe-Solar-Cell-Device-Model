# Option C: can one shared front-interface S explain the Cu-doped MgZnO series? (pandey_oneS)

**Data.** Pandey et al. 2021, Cu-doped CdSeTe/CdTe with an RF-sputtered MgxZn1−xO emitter. x = 0, 0.10, 0.15, 0.20
and 0.25 are used; x = 0.35 is excluded because of the structural change. The targets are the **best cells** of 25
per composition; the averages are scored only for reference.

**Model.** The option-A Sesame cell (`sesame_cell.case_layers`): FTO / 100 nm MgZnO / 0.5 µm CdSeTe / 3 µm CdTe, with
optics T_front 0.9 and R_back 0.2.

- **Front recombination** goes through interface states that couple the buffer conduction band to the absorber
  valence band (level at mid interface gap), exactly as in `grid.py --interface`. The 10 nm IL keeps only the bulk τ.
- **Per cell:** the buffer takes the XPS dEc (−0.10, +0.10, +0.19, +0.25, +0.27 eV) and the optical gap (3.28–3.83
  eV). The electrical gap is capped at 3.5 eV, as in `mzo_model`.
- **Shared by all five cells:**
  - log10 S_if (cm/s): 1, 2, 3, 3.5, 4, 4.5, 5, 5.5, 6
  - τ: 10, 30, 60 ns
  - NA: 2e14, 1e15 cm⁻³
  - φ_b: 0.20, 0.35, 0.50 eV, plus 0.65 at log10 S ≥ 3.5. The metal work function is 5.40 − φ_b.
  - ND_MZO: 1e15, 1e17 cm⁻³
  - Rs: fitted on a 0–4 Ω cm² grid, or fixed at 1.3 Ω cm².
- **Grid passes.** The first pass was the requested decade grid in S. A single refinement added the half-decade S
  points and φ_b 0.65, because the first optimum sat at the φ_b 0.50 grid edge. That gives 396 parameter sets × 5
  cells = **1980 J-V curves, none failed**, at 2–5 s each.
- **χ² per cell:** ((Voc − Voc_t)/10 mV)² + ((FF − FF_t)/2 pt)² + ((Jsc − Jsc_t)/0.5 mA/cm²)², summed over the five
  cells.

**Jsc systematic.** This cell's total optical generation is 27.98 mA/cm². The best Mg cells' Jsc of 28.1–28.4 is above
that, so with absolute Jsc the χ² penalises every front loss. Three treatments are therefore reported:

- **abs:** Jsc as specified.
- **kscale:** one shared optical factor k multiplies every model Jsc. It is fitted analytically and clipped to 0.9–1.1;
  the ~1 mV Voc effect of k is ignored. This keeps the *relative* Jsc between cells, which is the S signal.
- **noJsc:** Voc and FF only.

## 1. One shared S (best cells, Rs fitted)

| Jsc treatment | best log10 S | other shared parameters | χ² (n data) | log10 S, Δχ² ≤ 4 |
|---|---|---|---|---|
| kscale (k = 1.061) | **5.0** | τ 30 ns, NA 2e14, φ_b 0.35, ND 1e15, Rs 2.3 | **13.8** (15) | **4.83 – 5.86** |
| noJsc | 5.0 | same | 13.4 (10) | 4.80 – 5.91 |
| abs | 4.5 | τ 60 ns, NA 1e15, φ_b 0.50, ND 1e15, Rs 2.0 | 44.1 (15) | 4.00 – 4.60 |
| abs, Rs fixed 1.3 | 4.5 | τ 30 ns, NA 1e15, φ_b 0.50, ND 1e15 | 47.1 (15) | 4.15 – 4.62 |

Ranges are interpolated linearly between half-decade grid points.

**Per cell at the kscale best (model Voc / Jsc×k / FF against best cell):**

| x | Voc (mV) | Jsc×k (mA/cm²) | FF (%) | χ² |
|---|---|---|---|---|
| 0 | 733 vs 748 | 27.44 vs 27.2 | **67.7 vs 62.8** | 8.6 |
| 0.10 | 853 vs 851 | 27.98 vs 28.1 | 73.8 vs 74.0 | 0.1 |
| 0.15 | 863 vs 860 | 28.23 vs 28.3 | 74.7 vs 78.0 | 2.7 |
| 0.20 | 864 vs 861 | 28.29 vs 28.4 | 74.8 vs 77.5 | 2.0 |
| 0.25 | 865 vs 861 | 28.30 vs 28.2 | 74.8 vs 73.9 | 0.4 |

**Cost of moving each parameter off the kscale best (Δχ²):**

| Parameter | Value: Δχ² |
|---|---|
| τ | 10 ns: +12.7; 60 ns: +0.6 |
| NA | 1e15: +4.6 (C-V's ~1 µm depletion suggests about 8e14) |
| φ_b | 0.20: +3.0; 0.50: +4.6; 0.65: +616 |
| ND_MZO | 1e17: +4.6 |
| Rs | 1.3 fixed: +5.3 |

**The x = 0 cell pins S.** These are the x = 0 and x = 0.15 cells as S is varied, with everything else at the kscale
best (model Voc / Jsc / FF):

| log10 S | 3 | 3.5 | 4 | 4.5 | 5 | 5.5 | 6 |
|---|---|---|---|---|---|---|---|
| x = 0 | 836 / 27.32 / 74.6 | 811 / 27.28 / 74.5 | 783 / 27.15 / 73.4 | 756 / 26.77 / 71.1 | 733 / 25.86 / 67.7 | 717 / 24.33 / 64.9 | 709 / 22.85 / 64.0 |
| x = 0.15 | 873 / 27.31 / 75.6 | 873 / 27.29 / 75.6 | 872 / 27.23 / 75.5 | 869 / 27.07 / 75.3 | 863 / 26.61 / 74.7 | 853 / 25.68 / 73.8 | 845 / 24.48 / 72.8 |

- **Below:** the x = 0 Voc pins S at ≥ ~10^4.5. At S ≤ 10^3.5 its Voc is ≥ 810 mV.
- **Above:** the Mg cells start losing Voc and Jsc at ~10^5.5–10^6, and the x = 0 Jsc drops.
- **The x = 0 Jsc deficit relative to the Mg cells is itself an S signal.** Measured, it is 27.2 against 28.1–28.4.
  In the model it is ≈ 0 at S ≤ 10^4 and ≈ −0.8 mA/cm² at S 1e5; ZnO's extra UV absorption accounts for less than
  0.05 mA/cm².

**Not reproduced: the x = 0 best-cell FF.** At the S that matches its Voc, the model gives FF 67–71% against 62.8%.
Fitted alone, x = 0 reaches 763 mV / FF 63.2% only with Rs 4.0 Ω cm², at the grid edge. The shared Rs cannot go
there without collapsing the Mg cells' FF.

## 2. Does S have to vary with x? (S free for x = 0 only)

| Jsc treatment | log10 S_Mg | log10 S_0 | χ² improvement over shared S | log10 S_0 range | log10 S_Mg range |
|---|---|---|---|---|---|
| kscale | 5 | 5 | **0.0** | 4.79–5.87 | 4.32–5.92 |
| noJsc | 5 | 5 | 0.0 | 4.74–≥6.0 (grid edge) | ≤ 5.94 |
| abs | 1 | 5 | 1.6 | 4.17–5.18 | ≤ 4.69 |
| abs, Rs 1.3 | 1 | 5 | 2.5 | 4.36–5.20 | ≤ 4.66 |

**No.** A separate S for x = 0 improves χ² by 0–2.5 for one extra parameter, which is not significant.

**What the data do and do not say:**
- The x = 0 interface needs S ≈ 10^4.7–10^5.9 (or 10^4.2–10^5.2 with abs Jsc).
- The Mg cells only bound S from above (≲ 10^5.9). Behind the spike they are insensitive to S, so they would also
  accept a much smaller S.

So "one shared S" is consistent with the data, but the Mg cells cannot test it. Only x = 0 measures S.

**Averages, for reference** (abs Jsc, Rs fitted). With one shared S the best is at the S = 1e6 grid edge, χ² 145.5;
x = 0 there gives 774 / 23.0 / 62.9 against 707 / 20.1 / 54.2. Freeing S for x = 0 only puts S_0 at the grid edge
(1e6), and x = 0 still gives 708 / 22.75 / 61.7, χ² 42. The average Jsc and FF are unreachable, as in task 1: they
need a loss outside this model (shunts, spread).

**Selection bias.** Best-of-25 is the upper tail.
- For x = 0 the spread is large: best 12.2% against average 8.0%.
- The best x = 0 cell is the least degraded, so its S (~1e5) is a lower bound on the typical x = 0 interface.
- For the Mg cells the best and average differ by only 10–14 mV in Voc and 3–6 points in FF.

## 3. Comparison with the As-doped 21.4% cell

The As cell has an effective S of about 2–20 cm/s (log10 0.3–1.3) at a cliff of −0.26 to −0.35 eV (`kujovic/ident`,
`kujovic/fluct`).

- **S_Cu / S_As ≥ 100? Yes, in every variant.**
  - kscale and noJsc: 10^4.8–10^5.9 against 10^0.3–10^1.3, a ratio of 10^3.5–10^5.6.
  - abs: 10^4.0–10^4.6, a ratio of 10^2.7–10^4.3.
- **The deeper cliff explains part of that gap.** At a cliff, each unit of S recombines more as the cliff deepens.
  Along the As cell's Voc(T) ridge, S rises ~1.3 decades per 0.1 eV shallower, reaching 10^3.6 at dEc −0.10 eV
  (`ident/ridge_points.csv`). That point is excluded by the As cell's Voc(T).
  - At the same −0.10 eV cliff, the Cu/ZnO x = 0 interface would be ~10^1.2–10^2.3 times more recombination-active
    (kscale), or ~10^0.4–10^1.0 times (abs). That is less than 10^4.
- **Is the paradox "same physics, different interface quality"? Yes, with that refinement.**
  - One interface-state model with the same formalism covers both cells.
  - The As cell has a *less* favourable offset (a deeper cliff) but a far cleaner interface, and the cleaner interface
    wins.
  - Doping is not the explanation (section 5).
  - Pandey's TRPL agrees: decays are fastest at x = 0.
- **Caveat.** The two S values come from different stacks and fits: graded As absorber with NA 1e16–3e16, τ 100 ns and
  φ_b 0.50, against Cu absorber with NA 2e14–1e15 and τ 30 ns. Both are effective two-node parameters, correlated
  with dEc, τ and φ_b.

## 4. x = 0 J-V at 300, 250 and 225 K (`oneS_lowT.png`, `oneS_lowT.csv`)

**Temperature model.** The absorber gap shifts by −0.4 meV/K, split half and half between the band edges. Buffer, FTO
and back metal are fixed in absolute energy, and Nc and Nv scale as T^1.5. The 300 K point from this builder matches
the grid (733 mV).

**Kscale best (φ_b 0.35, NA 2e14, S 1e5, Rs 2.3):**

| Cell | 300 K | 250 K | 225 K | Voc(T→0) from 3 T |
|---|---|---|---|---|
| x = 0 | 733 mV, FF 67.7% | 846 mV, FF 68.9% | 898 mV, FF 67.5% | 1.40 eV |
| x = 0.15 | 863 mV, FF 74.8% | 982 mV, FF 75.8% | 1028 mV, FF 75.0% | 1.53 eV |

- **The only distortion is forward-bias roll-over beyond Voc** from the 0.35 eV back barrier. The slope ratio at Voc
  + 0.2 V against Voc is:
  - x = 0: 1.32 at 300 K, 0.23 at 250 K, 0.06 at 225 K.
  - x = 0.15: 1.33, 0.37 and 0.08.
- **No S-shape in the power quadrant at any temperature.** FF does not fall.
- **The roll-over sets in about 25 K earlier for x = 0, but both cells show it.**
- **Pandey's pronounced x = 0 kink just below room temperature,** and its absence with Mg, is **not reproduced.** A
  photocurrent-blocking kink needs a barrier in the collection path, which a −0.10 eV cliff does not provide.
- **The Voc(T) intercepts follow Pandey qualitatively:** x = 0 lies ~0.14 eV below x = 0.15, because its Ea is the
  interface gap.
- **The abs-Jsc best (φ_b 0.50) is disfavoured by J-V-T.** It shows roll-over already at 300 K in both cells, with
  Voc(T) saturating (−0.9 mV/K, intercepts 1.00 and 1.14 eV). That contradicts the Mg cells' Voc(T) extrapolating
  near the gap.

## 5. NA at fixed S (S 1e5, τ 30 ns, φ_b 0.35, ND 1e15, Rs 2.3; `oneS_NAscan.csv`)

Voc in mV:

| NA (cm⁻³) | 2e14 | 1e15 | 3e15 | 1e16 | 3e16 |
|---|---|---|---|---|---|
| x = 0 | 733 | 705 | 662 | 563 | 661 |
| x = 0.10 | 853 | 860 | 844 | 758 | 867 |
| x = 0.15 | 863 | 877 | 876 | 849 | 960 |
| x = 0.20 | 864 | 881 | 888 | 931 | 984 |
| x = 0.25 | 865 | 883 | 897 | 944 | 986 |

- **NA matters a lot at fixed S, and not monotonically.** The dip at 1e16 for x ≤ 0.15 is numerically converged: a 2×
  finer mesh with dV 0.005 V reproduces it within 0.1 mV.
- **At the Cu-cell S, As-level doping makes the ZnO (x = 0) cell worse:** 563–661 mV against 733 mV.
- **So the As cell's 875 mV on ZnO cannot come from doping at the Cu-cell S.** It needs the low S. This was scanned at
  ND_MZO 1e15 only.

## Files

| File | What it is |
|---|---|
| `oneS.py` | `run` (main grid), `run ext` (refinement), `lowT`, `nascan`. |
| `curves/` | One internal-voltage J-V per cell and parameter set. |
| `lowT/` | 300, 250 and 225 K J-V curves. |
| `analyze.py` | `oneS_fits.csv`, `oneS_profiles.csv`, `oneS_summary.csv`, `oneS_fits.png`. |
| `post.py` | `oneS_lowT.csv`, `oneS_lowT.png`, `oneS_NAscan.csv`. |

Run with `../../../.venv/bin/python <script>` from this folder. Every run is single-process and resumable, and each
curve is written atomically.
