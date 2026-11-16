"""Which reading of the authors' model reproduces their SCAPS output (872 mV / 30.8 / 79.6% / 21.4%)?
Five configurations bracketing the stated text and their published band diagram (thesis Fig. 3.11).
Output: optionA/kujovic_configs.csv and figures/kujovic_rebuild_<tag>.png"""
import csv, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import kujovic_model as k
from scaps_tools import run_parallel, read_iv, read_qe, RESULTS
CFG = {  # tag: reconstruction overrides
    "graded_flat": {},
    "graded_bar0655": {"back": 0.655},
    "uniform_bar0655": {"Eg_mode": "uniform", "back": 0.655},
    "uniform_flat": {"Eg_mode": "uniform"},
    "graded_bar0655_win": {"back": 0.655, "window_defects": True},
}
cases = []
for tag, ra in CFG.items():
    name = k.build(dict(k.AUTH), {**k.RECON, **ra}, name=f"K_c_{tag}")
    cases.append(dict(deffile=f"{name}.def", out=name, step=0.01, stopV=1.2, qe=(300, 960, 10)))
t = time.time(); run_parallel("K_configs", cases, timeout=2 * 3600); print("wall", round(time.time() - t), "s")
rows = []
for tag, c in zip(CFG, cases):
    f = RESULTS / f"{c['out']}.iv"; iv = read_iv(f) if f.exists() else {}
    ok = bool(iv) and iv.get("deffile") == c["deffile"] and iv["Voc"] == iv["Voc"]
    r = {"config": tag, "ok": ok}
    if ok:
        r.update(Voc_mV=round(iv["Voc"] * 1000, 1), Jsc=round(iv["Jsc"], 2), FF=round(iv["FF"], 2), eta=round(iv["eta"], 2))
        q = RESULTS / f"{c['out']}.qe"
        if q.exists():
            k.compare(tag, iv, read_qe(q))
    rows.append(r); print(r)
with open(Path(__file__).with_name("kujovic_configs.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["config", "ok", "Voc_mV", "Jsc", "FF", "eta"]); w.writeheader(); w.writerows(rows)
