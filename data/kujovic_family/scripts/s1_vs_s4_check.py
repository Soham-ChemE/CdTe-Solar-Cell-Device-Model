"""Accuracy of the journal (S1) centreline extraction, measured against the exact
vertices of the same curves in the thesis (S4 Ch. 3), which are stroked polylines.

Usage: python -I s1_vs_s4_check.py <kujovic_family folder>
"""
import json
import os
import sys

import numpy as np

CUR = os.path.join(sys.argv[1], "curves")


def load(f):
    return np.genfromtxt(os.path.join(CUR, f), delimiter=",", skip_header=1)[:, :2]


res = {}
# J-V: compare in V at fixed J for the steep part and in J at fixed V for the flat part
a, b = load("S1_fig3a_JV_light.csv"), load("S4_fig3.3_JV_21p4pct_S1fig3a_light.csv")
a = a[(a[:, 0] >= -195) & (a[:, 0] <= 925) & (a[:, 1] <= 40)]
flat = (a[:, 0] > -190) & (a[:, 0] < 700)
dJ = a[flat, 1] - np.interp(a[flat, 0], b[:, 0], b[:, 1])
st = (a[:, 1] > -20) & (a[:, 1] < 35)
o = np.argsort(b[:, 1])
dV = a[st, 0] - np.interp(a[st, 1], b[o, 1], b[o, 0])
res["JV_flat_dJ_mA_cm2"] = dict(median_abs=float(np.median(np.abs(dJ))), p95_abs=float(np.percentile(np.abs(dJ), 95)),
                                max_abs=float(np.abs(dJ).max()), n=int(len(dJ)))
res["JV_steep_dV_mV"] = dict(median_abs=float(np.median(np.abs(dV))), p95_abs=float(np.percentile(np.abs(dV), 95)),
                             max_abs=float(np.abs(dV).max()), n=int(len(dV)))
# EQE: both on the 10 nm grid
a, b = load("S1_fig3b_EQE.csv"), load("S4_fig3.4_EQE_21p4pct_S1fig3b_EQE.csv")
res["thesis_EQE_wavelengths_on_10nm_grid_max_offset_nm"] = float(np.max(np.abs(b[:, 0] - 10 * np.round(b[:, 0] / 10))))
bg = np.column_stack([10 * np.round(b[:, 0] / 10), b[:, 1]])
common = np.intersect1d(a[:, 0], bg[:, 0])
d = np.array([a[a[:, 0] == L, 1][0] - bg[bg[:, 0] == L, 1][0] for L in common])
res["EQE_grid_dEQE_pct"] = dict(median_abs=float(np.median(np.abs(d))), p95_abs=float(np.percentile(np.abs(d), 95)),
                                max_abs=float(np.abs(d).max()), n=int(len(d)))
# C-V
a, b = load("S1_fig3c_NA_vs_depletion_width.csv"), load("S4_fig3.5_CV_21p4pct_S1fig3c_NA.csv")
m = (a[:, 0] > b[:, 0].min()) & (a[:, 0] < b[:, 0].max())
o = np.argsort(b[:, 0])
r = a[m, 1] / np.interp(a[m, 0], b[o, 0], b[o, 1]) - 1
res["CV_relative_dNA"] = dict(median_abs=float(np.median(np.abs(r))), p95_abs=float(np.percentile(np.abs(r), 95)),
                              max_abs=float(np.abs(r).max()), n=int(len(r)))
# Voc(T) markers
a, b = load("S1_fig3d_Voc_vs_T.csv"), load("S4_fig3.6_VocT_21p4pct_S1fig3d_Voc.csv")
res["VocT_markers"] = dict(n_journal=int(len(a)), n_thesis=int(len(b)),
                           max_abs_dT_K=float(np.max(np.abs(a[:, 0] - b[:, 0]))) if len(a) == len(b) else None,
                           max_abs_dVoc_V=float(np.max(np.abs(a[:, 1] - b[:, 1]))) if len(a) == len(b) else None)
with open(os.path.join(CUR, "S1_vs_S4_accuracy.json"), "w") as f:
    json.dump(res, f, indent=1)
print(json.dumps(res, indent=1))
