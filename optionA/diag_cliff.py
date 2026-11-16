"""Pinpoint what makes ZnO-front cells fail to converge in SCAPS."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import mzo_model as m
from scaps_tools import run_parallel, read_iv, RESULTS, Batch
B = {**m.P, "tau": 7.24e-9, "phi_back": 5.27, "chi_FTO": 4.6}
specs = [("c022_noIL", -0.22, {**B, "S_front": 1e-2, "ND_MZO": 1e17, "NA": 4.14e14}, []),
         ("c022_ND1e19", -0.22, {**B, "S_front": 1e5, "ND_MZO": 1e19, "NA": 4.14e14}, []),
         ("c022_dark", -0.22, {**B, "S_front": 1e5, "ND_MZO": 1e17, "NA": 4.14e14}, ["action dark"]),
         ("As2e16_noIL", -0.10, {**B, "S_front": 1e-2, "ND_MZO": 1e17, "NA": 2e16}, [])]
cases = []
for tag, dEc, p, extra in specs:
    name = m.build(0.0, dEc, 3.28, p=p, suffix=f"_c_{tag}")
    cases.append(dict(deffile=f"{name}.def", out=name, step=0.01, stopV=1.2, sets=["set external.Rs 1.32", *extra]))
t = time.time(); run_parallel("A_dcliff", cases, timeout=1800); print("wall", round(time.time() - t))
for c in cases:
    f = RESULTS / f"{c['out']}.iv"; iv = read_iv(f) if f.exists() else {}
    ok = bool(iv) and iv.get("deffile") == c["deffile"] and bool(iv.get("table"))
    print(f"{c['out']:36s}", (f"Voc {iv['Voc']*1000:6.0f} Jsc {iv['Jsc']:6.2f} FF {iv['FF']:5.1f} eta {iv['eta']:5.2f} | J(0)={iv['table'][0][1]:.3g}" if ok else "FAILED"))
