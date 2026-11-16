"""Digitise Kujovic et al., Adv. Funct. Mater. 34, 2312528 (2024): Figures 2 and 3.

Usage: python -I s1_extract.py <path to S1 PDF> <output folder (kujovic_family)>
Writes curves/S1_*.csv, curves/S1_*_overlay.png and curves/S1_validation.json.
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

PDF, OUT = sys.argv[1], sys.argv[2]
CUR = os.path.join(OUT, "curves")
os.makedirs(CUR, exist_ok=True)
RED = (0.931, 0.130, 0.141)
BLUE = (0.230, 0.330, 0.640)
DARK = (0.137, 0.122, 0.125)
TEAL = (0.403, 0.607, 0.607)
val = {}


def overlay(page, clip, layers, fname, title, dpi=300):
    img, _ = V.render(page, clip, dpi)
    w = clip[2] - clip[0]
    h = clip[3] - clip[1]
    fig, ax = plt.subplots(figsize=(7, 7 * h / w))
    ax.imshow(img, extent=[clip[0], clip[2], clip[3], clip[1]])
    for L in layers:
        P = np.asarray(L["pts"])
        if len(P) == 0:
            continue
        ax.plot(P[:, 0], P[:, 1], L.get("fmt", "o"), ms=L.get("ms", 1.2), mfc="none" if L.get("open") else None,
                color=L.get("color", "lime"), lw=L.get("lw", 0.6), label=L["label"])
    ax.set_xlim(clip[0], clip[2])
    ax.set_ylim(clip[3], clip[1])
    ax.set_title(title, fontsize=8)
    ax.legend(fontsize=6, loc="best")
    ax.set_xlabel("page x (pt)", fontsize=7)
    ax.set_ylabel("page y (pt)", fontsize=7)
    ax.tick_params(labelsize=6)
    fig.tight_layout()
    fig.savefig(os.path.join(CUR, fname), dpi=200)
    plt.close(fig)


def write_csv(fname, header, rows, fmt):
    with open(os.path.join(CUR, fname), "w") as f:
        f.write(",".join(header) + "\n")
        for r in rows:
            f.write(",".join(fm % v if v == v else "" for fm, v in zip(fmt, r)) + "\n")


doc, p3 = V.open_page(PDF, 3)
_, p4 = V.open_page(PDF, 4)

# ------------------------------------------------------------------ Figure 2
thick = [30, 50, 75, 100, 200]
panels = {
    "eta_pct": ((119, 72, 290, 205), 139.178, 197.856, (79.8, 198.1), [22, 21, 20, 19, 18]),
    "Voc_mV": ((300, 72, 470, 205), 323.997, 197.856, (79.8, 198.1), [885, 880, 875, 870, 865, 860, 855]),
    "Jsc_mA_cm2": ((119, 220, 290, 360), 139.178, 357.935, (239.9, 358.2), [31, 30, 29, 28]),
    "FF_pct": ((300, 220, 470, 360), 323.997, 357.935, (239.9, 358.2), [82, 80, 78, 76]),
}
rows = []
fig2 = {}
for name, (clip, xline, yline, yspan, yvals) in panels.items():
    ps = V.prims(p3, clip)
    yax = V.calibrate(ps, "y", xline, yspan, yvals, label="S1 Fig2 " + name)
    plot_rect = (xline, yspan[0], clip[2] - 4, yline)
    bx = V.boxplots(ps, plot_rect, [TEAL], yax)
    assert len(bx) == 5, (name, len(bx))
    fig2[name] = bx
    for t, b in zip(thick, bx):
        rows.append([t, name, b["q1"], b["median"], b["q3"], b["mean"], b["whisker_lo"], b["whisker_hi"],
                     ";".join("%.4f" % o for o in b["outliers"]), yax.resid_pt, yax.per_pt()])
    lay = []
    for k, c in (("q1", "cyan"), ("q3", "cyan"), ("median", "red"), ("mean", "magenta"),
                 ("whisker_lo", "orange"), ("whisker_hi", "orange")):
        lay.append(dict(pts=[(b["x_center_pt"], b[k + "_pt"]) for b in bx], label=k, color=c, fmt="_", ms=14))
    lay.append(dict(pts=[(b["x_center_pt"], o) for b in bx for o in b["outlier_pts"]], label="outlier",
                    color="blue", fmt="x", ms=5))
    overlay(p3, clip, lay, f"S1_fig2_{name}_overlay.png", f"S1 Fig. 2 {name}: extracted box-plot statistics")
    val[f"fig2_{name}_axis_residual_pt"] = yax.resid_pt

with open(os.path.join(CUR, "S1_fig2_boxplots.csv"), "w") as f:
    f.write("ZnO_thickness_nm,parameter,Q1,median,Q3,mean,whisker_lo,whisker_hi,outliers,axis_fit_residual_pt,"
            "units_per_pt\n")
    for r in rows:
        f.write("%d,%s,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%s,%.4f,%.5f\n" % tuple(r))

# highest values per thickness (max of whisker_hi and outliers) to compare with the text
for name, bx in fig2.items():
    val[f"fig2_{name}_max_by_thickness"] = {t: max([b["whisker_hi"]] + b["outliers"]) for t, b in zip(thick, bx)}

# ------------------------------------------------------------------ Figure 3a J-V
clip = (130, 70, 290, 185)
ps = V.prims(p4, clip)
xax = V.calibrate(ps, "x", 127.984, (156.0, 276.6), [-200, 0, 200, 400, 600, 800, 1000], label="3a x")
yax = V.calibrate(ps, "y", 176.410, (79.4, 176.5), [40, 30, 20, 10, 0, -10, -20, -30, -40], label="3a y")
reds = [d for d in ps if V.close(V.pcol(d), RED)]
solid = max(reds, key=lambda d: len(d["items"]))
dashes = [d for d in reds if d is not solid]
C, w = V.centreline(V.subpaths(solid))
C = V.despike(V.refine_normal(V.subpaths(solid), C))
C = V.trim_ends(C, w / 2)
Cr = V.rdp(C, 0.02)
jv = np.column_stack([xax(Cr[:, 0]), yax(Cr[:, 1])])
outside = ((jv[:, 0] < -200) | (jv[:, 0] > 1000) | (jv[:, 1] < -40) | (jv[:, 1] > 40)).astype(float)
jv = np.column_stack([jv, outside])
dk = V.dash_centres(dashes)
jvd = np.column_stack([xax(dk[:, 0]), yax(dk[:, 1])])
write_csv("S1_fig3a_JV_light.csv", ["V_mV", "J_mA_cm2", "outside_plotted_axes"], jv, ["%.2f", "%.4f", "%d"])
write_csv("S1_fig3a_JV_dark.csv", ["V_mV", "J_mA_cm2"], jvd, ["%.2f", "%.4f"])
# figures of merit from the dense centreline
Vd, Jd = xax(C[:, 0]), yax(C[:, 1])
o = np.argsort(Vd)
Vd, Jd = Vd[o], Jd[o]
jsc = -np.interp(0.0, Vd, Jd)
oo = np.argsort(Jd)
voc = np.interp(0.0, Jd[oo], Vd[oo])
m = (Vd > 0) & (Vd < voc)
P = -(Vd[m] * Jd[m]) / 1000.0  # mW/cm2
pmax = P.max()
val["fig3a"] = dict(Jsc_mA_cm2=jsc, Voc_mV=voc, FF_pct=100 * pmax * 1000 / (voc * jsc), eta_pct=pmax,
                    Vmp_mV=float(Vd[m][np.argmax(P)]), stroke_width_pt=w, x_resid_pt=xax.resid_pt,
                    y_resid_pt=yax.resid_pt, mV_per_pt=xax.per_pt(), mAcm2_per_pt=yax.per_pt(),
                    n_light_vertices=len(jv), n_dark_points=len(jvd),
                    light_V_range=[float(jv[:, 0].min()), float(jv[:, 0].max())],
                    light_J_range=[float(jv[:, 1].min()), float(jv[:, 1].max())])
overlay(p4, clip, [dict(pts=Cr, label="light, vector centreline (RDP vertices)", color="lime", fmt="o", ms=1.5),
                   dict(pts=dk, label="dark, dash centres", color="cyan", fmt="o", ms=1.5)],
        "S1_fig3a_JV_overlay.png", "S1 Fig. 3a J-V: extracted points on the published figure")

# ------------------------------------------------------------------ Figure 3b EQE
clip = (300, 70, 470, 185)
ps = V.prims(p4, clip)
xax = V.calibrate(ps, "x", 176.272, (335.5, 456.2), [300, 400, 500, 600, 700, 800, 900, 1000], label="3b x")
yax = V.calibrate(ps, "y", 335.859, (79.4, 176.5), [100, 80, 60, 40, 20, 0], label="3b y")
eqe_d = max([d for d in ps if V.close(V.pcol(d), RED)], key=lambda d: len(d["items"]))
der_d = max([d for d in ps if V.close(V.pcol(d), BLUE)], key=lambda d: len(d["items"]))
Ce, we = V.centreline(V.subpaths(eqe_d))
Cd, wd = V.centreline(V.subpaths(der_d))
Ce = V.despike(V.refine_normal(V.subpaths(eqe_d), Ce))
Cd = V.despike(V.refine_normal(V.subpaths(der_d), Cd))
Ce, Cd = V.trim_ends(Ce, we / 2), V.trim_ends(Cd, wd / 2)
Cer, Cdr = V.rdp(Ce, 0.02), V.rdp(Cd, 0.02)
# The polyline vertices sit on a 10 nm grid (see validation); resample the dense
# centreline exactly on that grid so each row is one plotted data point.
lam_e, lam_d = xax(Ce[:, 0]), xax(Cd[:, 0])
grid_e = np.arange(np.ceil((lam_e.min() - 0.6) / 10) * 10, lam_e.max() + 0.6, 10.0)
grid_d = np.arange(np.ceil((lam_d.min() - 0.6) / 10) * 10, lam_d.max() + 0.6, 10.0)
ge, dis_e = V.grid_vertices(lam_e, yax(Ce[:, 1]), grid_e, 2.6)
gd, dis_d = V.grid_vertices(lam_d, yax(Cd[:, 1]), grid_d, 2.6)
eqe = np.column_stack([grid_e, ge])
der = np.column_stack([grid_d, gd])
vx = xax(Cer[:, 0])
turn = []
for i in range(1, len(Cer) - 1):
    a, b = Cer[i] - Cer[i - 1], Cer[i + 1] - Cer[i]
    ang = abs(np.degrees(np.arctan2(a[0] * b[1] - a[1] * b[0], a @ b)))
    if ang > 8:
        turn.append(vx[i])
turn = np.array(turn)
off = (turn + 5) % 10 - 5
write_csv("S1_fig3b_EQE.csv", ["wavelength_nm", "EQE_pct"], eqe, ["%.1f", "%.3f"])
der = np.column_stack([der, (der[:, 1] < 0).astype(float)])
write_csv("S1_fig3b_minus_dEQE_dlambda.csv",
          ["wavelength_nm", "minus_dEQE_dlambda_plotted_on_EQE_pct_axis", "outside_plotted_axes"], der,
          ["%.1f", "%.3f", "%d"])
# band gap from the derivative peak (authors: 1.41 eV)
lam = xax(Cd[:, 0])
pk = lam[np.argmax(yax(Cd[:, 1]))]
# Jsc from EQE x AM1.5G is not computed here (no spectrum file shipped); grid check instead
gx = eqe[:, 0]
val["fig3b"] = dict(n_points=len(eqe), lambda_min=float(gx.min()), lambda_max=float(gx.max()),
                    sharp_vertices_n=len(turn), sharp_vertex_offset_from_10nm_grid_median_abs_nm=float(np.median(np.abs(off))),
                    sharp_vertex_offset_from_10nm_grid_max_abs_nm=float(np.max(np.abs(off))),
                    stroke_width_pt=we,
                    grid_vertex_two_sided_disagreement_median_pct=float(np.nanmedian(dis_e)),
                    grid_vertex_two_sided_disagreement_p95_pct=float(np.nanpercentile(dis_e, 95)),
                    grid_vertex_two_sided_disagreement_max_pct=float(np.nanmax(dis_e)),
                    dEQE_peak_nm=float(pk), Eg_from_peak_eV=1239.84 / float(pk),
                    EQE_max_pct=float(eqe[:, 1].max()), x_resid_pt=xax.resid_pt, y_resid_pt=yax.resid_pt,
                    nm_per_pt=xax.per_pt(), pct_per_pt=yax.per_pt())
overlay(p4, clip, [dict(pts=np.column_stack([xax.inv(eqe[:, 0]), yax.inv(eqe[:, 1])]), label="EQE, 10 nm grid points",
                        color="lime", ms=2),
                   dict(pts=np.column_stack([xax.inv(der[:, 0]), yax.inv(der[:, 1])]),
                        label="-dEQE/dlambda, 10 nm grid points", color="cyan", ms=2)],
        "S1_fig3b_EQE_overlay.png", "S1 Fig. 3b EQE: extracted points on the published figure")

# ------------------------------------------------------------------ Figure 3c N_A(W)
clip = (130, 220, 290, 335)
ps = V.prims(p4, clip)
xax = V.calibrate(ps, "x", 326.001, (156.0, 276.6), [0.0, 0.1, 0.2, 0.3, 0.4], label="3c x")
yax = V.calibrate(ps, "y", 156.394, (229.0, 326.3), [1e17, 1e16, 1e15], log=True, label="3c y")
cv_d = max([d for d in ps if V.close(V.pcol(d), RED)], key=lambda d: len(d["items"]))
sq = [d for d in ps if V.close(V.pcol(d), BLUE)]
Cc, wc = V.centreline(V.subpaths(cv_d))
Cc = V.despike(V.refine_normal(V.subpaths(cv_d), Cc))
Cc = V.trim_ends(Cc, wc / 2)
Ccr = V.rdp(Cc, 0.02)
cv = np.column_stack([xax(Ccr[:, 0]), yax(Ccr[:, 1])])
write_csv("S1_fig3c_NA_vs_depletion_width.csv", ["depletion_width_um", "N_A_cm-3"], cv, ["%.5f", "%.5e"])
sx, sy = V.center(sq[0])
val["fig3c"] = dict(zero_bias_W_um=float(xax(sx)), zero_bias_NA_cm3=float(yax(sy)), n_vertices=len(cv),
                    W_range_um=[float(cv[:, 0].min()), float(cv[:, 0].max())],
                    NA_min=float(cv[:, 1].min()), NA_max=float(cv[:, 1].max()),
                    x_resid_pt=xax.resid_pt, y_resid_pt=yax.resid_pt, um_per_pt=xax.per_pt(),
                    decades_per_pt=yax.per_pt())
write_csv("S1_fig3c_zero_bias_point.csv", ["depletion_width_um", "N_A_cm-3"], [[xax(sx), yax(sy)]],
          ["%.5f", "%.5e"])
overlay(p4, clip, [dict(pts=Ccr, label="N_A(W) vertices", color="lime", ms=1.5),
                   dict(pts=[(sx, sy)], label="zero-bias square centre", color="yellow", fmt="+", ms=8)],
        "S1_fig3c_CV_overlay.png", "S1 Fig. 3c C-V profile: extracted points on the published figure")

# ------------------------------------------------------------------ Figure 3d Voc(T)
clip = (300, 220, 470, 335)
ps = V.prims(p4, clip)
xax = V.calibrate(ps, "x", 325.947, (335.5, 456.2), [0, 50, 100, 150, 200, 250, 300, 350, 400], label="3d x")
yax = V.calibrate(ps, "y", 335.805, (229.0, 326.3), [1.4, 1.3, 1.2, 1.1, 1.0, 0.9, 0.8, 0.7], label="3d y")
mk = [d for d in ps if V.close(V.pcol(d), BLUE)]
mxy = np.array([V.center(d) for d in mk])
mxy = mxy[np.argsort(mxy[:, 0])]
vt = np.column_stack([xax(mxy[:, 0]), yax(mxy[:, 1])])
write_csv("S1_fig3d_Voc_vs_T.csv", ["T_K", "Voc_V"], vt, ["%.2f", "%.5f"])
lines = [d for d in ps if V.close(V.pcol(d), RED)]
fitpts = []
for d in lines:
    Cl, wl = V.centreline(V.subpaths(d))
    fitpts.append(V.trim_ends(Cl, wl / 2))
Cl = np.vstack(fitpts)
Cl = Cl[np.argsort(Cl[:, 0])]
ft = np.column_stack([xax(Cl[:, 0]), yax(Cl[:, 1])])
k = np.polyfit(ft[:, 0], ft[:, 1], 1)
hi = (vt[:, 0] >= 314) & (vt[:, 0] <= 356)
kk = np.polyfit(vt[hi, 0], vt[hi, 1], 1)
val["fig3d"] = dict(n_markers=len(vt), plotted_fit_line_intercept_V=float(k[1]), plotted_fit_line_slope_V_per_K=float(k[0]),
                    refit_315_355K_intercept_V=float(kk[1]), refit_slope_V_per_K=float(kk[0]),
                    refit_n_points=int(hi.sum()), x_resid_pt=xax.resid_pt, y_resid_pt=yax.resid_pt,
                    K_per_pt=xax.per_pt(), V_per_pt=yax.per_pt())
write_csv("S1_fig3d_fit_line.csv", ["T_K", "Voc_V"], ft[:: max(1, len(ft) // 200)], ["%.2f", "%.5f"])
overlay(p4, clip, [dict(pts=mxy, label="marker centres", color="lime", fmt="+", ms=6),
                   dict(pts=Cl[:: max(1, len(Cl) // 300)], label="fit line centreline", color="cyan", ms=0.8)],
        "S1_fig3d_VocT_overlay.png", "S1 Fig. 3d Voc(T): extracted points on the published figure")

with open(os.path.join(CUR, "S1_validation.json"), "w") as f:
    json.dump(val, f, indent=1, default=float)
print(json.dumps(val, indent=1, default=float))
