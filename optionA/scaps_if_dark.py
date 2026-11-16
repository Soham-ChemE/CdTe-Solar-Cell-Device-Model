"""Dark J-V cross-check (SCAPS vs Sesame) of the interface-state front model for the cliff cases, where SCAPS
fails to converge under illumination. Dark forward current is set by the same recombination (front interface
states, bulk, back contact), so agreement in the dark validates the recombination model itself.
Output: optionA/scaps_if_dark.csv (V, J_scaps, J_sesame per case)."""
import csv, sys, time
from pathlib import Path
import numpy as np
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts")); sys.path.insert(0, str(REPO / "optionA"))
from scaps_tools import Batch, read_iv, RESULTS
import scaps_if_xcheck as x

CASES = [(0.50, +0.10, 1e4), (0.55, -0.10, 1e3), (0.50, -0.22, 1e3), (0.50, -0.32, 1e3)]

def scaps_dark():
    b = Batch("X_ifdark")
    names = []
    for phi, dEc, S in CASES:
        name, _, _ = x.make(phi, dEc, S, f"X_ifd_phi{phi:.2f}_dEc{dEc:+.2f}_S{S:.0e}".replace("+", "p").replace("-", "m").replace(".", "p"))
        b.lines += [f"load definitionfile {name}.def", "clear actions", "action workingpoint.temperature 300", "action dark",
                    "action iv.doiv", "action iv.startV 0", "action iv.stopV 1.0", "action iv.increment 0.02",
                    "clear simulations", "calculate", f"save results.iv {name}.iv"]
        names.append(name)
    r = b.run(timeout=3600)
    return names

def sesame_dark(phi, dEc, S):
    sys.path.insert(0, str(REPO / "optionA/sesame/kujovic/calib")); sys.path.insert(0, str(REPO / "optionA/sesame"))
    import calibrate as cal, sesame_cell as sc
    cell = cal.make_cell(phi, dEc, S, 300)
    cell.g_full[:] = 0.0
    cell.system.g = cell.g_full.copy()
    jv = sc.run_jv(cell, V_max=1.0, dV=0.02, stop_after_voc=10_000, ramp=[1.0])
    return np.array(jv.V), np.array(jv.J)

if __name__ == "__main__":
    t = time.time(); names = scaps_dark(); print("SCAPS wall", round(time.time() - t), "s")
    rows = []
    for (phi, dEc, S), name in zip(CASES, names):
        f = RESULTS / f"{name}.iv"; iv = read_iv(f) if f.exists() else {}
        ok = bool(iv.get("table")) and iv.get("deffile") == f"{name}.def"
        Vs, Js = sesame_dark(phi, dEc, S)
        if ok:
            tab = np.array(iv["table"]); Vc, Jc = tab[:, 0], tab[:, 1]      # SCAPS: consumer convention, dark J > 0 forward
        for V in np.round(np.arange(0.3, 1.0001, 0.05), 3):
            jc = float(np.interp(V, Vc, Jc)) if ok and V <= Vc.max() else float("nan")
            js = float(np.interp(V, Vs, -Js)) if V <= Vs.max() else float("nan")   # Sesame generator convention -> forward positive
            rows.append(dict(phi_b=phi, dEc=dEc, S=S, V=V, J_scaps_mAcm2=jc, J_sesame_mAcm2=js,
                             ratio=(js / jc) if jc and jc == jc and js == js and jc != 0 else float("nan")))
        print(f"dEc {dEc:+.2f}: SCAPS {'ok' if ok else 'FAILED'}")
    with open(REPO / "optionA/scaps_if_dark.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    for r in rows:
        if abs(r["V"] * 100 % 10) < 1e-6 and r["V"] >= 0.5:
            print(f"dEc {r['dEc']:+.2f} V {r['V']:.2f}  SCAPS {r['J_scaps_mAcm2']:.4g}  Sesame {r['J_sesame_mAcm2']:.4g}  ratio {r['ratio']:.3f}")
