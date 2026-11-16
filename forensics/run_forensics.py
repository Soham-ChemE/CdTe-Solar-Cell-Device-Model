"""Phase 1: re-run every original PR 2 SCAPS file with its original sweeps, then undo the setup errors.

Outputs: scaps/results/F_*.iv (raw SCAPS), forensics/forensics_results.csv (one row per case).
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from scaps_tools import SCAPS_DIR, RESULTS, DefFile, Batch, read_iv, at_short_circuit  # noqa: E402

HERE = Path(__file__).resolve().parent
DEFS = HERE.parent / "scaps/defs"
THICK = [0.4, 0.8, 1.2, 1.6, 2.0]
DEVICES = {  # material -> original file (layer1 is the swept "ETL")
    "C60": "C60", "Cs2BiAgI6": "Cs2BiAgI6 FINAL", "Cu2O": "Cu2O", "CuO": "CuO", "PC16BM": "PC16BM",
    "PCBM": "PCBM FINAL", "Sb2Se3": "Sb2Se3", "TiO2": "TiO2", "WO3": "WO3", "WS2": "WS2 FINAL",
}
cases = []  # (group, label, x, outname)
b = Batch("F_forensics")
STEP = 0.02  # the voltage step of the original PR 2 sweeps

# A. original transport-layer thickness sweeps, files untouched
for mat, f in DEVICES.items():
    for t in THICK:
        out = f"F_A_{mat}_{t:.1f}"
        b.case(f"{f}.def", out, sets=[f"set layer1.thickness {t:g}"], step=STEP)
        cases.append(("A_sweep", mat, t, out))
# earlier PR 2 baselines, as saved
for f, lab in [("CdTe-base-L1234_Correct[1]", "WS2 base with defects (5 Nov 2024)"), ("WS2-base", "WS2 base (23 Sep 2024)")]:
    out = "F_A0_" + f.split("[")[0].replace(" ", "_")
    b.case(f"{f}.def", out, step=STEP)
    cases.append(("A0_baseline", lab, float("nan"), out))

# B. back-contact metals on the 27.99% device at 2 um (metal list and work functions as in the report)
METALS = {"Al": 4.3, "Cu": 4.6, "Fe": 4.8, "C": 5.0, "Au": 5.1, "W": 5.2, "Ni": 5.55, "Pt": 5.7, "Se": 5.9}
base = DefFile.load(DEFS / "Cs2BiAgI6 FINAL.def")
for m, phi in METALS.items():
    d = DefFile.load(DEFS / "Cs2BiAgI6 FINAL.def").set_back_workfunction(phi)
    d.save(f"F_B_{m}")
    out = f"F_B_{m}"
    b.case(f"F_B_{m}.def", out, sets=["set layer1.thickness 2"], step=STEP)
    cases.append(("B_metal", m, phi, out))

# C. temperature 300-400 K on the 27.99% device at 2 um
for T in range(300, 401, 20):
    out = f"F_C_T{T}"
    b.case("Cs2BiAgI6 FINAL.def", out, T=T, sets=["set layer1.thickness 2"], step=STEP)
    cases.append(("C_temperature", "Cs2BiAgI6", T, out))

# D. which layer absorbs? switch absorption off in layer1 ("ETL") at 2 um
for mat in ["C60", "Cs2BiAgI6", "Cu2O", "TiO2"]:
    d = DefFile.load(DEFS / f"{DEVICES[mat]}.def").set_absorption_sqrt(0, A=0.0)
    d.save(f"F_D_{mat}_noabs")
    out = f"F_D_{mat}_noabs"
    b.case(f"F_D_{mat}_noabs.def", out, sets=["set layer1.thickness 2"], step=STEP)
    cases.append(("D_layer1_absorption_off", mat, 2.0, out))

# E. undo the setup errors in the 27.99% device (2 um Cs2BiAgI6), one at a time and cumulatively
ref = DefFile.load(SCAPS_DIR / "def/CdTe-base.def")
cdte_defect = ref.defect_blocks("CdTe")[0]          # Gloeckler et al. 2003 CdTe bulk donor defect


def fix_eg(d):            # CdTe band gap 1.6 eV (file) -> 1.5 eV (stated in paper and literature)
    return d.set_param("CdTe", "Eg", 1.5)


def fix_doping(d):        # CdTe Na = Nd = 1e15 cm-3 (compensated) -> p-type Na 2e14, Nd 0 (paper Table 1, Gloeckler)
    return d.set_param("CdTe", "Na(uniform)", 2e20).set_param("CdTe", "Nd(uniform)", 0.0)


def fix_absorption(d):    # Cs2BiAgI6 used CdTe's absorption file -> sqrt(hv-Eg) model at its own gap
    return d.set_absorption_sqrt("Cs2BiAgI6", A=1e7)


def fix_defects(d):       # zero defects -> Gloeckler CdTe bulk defect (donor, 2e14 cm-3, Ev+0.75 eV)
    return d.add_defect_block("CdTe", cdte_defect)


FIXES = [("Eg", fix_eg), ("doping", fix_doping), ("absorption", fix_absorption), ("defects", fix_defects)]
src = DEFS / "Cs2BiAgI6 FINAL.def"
for name, fn in FIXES:                                   # one at a time
    fn(DefFile.load(src)).save(f"F_E1_{name}")
    b.case(f"F_E1_{name}.def", f"F_E1_{name}", sets=["set layer1.thickness 2"], step=STEP)
    cases.append(("E_single_fix", name, 2.0, f"F_E1_{name}"))
d = DefFile.load(src)
for k, (name, fn) in enumerate(FIXES, 1):                # cumulative
    d = fn(d)
    tag = "+".join(n for n, _ in FIXES[:k])
    d.save(f"F_E2_{k}")
    b.case(f"F_E2_{k}.def", f"F_E2_{k}", sets=["set layer1.thickness 2"], step=STEP)
    cases.append(("E_cumulative", tag, 2.0, f"F_E2_{k}"))
# fully corrected device with the Cs2BiAgI6 layer removed (CdTe straight onto Ni)
d.layers.pop(0)
d.save("F_E3_no_backlayer")
b.case("F_E3_no_backlayer.def", "F_E3_no_backlayer", step=STEP)
cases.append(("E_reference", "all fixes, no Cs2BiAgI6 layer", float("nan"), "F_E3_no_backlayer"))

print(f"{len(cases)} cases -> running SCAPS once ...", flush=True)
r = b.run(timeout=5400)
print(r.stdout[-2000:], r.stderr[-2000:])

rows = []
for g, lab, x, out in cases:
    p = RESULTS / f"{out}.iv"
    if not p.exists():
        rows.append([g, lab, x, out, "", "", "", "", "", "", "missing"])
        continue
    res = read_iv(p)
    expected = dict(b.outputs)[out]
    status = "ok" if res["deffile"].lower() == expected.lower() else f"STALE (file says {res['deffile']})"
    rows.append([g, lab, x, out, res["Voc"], res["Jsc"], res["FF"], res["eta"],
                 at_short_circuit(res, "j_SRH(mA/cm2)"), at_short_circuit(res, "jifr(mA/cm2)"), status])
with open(HERE / "forensics_results.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["group", "case", "x", "file", "Voc_V", "Jsc_mA_cm2", "FF_pct", "eta_pct", "J_SRH_at_0V", "J_interface_at_0V", "status"])
    w.writerows(rows)
bad = [r for r in rows if r[-1] != "ok"]
print("wrote", HERE / "forensics_results.csv", "rows:", len(rows), "not ok:", len(bad))
for r in bad: print("  ", r[0], r[1], r[2], r[-1])
