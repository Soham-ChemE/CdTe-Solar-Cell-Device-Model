"""Try SCAPS numerical settings on two ZnO-front cells that fail to converge at V = 0."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import mzo_model as m
from scaps_tools import run_parallel, read_iv, RESULTS
BEST = {"tau": 7.24e-9, "phi_back": 5.27, "S_front": 1e5, "ND_MZO": 1e17, "chi_FTO": 4.6}
OPTS = {"wp20": ["action workingpoint.numberofpoints 20"],
        "mesh": ["set numerical.recalculate_mesh 1", "set numerical.recalculate_mesh.points 600"]}
cases = []
for tag, dEc, na in [("cliff022", -0.22, 4.14e14), ("As2e16", -0.10, 2e16)]:
    name = m.build(0.0, dEc, 3.28, p={**m.P, **BEST, "NA": na}, suffix=f"_n_{tag}")
    for o, sets in OPTS.items():
        cases.append(dict(deffile=f"{name}.def", out=f"{name}_{o}", step=0.01, stopV=1.2, sets=["set external.Rs 1.32", *sets]))
t = time.time(); res = run_parallel("A_dnum", cases, timeout=1800); print("wall", round(time.time() - t))
for c in cases:
    f = RESULTS / f"{c['out']}.iv"; iv = read_iv(f) if f.exists() else {}
    ok = bool(iv) and iv.get("Voc") == iv.get("Voc") and iv.get("deffile") == c["deffile"]
    print(f"{c['out']:40s}", f"Voc {iv['Voc']*1000:6.0f}  Jsc {iv['Jsc']:6.2f}  FF {iv['FF']:5.1f}  eta {iv['eta']:5.2f}" if ok else "FAILED")
for r in res:
    if "error" in r.stdout.lower(): print(r.stdout[-250:])
