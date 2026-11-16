"""Cross-check: box plots of the journal version of the CeZnO paper (S3, Fig. 2,
filled-outline vector graphics) against the thesis version (Fig. 5.9).

Usage: python -I s3_crosscheck.py <S3 PDF> <kujovic_family folder>
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import vecfig as V  # noqa: E402

PDF, OUT = sys.argv[1], sys.argv[2]
doc, p = V.open_page(PDF, 4)
TEAL = (0.400, 0.605, 0.605)
ORANGE = (0.942, 0.509, 0.149)
labels = ["ZnO/50", "ZnO/100", "3%CeZnO/50", "3%CeZnO/100", "6%CeZnO/50", "6%CeZnO/100", "9%CeZnO/50", "9%CeZnO/100"]
panels = {
    "eta_pct": ((119, 165, 330, 340), 161.597, (177.85, 303.67), [21, 20, 19, 18, 17, 16]),
    "Voc_mV": ((330, 165, 560, 340), 377.830, (177.85, 303.67), [860, 840, 820, 800]),
    "Jsc_mA_cm2": ((119, 340, 330, 560), 161.597, (367.91, 493.73), [31, 30, 29, 28]),
    "FF_pct": ((330, 340, 560, 560), 377.830, (367.91, 493.73), [82, 80, 78, 76, 74, 72, 70]),
}
th = {}
for r in csv.DictReader(open(os.path.join(OUT, "curves", "S4_fig5.9_CeZnO_compound_target_S3fig2_boxplots.csv"))):
    th[(r["buffer/thickness_nm"], r["parameter"])] = r
res, rows = {}, []
for name, (clip, xline, span, vals) in panels.items():
    ps = V.prims(p, clip)
    yax = V.calibrate(ps, "y", xline, (span[0] - 0.3, span[1] + 0.3), vals, label=name)
    xr = 317.0 if xline < 300 else 533.2  # right frame of the panel
    bx = V.boxplots(ps, (xline, span[0], xr, span[1]), [TEAL, ORANGE], yax)
    assert len(bx) == 8, (name, len(bx))
    for lab, b in zip(labels, bx):
        t = th[(lab, name)]
        d = {k: b[k] - float(t[k2]) for k, k2 in (("q1", "Q1"), ("median", "median"), ("q3", "Q3"), ("mean", "mean"),
                                                   ("whisker_lo", "whisker_lo"), ("whisker_hi", "whisker_hi"))}
        rows.append((name, lab, max(abs(v) for v in d.values())))
    res[name + "_max_abs_diff_journal_minus_thesis"] = max(r[2] for r in rows if r[0] == name)
    res[name + "_units_per_pt"] = yax.per_pt()
with open(os.path.join(OUT, "curves", "S3_vs_S4_boxplot_crosscheck.json"), "w") as f:
    json.dump(res, f, indent=1)
print(json.dumps(res, indent=1))
