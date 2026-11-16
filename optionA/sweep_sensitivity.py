"""One-at-a-time sensitivity sweeps of the MgZnO-series model at three offsets (cliff, optimum, large spike).
Tells the calibration which priors can move Voc, FF and the offset trend. Runs on all SCAPS prefixes in parallel.
Output: optionA/sweep_sensitivity.csv
"""
import csv
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import mzo_model as m
from scaps_tools import run_parallel, read_iv, RESULTS

POINTS = {0.00: (-0.10, 3.28), 0.15: (0.19, 3.71), 0.25: (0.27, 3.83)}
SWEEPS = {
    "S_front": [1e2, 1e3, 1e4, 1e5, 1e6, 1e7],
    "ND_MZO": [1e14, 1e15, 1e16, 1e17, 1e18],
    "NA": [2e14, 5e14, 1e15, 3e15, 1e16],
    "tau": [3e-9, 10e-9, 30e-9, 100e-9, 300e-9],
    "phi_back": [4.8, 4.95, 5.1, 5.25, 5.4],
}
cases, meta = [], []
for x, (dEc, Eg) in POINTS.items():
    for par, vals in SWEEPS.items():
        for k, v in enumerate(vals):
            p = {**m.P, par: v}
            suf = f"_s_{par}_{k}"
            name = m.build(x, dEc, Eg, p=p, suffix=suf)
            cases.append(dict(deffile=f"{name}.def", out=name, step=0.01, stopV=1.2))
            meta.append((x, dEc, par, v, name))
t = time.time()
run_parallel("A_sens", cases, timeout=5400)
print(f"{len(cases)} cases, wall {time.time() - t:.0f} s")
rows = []
for x, dEc, par, v, name in meta:
    f = RESULTS / f"{name}.iv"
    iv = read_iv(f) if f.exists() else {}
    ok = bool(iv) and iv.get("deffile", "") == f"{name}.def" and iv["Voc"] == iv["Voc"]
    rows.append({"x": x, "dEc": dEc, "param": par, "value": v,
                 "Voc_mV": iv["Voc"] * 1000 if ok else "", "Jsc": iv["Jsc"] if ok else "",
                 "FF": iv["FF"] if ok else "", "eta": iv["eta"] if ok else "", "ok": ok})
with open(Path(__file__).with_name("sweep_sensitivity.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print("failed:", sum(not r["ok"] for r in rows), "of", len(rows))
