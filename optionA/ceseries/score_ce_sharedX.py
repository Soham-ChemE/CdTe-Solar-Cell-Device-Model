"""Same as score_ce.py, but with ONE light level X shared by all four cells (same JVT rig).
For each X on a grid, each sample's best (dEc, logS, phi_b) is found; the total chi2 is minimised over X.
Output: optionA/ceseries/ce_sharedX.csv"""
import csv, math, sys
from pathlib import Path
import numpy as np
from scipy.interpolate import PchipInterpolator
sys.path.insert(0, str(Path(__file__).resolve().parent))
import score_ce as s
C = s.curves(); M = {t: s.meas(t) for t in s.SAMPLES}
def chi2_at(c, Mx, lnx):
    v = PchipInterpolator(c["T"], c["V1"], extrapolate=True)(Mx[:, 0]); mm = np.interp(Mx[:, 0], c["T"], c["m"])
    return float((((Mx[:, 1] - v - mm * lnx) / s.SIG) ** 2).sum())
best_tot, table = None, []
for X in np.exp(np.linspace(math.log(0.1), math.log(5.0), 61)):
    lnx = math.log(X); tot = 0; picks = {}
    for t, Mx in M.items():
        x2, c = min(((chi2_at(c, Mx, lnx), c) for c in C), key=lambda z: z[0])
        tot += x2; picks[t] = (x2, c)
    table.append((tot, X, picks))
table.sort(key=lambda z: z[0])
tot, X, picks = table[0]
print(f"shared light level X = {X:.3f} sun, total chi2 = {tot:.1f} for {sum(len(m) for m in M.values())} points")
rows = []
for t, (x2, c) in picks.items():
    # profile over dEc at this X
    prof = {}
    for cc in C:
        prof[cc["dEc"]] = min(prof.get(cc["dEc"], 1e99), chi2_at(cc, M[t], math.log(X)))
    b = min(prof.values()); ok = sorted(k for k, v in prof.items() if v - b <= 4.0)
    print(f"  {t:8s} dEc {c['dEc']:+.2f}  logS {c['logS']:.2f}  phi_b {c['phi']:.2f}  chi2 {x2:.1f}   dEc within dchi2<=4: {ok}")
    rows.append(dict(sample=t, Ce=s.SAMPLES[t], X_shared=round(X, 3), dEc=c["dEc"], logS=c["logS"], phi_b=c["phi"], chi2=round(x2, 2),
                     dEc_dchi2le4=" ".join(f"{k:+.2f}" for k in ok)))
print("next-best shared X:", [(round(z[1], 3), round(z[0], 1)) for z in table[1:4]])
with open(Path(__file__).with_name("ce_sharedX.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
