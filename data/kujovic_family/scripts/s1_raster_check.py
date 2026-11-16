"""Independent raster digitisation of S1 Figure 3 and Figure 2 medians.

The page is rendered at 600 dpi, curve pixels are found by colour, and the centre
of each run of curve pixels is converted to data with the tick calibration.
Results are compared with the vector extraction (curves/S1_*.csv) and with the
values printed in the paper.

Usage: python -I s1_raster_check.py <S1 PDF> <kujovic_family folder>
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
DPI = 600
RED255 = (237, 33, 36)
BLUE255 = (59, 84, 163)
res = {}
doc, p3 = V.open_page(PDF, 3)
_, p4 = V.open_page(PDF, 4)


def load(fname):
    return np.genfromtxt(os.path.join(CUR, fname), delimiter=",", names=True)


def stats(d):
    d = np.abs(np.asarray(d))
    return dict(median=float(np.median(d)), p95=float(np.percentile(d, 95)), max=float(d.max()), n=int(len(d)))


def both_scans(img, clip, rgb, tol, wmax_px):
    """Raster centreline: column runs where thin in y, row runs where thin in x."""
    cx, m = V.raster_curve(img, clip, DPI, rgb, tol, "x")
    out = []
    s = 72.0 / DPI
    # recompute with run lengths to filter thick (steep) runs
    for c in range(m.shape[1]):
        rows = np.flatnonzero(m[:, c])
        if not len(rows):
            continue
        for r in np.split(rows, np.flatnonzero(np.diff(rows) > 1) + 1):
            if len(r) <= wmax_px:
                out.append(V.pix_to_pt(clip, DPI, c, r.mean()))
    for rr in range(m.shape[0]):
        cols = np.flatnonzero(m[rr, :])
        if not len(cols):
            continue
        for r in np.split(cols, np.flatnonzero(np.diff(cols) > 1) + 1):
            if len(r) <= wmax_px:
                out.append(V.pix_to_pt(clip, DPI, r.mean(), rr))
    return np.array(out).reshape(-1, 2), m


# ------------------------------------------------------------------ 3a J-V
clip = (130, 70, 290, 185)
ps = V.prims(p4, clip)
xax = V.calibrate(ps, "x", 127.984, (156.0, 276.6), [-200, 0, 200, 400, 600, 800, 1000])
yax = V.calibrate(ps, "y", 176.410, (79.4, 176.5), [40, 30, 20, 10, 0, -10, -20, -30, -40])
img, _ = V.render(p4, clip, DPI)
P, m = both_scans(img, clip, RED255, 90, 12)
vl = load("S1_fig3a_JV_light.csv")
vd = load("S1_fig3a_JV_dark.csv")
Lp = np.column_stack([xax.inv(vl["V_mV"]), yax.inv(vl["J_mA_cm2"])])
Dp = np.column_stack([xax.inv(vd["V_mV"]), yax.inv(vd["J_mA_cm2"])])
dist = np.minimum(V.dist_to_polyline(P, Lp), V.dist_to_polyline(P, Dp))
res["fig3a_raster_vs_vector_pt"] = stats(dist)
# figures of merit from raster pixels only (fourth quadrant = light curve)
Vr, Jr = xax(P[:, 0]), yax(P[:, 1])
q4 = (Jr < 0.5) & (Vr > -50)
near0 = q4 & (np.abs(Vr) < 3)
jsc = -np.mean(Jr[near0 & (Jr < -20)])
cross = q4 & (Vr > 800) & (np.abs(Jr) < 1.5)
kk = np.polyfit(Jr[cross], Vr[cross], 1)
voc = kk[1]
sel = q4 & (Vr > 0) & (Vr < voc) & (Jr < 0)
Pw = -(Vr[sel] * Jr[sel]) / 1000
pmax = Pw.max()
res["fig3a_raster_FoM"] = dict(Jsc_mA_cm2=float(jsc), Voc_mV=float(voc), FF_pct=float(100 * pmax * 1000 / (voc * jsc)),
                               eta_pct=float(pmax))
fig, ax = plt.subplots(figsize=(7, 5))
ax.imshow(img, extent=[clip[0], clip[2], clip[3], clip[1]])
ax.plot(P[:, 0], P[:, 1], ".", ms=0.6, color="cyan", label="raster run centres")
ax.plot(Lp[:, 0], Lp[:, 1], "-", lw=0.5, color="black", label="vector centreline")
ax.legend(fontsize=6)
ax.set_title("S1 Fig. 3a: raster digitisation (cyan) vs vector extraction (black)", fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(CUR, "S1_fig3a_JV_raster_check.png"), dpi=200)
plt.close(fig)

# ------------------------------------------------------------------ 3b EQE
clip = (300, 70, 470, 185)
ps = V.prims(p4, clip)
xax = V.calibrate(ps, "x", 176.272, (335.5, 456.2), [300, 400, 500, 600, 700, 800, 900, 1000])
yax = V.calibrate(ps, "y", 335.859, (79.4, 176.5), [100, 80, 60, 40, 20, 0])
img, _ = V.render(p4, clip, DPI)
P, m = both_scans(img, clip, RED255, 90, 12)
# drop the legend line: the short red drawing that is not the EQE curve
REDF = (0.931, 0.130, 0.141)
reds = sorted([d for d in ps if V.close(V.pcol(d), REDF)], key=lambda d: len(d["items"]))
lr = reds[0]["rect"]
leg = (P[:, 0] > lr.x0 - 0.5) & (P[:, 0] < lr.x1 + 0.5) & (P[:, 1] > lr.y0 - 0.5) & (P[:, 1] < lr.y1 + 0.5)
res["fig3b_legend_pixels_removed"] = int(leg.sum())
P = P[~leg]
ve = load("S1_fig3b_EQE.csv")
Ep = np.column_stack([xax.inv(ve["wavelength_nm"]), yax.inv(ve["EQE_pct"])])
inside = (P[:, 1] < 176.0)  # exclude pixels merged with the x-axis line
dist = V.dist_to_polyline(P[inside], Ep)
res["fig3b_raster_vs_vector_pt"] = stats(dist)
# EQE at 600 nm from raster columns
col = np.abs(xax(P[:, 0]) - 600) < 1.0
res["fig3b_raster_EQE_at_600nm"] = float(np.mean(yax(P[col, 1])))
res["fig3b_vector_EQE_at_600nm"] = float(np.interp(600, ve["wavelength_nm"], ve["EQE_pct"]))

# ------------------------------------------------------------------ 3c C-V
clip = (130, 220, 290, 335)
ps = V.prims(p4, clip)
xax = V.calibrate(ps, "x", 326.001, (156.0, 276.6), [0.0, 0.1, 0.2, 0.3, 0.4])
yax = V.calibrate(ps, "y", 156.394, (229.0, 326.3), [1e17, 1e16, 1e15], log=True)
img, _ = V.render(p4, clip, DPI)
P, m = both_scans(img, clip, RED255, 90, 12)
vc = load("S1_fig3c_NA_vs_depletion_width.csv")
Cp = np.column_stack([xax.inv(vc["depletion_width_um"]), yax.inv(vc["N_A_cm3"])])
dist = V.dist_to_polyline(P, Cp)
res["fig3c_raster_vs_vector_pt"] = stats(dist)
# zero-bias square: centroid of blue pixels
mb = np.sqrt(((img.astype(float) - np.array(BLUE255)) ** 2).sum(-1)) < 60
rr, cc = np.nonzero(mb)
sx, sy = V.pix_to_pt(clip, DPI, cc.mean(), rr.mean())
res["fig3c_raster_zero_bias"] = dict(W_um=float(xax(sx)), NA_cm3=float(yax(sy)))

# ------------------------------------------------------------------ 3d Voc(T) markers
clip = (300, 220, 470, 335)
ps = V.prims(p4, clip)
xax = V.calibrate(ps, "x", 325.947, (335.5, 456.2), [0, 50, 100, 150, 200, 250, 300, 350, 400])
yax = V.calibrate(ps, "y", 335.805, (229.0, 326.3), [1.4, 1.3, 1.2, 1.1, 1.0, 0.9, 0.8, 0.7])
img, _ = V.render(p4, clip, DPI)
# markers are blue; where the red fit line crosses them they look purple, so accept both
f = img.astype(float)
mb = (f[:, :, 2] > 110) & (f[:, :, 1] < 120) & (f[:, :, 0] < 200)
from scipy import ndimage  # noqa: E402

# the red fit line is drawn over some markers and splits them; close the gap
# (line width ~4 px at 600 dpi) and use the bounding-box centre of each blob
mbc = ndimage.binary_closing(mb, structure=np.ones((7, 7)))
lab, n = ndimage.label(mbc)
sl = ndimage.find_objects(lab)
sizes = ndimage.sum(mbc, lab, range(1, n + 1))
pts = np.array([V.pix_to_pt(clip, DPI, 0.5 * (s[1].start + s[1].stop - 1), 0.5 * (s[0].start + s[0].stop - 1))
                for s, z in zip(sl, sizes) if z > 60])
vt = load("S1_fig3d_Voc_vs_T.csv")
vpts = np.column_stack([xax.inv(vt["T_K"]), yax.inv(vt["Voc_V"])])
dd = [np.min(np.hypot(*(vpts - q).T)) for q in pts]
res["fig3d_raster_marker_blobs"] = int(len(pts))
res["fig3d_raster_vs_vector_marker_centre_pt"] = stats(dd)
hi = (xax(pts[:, 0]) > 312) & (xax(pts[:, 0]) < 358)
kk = np.polyfit(xax(pts[hi, 0]), yax(pts[hi, 1]), 1)
res["fig3d_raster_refit_intercept_V"] = float(kk[1])
res["fig3d_raster_refit_npts"] = int(hi.sum())

# ------------------------------------------------------------------ Fig 2 medians
bx = np.genfromtxt(os.path.join(CUR, "S1_fig2_boxplots.csv"), delimiter=",", names=True, dtype=None, encoding=None)
panels = {
    "eta_pct": ((119, 72, 290, 205), 139.178, (79.8, 198.1), [22, 21, 20, 19, 18]),
    "Voc_mV": ((300, 72, 470, 205), 323.997, (79.8, 198.1), [885, 880, 875, 870, 865, 860, 855]),
    "Jsc_mA_cm2": ((119, 220, 290, 360), 139.178, (239.9, 358.2), [31, 30, 29, 28]),
    "FF_pct": ((300, 220, 470, 360), 323.997, (239.9, 358.2), [82, 80, 78, 76]),
}
diffs = {}
for name, (clip, xline, yspan, vals) in panels.items():
    ps = V.prims(p3, clip)
    yax = V.calibrate(ps, "y", xline, yspan, vals)
    img, _ = V.render(p3, clip, DPI)
    f = img.astype(float)
    teal = np.sqrt(((f - np.array([103, 155, 155])) ** 2).sum(-1)) < 40
    dark = f.max(-1) < 90
    rows = bx[bx["parameter"] == name]
    # box columns: x ranges where teal pixels exist
    colsum = teal.sum(0)
    on = np.flatnonzero(colsum > 3)
    groups = np.split(on, np.flatnonzero(np.diff(on) > 3) + 1)
    groups = [g for g in groups if len(g) > 40]
    out = []
    for g, r in zip(groups, rows):
        c0, c1 = g[0], g[-1]
        mid = slice(c0 + (c1 - c0) // 4, c1 - (c1 - c0) // 4)
        tr = np.flatnonzero(teal[:, mid].sum(1) > 0)
        top, bot = tr.min(), tr.max()
        drows = np.flatnonzero(dark[top + 4:bot - 3, mid].mean(1) > 0.8) + top + 4
        if len(drows) == 0:
            out.append(np.nan)
            continue
        runs = np.split(drows, np.flatnonzero(np.diff(drows) > 1) + 1)
        best = max(runs, key=len)
        _, ypt = V.pix_to_pt(clip, DPI, 0, best.mean())
        out.append(float(yax(ypt)) - float(r["median"]))
    diffs[name] = out
res["fig2_raster_minus_vector_median"] = diffs

with open(os.path.join(CUR, "S1_raster_check.json"), "w") as fh:
    json.dump(res, fh, indent=1)
print(json.dumps(res, indent=1))
