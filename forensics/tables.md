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
