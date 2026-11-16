"""Questions 4 and 5: low-temperature J-V of the x = 0 (and x = 0.15) cell at the best shared fits, and the NA scan
at fixed S. Reads lowT/*.csv and curves/*.csv written by oneS.py; writes oneS_lowT.csv, oneS_NAscan.csv and
oneS_lowT.png."""
import csv
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import oneS as o  # noqa: E402

sc = o.sc
FITS = {"shared S, Jsc scaled (k 1.061) / Voc+FF only": ((5.0, 30e-9, 2e14, 0.35, 1e15), 2.3),
        "shared S, absolute Jsc": ((4.5, 60e-9, 1e15, 0.50, 1e15), 2.0)}
TEMPS = (300.0, 250.0, 225.0)


def read(f):
    rows = list(csv.DictReader(open(f)))
    if not rows or rows[0]["status"] != "ok":
        return None, rows[0]["status"] if rows else "empty"
    return (np.array([float(r["V_int"]) for r in rows]), np.array([float(r["J_mAcm2"]) for r in rows])), "ok"


def shape(V, J, Rs):
    """Kink diagnostics on the external-voltage curve (generator convention, J > 0 below Voc).
    s_shape: largest positive d2J/dV2 between 0 and Voc (a normal diode curve is concave there, d2J/dV2 < 0);
    rollover: |dJ/dV| at Voc + 0.20 V divided by |dJ/dV| at Voc (> 1 for a diode, < 1 when the forward current saturates)."""
    Vx = V - J * 1e-3 * Rs
    m = sc.jv_metrics(V, J, Rs)
    o_ = np.argsort(Vx)
    Vx, Jx = Vx[o_], J[o_]
    from scipy.interpolate import PchipInterpolator
    f = PchipInterpolator(Vx, Jx)
    voc = m["Voc"] / 1000
    vv = np.linspace(0.02, voc - 0.01, 400)
    d2 = f.derivative(2)(vv)
    i = int(np.argmax(d2))
    s1 = abs(f.derivative(1)(voc))
    s2 = abs(f.derivative(1)(min(voc + 0.20, Vx[-1])))
    return m, float(d2[i]), float(vv[i]), float(s2 / s1) if s1 > 0 else float("nan"), float(Vx[-1])


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rows = []
    fig, ax = plt.subplots(1, 4, figsize=(19, 4.6))
    cols = {300.0: "#0b0b0b", 250.0: "#2a78d6", 225.0: "#eb6834"}
    pi = 0
    for lab, (c, Rs) in FITS.items():
        for x in (0.0, 0.15):
            a = ax[pi]; pi += 1
            vocs = []
            for T in TEMPS:
                f = o.LOWT / f"{o.tag(x, c)}_T{T:g}.csv"
                if not f.exists():
                    continue
                d, st = read(f)
                if d is None:
                    rows.append(dict(fit=lab, x=x, T=T, status=st)); continue
                V, J = d
                m, d2max, v_d2, roll, vmax = shape(V, J, Rs)
                vocs.append((T, m["Voc"]))
                rows.append(dict(fit=lab, x=x, T=T, status="ok", Rs=Rs, Voc_mV=m["Voc"], Jsc=m["Jsc"], FF=m["FF"], eta=m["eta"],
                                 max_d2JdV2_below_Voc=d2max, at_V=v_d2, rollover_ratio_Voc_plus_0p2=roll, V_ext_max=vmax))
                Vx = V - J * 1e-3 * Rs
                a.plot(Vx, J, color=cols[T], lw=1.6, label=f"{T:g} K: Voc {m['Voc']:.0f} mV, FF {m['FF']:.1f}%")
            if len(vocs) >= 2:
                Ts, Vo = np.array(vocs).T
                p = np.polyfit(Ts, Vo / 1000, 1)
                for r in rows:
                    if r["fit"] == lab and r["x"] == x:
                        r["Voc_T0_intercept_eV"] = float(p[1]); r["dVoc_dT_mVK"] = float(1000 * p[0])
                a.set_title(f"x = {x:.2f}; {lab}\nVoc(T→0) from 3 T: {p[1]:.2f} eV, dVoc/dT {1000 * p[0]:.2f} mV/K", fontsize=8, loc="left")
            a.axhline(0, color="#999", lw=0.6); a.set_ylim(-30, 32); a.set_xlim(0, 1.25)
            a.set_xlabel("V (V)"); a.set_ylabel("J (mA/cm², generator convention)"); a.legend(frameon=False, fontsize=7.5, loc="lower left")
            a.grid(color="#e4e3df", lw=0.6)
            for s_ in ("top", "right"):
                a.spines[s_].set_visible(False)
    fig.tight_layout(); fig.savefig(HERE / "oneS_lowT.png", dpi=140)
    keys = list(dict.fromkeys(k for r in rows for k in r))
    if rows:
        o.write_atomic(HERE / "oneS_lowT.csv", [[r.get(k, "") for k in keys] for r in rows], keys)
    for r in rows:
        print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})
    # question 5: NA at fixed S (best shared fit, Rs 2.3)
    nas = []
    c0, Rs = FITS["shared S, Jsc scaled (k 1.061) / Voc+FF only"]
    for cd in o.cells():
        for na in (2e14, 1e15, 3e15, 1e16, 3e16):
            f = o.CURVES / f"{o.tag(cd['x'], (c0[0], c0[1], na, c0[3], c0[4]))}.csv"
            if not f.exists():
                continue
            d, st = read(f)
            if d is None:
                nas.append(dict(x=cd["x"], NA=na, status=st)); continue
            m = sc.jv_metrics(*d, Rs)
            nas.append(dict(x=cd["x"], NA=na, status="ok", Voc_mV=m["Voc"], Jsc=m["Jsc"], FF=m["FF"], eta=m["eta"]))
    if nas:
        k2 = list(dict.fromkeys(k for r in nas for k in r))
        o.write_atomic(HERE / "oneS_NAscan.csv", [[r.get(k, "") for k in k2] for r in nas], k2)
        for r in nas:
            print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()})


if __name__ == "__main__":
    main()
