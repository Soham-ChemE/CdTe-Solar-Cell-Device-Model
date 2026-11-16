"""Diagnose the gap between the rebuilt Loughborough model (12.3%) and the authors' SCAPS result (21.4%).
Each variant changes one stated or unstated input; run in parallel on the 4 SCAPS prefixes.
Output: optionA/kujovic_unstated.csv"""
import csv, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import kujovic_model as k
from scaps_tools import run_parallel, read_iv, RESULTS, DefFile, DEFS
V = {  # tag: (author-param overrides, reconstruction overrides)
    "base": ({}, {}),
    "noIFdefect": ({"S_front": 1e-3}, {}),
    "NDZnO1e17": ({"ND_ZnO": 1e17}, {}),
    "NDZnO1e15": ({"ND_ZnO": 1e15}, {}),
    "tau100ns": ({"tau": 100e-9, "Nt_bulk": 5e11}, {}),
    "nsub1": ({}, {"n_sub": 1}),
    "chiFTO40": ({}, {"chi_FTO": 4.0}),
    "backPhi581": ({}, {"back": "phi"}),
}
cases = []
for tag, (pa, ra) in V.items():
    name = k.build({**k.AUTH, **pa}, {**k.RECON, **ra}, name=f"K_u_{tag}")
    if ra.get("back") == "phi":
        DefFile.load(DEFS / f"{name}.def").set_back_workfunction(5.81).save(name)
    cases.append(dict(deffile=f"{name}.def", out=name, step=0.01, stopV=1.2))
t = time.time(); run_parallel("K_unstated", cases, timeout=2 * 3600); print("wall", round(time.time() - t), "s")
print("authors' SCAPS: 872 mV / 30.8 / 79.6 / 21.4")
rows = []
for tag, c in zip(V, cases):
    f = RESULTS / f"{c['out']}.iv"; iv = read_iv(f) if f.exists() else {}
    ok = bool(iv) and iv.get("deffile") == c["deffile"] and iv["Voc"] == iv["Voc"]
    r = {"variant": tag, "ok": ok}
    if ok:
        cols, tab = iv["columns"], iv["table"]
        last = tab[-1]
        r.update(Voc_mV=round(iv["Voc"] * 1000, 1), Jsc=round(iv["Jsc"], 2), FF=round(iv["FF"], 2), eta=round(iv["eta"], 2),
                 jbulk_at_end=round(last[cols.index("jbulk(mA/cm2)")], 2), jifr_at_end=round(last[cols.index("jifr(mA/cm2)")], 3),
                 jminor_left_end=round(last[cols.index("jminor_left(mA/cm2)")], 3))
    rows.append(r); print(r)
keys = sorted({kk for r in rows for kk in r}, key=lambda s: ["variant", "ok", "Voc_mV", "Jsc", "FF", "eta"].index(s) if s in ["variant", "ok", "Voc_mV", "Jsc", "FF", "eta"] else 9)
with open(Path(__file__).with_name("kujovic_unstated.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(rows)
