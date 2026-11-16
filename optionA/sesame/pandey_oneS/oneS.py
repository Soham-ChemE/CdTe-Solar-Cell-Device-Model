"""Option C (the ZnO paradox): can ONE shared front-interface S explain the Cu-doped MgZnO series (Pandey 2021)?

Option-A Sesame cell (sesame_cell.case_layers: FTO / 100 nm MgZnO / 0.5 um CdSeTe / 3 um CdTe), with front
recombination through buffer-CB <-> absorber-VB interface states (the IL keeps only the bulk tau), exactly as
grid.py --interface. Per Mg fraction x the buffer takes the XPS dEc and the optical gap (electrical gap capped at
3.5 eV as in mzo_model); everything else is shared across the five cells:
  log10 S_if {1..6} x tau {10,30,60} ns x NA {2e14,1e15} x phi_b {0.2,0.35,0.5} eV x ND_MZO {1e15,1e17}
phi_b is the hole barrier at the CdTe back: metal work function = (chi_CdTe + Eg_CdTe) - phi_b = 5.40 - phi_b.

Usage:  python oneS.py run          -> curves/<tag>.csv (internal-voltage J-V, one file per cell and parameter set)
        python oneS.py lowT <tag>   -> lowT/<tag>_T<T>.csv for x = 0 at 300, 250, 225 K
Resumable (existing curves are skipped), single process, atomic writes.
"""
import csv
import itertools
import math
import os
import random
import sys
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "kujovic"))
import sesame_cell as sc  # noqa: E402

CURVES = HERE / "curves"
LOWT = HERE / "lowT"
DATA = sc.REPO / "data/pandey2021/pandey2021_mzo_series.csv"
X_USED = (0.0, 0.10, 0.15, 0.20, 0.25)                       # x = 0.35 excluded (wurtzite -> zinc-blende change)
VBM_BACK = sc.P["chi_CdTe"] + sc.P["Eg_CdTe"]                # 5.40 eV
LOGS = [1, 2, 3, 4, 5, 6]
TAUS = [10e-9, 30e-9, 60e-9]
NAS = [2e14, 1e15]
PHIB = [0.20, 0.35, 0.50]
NDS = [1e15, 1e17]
VLIST = np.round(np.arange(0.02, 1.2001, 0.02), 6)
# one refinement pass after the first grid: half-decade S around the optimum, and phi_b 0.65 (the shared optimum sat
# at the phi_b = 0.50 grid edge) for log10 S >= 3.5
LOGS_HALF = [3.5, 4.5, 5.5]
PHIB_EXT = 0.65
LOGS_ALL = sorted(LOGS + LOGS_HALF)
PHIB_ALL = PHIB + [PHIB_EXT]


def cells():
    out = []
    for r in csv.DictReader(open(DATA)):
        x = float(r["mg_fraction"])
        if any(abs(x - u) < 1e-9 for u in X_USED):
            out.append(dict(x=x, dEc=float(r["dEc_XPS_eV"]), Eg=float(r["Eg_MZO_eV"]),
                            best=dict(Voc=float(r["Voc_best_mV"]), Jsc=float(r["Jsc_best_mAcm2"]), FF=float(r["FF_best_pct"]), eta=float(r["eta_best_pct"])),
                            avg=dict(Voc=float(r["Voc_avg_mV"]), Jsc=float(r["Jsc_avg_mAcm2"]), FF=float(r["FF_avg_pct"]), eta=float(r["eta_avg_pct"]))))
    return out


def combos(stage="main"):
    if stage == "main":
        cs = list(itertools.product(LOGS, TAUS, NAS, PHIB, NDS))
    else:                                       # refinement: half-decade S, then phi_b 0.65 at log10 S >= 3.5
        cs = list(itertools.product(LOGS_HALF, TAUS, NAS, PHIB, NDS))
        cs += list(itertools.product([l for l in LOGS_ALL if l >= 3.5], TAUS, NAS, [PHIB_EXT], NDS))
    random.Random(20261116).shuffle(cs)         # a partial run is then a uniform subsample of the grid
    return cs


def all_combos():
    """Every parameter set that exists in the main grid or the refinement."""
    return sorted(set(combos("main")) | set(combos("ext")))


def tag(x, c):
    lS, tau, na, pb, nd = c
    return f"x{x:.2f}_lS{lS:g}_t{tau * 1e9:g}_NA{na:.0e}_pb{pb:.2f}_ND{nd:.0e}".replace("+", "")


def params(c):
    lS, tau, na, pb, nd = c
    return {**sc.BEST, "S_front": 10.0 ** lS, "tau": tau, "NA": na, "phi_back": VBM_BACK - pb, "ND_MZO": nd}


def build(cell_d, c):
    p = params(c)
    layers, contacts = sc.case_layers(cell_d["x"], cell_d["dEc"], cell_d["Eg"], p)
    layers[2]["tau"] = layers[3]["tau"]           # IL keeps only the bulk lifetime
    cell = sc.build_cell(layers, contacts, 0.9, 0.2)
    sc.add_interface_defect(cell, p["S_front"])
    return cell


def write_atomic(path, rows, header):
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(header); w.writerows(rows)
    os.replace(tmp, path)


def run_one(cell_d, c):
    CURVES.mkdir(exist_ok=True)
    out = CURVES / f"{tag(cell_d['x'], c)}.csv"
    if out.exists():
        return None
    cell = build(cell_d, c)
    jv = sc.run_jv(cell, vlist=VLIST, tol=1e-8, stop_after_voc=2, time_limit=900)
    st = "ok" if jv.ok else jv.note.replace(",", ";")
    rows = [[f"{v:.6f}", f"{j:.8g}", st] for v, j in zip(jv.V, jv.J)] or [["", "", st]]
    write_atomic(out, rows, ["V_int", "J_mAcm2", "status"])
    m = sc.jv_metrics(jv.V, jv.J, 1.3) if jv.ok else {}
    print(f"{out.stem}: {st} Voc {m.get('Voc', float('nan')):.1f} Jsc {m.get('Jsc', float('nan')):.2f} "
          f"FF {m.get('FF', float('nan')):.1f} ({jv.seconds:.0f} s, halvings {jv.stats.get('step_halvings')})", flush=True)
    return jv


def run(stage="main"):
    CURVES.mkdir(exist_ok=True)
    cl = cells()
    for c in combos(stage):
        for cd in cl:
            run_one(cd, c)


DEGDT = -4e-4                                   # eV/K for CdSeTe and CdTe, split half/half between the band edges


def run_lowT(cell_d, c, temps=(300.0, 250.0, 225.0), na=None, label=""):
    """J-V of one cell at several temperatures. Absorber gaps shift by dEg/dT with f_cb 0.5; buffer, FTO and the
    back metal stay fixed in absolute energy (so dEc changes by half the gap shift and phi_b by the other half).
    Nc, Nv scale as T^1.5 (kj_sesame.build_cell). Sweep to 1.3 V to show forward-bias roll-over."""
    import kj_sesame as kj
    LOWT.mkdir(exist_ok=True)
    res = {}
    for T in temps:
        out = LOWT / f"{tag(cell_d['x'], c)}{label}_T{T:g}.csv"
        if not out.exists():
            p = params(c)
            if na is not None:
                p["NA"] = na
            layers, contacts = sc.case_layers(cell_d["x"], cell_d["dEc"], cell_d["Eg"], p)
            layers[2]["tau"] = layers[3]["tau"]
            dEg = DEGDT * (T - 300.0)
            for L in layers[2:]:
                L["Eg"] += dEg
                L["chi"] -= 0.5 * dEg
            contacts = dict(contacts, back_type="Schottky", front_type="Ohmic")
            cell = kj.build_cell(layers, contacts, T=T, T_front=0.9, R_back=0.2)
            sc.add_interface_defect(cell, p["S_front"])
            jv = sc.run_jv(cell, V_max=1.3, dV=0.01, tol=1e-8, stop_after_voc=40, time_limit=1500)
            st = "ok" if jv.ok else jv.note.replace(",", ";")
            rows = [[f"{v:.6f}", f"{j:.8g}", st] for v, j in zip(jv.V, jv.J)] or [["", "", st]]
            write_atomic(out, rows, ["V_int", "J_mAcm2", "status"])
            print(f"{out.stem}: {st} ({jv.seconds:.0f} s)", flush=True)
        res[T] = out
    return res


if __name__ == "__main__":
    if sys.argv[1] == "run":
        run(sys.argv[2] if len(sys.argv) > 2 else "main")
    elif sys.argv[1] == "lowT":            # python oneS.py lowT lS tau_ns NA phib ND [NA_override label]
        lS, tau, na, pb, nd = float(sys.argv[2]), float(sys.argv[3]) * 1e-9, float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6])
        c = (lS, tau, na, pb, nd)
        x0 = cells()[0]
        run_lowT(x0, c)
    elif sys.argv[1] == "nascan":          # python oneS.py nascan lS tau_ns phib ND : NA scan at fixed S (question 5)
        lS, tau, pb, nd = float(sys.argv[2]), float(sys.argv[3]) * 1e-9, float(sys.argv[4]), float(sys.argv[5])
        for cd in cells():
            for na in (2e14, 1e15, 3e15, 1e16, 3e16):
                run_one(cd, (lS, tau, na, pb, nd))
    elif sys.argv[1] == "smoke":
        cl = cells()
        for cd in (cl[0], cl[2]):
            for c in ((3, 30e-9, 1e15, 0.35, 1e17), (6, 30e-9, 1e15, 0.35, 1e17)):
                t = time.time(); jv = run_one(cd, c); print("wall", round(time.time() - t, 1))
