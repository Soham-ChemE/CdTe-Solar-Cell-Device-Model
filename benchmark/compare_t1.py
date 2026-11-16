"""Compare SCAPS 3.3.11 and Sesame 2.0 J-V curves for the same device (Sesame tutorial 1)."""
import numpy as np, re, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt

def scaps_iv(path):
    lines = open(path, encoding="latin-1").read().replace("\r", "").split("\n")
    i = next(k for k, l in enumerate(lines) if l.strip().startswith("v(V)"))
    rows = []
    for l in lines[i + 1:]:
        p = l.split()
        if len(p) < 2:
            if rows: break
            continue
        try: rows.append((float(p[0]), float(p[1])))
        except ValueError: break
    a = np.array(rows); return a[:, 0], -a[:, 1]          # SCAPS: J<0 under illumination -> flip

def metrics(V, J):
    jsc = np.interp(0, V, J)
    k = np.where(np.diff(np.sign(J)) != 0)[0][0]
    voc = V[k] - J[k] * (V[k + 1] - V[k]) / (J[k + 1] - J[k])
    Vf = np.linspace(0, voc, 2000); P = Vf * np.interp(Vf, V, J)
    return jsc, voc, P.max() / (jsc * voc) * 100

Vs, Js = scaps_iv("scaps_t1.iv")
d = np.loadtxt("sesame_t1_iv.txt"); Vn, Jn = d[:, 0], d[:, 1]
if Jn[0] < 0: Jn = -Jn
ms, mn = metrics(Vs, Js), metrics(Vn, Jn)
print(f"{'':10s}{'Jsc mA/cm2':>12s}{'Voc V':>10s}{'FF %':>8s}")
print(f"{'SCAPS':10s}{ms[0]:12.3f}{ms[1]:10.4f}{ms[2]:8.2f}")
print(f"{'Sesame':10s}{mn[0]:12.3f}{mn[1]:10.4f}{mn[2]:8.2f}")
print(f"{'diff':10s}{(ms[0]-mn[0])/mn[0]*100:11.2f}%{(ms[1]-mn[1])*1000:8.1f}mV{ms[2]-mn[2]:8.2f}")
Vc = np.linspace(0, min(ms[1], mn[1]), 50)
print("max |J_SCAPS - J_Sesame| below Voc: %.3f mA/cm2" % np.max(np.abs(np.interp(Vc, Vs, Js) - np.interp(Vc, Vn, Jn))))
fig, ax = plt.subplots(figsize=(5.2, 3.8))
ax.plot(Vs, Js, "-", lw=2.2, label="SCAPS 3.3.11 (Ghent)")
ax.plot(Vn, Jn, "o", ms=3.5, mfc="none", label="Sesame 2.0 (NIST)")
ax.set_xlim(0, 1.0); ax.set_ylim(0, 17); ax.set_xlabel("Voltage (V)"); ax.set_ylabel("Current density (mA/cm²)")
ax.set_title("Same CdTe p-n junction, two independent solvers", fontsize=10); ax.legend(frameon=False); ax.grid(alpha=0.3)
fig.tight_layout(); fig.savefig("../figures/benchmark_scaps_vs_sesame.png", dpi=200)
