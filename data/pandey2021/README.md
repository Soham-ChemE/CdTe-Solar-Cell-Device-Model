# Calibration set: Pandey et al. 2021, MgZnO Mg-fraction series on CdSeTe/CdTe

R. Pandey, A. Munshi, T. Shimpi, A. Shah, A. Bothwell, D. Kuciauskas, J. R. Sites, "CdTe-based solar cells with variation in the Mg concentration of the MgZnO emitter" (Colorado State University and NREL, accepted manuscript dated 2021-02-02). Public-access copy: OSTI https://www.osti.gov/pages/servlets/purl/3484939. The PDF and its extracted text are kept locally and are not redistributed.

## Device (paper's Experimental section)

- **Stack:** Tec10 glass (FTO) / 100 nm MgxZn1-xO, RF-sputtered at room temperature in Ar/O2 97/3 / 0.5 µm CdSeTe + 3 µm CdTe, both CSS at 500 °C / CdCl2 at 450 °C / CuCl at 200 °C (Cu doping) / 30 nm evaporated Te / C/Ni paint.
- **Cell size:** 0.8 cm x 0.8 cm cells, 25 per composition.
- **Caveat: this absorber is Cu-doped, not As-doped.** The series tests front-buffer physics. It does not test group-V absorbers directly.

## Data

- `pandey2021_mzo_series.csv`. The band energies and offsets come from Table 1 (XPS, Kraut method); the CdSeTe VBM is 5.68 eV and its gap 1.4 eV. Average and best J-V parameters are read from the Fig. 2 insets.
- **Consistency check:** average Voc × Jsc × FF reproduces the average efficiency within rounding, e.g. 0.846 × 27.8 × 0.745 = 17.5% at x = 0.15.
- **Other measured values (text):**
  - TRPL recombination time ≈ 30 ns at x = 0.15 and ≈ 60 ns at x = 0.25. Decays are fastest at x = 0 and x = 0.35.
  - C-V depletion widths are about 1 µm, increasing slightly with Mg. Carrier densities are in the paper's supporting information, which is not yet retrieved.
  - PL peaks near 885 nm, consistent with a CdSeTe gap of 1.40 eV.
  - J-V-T: Voc(T → 0) extrapolates near the CdSeTe gap with Mg. Without Mg it is clearly lower, and the J-V kink is strong just below room temperature.
  - At x = 0.35, XRD shows MgZnO changing from wurtzite toward zinc-blende. The performance collapse there may be structural rather than an offset effect.

## How it is used in Option A

1. Fit on three Mg fractions.
2. Predict the other three blind before the buffer model is trusted for ZnO or ZnSe.
3. Exclude x = 0.35, or treat it separately, because of the structural change.
