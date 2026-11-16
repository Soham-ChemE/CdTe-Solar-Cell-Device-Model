"""Write curves/index.csv: one row per data file in curves/ with source, figure,
page, columns, method, overlay image and digitisation uncertainty.

Usage: python -I make_index.py <kujovic_family folder>
"""
import csv
import json
import os
import re
import sys

OUT = sys.argv[1]
CUR = os.path.join(OUT, "curves")
acc = json.load(open(os.path.join(CUR, "S1_vs_S4_accuracy.json")))
v1 = json.load(open(os.path.join(CUR, "S1_validation.json")))
rows = []


def header(f):
    with open(os.path.join(CUR, f)) as fh:
        return fh.readline().strip()


def nrows(f):
    with open(os.path.join(CUR, f)) as fh:
        return sum(1 for _ in fh) - 1


S1 = [
    ("S1_fig2_boxplots.csv", "S1 Fig. 2a-d", 3, "box-plot statistics (Q1, median, Q3, mean, whiskers, outliers)",
     "vector geometry of boxes, bars and markers", "S1_fig2_*_overlay.png",
     "< 0.001 in each unit (axis-fit residual <= 0.026 pt; e.g. 0.034 %eff per pt)"),
    ("S1_fig3a_JV_light.csv", "S1 Fig. 3a", 4, "illuminated J-V of the 21.44% cell (MAR coated)",
     "vector centreline of the filled stroke outline (slices + normal refinement), RDP 0.02 pt",
     "S1_fig3a_JV_overlay.png",
     "vs exact thesis vertices: |dJ| median %.4f, max %.4f mA/cm2 (flat); |dV| max %.3f mV (steep)" % (
         acc["JV_flat_dJ_mA_cm2"]["median_abs"], acc["JV_flat_dJ_mA_cm2"]["max_abs"], acc["JV_steep_dV_mV"]["max_abs"])),
    ("S1_fig3a_JV_dark.csv", "S1 Fig. 3a", 4, "dark J-V (dashed) of the same cell",
     "centre line of each dash (two points per dash)", "S1_fig3a_JV_overlay.png", "about 0.02 pt (0.2 mV, 0.02 mA/cm2)"),
    ("S1_fig3b_EQE.csv", "S1 Fig. 3b", 4, "EQE of the 21.44% cell on the 10 nm measurement grid",
     "vector centreline, then straight-segment fits evaluated at the 10 nm grid", "S1_fig3b_EQE_overlay.png",
     "vs thesis vertices: median %.3f, max %.2f EQE-%% (max at the steep edges; = 0.1 nm in wavelength)" % (
         acc["EQE_grid_dEQE_pct"]["median_abs"], acc["EQE_grid_dEQE_pct"]["max_abs"])),
    ("S1_fig3b_minus_dEQE_dlambda.csv", "S1 Fig. 3b", 4,
     "-dEQE/dlambda as plotted on the EQE axis (arbitrary scale); negative values are clipped in the figure",
     "as EQE", "S1_fig3b_EQE_overlay.png", "as EQE"),
    ("S1_fig3c_NA_vs_depletion_width.csv", "S1 Fig. 3c", 4, "C-V hole density vs depletion width (40 kHz)",
     "vector centreline, log10 y-axis calibration", "S1_fig3c_CV_overlay.png",
     "vs thesis vertices: median %.3f%%, max %.3f%% in N_A" % (100 * acc["CV_relative_dNA"]["median_abs"],
                                                              100 * acc["CV_relative_dNA"]["max_abs"])),
    ("S1_fig3c_zero_bias_point.csv", "S1 Fig. 3c", 4, "zero-bias point (blue square centre)", "marker centre",
     "S1_fig3c_CV_overlay.png", "0.2% in N_A"),
    ("S1_fig3d_Voc_vs_T.csv", "S1 Fig. 3d", 4, "Voc vs temperature markers", "marker centres",
     "S1_fig3d_VocT_overlay.png", "identical to thesis markers within 0.006 K and 1e-5 V"),
    ("S1_fig3d_fit_line.csv", "S1 Fig. 3d", 4, "the authors' linear fit line (subsampled)", "vector centreline",
     "S1_fig3d_VocT_overlay.png", "intercept 1.3587 V vs 1.36 eV stated"),
]
for f, fig, pg, what, meth, ov, unc in S1:
    rows.append(dict(file=f, source_id="S1", paper_figure=fig, thesis_figure="", read_from="S1 journal PDF",
                     pdf_page=pg, series=what,
                     columns=header(f), n_rows=nrows(f), method=meth, overlay_png=ov, est_uncertainty=unc))

PAPER = {"S1fig2": ("S1", "S1 Fig. 2"), "S1fig3a": ("S1", "S1 Fig. 3a"), "S1fig3b": ("S1", "S1 Fig. 3b"),
         "S1fig3c": ("S1", "S1 Fig. 3c"), "S1fig3d": ("S1", "S1 Fig. 3d"), "S2fig2": ("S2", "S2 Fig. 2"),
         "S2fig3": ("S2", "S2 Fig. 3"), "S2fig4a": ("S2", "S2 Fig. 4a"), "S2fig4b": ("S2", "S2 Fig. 4b"),
         "S2fig5": ("S2", "S2 Fig. 5"), "S2fig6": ("S2", "S2 Fig. 6"), "S3fig2": ("S3", "S3 Fig. 2"),
         "S3fig3": ("S3", "S3 Fig. 3"), "S3fig4a": ("S3", "S3 Fig. 4a"), "S3fig4b": ("S3", "S3 Fig. 4b"),
         "S3fig5a": ("S3", "S3 Fig. 5a"), "S3fig5b": ("S3", "S3 Fig. 5b"), "S3fig6a": ("S3", "S3 Fig. 6a"),
         "S3fig6b": ("S3", "S3 Fig. 6b"), "S3fig7": ("S3", "S3 Fig. 7")}
idx = json.load(open(os.path.join(CUR, "S4_index.json")))
seen = set()
for e in idx:
    f = e["file"]
    if f in seen and e["kind"] == "boxplot":
        continue
    seen.add(f)
    fid = e["figure"]
    m = re.search(r"_(S\dfig\d+[ab]?)$", fid) or re.search(r"_(S\dfig\d+[ab]?)_", fid)
    src, pfig = PAPER.get(m.group(1), ("S4", "")) if m else ("S4", "")
    tfig = "Fig. " + fid.split("_")[0].replace("fig", "")
    if e["kind"] == "boxplot":
        boxes = [x for x in idx if x["file"] == f]
        unc = "< %.3g in each unit (axis-fit residual <= %.3f pt)" % (
            max(0.03 * x["y_units_per_pt"] for x in boxes if not x["y_log"]) if any(not x["y_log"] for x in boxes)
            else 0, max(x["y_resid_pt"] for x in boxes))
        if any(x["y_log"] for x in boxes):
            unc += "; J0 (log axis) < 0.5%"
        what = "box-plot statistics (Q1, median, Q3, mean, whiskers, outliers): " + ", ".join(x["series"] for x in boxes)
        meth = "vector geometry of boxes, bars and markers (thesis stroked paths, tick labels read as text)"
        ov = f"S4_{fid}_*_overlay.png"
    else:
        r = max(0.03, e["y_resid_pt"] or 0)
        if e["y_log"]:
            uy = "%.2g%% (log)" % (100 * (10 ** (r * e["y_units_per_pt"]) - 1))
        else:
            uy = "%.2g" % (r * e["y_units_per_pt"])
        ux = "%.2g" % (max(0.03, e["x_resid_pt"] or 0) * e["x_units_per_pt"]) if e["x_units_per_pt"] else "n/a"
        unc = f"x {ux}, y {uy} (data units; plotted vertices, error = axis calibration)"
        meth = {"solid": "vertices of the stroked polyline (= plotted data points)",
                "dash": "end points of the dash segments (= points on the plotted line)",
                "pieces": "end points of the separate line segments (= plotted data points)",
                "markers": "marker centres"}[e["kind"]]
        what = e["series"]
        ov = f"S4_{fid}_overlay.png"
        if e["n_outside"]:
            what += f" ({e['n_outside']} points lie outside the plotted axes and are hidden in the figure)"
    rows.append(dict(file=f, source_id=src, paper_figure=pfig, thesis_figure=tfig, read_from="S4 thesis PDF",
                     pdf_page=e["page"], series=what,
                     columns=header(f), n_rows=nrows(f), method=meth, overlay_png=ov, est_uncertainty=unc))

with open(os.path.join(CUR, "index.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print("index rows", len(rows))
