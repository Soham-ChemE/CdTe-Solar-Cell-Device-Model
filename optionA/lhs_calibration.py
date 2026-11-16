"""Latin-hypercube sampling of the MgZnO-series model for calibration and identifiability.

Six uncertain inputs, sampled within literature-backed ranges (log-uniform where marked):
  tau 3-100 ns (log; TRPL 30-60 ns, Pandey 2021)      NA 2e14-3e15 cm-3 (log; Cu doping)
  phi_back 4.85-5.30 eV (back hole barrier 0.10-0.55)  S_front 1e2-1e7 cm/s (log)
  ND_MZO 1e14-1e18 cm-3 (log)                          Rs 0-3 ohm cm2
Each sample is run on the x = 0.15 spike cell and the x = 0.00 cliff cell (measured XPS offsets).
Output: optionA/lhs_results.csv (one row per sample with both cells' Voc, Jsc, FF, eta).
"""
import csv
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import mzo_model as m
from scaps_tools import run_parallel, read_iv, RESULTS

N = int(sys.argv[1]) if len(sys.argv) > 1 else 240
SEED = 20261115
RANGES = {  # name: (low, high, log)
    "tau": (3e-9, 100e-9, True), "NA": (2e14, 3e15, True), "phi_back": (4.85, 5.30, False),
    "S_front": (1e2, 1e7, True), "ND_MZO": (1e14, 1e18, True), "Rs": (0.0, 3.0, False),
}
CELLS = {"x0p15": (0.15, 0.19, 3.71), "x0p00": (0.00, -0.10, 3.28)}


def lhs(n, k, rng):
    u = (rng.permuted(np.tile(np.arange(n), (k, 1)), axis=1).T + rng.random((n, k))) / n
    return u


rng = np.random.default_rng(SEED)
U = lhs(N, len(RANGES), rng)
samples = []
for i in range(N):
    s = {}
    for j, (name, (lo, hi, lg)) in enumerate(RANGES.items()):
        s[name] = float(10 ** (np.log10(lo) + U[i, j] * (np.log10(hi) - np.log10(lo)))) if lg else float(lo + U[i, j] * (hi - lo))
    samples.append(s)

cases = []
for i, s in enumerate(samples):
    p = {**m.P, **{k: v for k, v in s.items() if k != "Rs"}}
    for tag, (x, dEc, Eg) in CELLS.items():
        name = m.build(x, dEc, Eg, p=p, suffix=f"_lhs{i:04d}")
        cases.append(dict(deffile=f"{name}.def", out=name, step=0.01, stopV=1.2, sets=[f"set external.Rs {s['Rs']:.4f}"]))
t = time.time()
run_parallel("A_lhs", cases, timeout=6 * 3600)
print(f"{len(cases)} runs, wall {time.time() - t:.0f} s")

rows = []
for i, s in enumerate(samples):
    row = {"sample": i, **s}
    for tag, (x, dEc, Eg) in CELLS.items():
        name = f"A_mzo_x{x:.2f}".replace(".", "p") + f"_lhs{i:04d}"
        f = RESULTS / f"{name}.iv"
        iv = read_iv(f) if f.exists() else {}
        ok = bool(iv) and iv.get("deffile", "") == f"{name}.def" and iv["Voc"] == iv["Voc"]
        for k in ("Voc", "Jsc", "FF", "eta"):
            row[f"{k}_{tag}"] = (iv[k] * (1000 if k == "Voc" else 1)) if ok else ""
        row[f"ok_{tag}"] = ok
    rows.append(row)
with open(Path(__file__).with_name("lhs_results.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print("ok x0.15:", sum(r["ok_x0p15"] for r in rows), " ok x0.00:", sum(r["ok_x0p00"] for r in rows), "of", N)
