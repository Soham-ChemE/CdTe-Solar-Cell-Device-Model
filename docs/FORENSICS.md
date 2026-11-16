# Forensics: re-running the original PR 2 SCAPS study (Phase 1)

"PR 2" is the project folder of the 2025 capstone study, archived with its correction in [`archive/2025-capstone/`](../archive/2025-capstone/README.md).

Run on 2026-11-15 with SCAPS 3.3.11 under Wine on macOS. Inputs are the 12 original `.def` files, unchanged. The voltage step is 0.02 V, the same as the original sweeps.

- Script: `forensics/run_forensics.py`
- Raw SCAPS output: `scaps/results/F_*.iv` (written locally when the script runs; SCAPS input and output files are not redistributed in this repository, see the README)
- Merged table: `forensics/forensics_results.csv`
- Reported values, read from the PR 2 spreadsheets and drafts: `forensics/reported_values.csv`

Every output file was checked against the input file it records, so a stale result cannot pass unnoticed. Rebuild the tables with `forensics/make_report.py`.

## Summary

1. **Most of the raw data is genuine.** These re-run exactly from the saved files: seven of the ten transport-layer sweeps (C60, Cs2BiAgI6, PC16BM, PCBM, Sb2Se3, TiO2, WS2), the back-contact metal table and the temperature table.
2. **The paper's Table 2 does not match the data for six layers.**
   - WS2 and PCBM: 26.07% and 25.33% reported, but their own files and spreadsheets give about 0.25%.
   - WO3: 7.37% reported, but its sweep gives 0.16% at 2 µm.
   - C60: 26.59% reported, but the file gives 27.50%.
   - Cu2O and CuO: the reported values match the spreadsheets but cannot be reproduced from the saved files (18.5% and 0.4% on re-run). The files were changed after those spreadsheets were made.
3. **In 7 of the 10 devices the "ETL" is the absorber.** Their layer named "CdTe" is 10 nm of CdS-like material. Switching off the "ETL" absorption removes 86–100% of the current (table D).
4. **The headline device breaks a basic physics limit.** With a declared CdTe band gap of 1.6 eV, the most current any cell can collect is 25.27 mA/cm² (detailed balance, from the SCAPS AM1.5G file; `physics/sq_limit.py`). The device reports 25.96 mA/cm², which is possible only because every layer uses CdTe's absorption data, extending below the declared gap.
5. **The metal contact, not a junction, sets the voltage.** Across metals, Voc follows the metal work function one-for-one (Voc ≈ Φm − 4.0 V) until it saturates near 1.23 V. That is what a cell with an undoped absorber and no real p-n junction does.
6. **Undoing the setup errors takes 27.99% to 18.2%** (table E, figure `figures/forensics_fix_waterfall.png`):
   - The band-gap fix alone costs 2.4 points.
   - Restoring a realistic CdTe defect, the one in the published SCAPS CdTe baseline, costs the most.
   - The doping fix changes almost nothing, because at NA 2e14 cm⁻³ the 1.75 µm absorber is still nearly fully depleted.
7. **With the physics corrected, the Cs2BiAgI6 layer lowers efficiency.** The same corrected cell without it gives 18.9%, against 18.2% with it.
8. **The team's own earlier baseline was realistic.** `CdTe-base-L1234_Correct[1].def` (5 Nov 2024) kept CdTe defects and gives 20.5%. The defects were removed in the later "FINAL" files.
9. **An additional error is not yet corrected.** The ZnSe layer uses CdS's absorption file (`CdS-base.abs`, 2.4 eV edge) instead of ZnSe data (about 2.7 eV). It is fixed in Phase 3.

## Limits of this analysis

The 18.2% is not a calibrated result. It still has these simplifications:

- one representative bulk defect, with no interface defects
- an ideal 5.55 eV nickel contact, where real CdTe back contacts show barriers of a few tenths of an eV
- ZnSe still using CdS absorption data
- no series or shunt resistance

Phases 2 and 3 replace these with calibrated, sourced inputs. Its role here is only to show the size and direction of each setup error.

## A. Transport-layer sweeps: paper vs spreadsheet vs re-run

Values at 2 µm. The paper column is Table 2 of the drafts. The spreadsheet column is the material's own `DATA POINTS` file. The re-run is the original `.def` file run again in SCAPS 3.3.11.

| Layer | Paper eta % | Spreadsheet eta % | Re-run eta % | Re-run Jsc mA/cm² | Re-run Voc V | Largest gap, re-run vs spreadsheet (eta points) | Verdict |
|---|---|---|---|---|---|---|---|
| C60 | 26.59 | 27.5 | 27.5 | 25.43 | 1.229 | 0.000 | file reproduces spreadsheet; paper value NOT supported |
| Cs2BiAgI6 | 27.99 | 27.99 | 27.99 | 25.96 | 1.207 | 0.000 | file reproduces spreadsheet; paper matches |
| Cu2O | 22.63 | 22.63 | 18.49 | 25.11 | 1.776 | 4.140 | file does NOT reproduce spreadsheet; paper value NOT supported |
| CuO | 20.56 | 20.56 | 0.4215 | 3.144 | 0.7167 | 20.136 | file does NOT reproduce spreadsheet; paper value NOT supported |
| PC16BM | 23.41 | 23.41 | 23.41 | 25.22 | 1.066 | 0.000 | file reproduces spreadsheet; paper matches |
| PCBM | 25.33 | 0.2455 | 0.2455 | 0.283 | 0.9965 | 0.000 | file reproduces spreadsheet; paper value NOT supported |
| Sb2Se3 | 20.50 | 20.5 | 20.5 | 25.55 | 0.937 | 0.000 | file reproduces spreadsheet; paper matches |
| TiO2 | 13.99 | 13.99 | 13.99 | 19.33 | 1.05 | 0.000 | file reproduces spreadsheet; paper matches |
| WO3 | 7.37 | 0.1643 | 0.1637 | 0.2138 | 1.154 | 0.118 | file does NOT reproduce spreadsheet; paper value NOT supported |
| WS2 | 26.07 | 0.2453 | 0.2453 | 0.2737 | 1.023 | 0.000 | file reproduces spreadsheet; paper value NOT supported |

Earlier PR 2 files, run as saved:

| File | Voc V | Jsc mA/cm² | FF % | eta % | J_SRH at 0 V (mA/cm²) |
|---|---|---|---|---|---|
| WS2 base with defects (5 Nov 2024) | 1.041 | 25.77 | 76.55 | 20.53 | 0.0865 |
| WS2 base (23 Sep 2024) | 1.889 | 0.1544 | 91.53 | 0.2669 | 0 |

## B. Back-contact metals (Cs2BiAgI6 device, 2 µm)

| Metal | Work function eV | Reported eta % | Re-run eta % | Re-run Voc V |
|---|---|---|---|---|
| Al | 4.30 | 5.26 | 5.26 | 0.2945 |
| Cu | 4.60 | 12.43 | 12.43 | 0.5945 |
| Fe | 4.80 | 17.35 | 17.35 | 0.7945 |
| C | 5.00 | 22.33 | 22.33 | 0.9943 |
| Au | 5.10 | 24.67 | 24.67 | 1.0876 |
| W | 5.20 | 25.72 | 25.72 | 1.1280 |
| Ni | 5.55 | 27.99 | 27.99 | 1.2075 |
| Pt | 5.70 | 28.44 | 28.44 | 1.2296 |
| Se | 5.90 | 28.45 | 28.45 | 1.2303 |

## C. Temperature (Cs2BiAgI6 device, 2 µm)

| T (K) | Re-run Voc V | Re-run Jsc mA/cm² | Re-run FF % | Re-run eta % |
|---|---|---|---|---|
| 300 | 1.2075 | 25.962 | 89.28 | 27.988 |
| 320 | 1.1750 | 25.962 | 88.55 | 27.012 |
| 340 | 1.1422 | 25.962 | 87.78 | 26.031 |
| 360 | 1.1087 | 25.962 | 87.02 | 25.047 |
| 380 | 1.0752 | 25.962 | 86.19 | 24.061 |
| 400 | 1.0415 | 25.962 | 85.33 | 23.073 |

## D. Which layer absorbs the light?

The "ETL" (layer 1) has its absorption switched off. Everything else is unchanged. Values at 2 µm.

| Device | Jsc as saved mA/cm² | Jsc, layer-1 absorption off | Drop |
|---|---|---|---|
| C60 | 25.43 | 3.42 | 87% |
| Cs2BiAgI6 | 25.96 | 25.43 | 2% |
| Cu2O | 25.11 | 3.46 | 86% |
| TiO2 | 19.33 | 0.00 | 100% |

## E. Undoing the setup errors in the 27.99% device

| Step | Voc V | Jsc mA/cm² | FF % | eta % | J_SRH at 0 V |
|---|---|---|---|---|---|
| As saved (PR 2) | 1.2075 | 25.962 | 89.28 | 27.99 | 0 |
| *One fix at a time* | | | | | |
| CdTe band gap 1.6 to 1.5 eV | 1.1295 | 25.962 | 87.36 | 25.62 | 0 |
| CdTe made p-type (NA 2e14 cm⁻³) | 1.2075 | 25.961 | 89.30 | 27.99 | 0 |
| Cs2BiAgI6 given its own absorption | 1.2070 | 25.448 | 89.29 | 27.43 | 0 |
| CdTe bulk defect added (Gloeckler baseline) | 1.1330 | 25.929 | 77.10 | 22.65 | 0.0336 |
| *Fixes stacked* | | | | | |
| + CdTe band gap 1.6 to 1.5 eV | 1.1295 | 25.962 | 87.36 | 25.62 | 0 |
| + CdTe made p-type (NA 2e14 cm⁻³) | 1.1295 | 25.962 | 87.42 | 25.64 | 0 |
| + Cs2BiAgI6 given its own absorption | 1.1289 | 25.449 | 87.43 | 25.12 | 0 |
| + CdTe bulk defect added (Gloeckler baseline) | 1.0117 | 25.417 | 70.72 | 18.18 | 0.0318 |
| All fixes, Cs2BiAgI6 layer removed | 0.9867 | 25.400 | 75.29 | 18.87 | 0.0289 |

## Figures

- `figures/forensics_reported_vs_rerun.png`: paper Table 2 against a re-run of each file.
- `figures/forensics_fix_waterfall.png`: the 27.99% device as the setup errors are undone.
