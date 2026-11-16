"""Ce-alloyed ZnO series (Kujovic thesis Fig. 5.7, co-sputtered Ce 0 / 5.0 / 7.8 / 8.7 %): score the measured Voc(T)
of each cell against the 130 simulated Voc(T) curves of the identifiability map (optionA/sesame/kujovic/ident: same
calibrated absorber, interface-state front, dead FTO/ZnO, back barrier 0.45/0.50/0.55 eV), with the light level X
profiled analytically (Voc_X = Voc_1sun + m ln X). No new simulation. Shape-only fit (the co-sputter batch's 1-sun
Voc, 821-840 mV, differs from the champion, so the 1-sun J-V is not used as a constraint here).
The ZnO curve in Fig. 5.7 is identical to the 21.4 % champion's Fig. 3d data. Points with Voc > 1.0 V are the
digitised fit-line label and are dropped.
Output: optionA/ceseries/ce_scores.csv, ce_profile.csv"""
import csv, glob, math
from pathlib import Path
import numpy as np
from scipy.interpolate import PchipInterpolator
REPO = Path(__file__).resolve().parents[2]
CUR = REPO / "data/kujovic_family/curves"
IDENT = REPO / "optionA/sesame/kujovic/ident/curves"
SIG = 0.004
LNX = (math.log(0.05), math.log(5.0))
SAMPLES = {"ZnO": 0.0, "Ce0.050": 0.050, "Ce0.078": 0.078, "Ce0.087": 0.087}

def meas(tag):
    rows = [(float(r["T_K"]), float(r["Voc_V"])) for r in csv.DictReader(open(CUR / f"S4_fig5.7_VocT_cosputtered_CeZnO_{tag}.csv"))]
    a = np.array(sorted(set(rows)))
    return a[a[:, 1] < 1.0]

def curves():
    out = []
    for f in glob.glob(str(IDENT / "*.csv")):
        d = list(csv.DictReader(open(f)))
        if not d or d[0]["T_K"] == "":
            continue
        T = np.array([float(r["T_K"]) for r in d]); V1 = np.array([float(r["Voc1"]) for r in d]); m = np.array([float(r["m_V"]) for r in d])
        if not (np.isfinite(V1).all() and np.isfinite(m).all()) or any(r["status"] != "ok" for r in d):
            continue
        o = np.argsort(T)
        out.append(dict(phi=float(d[0]["phi_b"]), dEc=float(d[0]["dEc"]), logS=float(d[0]["logS"]), T=T[o], V1=V1[o], m=m[o]))
    return out

def chi2(c, M):
    v = PchipInterpolator(c["T"], c["V1"], extrapolate=True)(M[:, 0]); mm = np.interp(M[:, 0], c["T"], c["m"])
    r0 = M[:, 1] - v
    lnx = float(np.clip((mm * r0).sum() / (mm * mm).sum(), *LNX))
    return float((((r0 - mm * lnx) / SIG) ** 2).sum()), math.exp(lnx)

if __name__ == "__main__":
    C = curves(); print(len(C), "simulated curves")
    rows = []
    for tag, ce in SAMPLES.items():
        M = meas(tag)
        hi = M[M[:, 0] >= 315]; s, b = np.polyfit(hi[:, 0], hi[:, 1], 1)
        sc = sorted(((chi2(c, M), c) for c in C), key=lambda z: z[0][0])
        for rank, ((x2, X), c) in enumerate(sc[:5]):
            rows.append(dict(sample=tag, Ce=ce, n_pts=len(M), meas_slope_hi=round(s * 1000, 2), meas_Ea=round(b, 3), rank=rank + 1,
                             phi_b=c["phi"], dEc=c["dEc"], logS=c["logS"], chi2=round(x2, 2), X=round(X, 3)))
        # profile over dEc (min over logS, phi)
        prof = {}
        for (x2, X), c in sc:
            prof[c["dEc"]] = min(prof.get(c["dEc"], 1e99), x2)
        best = min(prof.values())
        print(f"\n{tag} (Ce {ce}): n={len(M)}  measured hi-T slope {s*1000:.2f} mV/K, Ea {b:.3f} eV")
        print("  best:", [(r['phi_b'], r['dEc'], r['logS'], r['chi2'], r['X']) for r in rows if r['sample'] == tag][:3])
        print("  profile dEc: " + "  ".join(f"{k:+.2f}:{v - best:.1f}" for k, v in sorted(prof.items())))
    with open(REPO / "optionA/ceseries/ce_scores.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
