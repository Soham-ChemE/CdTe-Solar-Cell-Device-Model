"""Build devices.csv, params_from_authors.csv, curves/index.csv and
curves/checks_against_reported_values.csv.

Reported numbers are typed in below with their exact location. Box-plot
statistics are read from the CSVs written by s1_extract.py and s4_extract.py.

Usage: python -I make_tables.py <kujovic_family folder>
"""
import csv
import json
import os
import sys

import numpy as np

OUT = sys.argv[1]
CUR = os.path.join(OUT, "curves")

# --------------------------------------------------------------------------- devices
COLS = ["source_id", "year", "buffer", "buffer_thickness_nm", "buffer_dep_temp_C", "Ce_fraction", "ARC",
        "Voc_mV", "Jsc_mA_cm2", "FF_pct", "eta_pct", "Rs", "Rsh", "J0", "n", "NA_cm3", "value_type", "where",
        "series", "n_cells", "notes"]
rows = []


def add(**kw):
    r = {c: "" for c in COLS}
    r.update({k: ("" if v is None else v) for k, v in kw.items()})
    rows.append(r)


# ---- S1: Kujovic et al. Adv. Funct. Mater. 34, 2312528 (2024)
add(source_id="S1", year=2024, buffer="ZnO", buffer_thickness_nm=50, buffer_dep_temp_C=22, Ce_fraction=0, ARC="y",
    Voc_mV=875.5, Jsc_mA_cm2=30.43, FF_pct=80.48, eta_pct=21.44, NA_cm3=2.1e16, value_type="best",
    where="S1 p.3 text and Fig. 3a legend (PDF p.4); N_A: S1 p.3 text, Fig. 3c (C-V, 0 V, 40 kHz)",
    series="S1 champion with MAR coating", n_cells=1,
    notes="Six-layer SiO2/ZrO2 anti-reflection coating on the glass. Rs/Rsh/J0/n not reported. "
          "Thesis Fig. 3.3 shows the same curve rounded to 876 mV / 30.4 / 80.5 / 21.4.")
add(source_id="S1", year=2024, buffer="ZnO", buffer_thickness_nm=50, buffer_dep_temp_C=22, Ce_fraction=0, ARC="n",
    Voc_mV=883, Jsc_mA_cm2=30.04, FF_pct=80.73, eta_pct=21.23, value_type="max_per_parameter",
    where="S1 p.3 text (Fig. 2a-d)", series="S1 thickness series", n_cells=12,
    notes="Highest value of each parameter at 50 nm, not one cell: 0.883 V x 30.04 mA/cm2 x 0.8073 = 21.41% "
          "not 21.23%. They equal the Fig. 2 whisker tops (digitised 21.228, 883.2, 30.039, 80.733).")

# ---- S2: Kujovic et al. Adv. Mater. Technol. 2025, 2401364
T1 = [  # temp, eta, Voc, Jsc, FF, Rs, Rsh, J0, n
    (22, 20.1, 859, 29.4, 79.4, 0.54, 3482, 9.14e-9, 1.55),
    (100, 20.74, 876.7, 29.60, 79.90, 0.42, 3346, 6.90e-9, 1.56),
    (200, 19.7, 857, 29.3, 78.5, 0.58, 1443, 6.19e-9, 1.61),
    (300, 20.0, 858, 29.7, 78.4, 0.35, 2729, 1.00e-7, 1.74),
    (400, 19.8, 859, 29.3, 78.6, 0.44, 2120, 1.56e-8, 1.59),
    (500, 20.1, 861, 29.6, 78.7, 0.36, 2545, 3.54e-8, 1.66),
]
for t, eta, voc, jsc, ff, rs, rsh, j0, n in T1:
    note = "Diode parameters from a single-diode Lambert-W fit (MATLAB) by the authors."
    where = "S2 Table 1 (PDF p.5)"
    na = None
    if t == 100:
        where = "S2 p.3-4 text (20.74%, 876.7 mV, 29.60, 79.90%) and Table 1 (PDF p.5) for Rs/Rsh/J0/n; N_A: S2 p.4 text, Fig. 4b"
        note += " Table 1 rounds this cell to 20.7/877/29.6/79.9. N_A is C-V at 0 V, 40 kHz on this cell."
        na = 1.8e16
    add(source_id="S2", year=2025, buffer="ZnO", buffer_thickness_nm=75, buffer_dep_temp_C=t, Ce_fraction=0, ARC="n",
        Voc_mV=voc, Jsc_mA_cm2=jsc, FF_pct=ff, eta_pct=eta, Rs=rs, Rsh=rsh, J0=j0, n=n, NA_cm3=na,
        value_type="best", where=where, series="S2 deposition-temperature series", n_cells=1, notes=note)
add(source_id="S2", year=2025, buffer="ZnO", buffer_thickness_nm=75, buffer_dep_temp_C=100, Ce_fraction=0, ARC="n",
    Voc_mV=876.7, Jsc_mA_cm2=29.77, FF_pct=80.25, eta_pct=20.74, value_type="max_per_parameter",
    where="S2 p.3 text (Fig. 2)", series="S2 deposition-temperature series", n_cells=12,
    notes="Highest value of each parameter at 100 C; Jsc 29.77 and FF 80.25 are not from the 20.74% cell (Table 1: "
          "29.6, 79.9). Digitised whisker/outlier maxima: 20.736, 876.67, 29.771, 80.248.")
add(source_id="S2", year=2025, buffer="ZnO", buffer_thickness_nm=75, buffer_dep_temp_C=250, Ce_fraction=0, ARC="n",
    FF_pct=80.47, value_type="max_per_parameter", where="S2 p.3 text (Fig. 2d)", series="S2 deposition-temperature series",
    n_cells=12, notes="Highest FF of the series. Digitised maximum 80.462.")
add(source_id="S2", year=2025, buffer="ZnO", buffer_thickness_nm=65, buffer_dep_temp_C=100, Ce_fraction=0, ARC="n",
    Voc_mV=858.9, FF_pct=81.06, eta_pct=20.14, value_type="max_per_parameter", where="S2 p.5 text (Fig. 6)",
    series="S2 thickness series at 100 C", n_cells=12,
    notes="Highest value of each parameter in the 40-70 nm series. Digitised maxima 20.14, 858.9, 81.06.")

# ---- S3: Kujovic et al. J. Phys. Energy 8, 025017 (2026)
T2 = [  # Ce, thickness, eta, Voc, Jsc, FF, Rs, Rsh, J0, n, NA(Table 3)
    (0.00, 50, 19.95, 840.9, 29.93, 79.27, 0.49, 3799, 1.54e-8, 1.56, 1.01e16),
    (0.00, 100, 19.81, 837.8, 29.62, 79.82, 0.38, 2585, 8.58e-9, 1.51, 1.18e16),
    (0.03, 50, 20.15, 854.2, 29.70, 79.43, 0.41, 3258, 2.25e-8, 1.61, 1.35e16),
    (0.03, 100, 19.58, 858.3, 29.36, 77.70, 0.38, 4271, 3.52e-7, 1.86, 1.34e16),
    (0.06, 50, 19.46, 844.1, 30.07, 76.68, 0.38, 3114, 1.21e-6, 1.96, 1.34e16),
    (0.06, 100, 19.08, 844.3, 29.07, 77.72, 0.55, 2690, 1.25e-7, 1.73, 1.33e16),
    (0.09, 50, 19.38, 841.0, 30.09, 76.59, 0.47, 6094, 1.21e-6, 1.95, 1.24e16),
    (0.09, 100, 18.61, 834.4, 29.60, 75.34, 0.48, 2984, 3.87e-6, 2.08, 1.28e16),
]
for ce, th, eta, voc, jsc, ff, rs, rsh, j0, n, na in T2:
    add(source_id="S3", year=2026, buffer="ZnO" if ce == 0 else "CeZnO", buffer_thickness_nm=th, buffer_dep_temp_C=22,
        Ce_fraction=ce, ARC="n", Voc_mV=voc, Jsc_mA_cm2=jsc, FF_pct=ff, eta_pct=eta, Rs=rs, Rsh=rsh, J0=j0, n=n,
        NA_cm3=na, value_type="best", where="S3 Table 2 (PDF p.7); N_A: S3 Table 3 (PDF p.8)",
        series="S3 Ce series (compound targets)", n_cells=1,
        notes="Same values in thesis Tables 5.2/5.3. N_A is C-V at 0 V, 40 kHz; the paper does not say the C-V "
              "cell is the Table 2 cell.")

# ---- S4 thesis-only data
add(source_id="S4", year=2025, buffer="ZnO", buffer_thickness_nm=65, buffer_dep_temp_C=100, Ce_fraction=0, ARC="n",
    Voc_mV=854, Jsc_mA_cm2=29.4, FF_pct=80.1, eta_pct=20.1, Rs=0.64, Rsh=4324, J0=2.32e-9, n=1.45, value_type="best",
    where="S4 thesis Fig. 6.3 legend and Table 6.1 (PDF p.124)", series="S4 Ch.6 ZnO vs SnO2", n_cells=1,
    notes="ZnO reference cell of the ZnO vs sputtered-SnO2 comparison (same absorber process).")
add(source_id="S4", year=2025, buffer="SnO2 (sputtered, 500 C)", buffer_thickness_nm="", buffer_dep_temp_C=500,
    Ce_fraction="", ARC="n", Voc_mV=833, Jsc_mA_cm2=30.2, FF_pct=78.7, eta_pct=19.8, Rs=0.63, Rsh=4567, J0=2.20e-8,
    n=1.57, value_type="best", where="S4 thesis Fig. 6.3 legend and Table 6.1 (PDF p.124)",
    series="S4 Ch.6 ZnO vs SnO2", n_cells=1,
    notes="Best of the 40-70 nm SnO2 buffers; the thesis does not say which thickness. Contrast case: conductive buffer.")
add(source_id="S4", year=2025, buffer="SnO2 (sputtered, 500 C)", buffer_thickness_nm=60, buffer_dep_temp_C=500,
    Ce_fraction="", ARC="n", Voc_mV=827, Jsc_mA_cm2=29.5, FF_pct=77.6, eta_pct=18.9, value_type="best",
    where="S4 thesis p.126 text (PDF p.126)", series="S4 Ch.6 bilayer series", n_cells=1, notes="")
add(source_id="S4", year=2025, buffer="SnO2/ZnO bilayer", buffer_thickness_nm="60/10", buffer_dep_temp_C="500/100",
    Ce_fraction=0, ARC="n", Voc_mV=841, Jsc_mA_cm2=29.8, FF_pct=79.6, eta_pct=20.0, value_type="best",
    where="S4 thesis p.126 text (PDF p.126)", series="S4 Ch.6 bilayer series", n_cells=1, notes="")
add(source_id="S4", year=2025, buffer="SnO2 (sputtered, 500 C)", buffer_thickness_nm=60, buffer_dep_temp_C=500,
    Ce_fraction="", ARC="n", Voc_mV=817, Jsc_mA_cm2=29.9, FF_pct=76.2, eta_pct=18.6, J0=2.24e-5, n=2.39,
    value_type="typical", where="S4 thesis Table 6.2 (PDF p.128)", series="S4 Ch.6 bilayer series", n_cells=1,
    notes="Author-selected average-performing cell. J0 and n from a fit of the dark J-V only (J = J0(exp(qV/nkT)-1)).")
add(source_id="S4", year=2025, buffer="SnO2/ZnO bilayer", buffer_thickness_nm="60/10", buffer_dep_temp_C="500/100",
    Ce_fraction=0, ARC="n", Voc_mV=828, Jsc_mA_cm2=30.3, FF_pct=79.2, eta_pct=19.9, J0=2.69e-7, n=1.81,
    value_type="typical", where="S4 thesis Table 6.2 (PDF p.128)", series="S4 Ch.6 bilayer series", n_cells=1,
    notes="Author-selected average-performing cell. J0 and n from a fit of the dark J-V only.")
add(source_id="S4", year=2025, buffer="SnO2/ZnO bilayer", buffer_thickness_nm="70/30", buffer_dep_temp_C="CVD/100",
    Ce_fraction=0, ARC="n", Voc_mV=882, Jsc_mA_cm2=30.3, FF_pct=81.0, eta_pct=21.7, NA_cm3=1.15e16, value_type="best",
    where="S4 thesis p.139-140 text, Fig. 6.16 (PDF p.139-140)", series="S4 Ch.6 21.7% bilayer", n_cells=1,
    notes="Commercial NSG SnO2 (~70 nm, atmospheric CVD) + 30 nm ZnO at 100 C. N_A is C-V at 0 V.")
add(source_id="S4", year=2025, buffer="SnO2/ZnO bilayer", buffer_thickness_nm="70/30", buffer_dep_temp_C="CVD/100",
    Ce_fraction=0, ARC="n", eta_pct=21.4, value_type="median", where="S4 thesis p.139 text (PDF p.139)",
    series="S4 Ch.6 21.7% bilayer", n_cells=11,
    notes="Median of the 12-cell substrate excluding one 18.0% outlier; IQR 21.2-21.5%, range 21.0-21.7%.")
add(source_id="S4", year=2025, buffer="ZnO", buffer_thickness_nm=50, buffer_dep_temp_C=22, Ce_fraction=0, ARC="n",
    eta_pct=19.5, value_type="best", where="S4 thesis p.107 text (PDF p.107)",
    series="S4 Ch.5.3.1 co-sputtered CeZnO batch", n_cells=1,
    notes="Reference ZnO cell of the co-sputtered batch (NSG TEC 15, 3.8 mm substrate). Digitised Fig. 5.5 curve gives "
          "19.48% / 841.4 mV / 28.19 mA/cm2 / 82.1% (see curves/checks_against_reported_values.csv).")
add(source_id="S4", year=2025, buffer="CeZnO (co-sputtered)", buffer_thickness_nm=50, buffer_dep_temp_C=22,
    Ce_fraction=0.050, ARC="n", eta_pct=19.2, value_type="best", where="S4 thesis p.107 text (PDF p.107)",
    series="S4 Ch.5.3.1 co-sputtered CeZnO batch", n_cells=1,
    notes="NSG TEC 15 substrate. Digitised Fig. 5.5 curve gives 19.21% / 839.5 mV / 28.26 mA/cm2 / 80.9%.")

# ---- box-plot medians and means
def boxrows(fname, key, cond, source, where, series, notes=""):
    data = {}
    for r in csv.DictReader(open(os.path.join(CUR, fname))):
        data.setdefault(r[key], {})[r["parameter"]] = r
    for lab, params in data.items():
        base = cond(lab)
        for vt in ("median", "mean"):
            out = dict(base)
            for p, col, fmt in (("Voc_mV", "Voc_mV", "%.2f"), ("Jsc_mA_cm2", "Jsc_mA_cm2", "%.3f"),
                                ("FF_pct", "FF_pct", "%.3f"), ("eta_pct", "eta_pct", "%.3f"),
                                ("Rs_ohm_cm2", "Rs", "%.3f"), ("Rsh_ohm_cm2", "Rsh", "%.0f"),
                                ("J0_mA_cm2", "J0", "%.3e"), ("n", "n", "%.3f")):
                if p in params:
                    v = float(params[p][vt])
                    out[col] = fmt % v if np.isfinite(v) else ""
            add(source_id=source, value_type=vt, where=where, series=series, n_cells=12, notes=notes, **out)


def s1cond(lab):
    return dict(year=2024, buffer="ZnO", buffer_thickness_nm=int(lab), buffer_dep_temp_C=22, Ce_fraction=0, ARC="n")


boxrows("S1_fig2_boxplots.csv", "ZnO_thickness_nm", s1cond, "S1",
        "S1 Fig. 2a-d box plots (PDF p.3), digitised from vector paths; identical to thesis Fig. 3.2 within 0.001",
        "S1 thickness series",
        "One 5x5 cm substrate (12 cells) per thickness (thesis PDF p.68). 75 nm FF mean lies below the lower whisker "
        "because one cell is below the 76% axis limit and not drawn.")


def s2cond(lab):
    return dict(year=2025, buffer="ZnO", buffer_thickness_nm=75, buffer_dep_temp_C=int(lab), Ce_fraction=0, ARC="n")


# merge Fig 2 (J-V) and Fig 3 (diode) per temperature by writing a combined temporary table
def merged(f1, f2, key):
    rows_ = list(csv.DictReader(open(os.path.join(CUR, f1)))) + list(csv.DictReader(open(os.path.join(CUR, f2))))
    tmp = os.path.join(CUR, ".merged_tmp.csv")
    with open(tmp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_[0].keys()))
        w.writeheader()
        w.writerows(rows_)
    return ".merged_tmp.csv"


boxrows(merged("S4_fig4.2_ZnO_dep_temperature_S2fig2_boxplots.csv",
               "S4_fig4.3_ZnO_dep_temperature_diode_S2fig3_boxplots.csv", "ZnO_dep_temp_C"),
        "ZnO_dep_temp_C", s2cond, "S2",
        "S2 Figs. 2 and 3 box plots (raster in the journal); read from the identical vector figures in thesis "
        "Figs. 4.2/4.3 (PDF p.85, p.87)", "S2 deposition-temperature series",
        "11 temperatures, 12 cells each, one batch. Thesis PDF p.86 states the 100 C medians as 20.0%, 869 mV, "
        "29.3 mA/cm2, the 250 C median FF as 78.9% and the 22 C median efficiency as 19.6%.")


def s2tcond(lab):
    return dict(year=2025, buffer="ZnO", buffer_thickness_nm=int(lab), buffer_dep_temp_C=100, Ce_fraction=0, ARC="n")


boxrows("S4_fig4.8_ZnO_thickness_100C_S2fig6_boxplots.csv", "ZnO_thickness_nm", s2tcond, "S2",
        "S2 Fig. 6 box plots (raster in the journal); read from the identical vector figure in thesis Fig. 4.8 (PDF p.93)",
        "S2 thickness series at 100 C", "5 thicknesses, one batch.")


def s3cond(lab):
    b, th = lab.split("/")
    ce = {"ZnO": 0, "3%CeZnO": 0.03, "6%CeZnO": 0.06, "9%CeZnO": 0.09}[b]
    return dict(year=2026, buffer="ZnO" if ce == 0 else "CeZnO", buffer_thickness_nm=int(th), buffer_dep_temp_C=22,
                Ce_fraction=ce, ARC="n")


boxrows(merged("S4_fig5.9_CeZnO_compound_target_S3fig2_boxplots.csv",
               "S4_fig5.10_CeZnO_compound_target_diode_S3fig3_boxplots.csv", "buffer/thickness_nm"),
        "buffer/thickness_nm", s3cond, "S3",
        "S3 Figs. 2 and 3 box plots (PDF p.4-5); read from thesis Figs. 5.9/5.10 (PDF p.110-111), identical to the "
        "journal Fig. 2 within 0.001 (scripts/s3_crosscheck.py)", "S3 Ce series (compound targets)",
        "8 conditions, 12 cells each, one batch.")


def cocond(lab):
    ce = float(lab) / 100
    return dict(year=2025, buffer="ZnO" if ce == 0 else "CeZnO (co-sputtered)", buffer_thickness_nm=50,
                buffer_dep_temp_C=200 if abs(ce - 0.087) < 1e-6 else 22, Ce_fraction="%.3f" % ce, ARC="n")


boxrows("S4_fig5.3_CeZnO_cosputtered_boxplots.csv", "Ce_at_pct", cocond, "S4",
        "S4 thesis Fig. 5.3 box plots (PDF p.105), digitised from vector paths", "S4 Ch.5.3.1 co-sputtered CeZnO batch",
        "NSG TEC 15 (3.8 mm) substrates. The 8.7% film was deposited at 200 C and vacuum-annealed at 500 C (thesis PDF p.102).")


def a1cond(lab):
    return dict(year=2025, buffer="ZnO", buffer_thickness_nm=int(lab), buffer_dep_temp_C=22, Ce_fraction=0, ARC="n")


boxrows("S4_figA.1_ZnO_thickness_repeat_thicker_FTO_boxplots.csv", "ZnO_thickness_nm", a1cond, "S4",
        "S4 thesis Fig. A.1 box plots (PDF p.204), digitised from vector paths",
        "S4 App. A repeat thickness series (thicker FTO)",
        "Repeat of the S1 thickness series on substrates with a thicker FTO layer (thesis PDF p.68 and p.204).")
os.remove(os.path.join(CUR, ".merged_tmp.csv"))

with open(os.path.join(OUT, "devices.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    w.writerows(rows)
print("devices rows", len(rows))

# --------------------------------------------------------------------------- checks table
val1 = json.load(open(os.path.join(CUR, "S1_validation.json")))
ras = json.load(open(os.path.join(CUR, "S1_raster_check.json")))
val4 = json.load(open(os.path.join(CUR, "S4_validation.json")))
chk = []


def c(check, file, qty, reported, extracted, where):
    d = "" if reported in ("", None) or extracted in ("", None) else "%.4g" % (extracted - reported)
    chk.append(dict(check=check, file=file, quantity=qty, reported="%.6g" % reported, extracted="%.6g" % extracted,
                    difference=d, reported_where=where))


def fom(check, file, F, rep, where):
    for q, k in (("Voc_mV", "Voc_mV"), ("Jsc_mA_cm2", "Jsc_mA_cm2"), ("FF_pct", "FF_pct"), ("eta_pct", "eta_pct")):
        if rep.get(q) is not None and k in F:
            c(check, file, q, rep[q], round(F[k], 4), where)


R14 = dict(Voc_mV=875.5, Jsc_mA_cm2=30.43, FF_pct=80.48, eta_pct=21.44)
fom("S1 Fig.3a J-V, journal vector centreline", "S1_fig3a_JV_light.csv", val1["fig3a"], R14, "S1 p.3 / Fig.3a legend")
fom("S1 Fig.3a J-V, raster (600 dpi) digitiser", "(raster, no file)", ras["fig3a_raster_FoM"], R14,
    "S1 p.3 / Fig.3a legend")
fom("Thesis Fig.3.3 = S1 Fig.3a, vector vertices", "S4_fig3.3_JV_21p4pct_S1fig3a_light.csv",
    val4["fig3.3_JV_21p4pct_S1fig3a_light_FoM"], R14, "S1 p.3 / Fig.3a legend")
fom("Thesis Fig.3.10 experiment", "S4_fig3.10_SCAPS_vs_experiment_JV_experiment.csv",
    val4["fig3.10_SCAPS_vs_experiment_JV_experiment_FoM"], dict(Voc_mV=875, Jsc_mA_cm2=30.4, FF_pct=80.5, eta_pct=21.4),
    "thesis Fig.3.10 inset table")
fom("Thesis Fig.3.10 SCAPS simulation", "S4_fig3.10_SCAPS_vs_experiment_JV_simulation.csv",
    val4["fig3.10_SCAPS_vs_experiment_JV_simulation_FoM"], dict(Voc_mV=872, Jsc_mA_cm2=30.8, FF_pct=79.6, eta_pct=21.4),
    "thesis Fig.3.10 inset table")
for t, eta, voc, jsc, ff, *_ in T1:
    fom(f"S2 best cell {t} C (thesis Fig.4.4)", f"S4_fig4.4_JV_dep_temperature_S2fig4a_{t}C_solid.csv",
        val4[f"fig4.4_JV_dep_temperature_S2fig4a_{t}C_solid_FoM"],
        dict(Voc_mV=voc, Jsc_mA_cm2=jsc, FF_pct=ff, eta_pct=eta), "S2 Table 1" + (" / p.3 text" if t == 100 else ""))
names = {0.0: "ZnO", 0.03: "Ce0.03", 0.06: "Ce0.06", 0.09: "Ce0.09"}
for ce, th, eta, voc, jsc, ff, *_ in T2:
    pan = "fig5.11a_JV_50nm_S3fig4a" if th == 50 else "fig5.11b_JV_100nm_S3fig4b"
    fom(f"S3 best cell {names[ce]} {th} nm (thesis Fig.5.11)", f"S4_{pan}_{names[ce]}.csv",
        val4[f"{pan}_{names[ce]}_FoM"], dict(Voc_mV=voc, Jsc_mA_cm2=jsc, FF_pct=ff, eta_pct=eta), "S3 Table 2")
fom("Thesis Fig.5.5 ZnO (co-sputter batch)", "S4_fig5.5_JV_cosputtered_CeZnO_ZnO_light.csv",
    val4["fig5.5_JV_cosputtered_CeZnO_ZnO_light_FoM"], dict(eta_pct=19.5), "thesis PDF p.107")
fom("Thesis Fig.5.5 Ce0.050 (co-sputter batch)", "S4_fig5.5_JV_cosputtered_CeZnO_Ce0.050_light.csv",
    val4["fig5.5_JV_cosputtered_CeZnO_Ce0.050_light_FoM"], dict(eta_pct=19.2), "thesis PDF p.107")
fom("Thesis Fig.6.3 ZnO 65 nm", "S4_fig6.3_JV_ZnO65nm_vs_SnO2_ZnO_light.csv",
    val4["fig6.3_JV_ZnO65nm_vs_SnO2_ZnO_light_FoM"], dict(Voc_mV=854, Jsc_mA_cm2=29.4, FF_pct=80.1, eta_pct=20.1),
    "thesis Fig.6.3 legend")
fom("Thesis Fig.6.3 SnO2", "S4_fig6.3_JV_ZnO65nm_vs_SnO2_SnO2_light.csv",
    val4["fig6.3_JV_ZnO65nm_vs_SnO2_SnO2_light_FoM"], dict(Voc_mV=833, Jsc_mA_cm2=30.2, FF_pct=78.7, eta_pct=19.8),
    "thesis Fig.6.3 legend")


def first(fname, col=1):
    r = list(csv.reader(open(os.path.join(CUR, fname))))[1:]
    return [float(x[col]) for x in r]


c("S1 Fig.3c zero-bias N_A, journal vector", "S1_fig3c_zero_bias_point.csv", "N_A_cm-3", 2.1e16,
  float("%.4g" % val1["fig3c"]["zero_bias_NA_cm3"]), "S1 p.3 text")
c("S1 Fig.3c zero-bias N_A, raster digitiser", "(raster)", "N_A_cm-3", 2.1e16,
  float("%.4g" % ras["fig3c_raster_zero_bias"]["NA_cm3"]), "S1 p.3 text")
c("Thesis Fig.3.5 zero-bias N_A", "S4_fig3.5_CV_21p4pct_S1fig3c_zero_bias.csv", "N_A_cm-3", 2.1e16,
  float("%.4g" % first("S4_fig3.5_CV_21p4pct_S1fig3c_zero_bias.csv")[0]), "S1 p.3 text")
c("S2 Fig.4b zero-bias N_A (thesis Fig.4.6)", "S4_fig4.6_CV_100C_S2fig4b_zero_bias.csv", "N_A_cm-3", 1.8e16,
  float("%.4g" % first("S4_fig4.6_CV_100C_S2fig4b_zero_bias.csv")[0]), "S2 p.4 text")
for ce, th, *rest in T2:
    pan = "fig5.13a_CV_50nm_S3fig6a" if th == 50 else "fig5.13b_CV_100nm_S3fig6b"
    fn = f"S4_{pan}_{names[ce]}_0V.csv"
    c(f"S3 zero-bias N_A {names[ce]} {th} nm (thesis Fig.5.13)", fn, "N_A_cm-3", rest[-1],
      float("%.4g" % first(fn)[0]), "S3 Table 3")
for t, v, got in zip((22, 100, 200, 500), (1.92e14, 8.57e13, 1.98e15, 2.07e15),
                     first("S4_fig4.7_interface_defect_density_S2fig5_Nit.csv")):
    c(f"S2 interface defect density {t} C (thesis Fig.4.7)", "S4_fig4.7_interface_defect_density_S2fig5_Nit.csv",
      "N_it_cm-3", v, float("%.4g" % got), "S2 p.4-5 text")
c("S1 Fig.3d Ea, plotted fit line (journal)", "S1_fig3d_fit_line.csv", "Ea_eV", 1.36,
  round(val1["fig3d"]["plotted_fit_line_intercept_V"], 4), "S1 p.3 text")
c("S1 Fig.3d Ea, refit of 315-355 K markers (journal)", "S1_fig3d_Voc_vs_T.csv", "Ea_eV", 1.36,
  round(val1["fig3d"]["refit_315_355K_intercept_V"], 4), "S1 p.3 text")
c("S1 Fig.3d Ea, raster digitiser refit", "(raster)", "Ea_eV", 1.36, round(ras["fig3d_raster_refit_intercept_V"], 4),
  "S1 p.3 text")
c("Thesis Fig.5.7 Ea ZnO (co-sputter batch)", "S4_fig5.7_VocT_cosputtered_CeZnO_ZnO_fit.csv", "Ea_eV", 1.36,
  round(val4["fig5.7_VocT_cosputtered_CeZnO_ZnO_fit_line_intercept_V"], 4), "thesis PDF p.107")
c("Thesis Fig.5.7 Ea Ce0.087 (co-sputter batch)", "S4_fig5.7_VocT_cosputtered_CeZnO_Ce0.087_fit.csv", "Ea_eV", 1.61,
  round(val4["fig5.7_VocT_cosputtered_CeZnO_Ce0.087_fit_line_intercept_V"], 4), "thesis PDF p.108")
c("S1 Fig.3b absorber band gap from -dEQE/dlambda peak", "S1_fig3b_minus_dEQE_dlambda.csv", "Eg_eV", 1.41,
  round(val1["fig3b"]["Eg_from_peak_eV"], 4), "S1 p.3 text")
for k, rep in (("eta_pct", 21.23), ("Voc_mV", 883), ("Jsc_mA_cm2", 30.04), ("FF_pct", 80.73)):
    c("S1 Fig.2 maximum at 50 nm (whisker top)", "S1_fig2_boxplots.csv", k, rep,
      round(val1[f"fig2_{k}_max_by_thickness"]["50"], 4), "S1 p.3 text")
bx = {(r["ZnO_dep_temp_C"], r["parameter"]): r for r in
      csv.DictReader(open(os.path.join(CUR, "S4_fig4.2_ZnO_dep_temperature_S2fig2_boxplots.csv")))}
for (t, p, rep, w) in (("100", "eta_pct", 20.0, "thesis PDF p.86"), ("100", "Voc_mV", 869, "thesis PDF p.86"),
                       ("100", "Jsc_mA_cm2", 29.3, "thesis PDF p.86"), ("250", "FF_pct", 78.9, "thesis PDF p.86"),
                       ("50", "FF_pct", 78.7, "thesis PDF p.86"), ("100", "FF_pct", 78.7, "thesis PDF p.86"),
                       ("22", "eta_pct", 19.6, "thesis PDF p.174")):
    c(f"S2 Fig.2 median {t} C (thesis Fig.4.2)", "S4_fig4.2_ZnO_dep_temperature_S2fig2_boxplots.csv", p, rep,
      round(float(bx[(t, p)]["median"]), 4), w)
m22, m100, m500 = (float(bx[(t, "eta_pct")]["mean"]) for t in ("22", "100", "500"))
c("S2 Fig.2 relative mean-efficiency gain 100 C vs 22 C", "S4_fig4.2_...boxplots.csv", "gain_pct", 2.41,
  round(100 * (m100 / m22 - 1), 3), "thesis PDF p.86")
c("S2 Fig.2 relative mean-efficiency gain 500 C vs 22 C", "S4_fig4.2_...boxplots.csv", "gain_pct", 0.57,
  round(100 * (m500 / m22 - 1), 3), "thesis PDF p.86")
with open(os.path.join(CUR, "checks_against_reported_values.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(chk[0].keys()))
    w.writeheader()
    w.writerows(chk)
print("checks", len(chk))
