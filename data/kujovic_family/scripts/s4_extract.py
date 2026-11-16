"""Extract plotted data from the vector figures of the Kujovic PhD thesis (S4).

In the thesis PDF every curve is a stroked polyline, so its vertices are the
plotted data points, and tick labels are real text. Chapters 3, 4 and 5 repeat
the figures of the 2024 AFM paper (S1), the 2025 AMT paper (S2) and the 2026
J. Phys. Energy paper (S3); Chapter 6 and Appendix A add ZnO reference data.

Usage: python -I s4_extract.py <thesis PDF> <kujovic_family folder>
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import vecfig as V  # noqa: E402
import thesisfig as T  # noqa: E402

PDF, OUT = sys.argv[1], sys.argv[2]
CUR = os.path.join(OUT, "curves")
os.makedirs(CUR, exist_ok=True)
doc = V.pymupdf.open(PDF)
LOG = {}

TEAL = (0.4, 0.6, 0.6)
ORANGE = (0.941, 0.51, 0.157)
K = (0.0, 0.0, 0.0)
R = (1.0, 0.0, 0.0)
B = (0.0, 0.0, 1.0)
G = (0.0, 0.502, 0.0)
O = (1.0, 0.502, 0.0)
M = (1.0, 0.0, 1.0)
GR = (0.318, 0.318, 0.318)
R2 = (0.945, 0.251, 0.251)
B2 = (0.102, 0.435, 0.875)
G2 = (0.216, 0.678, 0.42)
P2 = (0.693, 0.467, 0.871)
O2 = (0.801, 0.6, 0.0)
O3 = (0.941, 0.51, 0.157)

COLS_L = (143.53, 278.87)
COLS_R = (345.98, 481.32)


def overlay(page, clip, layers, fname, title, dpi=250):
    pix = page.get_pixmap(dpi=dpi, clip=V.pymupdf.Rect(*clip), alpha=False)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3]
    w, h = clip[2] - clip[0], clip[3] - clip[1]
    fig, ax = plt.subplots(figsize=(7, max(3, 7 * h / w)))
    ax.imshow(img, extent=[clip[0], clip[2], clip[3], clip[1]])
    for L in layers:
        P = np.asarray(L["pts"]).reshape(-1, 2)
        if len(P):
            ax.plot(P[:, 0], P[:, 1], L.get("fmt", "o"), ms=L.get("ms", 1.6), color=L.get("color", "lime"),
                    label=L["label"], mew=0.8)
    ax.set_xlim(clip[0], clip[2])
    ax.set_ylim(clip[3], clip[1])
    ax.set_title(title, fontsize=8)
    ax.legend(fontsize=5, loc="best")
    ax.tick_params(labelsize=6)
    fig.tight_layout()
    fig.savefig(os.path.join(CUR, fname), dpi=200)
    plt.close(fig)


def write(fname, header, rows, fmts):
    with open(os.path.join(CUR, fname), "w") as f:
        f.write(",".join(header) + "\n")
        for r in rows:
            f.write(",".join("" if (isinstance(v, float) and v != v) else (fm % v) for fm, v in zip(fmts, r)) + "\n")


def jv_fom(Vm, J):
    o = np.argsort(Vm)
    Vm, J = Vm[o], J[o]
    jsc = -np.interp(0.0, Vm, J)
    # Voc: last sign change of J from negative to positive
    s = np.flatnonzero((J[:-1] < 0) & (J[1:] >= 0))
    note = "interpolated"
    if len(s) == 0:
        if J[-1] < -1.0:
            return dict(Jsc_mA_cm2=float(jsc))
        i = len(J) - 2  # curve stops just below J=0: extrapolate the last segment
        note = "extrapolated from last segment (curve ends at J=%.3f)" % J[-1]
    else:
        i = s[-1]
    voc = Vm[i] + (0 - J[i]) * (Vm[i + 1] - Vm[i]) / (J[i + 1] - J[i])
    m = (Vm > 0) & (Vm < voc)
    P = -(Vm[m] * J[m]) / 1000.0
    pm = P.max()
    return dict(Jsc_mA_cm2=float(jsc), Voc_mV=float(voc), FF_pct=float(100 * pm * 1000 / (voc * jsc)),
                eta_pct=float(pm), n_points=int(len(Vm)), Voc_method=note)


# ---------------------------------------------------------------- box plots
BOX = [
    # fig id, page, panel list: (param, ycol, (row y0,y1), log)
    ("fig3.2_ZnO_thickness_S1fig2", 67, ["30", "50", "75", "100", "200"], "ZnO_thickness_nm",
     [("eta_pct", COLS_L, (239.4, 348.4), False), ("Voc_mV", COLS_R, (239.4, 348.4), False),
      ("Jsc_mA_cm2", COLS_L, (425.3, 534.3), False), ("FF_pct", COLS_R, (425.3, 534.3), False)]),
    ("fig4.2_ZnO_dep_temperature_S2fig2", 85, ["22", "50", "100", "150", "200", "250", "300", "350", "400", "450", "500"],
     "ZnO_dep_temp_C",
     [("eta_pct", COLS_L, (279.1, 388.1), False), ("Voc_mV", COLS_R, (279.1, 388.1), False),
      ("Jsc_mA_cm2", COLS_L, (465.0, 574.0), False), ("FF_pct", COLS_R, (465.0, 574.0), False)]),
    ("fig4.3_ZnO_dep_temperature_diode_S2fig3", 87,
     ["22", "50", "100", "150", "200", "250", "300", "350", "400", "450", "500"], "ZnO_dep_temp_C",
     [("Rs_ohm_cm2", COLS_L, (89.7, 198.7), False), ("Rsh_ohm_cm2", COLS_R, (89.7, 198.7), False),
      ("J0_mA_cm2", COLS_L, (275.7, 384.7), True), ("n", COLS_R, (275.7, 384.7), False)]),
    ("fig4.8_ZnO_thickness_100C_S2fig6", 93, ["40", "50", "55", "65", "70"], "ZnO_thickness_nm",
     [("eta_pct", COLS_L, (89.7, 198.7), False), ("Voc_mV", COLS_R, (89.7, 198.7), False),
      ("Jsc_mA_cm2", COLS_L, (275.7, 384.7), False), ("FF_pct", COLS_R, (289.2, 398.2), False)]),
    ("fig5.3_CeZnO_cosputtered", 105, ["0.0", "5.0", "5.3", "7.8", "8.7"], "Ce_at_pct",
     [("eta_pct", COLS_L, (89.7, 198.7), False), ("Voc_mV", COLS_R, (89.7, 198.7), False),
      ("Jsc_mA_cm2", COLS_L, (262.1, 371.1), False), ("FF_pct", COLS_R, (262.1, 371.1), False)]),
    ("fig5.9_CeZnO_compound_target_S3fig2", 110,
     ["ZnO/50", "ZnO/100", "3%CeZnO/50", "3%CeZnO/100", "6%CeZnO/50", "6%CeZnO/100", "9%CeZnO/50", "9%CeZnO/100"],
     "buffer/thickness_nm",
     [("eta_pct", COLS_L, (89.7, 198.7), False), ("Voc_mV", COLS_R, (89.7, 198.7), False),
      ("Jsc_mA_cm2", COLS_L, (275.7, 384.7), False), ("FF_pct", COLS_R, (275.7, 384.7), False)]),
    ("fig5.10_CeZnO_compound_target_diode_S3fig3", 111,
     ["ZnO/50", "ZnO/100", "3%CeZnO/50", "3%CeZnO/100", "6%CeZnO/50", "6%CeZnO/100", "9%CeZnO/50", "9%CeZnO/100"],
     "buffer/thickness_nm",
     [("Rs_ohm_cm2", COLS_L, (197.6, 306.6), False), ("Rsh_ohm_cm2", COLS_R, (197.6, 306.6), False),
      ("J0_mA_cm2", COLS_L, (383.6, 492.6), True), ("n", COLS_R, (383.6, 492.6), False)]),
    ("figA.1_ZnO_thickness_repeat_thicker_FTO", 204, ["30", "50", "75", "100", "200"], "ZnO_thickness_nm",
     [("eta_pct", COLS_L, (348.5, 457.5), False), ("Voc_mV", COLS_R, (348.5, 457.5), False),
      ("Jsc_mA_cm2", COLS_L, (534.5, 643.5), False), ("FF_pct", COLS_R, (534.5, 643.5), False)]),
]

index = []
for fid, pg, labels, xname, panels in BOX:
    page = doc[pg - 1]
    rows = []
    for param, (xl, xr), (y0, y1), lg in panels:
        clip = (xl - 45, y0 - 6, xr + 6, y1 + 22)
        ps = V.prims(page, clip)
        yax, vals = T.axis_auto(page, ps, "y", xl, (y0 - 0.3, y1 + 0.3), log=lg, label=f"{fid} {param}")
        bx = V.boxplots(ps, (xl, y0, xr, y1), [TEAL, ORANGE], yax)
        if len(bx) != len(labels):
            raise RuntimeError(f"{fid} {param}: {len(bx)} boxes for {len(labels)} labels")
        for lab, b in zip(labels, bx):
            rows.append([lab, param, b["q1"], b["median"], b["q3"], b["mean"], b["whisker_lo"], b["whisker_hi"],
                         ";".join("%.6g" % o for o in b["outliers"]), b["n_median_bars"], b["n_mean"],
                         yax.resid_pt])
        lay = []
        for k, c in (("q1", "cyan"), ("q3", "cyan"), ("median", "red"), ("mean", "magenta"),
                     ("whisker_lo", "orange"), ("whisker_hi", "orange")):
            lay.append(dict(pts=[(b["x_center_pt"], b[k + "_pt"]) for b in bx], label=k, color=c, fmt="_", ms=10))
        lay.append(dict(pts=[(b["x_center_pt"], o) for b in bx for o in b["outlier_pts"]], label="outlier",
                        color="blue", fmt="x", ms=4))
        overlay(page, clip, lay, f"S4_{fid}_{param}_overlay.png", f"thesis {fid} {param}: extracted box statistics")
        LOG[f"{fid}_{param}_ticks"] = vals
        LOG[f"{fid}_{param}_axis_resid_pt"] = yax.resid_pt
        LOG[f"{fid}_{param}_units_per_pt"] = yax.per_pt()
        index.append(dict(file=f"S4_{fid}_boxplots.csv", figure=fid, page=pg, series=param, kind="boxplot",
                          n=len(bx), n_outside=0, x_units_per_pt=None, y_units_per_pt=yax.per_pt(), y_log=lg,
                          x_resid_pt=None, y_resid_pt=yax.resid_pt))
    with open(os.path.join(CUR, f"S4_{fid}_boxplots.csv"), "w") as f:
        f.write(f"{xname},parameter,Q1,median,Q3,mean,whisker_lo,whisker_hi,outliers,n_median_bars,n_mean_markers,"
                "axis_fit_residual_pt\n")
        for r in rows:
            f.write("%s,%s,%.6g,%.6g,%.6g,%.6g,%.6g,%.6g,%s,%d,%d,%.4f\n" % tuple(r))

# ---------------------------------------------------------------- curves
# each entry: id, page, clip, x-axis (line, span, values|None, log), y-axis (...),
# series: list of (name, colour, kind, extra) ; columns (xname, yname)
CURVES = [
    ("fig3.3_JV_21p4pct_S1fig3a", 68, (180, 410, 430, 600),
     (508.13, (212.9, 415.9), None, False), (246.78, (426.3, 589.9), None, False),
     [("light", R, "solid", {}), ("dark", R, "dash", {})], ("V_mV", "J_mA_cm2")),
    ("fig3.4_EQE_21p4pct_S1fig3b", 69, (180, 140, 430, 330),
     (315.15, (212.9, 415.9), None, False), (212.92, (151.6, 315.2), None, False),
     [("EQE", R, "solid", {}), ("minus_dEQE_dlambda", B, "solid", {})], ("wavelength_nm", "EQE_pct")),
    ("fig3.5_CV_21p4pct_S1fig3c", 70, (180, 90, 430, 280),
     (262.01, (212.9, 415.9), None, False), (212.92, (98.5, 262.1), None, True),
     [("NA", R, "solid", {}), ("zero_bias", B, "markers", {})], ("depletion_width_um", "N_A_cm-3")),
    ("fig3.6_VocT_21p4pct_S1fig3d", 70, (180, 480, 430, 670),
     (655.65, (212.8, 416.0), None, False), (212.82, (492.1, 655.7), None, False),
     [("Voc", B, "markers", {}), ("fit", R, "solid", {})], ("T_K", "Voc_V")),
    ("fig3.10_SCAPS_vs_experiment_JV", 76, (180, 85, 430, 280),
     (262.11, (213.0, 416.2), None, False), (213.01, (98.4, 262.2), None, False),
     [("simulation", B, "pieces", {"exclude": [(220, 100, 260, 125)]}),
      ("experiment", R, "pieces", {"exclude": [(220, 100, 260, 125)]})], ("V_mV", "J_mA_cm2")),
    ("fig3.11_SCAPS_band_diagram", 77, (180, 85, 430, 280),
     (262.01, (212.9, 415.9), None, False), (212.92, (98.5, 262.1), None, False),
     [("Ec", R, "solid", {}), ("Ef", GR, "pieces", {}), ("Ev", B2, "solid", {})],
     ("distance_from_back_contact_um", "energy_eV")),
    ("fig3.12_SCAPS_Ec_vs_FTO_doping", 78, (175, 95, 425, 285),
     (265.90, (209.4, 407.6), None, False), (209.40, (106.1, 266.0), None, False),
     [("Ef", GR, "pieces", {}), ("Ec_FTO_1e16", R2, "solid", {}), ("Ec_FTO_1e17", B2, "solid", {}),
      ("Ec_FTO_1e18", G2, "solid", {}), ("Ec_FTO_1e19", P2, "solid", {}), ("Ec_FTO_1e20", O2, "solid", {})],
     ("distance_from_back_contact_um", "energy_eV")),
    ("fig4.4_JV_dep_temperature_S2fig4a", 88, (180, 160, 430, 370),
     (276.77, (212.9, 415.9), None, False), (246.78, (195.0, 358.6), None, False),
     [(f"{t}C_{kind}", c, kind, {"exclude": [(266, 185, 356, 270), (416, 150, 440, 300)]})
      for t, c in (("22", K), ("100", R), ("200", G), ("300", O), ("400", M), ("500", B))
      for kind in ("solid", "dash")], ("V_mV", "J_mA_cm2")),
    ("fig4.4inset_EQE_100C_S2fig4a", 88, (262, 185, 360, 272),
     (261.01, (273.0, 349.6), None, False), (272.96, (194.8, 261.1), None, False),
     [("EQE", R, "solid", {"rect": (273.0, 194.8, 349.6, 261.1)})], ("wavelength_nm", "EQE_pct")),
    ("fig4.6_CV_100C_S2fig4b", 91, (180, 90, 430, 280),
     (262.01, (212.9, 415.9), None, False), (212.92, (98.5, 262.1), None, True),
     [("NA", R, "solid", {}), ("zero_bias", B, "markers", {})], ("profile_depth_um", "N_A_cm-3")),
    ("fig4.7_interface_defect_density_S2fig5", 92, (180, 90, 430, 280),
     (262.01, (212.9, 415.9), None, False), (212.92, (98.5, 262.1), None, True),
     [("Nit", B, "markers", {})], ("ZnO_dep_temp_C", "interface_defect_density_cm-3")),
    ("fig5.5_JV_cosputtered_CeZnO", 106, (180, 480, 430, 670),
     (576.96, (212.9, 415.9), None, False), (246.78, (495.2, 658.8), None, False),
     [("ZnO_light", B, "solid", {}), ("ZnO_dark", B, "dash", {}),
      ("Ce0.050_light", R, "solid", {}), ("Ce0.050_dark", R, "dash", {})], ("V_mV", "J_mA_cm2")),
    ("fig5.6_EQE_cosputtered_CeZnO", 107, (180, 270, 430, 460),
     (442.84, (212.9, 415.9), None, False), (212.92, (279.3, 442.9), None, False),
     [("ZnO", B, "solid", {}), ("Ce0.050", R, "solid", {}), ("Ce0.078", G, "solid", {}),
      ("Ce0.087", O3, "solid", {})], ("wavelength_nm", "EQE_pct")),
    ("fig5.7_VocT_cosputtered_CeZnO", 108, (180, 85, 430, 265),
     (245.70, (213.0, 415.9), None, False), (212.98, (96.4, 245.8), None, False),
     [("ZnO", B, "markers", {}), ("ZnO_fit", B, "solid", {}), ("Ce0.050", R, "markers", {}),
      ("Ce0.050_fit", R, "solid", {}), ("Ce0.078", G, "markers", {}), ("Ce0.078_fit", G, "solid", {}),
      ("Ce0.087", O3, "markers", {}), ("Ce0.087_fit", O3, "solid", {})], ("T_K", "Voc_V")),
    ("fig5.11a_JV_50nm_S3fig4a", 112, (100, 215, 290, 350),
     (334.24, (143.5, 278.9), None, False), (143.53, (225.2, 334.3), None, False),
     [("ZnO", GR, "solid", {}), ("Ce0.03", R, "solid", {}), ("Ce0.06", B, "solid", {}),
      ("Ce0.09", G2, "solid", {})], ("V_mV", "J_mA_cm2")),
    ("fig5.11b_JV_100nm_S3fig4b", 112, (300, 215, 490, 350),
     (334.24, (346.0, 481.4), None, False), (345.98, (225.2, 334.3), None, False),
     [("ZnO", GR, "solid", {}), ("Ce0.03", R, "solid", {}), ("Ce0.06", B, "solid", {}),
      ("Ce0.09", G2, "solid", {})], ("V_mV", "J_mA_cm2")),
    ("fig5.12a_EQE_50nm_S3fig5a", 114, (100, 80, 290, 215),
     (198.68, (143.5, 278.9), None, False), (143.53, (89.7, 198.8), None, False),
     [("ZnO", GR, "solid", {}), ("Ce0.03", R2, "solid", {}), ("Ce0.06", B2, "solid", {}),
      ("Ce0.09", G2, "solid", {})], ("wavelength_nm", "EQE_pct")),
    ("fig5.12b_EQE_100nm_S3fig5b", 114, (300, 80, 490, 215),
     (198.68, (346.0, 481.4), None, False), (345.98, (89.7, 198.8), None, False),
     [("ZnO", GR, "solid", {}), ("Ce0.03", R2, "solid", {}), ("Ce0.06", B2, "solid", {}),
      ("Ce0.09", G2, "solid", {})], ("wavelength_nm", "EQE_pct")),
    ("fig5.13a_CV_50nm_S3fig6a", 114, (100, 365, 290, 500),
     (484.22, (143.5, 278.9), None, False), (143.53, (375.2, 484.3), None, True),
     [("ZnO", GR, "solid", {}), ("Ce0.03", R, "solid", {}), ("Ce0.06", B, "solid", {}),
      ("Ce0.09", G2, "solid", {}), ("ZnO_0V", GR, "markers", {}), ("Ce0.03_0V", R, "markers", {}),
      ("Ce0.06_0V", B, "markers", {}), ("Ce0.09_0V", G2, "markers", {})], ("profile_depth_um", "N_A_cm-3")),
    ("fig5.13b_CV_100nm_S3fig6b", 114, (300, 365, 490, 500),
     (484.22, (346.0, 481.4), None, False), (345.98, (375.2, 484.3), None, True),
     [("ZnO", GR, "solid", {}), ("Ce0.03", R, "solid", {}), ("Ce0.06", B, "solid", {}),
      ("Ce0.09", G2, "solid", {}), ("ZnO_0V", GR, "markers", {}), ("Ce0.03_0V", R, "markers", {}),
      ("Ce0.06_0V", B, "markers", {}), ("Ce0.09_0V", G2, "markers", {})], ("profile_depth_um", "N_A_cm-3")),
    ("fig5.14_interface_defect_density_50nm_S3fig7", 115, (180, 400, 430, 600),
     (None, None, None, False), (212.92, (410.7, 574.3), None, True),
     [("Nit", B, "markers", {})], ("buffer_index", "interface_defect_density_cm-3")),
    ("fig6.3_JV_ZnO65nm_vs_SnO2", 124, (180, 90, 430, 280),
     (180.31, (212.9, 415.9), None, False), (246.78, (98.5, 262.1), None, False),
     [("ZnO_light", R, "solid", {}), ("ZnO_dark", R, "dash", {}), ("SnO2_light", B, "solid", {}),
      ("SnO2_dark", B, "dash", {})], ("V_mV", "J_mA_cm2")),
]


def in_rect(P, r):
    return (P[:, 0] >= r[0]) & (P[:, 0] <= r[2]) & (P[:, 1] >= r[1]) & (P[:, 1] <= r[3])


for cid, pg, clip, xa, ya, series, (xn, yn) in CURVES:
    page = doc[pg - 1]
    ps = V.prims(page, clip)
    if xa[0] is not None:
        xax, xv = T.axis_auto(page, ps, "x", xa[0], xa[1], values=xa[2], log=xa[3], label=cid + " x")
    else:
        xax, xv = None, None
    yax, yv = T.axis_auto(page, ps, "y", ya[0], ya[1], values=ya[2], log=ya[3], label=cid + " y")
    LOG[f"{cid}_xticks"], LOG[f"{cid}_yticks"] = xv, yv
    LOG[f"{cid}_resid_pt"] = [xax.resid_pt if xax else None, yax.resid_pt]
    plot = (xa[1][0] if xa[1] else clip[0], ya[1][0], xa[1][1] if xa[1] else clip[2], ya[1][1])
    layers = []
    for name, col, kind, ex in series:
        rect = ex.get("rect", (clip[0], clip[1], clip[2], clip[3]))
        if kind in ("solid", "dash"):
            solid, dash = T.stroke_curves(ps, col, rect, axes=(xa[0], ya[0]))
            if kind == "solid":
                cand = [P for P in solid if not any(in_rect(P, e).all() for e in ex.get("exclude", []))]
                # legend keys are short; keep the longest polyline(s) inside the plot
                cand = [P for P in cand if np.mean(in_rect(P, (plot[0] - 1, plot[1] - 1, plot[2] + 1, plot[3] + 1))) > 0.3]
                if not cand:
                    raise RuntimeError(f"{cid} {name}: no solid curve")
                P = max(cand, key=len)
            else:
                P = dash
                for e in ex.get("exclude", []):
                    P = P[~in_rect(P, e)]
        elif kind == "pieces":
            pts = []
            for d in ps:
                if d["type"] in ("s", "fs") and V.close(d.get("color"), col) and len(d["items"]) <= 2:
                    Pp = V.polyline(d)
                    if not T._is_tick(Pp, (xa[0], ya[0])):
                        pts.append(Pp)
            P = np.vstack(pts)
            for e in ex.get("exclude", []):
                P = P[~in_rect(P, e)]
            P = P[in_rect(P, clip)]
            P = P[np.argsort(P[:, 0], kind="stable")]
            keep = np.ones(len(P), bool)
            keep[1:] = np.hypot(*np.diff(P, axis=0).T) > 1e-3
            P = P[keep]
        elif kind == "markers":
            P = np.array([V.center(d) for d in ps if d["type"] in ("f", "fs") and V.close(d.get("fill"), col)
                          and 0.8 < d["rect"].width < 4 and 0.8 < d["rect"].height < 4
                          and in_rect(np.array([V.center(d)]), plot)[0]]).reshape(-1, 2)
            P = P[np.argsort(P[:, 0])]
        xd = xax(P[:, 0]) if xax else np.arange(len(P), dtype=float)  # fig5.14: 0=ZnO,1=3%,2=6%,3=9% Ce
        yd = yax(P[:, 1])
        outside = (~in_rect(P, (plot[0] - 0.05, plot[1] - 0.05, plot[2] + 0.05, plot[3] + 0.05))).astype(float)
        fname = f"S4_{cid}_{name}.csv"
        lg = "%.5e" if (ya[3]) else "%.5f"
        write(fname, [xn, yn, "outside_plotted_axes"], np.column_stack([xd, yd, outside]), ["%.5f", lg, "%d"])
        index.append(dict(file=fname, figure=cid, page=pg, series=name, kind=kind, n=int(len(P)),
                          n_outside=int(outside.sum()),
                          x_units_per_pt=(xax.per_pt() if xax else None), y_units_per_pt=yax.per_pt(),
                          y_log=bool(ya[3]), x_resid_pt=(xax.resid_pt if xax else None), y_resid_pt=yax.resid_pt))
        if "JV" in cid and kind in ("solid", "pieces") and "dark" not in name and "fit" not in name:
            LOG[f"{cid}_{name}_FoM"] = jv_fom(xd, yd)
        if "VocT" in cid and kind == "markers":
            hi = (xd > 312) & (xd < 358)
            if hi.sum() >= 2:
                k = np.polyfit(xd[hi], yd[hi], 1)
                LOG[f"{cid}_{name}_refit_315_355K_intercept_V"] = float(k[1])
        if "VocT" in cid and kind == "solid":
            k = np.polyfit(xd, yd, 1)
            LOG[f"{cid}_{name}_line_intercept_V"] = float(k[1])
        layers.append(dict(pts=P, label=f"{name} ({kind})", color=["lime", "cyan", "yellow", "magenta", "orange",
                                                                     "deepskyblue", "red", "blue", "black",
                                                                     "saddlebrown", "olive", "pink"][len(layers) % 12],
                           fmt="+" if kind == "markers" else "o", ms=5 if kind == "markers" else 1.2))
    overlay(page, clip, layers, f"S4_{cid}_overlay.png", f"thesis {cid}: extracted points")

with open(os.path.join(CUR, "S4_index.json"), "w") as f:
    json.dump(index, f, indent=1)
with open(os.path.join(CUR, "S4_validation.json"), "w") as f:
    json.dump(LOG, f, indent=1, default=float)
print(json.dumps({k: v for k, v in LOG.items() if "FoM" in k or "intercept" in k}, indent=1))
for e in index:
    print(e)
