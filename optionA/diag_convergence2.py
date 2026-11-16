"""Second convergence test: separate band gap, conduction-band spike and absorption (x = 0.15 cell)."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import mzo_model as m
from scaps_tools import run_parallel, read_iv, RESULTS, DefFile, DEFS

specs = {  # suffix: (dEc, Eg_MZO, mzo_absorption_off)
    "_dE_noSpike_Eg371": (-0.10, 3.71, False),
    "_dF_spike019_Eg328": (0.19, 3.28, False),
    "_dG_spike005_Eg371": (0.05, 3.71, False),
    "_dH_spike019_noAbs": (0.19, 3.71, True),
}
cases = []
for suf, (dEc, Eg, noabs) in specs.items():
    name = m.build(0.15, dEc, Eg, suffix=suf)
    if noabs:
        DefFile.load(DEFS / f"{name}.def").set_absorption_sqrt("MgZnO", A=0.0).save(name)
    cases.append(dict(deffile=f"{name}.def", out=name, step=0.01, stopV=1.2))
t = time.time(); res = run_parallel("A_diag2", cases, timeout=1200)
print("wall s:", round(time.time() - t))
for c in cases:
    p = RESULTS / f"{c['out']}.iv"
    iv = read_iv(p) if p.exists() else {}
    ok = iv.get("Voc") == iv.get("Voc")
    print(f"{c['out']:30s} " + (f"Voc {iv['Voc']*1000:7.1f} mV  Jsc {iv['Jsc']:6.2f}  FF {iv['FF']:6.2f}  eta {iv['eta']:6.2f}" if ok and iv else "FAILED"))
