"""Why do ZnO-buffered (x = 0) cells fail on Cu-doped absorbers but reach 21.4% on As-doped ones?
Start from the best fit to the optimised x = 0.15 cells, swap in the ZnO front, and vary:
  dEc in {-0.10 (Pandey XPS), -0.22, -0.32 (Loughborough XPS on films)} eV
  S_front in {1e3, 1e5, 1e6, 1e7} cm/s,  ND_ZnO in {1e15, 1e17} cm-3,
  absorber NA in {4.1e14 (Cu-cell fit), 2e16 (As-doped level, Kujovic C-V)} cm-3.
Output: optionA/zno_hypotheses.csv"""
import csv, itertools, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import mzo_model as m
from scaps_tools import run_parallel, read_iv, RESULTS

BEST = {"tau": 7.24e-9, "NA": 4.14e14, "phi_back": 5.27, "S_front": 7.51e3, "ND_MZO": 6.47e17}
RS = 1.32
grid = list(itertools.product([-0.10, -0.22, -0.32], [1e3, 1e5, 1e6, 1e7], [1e15, 1e17], [4.14e14, 2e16]))
cases, meta = [], []
for i, (dEc, S, nd, na) in enumerate(grid):
    p = {**m.P, **BEST, "S_front": S, "ND_MZO": nd, "NA": na}
    name = m.build(0.0, dEc, 3.28, p=p, suffix=f"_h{i:03d}")
    cases.append(dict(deffile=f"{name}.def", out=name, step=0.01, stopV=1.2, sets=[f"set external.Rs {RS}"]))
    meta.append((dEc, S, nd, na, name))
t = time.time(); run_parallel("A_hyp", cases, timeout=4 * 3600)
print(f"{len(cases)} runs, wall {time.time() - t:.0f} s")
rows = []
for dEc, S, nd, na, name in meta:
    f = RESULTS / f"{name}.iv"; iv = read_iv(f) if f.exists() else {}
    ok = bool(iv) and iv.get("deffile", "") == f"{name}.def" and iv["Voc"] == iv["Voc"]
    rows.append({"dEc": dEc, "S_front": S, "ND_ZnO": nd, "NA": na,
                 "Voc_mV": iv["Voc"] * 1000 if ok else "", "Jsc": iv["Jsc"] if ok else "",
                 "FF": iv["FF"] if ok else "", "eta": iv["eta"] if ok else "", "ok": ok})
with open(Path(__file__).with_name("zno_hypotheses.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print("failed:", sum(not r["ok"] for r in rows))
