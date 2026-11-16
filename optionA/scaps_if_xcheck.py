"""SCAPS cross-check of the Sesame interface-state front model (optionA/sesame/sesame_cell.add_interface_defect).

Sesame model: neutral interface states at the IL/ZnO boundary, level at mid interface gap (Ec_ZnO + Ev_abs)/2,
capturing ZnO conduction-band electrons and absorber valence-band holes, S = sigma*vth*N_s; the IL keeps only
its bulk defect. SCAPS equivalent: an 'interface recombination' block in the IL's interface properties with
sigma_nright = sigma_pleft = 1e-16 m^2 (ZnO electrons, absorber holes), the other two cross-sections negligible,
reference 9 (above middle of interface gap), Et = 0, N_s = S/(sigma*vth).
Cases: the 300 K defs of the Sesame calibration (optionA/sesame/kujovic/calib/defs/*_T300.def), tau 10 ns, live window.
Output: optionA/scaps_if_xcheck.csv
"""
import csv, re, sys, time
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from scaps_tools import DefFile, run_parallel, read_iv, RESULTS

SIG = 1e-16          # m^2
VTH = 1e5            # m/s
IFBLOCK = """interface recombination

type : neutral
sigma_nleft : 1.000e-25 [m^2]
sigma_nright : {sig:.3e} [m^2]
sigma_pleft : {sig:.3e} [m^2]
sigma_pright : 1.000e-25 [m^2]
Tunneling to trap: 0 (0: no tunneling, 1: with tunneling)
Relative electron mass :  1.00e+00
Relative hole mass :  1.00e+00
energy distribution : single
Reference for defect energy :  9 ; 3 = above highest EV; 4 = below lowest EC; 5 = above Ei left; 6 = above Ei right; 7 = above EV left (= SCAPS%<2.7 reference); 8 = above EV right; 9 = above middle of interface gap
Et :  0.00 [eV]
Ekar :  0.10 [eV]
N : {N:.3e} [/m^2]
"""

def make(phi, dEc, S_cm_s, name):
    src = REPO / "optionA/sesame/kujovic/calib/defs" / f"C_phi{phi:.2f}_dEc{dEc:+.2f}_g4p0_T300.def".replace("+", "p").replace("-", "m").replace(".", "p").replace("pdef", ".def")
    d = DefFile.load(src)
    blocks = d.defect_blocks("IL")
    d.remove_defects("IL").add_defect_block("IL", blocks[0])          # bulk defect only
    i = d.idx("IL")
    N = (S_cm_s / 100.0) / (SIG * VTH)
    d.layers[i] = d.layers[i].rstrip("\n") + "\n\n" + IFBLOCK.format(sig=SIG, N=N) + "\n\n"
    d.save(name)
    return name, src.name, N

if __name__ == "__main__":
    CASES = [(0.50, +0.10, 1e4), (0.55, -0.10, 1e3), (0.50, -0.22, 1e3), (0.50, -0.32, 1e3)]
    sesame = {r["tag"]: r for r in csv.DictReader(open(REPO / "optionA/sesame/kujovic/calib/calib_scores.csv"))}
    cases, meta = [], []
    for phi, dEc, S in CASES:
        name, srcname, N = make(phi, dEc, S, f"X_if_phi{phi:.2f}_dEc{dEc:+.2f}_S{S:.0e}".replace("+", "p").replace("-", "m").replace(".", "p"))
        cases.append(dict(deffile=f"{name}.def", out=name, step=0.01, stopV=1.3))
        meta.append((phi, dEc, S, name, srcname, N))
    t = time.time(); run_parallel("X_ifcheck", cases, n_workers=1, timeout=3600); print("wall", round(time.time() - t), "s")
    rows = []
    for phi, dEc, S, name, srcname, N in meta:
        f = RESULTS / f"{name}.iv"; iv = read_iv(f) if f.exists() else {}
        ok = bool(iv) and iv.get("deffile") == f"{name}.def" and iv["Voc"] == iv["Voc"]
        tg = f"phi{phi:.2f}_dEc{dEc:+.2f}_S{S:.0e}".replace("+", "p").replace("-", "m").replace("e+0", "ep0")
        s = sesame.get(tg, {})
        r = dict(phi_b=phi, dEc=dEc, S=S, N_m2=f"{N:.3e}", scaps_ok=ok,
                 Voc_scaps=round(iv["Voc"] * 1000, 1) if ok else "", FF_scaps=round(iv["FF"], 2) if ok else "",
                 Jsc_scaps=round(iv["Jsc"], 3) if ok else "", Voc_sesame=s.get("Voc300", ""), FF_sesame=s.get("FF300", ""),
                 Jsc_sesame=s.get("Jsc300", ""))
        rows.append(r); print(r)
    with open(REPO / "optionA/scaps_if_xcheck.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
