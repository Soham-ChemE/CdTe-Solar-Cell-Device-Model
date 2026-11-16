"""Diagnose the SCAPS convergence failure of spike-offset MgZnO cells (x = 0.15), four variants in parallel."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import mzo_model as m
from scaps_tools import run_parallel, read_iv, RESULTS

variants = {
    "_dA_nominal": dict(m.P),
    "_dB_ND1e18": {**m.P, "ND_MZO": 1e18},
    "_dC_noIF": {**m.P, "S_front": 1e-2},
    "_dD_chiFTO": {**m.P, "chi_FTO": 4.0 - 0.19},
}
cases = []
for suf, p in variants.items():
    name = m.build(0.15, 0.19, 3.71, p=p, suffix=suf)
    cases.append(dict(deffile=f"{name}.def", out=name, step=0.01, stopV=1.2))
t = time.time(); res = run_parallel("A_diag", cases, timeout=1200)
print("wall s:", round(time.time() - t))
for r in res: print(r.stdout.strip()[-300:])
for c in cases:
    p = RESULTS / f"{c['out']}.iv"
    iv = read_iv(p) if p.exists() else {"Voc": float("nan"), "Jsc": float("nan"), "FF": float("nan"), "eta": float("nan")}
    print(f"{c['out']:28s} Voc {iv['Voc']*1000:7.1f} mV  Jsc {iv['Jsc']:6.2f}  FF {iv['FF']:6.2f}  eta {iv['eta']:6.2f}")
