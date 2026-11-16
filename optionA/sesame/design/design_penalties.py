"""Conservative design and penalised comparison (follow-up to design.py).

Conservative = realistic with NA x3 (not x10), radiative B = 1e-10 cm3/s on. Every case here (baselines included)
gets B = 1e-10 and Rs 0.45 ohm cm2 / Rsh 2500 ohm cm2 applied to the J-V (shunt across the junction, then Rs):
J_ext = J(Vj) - Vj/Rsh, V_ext = Vj - J_ext*Rs. EQE-anchored projection = 19.51% x eta / eta_baseline(same penalties).
  python design_penalties.py   -> design_penalties.csv (runs what is missing; resumable via design.py's curves)
"""
import numpy as np

import design as D

sc = D.sc
B, RS, RSH = 1e-10, 0.45, 2500.0
ETA_EQE_ANCHOR = 0.8755 * 27.69 * 0.8048


def curve(d):
    """Internal-voltage J-V of the design: the delta = 0 curve, or the sigma composite on D.VG."""
    c0 = D.read_curve(D.CURVES / f"{D.key(d)}_d{0.0:+.3f}.csv")
    if d["sigma"] <= 0:
        return c0
    ds, JSC, L = [], [], []
    for dl in D.DELTAS:
        c = D.read_curve(D.CURVES / f"{D.key(d)}_d{dl:+.3f}.csv")
        jsc, lj = D.lnJd_on(*c, D.VG)
        ds.append(dl); JSC.append(jsc); L.append(lj)
    ds, JSC, L = np.array(ds), np.array(JSC), np.array(L)
    sg = d["sigma"]
    dl = D.FINE[(D.FINE >= -4.5 * sg) & (D.FINE <= 4.5 * sg)]
    w = np.exp(-0.5 * (dl / sg) ** 2); w /= w.sum()
    i = np.clip(np.searchsorted(ds, dl, side="right") - 1, 0, len(ds) - 2)
    t = ((dl - ds[i]) / (ds[i + 1] - ds[i]))[:, None]
    Lf = (1 - t) * L[i] + t * L[i + 1]
    return D.VG, float((w * np.interp(dl, ds, JSC)).sum()) - (w[:, None] * np.exp(Lf)).sum(0)


def penalised(d, rs=RS, rsh=RSH):
    V, J = curve(d)
    return sc.jv_metrics(V, J - 1000.0 * V / rsh, rs)


def cases():
    out = []
    for br, b in D.BRANCHES.items():
        base = dict(b, B=B)
        cons = dict(b, dEc=0.20, S=10 * b["S"], tau=300e-9, nas=3.0, Tf=0.97, dFTO=150,
                    back="ohm" if b["back"] == "ohm" else "b0.30", B=B)
        out.append((br, "baseline (+B)", base, base))
        out.append((br, "conservative", cons, base))
    rb = dict(D.BASE, B=B)
    for lab, d in D.combined("base"):
        out.append(("base", lab.split()[1] + " (+B)", dict(d, B=B), rb))
    return out


def main():
    rows = []
    for br, lab, d, base in cases():
        D.simulate(d)
        D.simulate(base)
        m, mb = penalised(d), penalised(base)
        m0 = D.metrics(d)
        rows.append(dict(branch=br, design=lab, params=D.label_params(d), Rs=RS, Rsh=RSH,
                         Voc_mV=m["Voc"], Jsc=m["Jsc"], FF=m["FF"], eta=m["eta"],
                         eta_no_RsRsh=m0["eta"], eta_baseline_same_penalties=mb["eta"],
                         eta_EQE_anchored=ETA_EQE_ANCHOR * m["eta"] / mb["eta"]))
        r = rows[-1]
        print(f"{br:18s} {lab:18s} {r['Voc_mV']:7.1f} {r['Jsc']:6.2f} {r['FF']:6.2f} {r['eta']:6.2f} "
              f"(no Rs/Rsh {r['eta_no_RsRsh']:.2f}) | base {r['eta_baseline_same_penalties']:.2f} | EQE-anchored {r['eta_EQE_anchored']:.2f}", flush=True)
    D.write_csv(D.HERE / "design_penalties.csv", rows)


if __name__ == "__main__":
    main()
