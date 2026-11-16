"""SCAPS cross-check of the Sesame design study (baseline / realistic / aggressive), ideal and with the measured
series/shunt resistance of the group's ZnO cells (S2: Rs 0.35-0.58, Rsh 1443-3482 ohm cm2 -> 0.45 / 2500).
Output: optionA/scaps_design_xcheck.csv"""
import csv, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from scaps_tools import run_parallel, read_iv, RESULTS
SES = {}
for r in csv.DictReader(open(REPO / "optionA/sesame/design/design_results.csv")):
    SES.setdefault(r.get("design", r.get("name", "")), r)
cases, meta = [], []
for d in ("baseline", "realistic", "aggressive"):
    for tag, sets in (("ideal", []), ("RsRsh", ["set external.Rs 0.45", "set external.Rsh 2500"])):
        out = f"X_design_{d}_{tag}"
        cases.append(dict(deffile=f"Design_{d}.def", out=out, step=0.01, stopV=1.3, sets=sets)); meta.append((d, tag, out))
run_parallel("X_design", cases, n_workers=1, timeout=3600)
rows = []
for d, tag, out in meta:
    f = RESULTS / f"{out}.iv"; iv = read_iv(f) if f.exists() else {}
    ok = bool(iv) and iv.get("deffile") == f"Design_{d}.def" and iv["Voc"] == iv["Voc"]
    rows.append(dict(design=d, resistance=tag, ok=ok, Voc=round(iv["Voc"] * 1000, 1) if ok else "", Jsc=round(iv["Jsc"], 2) if ok else "",
                     FF=round(iv["FF"], 2) if ok else "", eta=round(iv["eta"], 2) if ok else ""))
    print(rows[-1])
with open(REPO / "optionA/scaps_design_xcheck.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
