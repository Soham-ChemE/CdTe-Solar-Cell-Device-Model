"""Do the ZnO-front convergence failures come from the default FTO electron affinity (4.0 eV)?"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import mzo_model as m
from scaps_tools import run_parallel, read_iv, RESULTS
BEST = {"tau": 7.24e-9, "phi_back": 5.27, "S_front": 1e5, "ND_MZO": 1e17}
cases = []
for tag, dEc, na in [("cliff022", -0.22, 4.14e14), ("As2e16", -0.10, 2e16)]:
    for chi in (None, 4.6):
        p = {**m.P, **BEST, "NA": na, "chi_FTO": chi}
        name = m.build(0.0, dEc, 3.28, p=p, suffix=f"_f_{tag}_{'def' if chi is None else 'c46'}")
        cases.append(dict(deffile=f"{name}.def", out=name, step=0.01, stopV=1.2, sets=["set external.Rs 1.32"]))
t = time.time(); run_parallel("A_dfto", cases, timeout=1800); print("wall", round(time.time() - t))
for c in cases:
    f = RESULTS / f"{c['out']}.iv"; iv = read_iv(f) if f.exists() else {}
    ok = bool(iv) and iv.get("Voc") == iv.get("Voc") and iv.get("deffile") == c["deffile"]
    print(f"{c['out']:40s}", f"Voc {iv['Voc']*1000:6.0f}  Jsc {iv['Jsc']:6.2f}  FF {iv['FF']:5.1f}  eta {iv['eta']:5.2f}" if ok else "FAILED")
