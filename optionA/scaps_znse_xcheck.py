"""SCAPS cross-check of large ZnSe spikes (Sesame drift-diffusion vs SCAPS thermionic emission at the interface).
Defs from optionA/sesame/kujovic/znse/defs/*_Sbest_*; adds the interface-state block (S = 5.21 cm/s) in the IL.
Output: optionA/scaps_znse_xcheck.csv"""
import csv, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts")); sys.path.insert(0, str(REPO / "optionA"))
from scaps_tools import DefFile, run_parallel, read_iv, RESULTS
from scaps_if_xcheck import IFBLOCK, SIG, VTH
SESAME = {0.30: "970.0 mV / 27.40 / 86.3 / 22.93", 0.55: "J(0) 13.70, J=0 at 1.005 V, FF 20.2, eta 2.78", 0.70: "J(0) 1.61, no Voc < 1.6 V"}
cases, meta = [], []
for dEc in (0.30, 0.55, 0.70):
    src = REPO / f"optionA/sesame/kujovic/znse/defs/ZnSe_dEcp{dEc:.2f}_Sbest_ND1e17_d80.def"
    d = DefFile.load(src); i = d.idx("IL")
    N = (5.21 / 100.0) / (SIG * VTH)
    d.layers[i] = d.layers[i].rstrip("\n") + "\n\n" + IFBLOCK.format(sig=SIG, N=N) + "\n\n"
    name = f"X_znse_dEcp{dEc:.2f}".replace(".", "p"); d.save(name)
    cases.append(dict(deffile=f"{name}.def", out=name, step=0.01, stopV=1.6)); meta.append((dEc, name))
run_parallel("X_znse", cases, n_workers=1, timeout=3600)
rows = []
for dEc, name in meta:
    f = RESULTS / f"{name}.iv"; iv = read_iv(f) if f.exists() else {}
    ok = bool(iv.get("table")) and iv.get("deffile") == f"{name}.def"
    J0 = -iv["table"][0][1] if ok else float("nan")
    rows.append(dict(dEc=dEc, scaps_ok=ok, J0_scaps=round(J0, 3) if ok else "", Voc_scaps=round(iv["Voc"] * 1000, 1) if ok and iv["Voc"] == iv["Voc"] else "",
                     FF_scaps=iv.get("FF", "") if ok else "", eta_scaps=iv.get("eta", "") if ok else "", sesame=SESAME[dEc]))
    print(rows[-1])
with open(REPO / "optionA/scaps_znse_xcheck.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
