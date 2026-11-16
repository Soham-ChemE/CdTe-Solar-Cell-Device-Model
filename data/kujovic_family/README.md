# Calibration data: Loughborough / First Solar ZnO and CeZnO buffers on As-doped CdSeTe/CdTe

Built on 2026-11-15 for the SCAPS-1D study of why a highly resistive ZnO buffer reaches 21.4%. Every number here is either printed by the authors or read from the vector drawing of one of their figures. Nothing is estimated or filled in. A blank cell means the value is not reported.

The figure data in `curves/` are read from the published figures and are the best available copy of the measurements. For the thesis figures those files hold the plotted data points themselves.

## Sources

| ID | Reference | Open copy | Licence | Local file (not redistributed) |
|---|---|---|---|---|
| S1 | L. Kujovic, X. Liu, A. Abbas, L. O. Jones, A. M. Law, M. Togay, K. M. Curson, K. L. Barth, J. W. Bowers, J. M. Walls, O. Oklobia, D. A. Lamb, S. J. C. Irvine, W. Zhang, C. Lee, T. Nagle, D. Lu, G. Xiong, "Achieving 21.4% efficient CdSeTe/CdTe solar cells using highly resistive intrinsic ZnO buffer layers", *Adv. Funct. Mater.* 34, 2312528 (2024), doi:10.1002/adfm.202312528 | Loughborough repository, figshare article 24902478 | CC BY 4.0 | `pdfs/S1_kujovic2024_AFM_21p4.pdf` |
| S2 | L. Kujovic et al. (same 18 authors as S1), "Development of ZnO buffer layers for As-doped CdSeTe/CdTe solar cells with efficiency exceeding 20%", *Adv. Mater. Technol.* 2025, 2401364, doi:10.1002/admt.202401364 | figshare 28695698. Supporting information: figshare 29269427, doi:10.17028/rd.lboro.29269427.v1 | CC BY 4.0 | `pdfs/S2_kujovic2025_AMT_ZnO_temperature.pdf`, `pdfs/S2_SI_kujovic2025_AMT_suppmat.docx` |
| S3 | L. Kujovic, X. Liu, Z. Zhou, S. Robertson, A. Abbas, M. Togay, S. E. Machin, J. Kenyon, Z. Elsayed, K. M. Curson, C. Llewelyn, D. A. Lamb, S. J. C. Irvine, W. Zhang, C. Lee, T. Nagle, D. Lu, G. Xiong, J. W. Bowers, J. M. Walls, "Improved Voc using Ce-alloyed ZnO buffer layers in thin film CdSeTe/CdTe solar cells", *J. Phys. Energy* 8, 025017 (2026), doi:10.1088/2515-7655/ae7760 | figshare 32911925. Supplementary: figshare 32957420 | CC BY 4.0 | `pdfs/S3_kujovic2026_JPhysEnergy_CeZnO.pdf`, `pdfs/S3_SI_kujovic2026_JPhysEnergy_CeZnO_supp.pdf` |
| S4 | L. Kujović, "Buffer layers for high efficiency thin film CdSeTe/CdTe solar cells", PhD thesis, Loughborough University (submitted August 2025), doi:10.26174/thesis.lboro.30724235.v1 | figshare 30724235 | **CC BY-NC-ND 4.0** | `pdfs/S4_kujovic_PhD_thesis_2025.pdf` |
| X1 | M. Togay, L. Kujovic, A. Abbas, K. M. Curson, L. O. Jones, R. D. Ellis, M. Bliss, K. L. Barth, J. W. Bowers, J. M. Walls, "The effect of annealing and CdCl2 activation on the electrical properties of thin film ZnO buffer layers for CdSeTe/CdTe solar cells", *J. Phys. Energy* (2025), doi:10.1088/2515-7655/adfd87 (accepted manuscript) | figshare 29958428 | CC BY 4.0 | `pdfs/X1_togay2025_JPhysEnergy_ZnO_Hall_AM.pdf` |
| X2 | X. Liu, L. Jones, L. Kujovic, N. Hunwick, L. Infante-Ortega, M. Walls, T. Shimpi, W. Sampath, K. Barth, S. Jones, O. Oklobia, S. Irvine, "Measurement of band alignment between ZnO based front emitters and CdCl2 treated CdSeTe/CdTe absorbers", 2022 IEEE 49th PVSC, pp. 387-389, doi:10.1109/PVSC48317.2022.9938648 (accepted manuscript) | figshare 19636824 | © IEEE, personal use only | `pdfs/X2_PVSC2022_band_alignment_ZnO_CdSeTe_AM.pdf` |

- All files were downloaded with curl from the `download_url` of the figshare API record.
- `pdfs/S1_...pdf` is byte-identical to `../kujovic2024/kujovic2024_AFM_21p4.pdf`.
- X1 and X2 are included because they hold the only Hall data that resolve ZnO carrier density and the only measured ZnO/CdSeTe band offset in this family. The thesis cites X2 as its band-offset source (ref. 136).
- Only facts and numbers are taken from X2; the PDF is kept locally and not redistributed.
- **Thesis licence (NC-ND).** The `curves/S4_*_overlay.png` images contain crops of thesis figures. They are verification aids. They are not redistributed in this public repository. The numbers themselves are facts.
- Same-family items found but not used, all on figshare:
  - 30533198: PVSC 2025, bilayer SnO2/ZnO, 21.7%.
  - 30929432: Sol. Energy Mater. Sol. Cells 297, 114139 (2026), the same bilayer work.
  - 30023332: PVSC 2025, Togay, ZnO electrical properties and device performance.
  - 27862176: PVSC 2024, Togay, PDL Hall on resistive ZnO.
  - 27890178 and 24878418: the anti-reflection coating papers.
  - The PVSC 2024 co-sputtered CeZnO paper (doi:10.1109/PVSC57443.2024.10749479) is not in the repository.

**Page references.**
- "PDF p." means the page of the downloaded PDF.
- S3's PDF has an IOP cover page, so S3 PDF page = journal page + 1.
- For S4 the printed page is 25 lower than the PDF page in the main chapters (Table 3.1 is on PDF p.75, printed p.50).

## Files

| File | Content |
|---|---|
| `devices.csv` | 107 rows, one per device or condition. Includes best cells, author-stated maxima, and box-plot medians and means for every series. |
| `params_from_authors.csv` | 108 rows: the authors' full SCAPS parameter table and every measured material, interface and process parameter, each with its location. |
| `curves/` | 105 data files listed in `curves/index.csv` and the validation outputs (`checks_against_reported_values.csv`, `S1_validation.json`, `S1_raster_check.json`, `S1_vs_S4_accuracy.json`, `S3_vs_S4_boxplot_crosscheck.json`, `S4_validation.json`). |
| `scripts/` | The digitiser and table builders. `sh scripts/run_all.sh <python>` rebuilds everything from `pdfs/` in about 30 s. It needs pymupdf, numpy, scipy and matplotlib. |
| `pdfs/` | Source documents (not redistributed; download them from the open copies listed under Sources). |

### devices.csv columns

| Column | Meaning |
|---|---|
| `source_id`, `year` | Paper the value belongs to. Box plots of S2 and S3 are read from the identical vector copies in the thesis; `where` says so. |
| `buffer` | ZnO, CeZnO, CeZnO (co-sputtered), SnO2 (sputtered, 500 C) or SnO2/ZnO bilayer. |
| `buffer_thickness_nm`, `buffer_dep_temp_C` | For bilayers these are "SnO2/ZnO" pairs. "CVD" marks commercial NSG SnO2. |
| `Ce_fraction` | x in CexZn1-xO. |
| `ARC` | y only for the 21.44% cell, which has the six-layer SiO2/ZrO2 coating. |
| `Voc_mV`, `Jsc_mA_cm2`, `FF_pct`, `eta_pct` | Standard J-V figures of merit. |
| `Rs`, `Rsh`, `J0`, `n` | Rs and Rsh in Ω cm², J0 in mA cm⁻². These come from the authors' single-diode Lambert-W fit of the light J-V. In the S4 Table 6.2 rows, J0 and n come from a dark J-V fit. |
| `NA_cm3` | C-V hole density at 0 V and 40 kHz. |
| `value_type` | One of the five types defined after this table. |
| `where` | Location of the value in the source. |
| `series`, `n_cells`, `notes` | Batch name, number of cells behind the statistic, and caveats. |

`value_type` values:
- `best`: one cell, as reported.
- `median` or `mean`: statistic over the 12 cells of one 5×5 cm substrate, read from the box plot.
- `max_per_parameter`: the authors' "highest Voc, Jsc, FF and efficiency". These are maxima taken parameter by parameter, not one cell; see the caveats section.
- `typical`: an author-selected average cell.

## How the figure data were extracted

**Every figure in S1, S3 and the thesis is vector graphics, so no pixel guessing was needed.**
- S2's figures are embedded raster images, so S2 data are read from the thesis copies (Ch. 4). Those copies reproduce S2 Table 1 and the S2 text values to within their rounding (see the checks below).
- **Axis calibration.** The major tick marks are found as short strokes or thin rectangles touching the axis line. Their centres are paired with the tick labels:
  - Thesis: labels are real text, including 10^n exponents.
  - Journal: labels are glyph outlines, so the values were typed in.
  - A least-squares linear (log10 for log axes) map converts page points to data. The residual is at most 0.026 pt for S1 and at most 0.043 pt for the thesis (median 0.021 pt).
- **Thesis curves** are stroked polylines. Their vertices are the plotted data points, written out unchanged. Dashed dark J-V curves give the end points of each dash. Markers give their centres.
- **Journal curves (S1 Fig. 3, S3)** are exported as filled outlines of the stroke, about 0.44 pt wide. The centreline is recovered in five steps:
  1. Slice the outline vertically where the curve is shallow and horizontally where it is steep, and take the midpoint of each crossing pair. This is exact for straight segments.
  2. Re-slice along the local normal (`vecfig.refine_normal`).
  3. Drop isolated spurious pairs (`despike`).
  4. Trim the round end caps by half the stroke width.
  5. Simplify with Ramer-Douglas-Peucker at 0.02 pt.

  The S1 EQE vertices sit on a 10 nm wavelength grid: the two-sided fits agree to a median of 0.005 EQE-% and the thesis vertices are within 0.16 nm of the grid. The EQE is therefore written at 320, 330, ..., 960 nm, each value fitted from the straight segments on both sides of the grid point.
- **Box plots** are read from geometry:
  - Q1 and Q3: the filled box edges.
  - Median: the full-width bar.
  - Whisker ends: the caps.
  - Mean: the open square, or open circle in Fig. A.1.
  - Outliers: the filled diamonds.

  Every box has exactly one median bar and one mean marker. Whiskers follow Origin's convention: the furthest cell within 1.5 IQR. These are exact readings, not estimates from the picture.
- **Independent raster check.** `scripts/s1_raster_check.py` renders S1 at 600 dpi, masks the curve colour, takes the centre of each run of curve pixels and applies the same tick calibration. This is the pixel digitiser that was requested.
- **Hidden points.** Points the PDF contains outside the plotted axes, hidden by the plot clip, are kept and flagged with `outside_plotted_axes = 1`.
- **Overlays.** Every data file was checked against an overlay of the extracted points on a render of the original panel (`scripts/`; the overlay images contain crops of the source figures and are not redistributed).

### Digitisation accuracy

| Test | Result |
|---|---|
| S1 journal centreline vs exact thesis vertices of the same 21.44% J-V | ΔJ ≤ 0.0006 mA cm⁻² on the flat part; ΔV ≤ 0.010 mV on the steep part |
| Same, EQE on the 10 nm grid | median 0.003, max 0.27 EQE-%. The maximum is on the steepest edges and equals 0.1 nm of wavelength. |
| Same, C-V N_A(W) | ≤ 0.015% |
| Same, Voc(T) markers | ≤ 0.006 K, ≤ 1e-5 V |
| 600 dpi raster vs vector, S1 Fig. 3a / 3b / 3c | median 0.041 / 0.025 / 0.041 pt, p95 0.09 / 0.07 / 0.08 pt. In data units 0.04 pt ≈ 0.4 mV, 0.03 mA cm⁻², 0.04 EQE-%. |
| Raster vs vector box medians, S1 Fig. 2 | ≤ 0.011 mV, ≤ 0.003 % |
| S1 Fig. 2 vs thesis Fig. 3.2; S3 Fig. 2 vs thesis Fig. 5.9 | ≤ 0.0006 and ≤ 0.0009 in any statistic. Same data, independent renderings. |

**Digitisation error is far below the rounding of the published numbers.** The limiting uncertainty is the data and the authors' rounding, not the reading.

### Checks against values stated in the text

All 121 checks are in `curves/checks_against_reported_values.csv`. Key ones:

| Quantity (21.44% cell, S1) | Stated | From plotted curve | Raster digitiser |
|---|---|---|---|
| Jsc (mA cm⁻²) | 30.43 | 30.405 | 30.456 |
| Voc (mV) | 875.5 | 875.16 | 875.77 |
| FF (%) | 80.48 | 80.59 | 80.53 |
| η (%) | 21.44 | 21.444 | 21.48 |
| N_A at 0 V (cm⁻³) | ≈2.1e16 | 2.103e16 | 2.094e16 |
| Ea from Voc(T→0) (eV) | 1.36 | 1.3587 (plotted fit line); 1.3572 (refit of the 315-355 K markers) | 1.3593 |
| Absorber Eg from the −dEQE/dλ peak (eV) | 1.41 | 1.4095 (879.9 nm) | n/a |

- The thesis vertices of the same J-V give 30.405 / 875.16 / 80.59 / 21.445. The −0.025 mA cm⁻², −0.34 mV and +0.11% offsets from the printed values are therefore in the plotted data itself. They are probably the measurement software's fitted Jsc and Voc, not a digitising error.
- For SCAPS targets use the printed values, with about ±0.03 mA cm⁻², ±0.4 mV and ±0.1% FF as the data-versus-report spread.
- The other J-V curves agree with their tables to within the printed rounding:
  - The six S2 best cells (Table 1) and the eight S3 best cells (Table 2), e.g. S3 3% CeZnO 50 nm: 20.156 / 854.3 / 29.70 / 79.45 vs 20.15 / 854.2 / 29.70 / 79.43.
  - The thesis Fig. 3.10 SCAPS simulation: 21.36% / 872.3 mV / 30.81 / 79.48 vs 21.4 / 872 / 30.8 / 79.6.
- **Zero-bias N_A** matches S2 (1.798e16 vs 1.8e16) and all eight S3 Table 3 values (within 0.5%).
- **S2 interface defect densities** match the text (1.917e14, 8.569e13, 1.978e15 and 2.065e15 vs 1.92e14, 8.57e13 and 1.98-2.07e15).
- **S2 box plots.** The digitised medians match the thesis text: 100 C gives 20.02%, 868.96 mV and 29.275 mA cm⁻² vs 20.0%, 869 and 29.3. The 100 C and 500 C mean-efficiency gains come out at 2.40% and 0.56% vs the stated 2.41% and 0.57%.

## Caveats that matter for the model

1. **The "best" 50 nm values in S1 (21.23%, 883 mV, 30.04 mA cm⁻², 80.73%) are not one cell.**
   - 0.883 V × 30.04 mA cm⁻² × 0.8073 = 21.41%, not 21.23%.
   - They are the maxima of each parameter, equal to the Fig. 2 whisker tops.
   - Likewise S2's "29.77 mA cm⁻²" and "80.25%" at 100 C are not the 20.74% cell, which has 29.60 mA cm⁻² and 79.90%.
2. **The 21.44% champion has no reported Rs, Rsh, J0 or n.** S1 gives none. The thesis tabulates diode parameters only for the S2, S3 and Ch. 6 cells.
3. **Box statistics are over 12 cells on one substrate.** The S1 caption says "five devices, which have 12 cells each", but the S1 Methods give n = 12 per box. The thesis (PDF p.68) says one substrate per thickness. Appendix A (Fig. A.1, in `devices.csv`) repeats the thickness series on thicker-FTO substrates.
   - At 75 nm the S1 FF mean (78.60%) lies below the lower whisker (79.15%), with no outlier drawn. One cell is below the 76% axis limit; Origin did not draw it.
4. **Two setups give different room-temperature Voc.** On the temperature stage the room-temperature Voc is about 0.848 V (Fig. 3d markers at 297-298 K), against 875.5 mV under the AM1.5G simulator. Use Fig. 3d for the slope and intercept, not the absolute Voc.
5. **The SCAPS parameter set is incomplete.** S4 Table 3.1 and the S1 Methods give: thicknesses, gaps, mobilities, dopings, bulk N_t, 10 ns lifetime, 1e9 cm⁻² acceptor interface defects (S = 1e4 cm/s) and CBO +0.1 eV. They do not give:
   - electron affinities;
   - permittivities;
   - Nc and Nv;
   - thermal velocities;
   - defect energies or capture cross-sections;
   - contact work functions or back-barrier;
   - optical data.

   The model uses Eg(ZnO) = 3.4 eV, but the measured Tauc gap is 3.2-3.26 eV (3.54 eV in X2's 150 nm film).
6. **The band offset conflicts across sources.**
   - The SCAPS model assumes a +0.1 eV spike, and S1 says the CBO was still to be measured by UPS.
   - The thesis never measured it. Its conclusions list it as future work, and S3 says "direct CBO measurements will be needed".
   - The only measurement is X2: XPS/Kraut on separate ZnO and CdSeTe films, giving −0.32 eV (CSU CSS CdSeTe) and −0.22 eV (Swansea MOCVD CdSeTe), both cliffs.
   - The thesis band diagram (Fig. 5.4) uses CBM(ZnO) = −4.62 eV and CBM(CdSeTe) = −4.40 eV, which also implies a −0.22 eV cliff.
7. **ZnO doping is undetermined in the device.**
   - As-deposited 50-500 nm films give no PDL Hall signal (n < 1e12 cm⁻³; S1, S2, S4 Ch. 3/5/7).
   - X1 shows that thicker films deposited at 100 C and 500 C reach about 1e16-1e17 cm⁻³ after vacuum anneal plus CdCl2. 22 C films still give no signal.
   - X1 also sees oxygen diffusing from a 22 C ZnO buffer into CdSeTe in a device. S1 reports no evidence of oxygen depletion.
   - The "1e11 cm⁻³ ZnO" model input is the authors' assumption.
8. **Chlorine at the interface differs by batch.** S1 and S2 find no Cl at the ZnO/CdSeTe interface for 22 C and 100 C ZnO. S3 does see Cl at its ZnO and CeZnO interfaces.
9. **Lifetime data come only from SnO2-based devices.** TRPL exists only for SnO2 (τ2 = 7.7 ns) and SnO2/10 nm ZnO (8.4 ns) devices (thesis Ch. 6). There is no TRPL for a ZnO-only device. The CL surface recombination velocities (265 vs 26 cm/s) are a relative metric by the authors' own statement.
10. **Interface defect density is in cm⁻³.** It is the C-V minus DLCP carrier density at 0 V, in cm⁻³ as printed, not an areal density.
11. **Solar simulator class differs.** It is AAA in S1 and ABB in the thesis and S3.

## Not available in the published record

- **Raw measurement files:** J-V, dark J-V, EQE, C-V and DLCP profiles, and full JVT curves. The thesis vertices are the plotted points, which may be decimated from the instrument files. The S1 J-V has 219 plotted points from −202 to 928 mV: 6.6 mV steps below 600 mV, 6.0 mV to 800 mV and about 2 mV near Voc. The EQE is on a 10 nm grid.
- Per-cell data behind every box plot.
- Diode parameters (Rs, Rsh, J0, n) of the 21.44% cell.
- **Unmeasured quantities:**
  - a measured CBO for the device ZnO/CdSeTe stack, by UPS or XPS;
  - the ZnO carrier density in a finished device;
  - TRPL lifetime of ZnO-buffered cells;
  - the absorber Se profile;
  - back-contact parameters;
  - carrier density and sheet resistance of the actual NSG FTO substrate (only TEC 12D was measured, at 12.19 Ω/sq).
- The authors' SCAPS definition file (.def) with the missing parameters listed in caveat 5.
- DLCP-only N_A for the ZnO devices. Only the C-V minus DLCP differences are given for ZnO; DLCP values exist only for the SnO2 devices.
- The CeZnO CBO, and the PVSC 2024 and PVSC 2023 conference papers (not in the open repository).
