"""Voc(T) of the rebuilt Loughborough model against the measured JVT data of the 21.44% cell
(S1 Fig. 3d, data/kujovic_family/curves/S1_fig3d_Voc_vs_T.csv).

The measured curve has two regimes: -1.70 mV/K between 316 and 355 K (the authors' linear fit, Ea = 1.36 eV) and
-0.74 mV/K between 216 and 248 K (Voc saturation). A room-temperature J-V cannot tell a back-contact barrier, a
front spike/resistive buffer and interface recombination apart; Voc(T) can, because each bends the curve differently.

Temperature model (stated assumptions, each a CLI key):
  dEgdT   absorber gap coefficient, eV/K (default -4.0e-4; CdTe literature range about -3e-4 to -4.5e-4)
  f_cb    fraction of the gap change taken by the conduction band (default 0.5)
  The back-contact metal work function is fixed in absolute energy, so the hole barrier changes with T.
  ZnO and FTO are temperature independent. SCAPS scales Nc, Nv and n_i with T itself.
Usage: python optionA/kujovic_vocT.py TAG [key=value ...]   (any AUTH / RECON key, plus dEgdT, f_cb, phi_back)
"""
import csv, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import kujovic_model as k
from scaps_tools import run_parallel, read_iv, RESULTS

REPO = Path(__file__).resolve().parents[1]
TEMPS = [216, 232, 248, 265, 282, 298, 316, 326, 336, 345, 355]


def parse(argv):
    p, r = dict(k.AUTH), dict(k.RECON)
    extra = {"dEgdT": -4.0e-4, "f_cb": 0.5, "phi_back": None}
    for kv in argv:
        key, v = kv.split("=")
        if key in extra:
            extra[key] = float(v)
        elif key in p:
            p[key] = float(v)
        elif key in r:
            r[key] = (v == "True") if v in ("True", "False") else (float(v) if v.replace(".", "").replace("e-", "").isdigit() else v)
        else:
            raise KeyError(key)
    return p, r, extra


def build_T(p, r, extra, T, name):
    d = extra["dEgdT"] * (T - 300.0)
    pT = {**p, "Eg_back": p["Eg_back"] + d, "Eg_front": p["Eg_front"] + d}
    rT = {**r, "VBM_abs": r["VBM_abs"] + (1.0 - extra["f_cb"]) * d}
    if extra["phi_back"] is not None:                 # metal fixed in absolute energy
        rT["back"] = rT["VBM_abs"] - extra["phi_back"]
    return k.build(pT, rT, name=name)


if __name__ == "__main__":
    tag = sys.argv[1]
    p, r, extra = parse(sys.argv[2:])
    if extra["phi_back"] is None and r["back"] != "flatband":
        extra["phi_back"] = r["VBM_abs"] - float(r["back"])
    cases = []
    for T in TEMPS:
        name = build_T(p, r, extra, T, f"K_T_{tag}_{T}")
        cases.append(dict(deffile=f"{name}.def", out=name, T=float(T), step=0.005, stopV=1.3))
    t0 = time.time(); run_parallel(f"K_vocT_{tag}", cases, timeout=3 * 3600); print("wall", round(time.time() - t0), "s")
    meas = np.array([[float(a), float(b)] for a, b in list(csv.reader(open(REPO / "data/kujovic_family/curves/S1_fig3d_Voc_vs_T.csv")))[1:]])
    rows = []
    for T, c in zip(TEMPS, cases):
        f = RESULTS / f"{c['out']}.iv"; iv = read_iv(f) if f.exists() else {}
        ok = bool(iv) and iv.get("deffile") == c["deffile"] and iv["Voc"] == iv["Voc"]
        rows.append({"T_K": T, "Voc_V": round(iv["Voc"], 5) if ok else "", "Jsc": round(iv["Jsc"], 3) if ok else "",
                     "FF": round(iv["FF"], 2) if ok else "", "ok": ok})
    out = REPO / f"optionA/vocT_{tag}.csv"
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    good = [(r_["T_K"], r_["Voc_V"]) for r_ in rows if r_["ok"]]
    if len(good) >= 3:
        Ts, Vs = np.array(good).T
        hi = Ts >= 316; lo = Ts <= 248
        for lab, m in (("316-355 K", hi), ("216-248 K", lo)):
            if m.sum() >= 2:
                s, b = np.polyfit(Ts[m], Vs[m], 1)
                print(f"[{tag}] model slope {lab}: {s*1000:.2f} mV/K, intercept (Ea) {b:.3f} eV")
        for lab, lo_, hi_ in (("316-355 K", 316, 356), ("216-248 K", 215, 249)):
            mm = (meas[:, 0] >= lo_) & (meas[:, 0] <= hi_)
            s, b = np.polyfit(meas[mm, 0], meas[mm, 1], 1)
            print(f"[{tag}] measured slope {lab}: {s*1000:.2f} mV/K, intercept {b:.3f} eV")
        v298 = np.interp(298, Ts, Vs); m298 = np.interp(298, meas[:, 0], meas[:, 1])
        print(f"[{tag}] Voc at 298 K: model {v298*1000:.1f} mV, JVT measured {m298*1000:.1f} mV (J-V champion 875.5)")
    print("wrote", out)
