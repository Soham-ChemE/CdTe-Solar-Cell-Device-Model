"""Bulk zinc-blende II-VI band edges: PBE for six compounds, plus an HSE timing test on CdTe.
Experimental room-temperature lattice constants (Angstrom), zinc-blende polytypes."""
import re, subprocess, time, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
QE = HERE.parents[1] / "tools/qe-env/bin"
PSEUDO = HERE.parent / "pseudo/sr"
BOHR = 0.529177210903
COMPOUNDS = {  # name: (cation, anion, a_exp in Angstrom, cation mass, anion mass)
    "CdTe": ("Cd", "Te", 6.481, 112.414, 127.60),
    "CdSe": ("Cd", "Se", 6.077, 112.414, 78.971),
    "ZnSe": ("Zn", "Se", 5.668, 65.38, 78.971),
    "ZnTe": ("Zn", "Te", 6.101, 65.38, 127.60),
    "ZnS":  ("Zn", "S",  5.409, 65.38, 32.06),
    "CdS":  ("Cd", "S",  5.818, 112.414, 32.06),
}

def zval(el):
    return float(re.search(r'z_valence="\s*([\d.]+)"', (PSEUDO / f"{el}.upf").read_text()).group(1))

def write(name, functional="pbe"):
    c, a, alat, mc, ma = COMPOUNDS[name]
    nel = zval(c) + zval(a)
    nbnd = int(nel // 2) + 8
    d = HERE / name; d.mkdir(exist_ok=True)
    hyb = ""
    if functional == "hse":
        hyb = ("  input_dft = 'hse'\n  nqx1 = 2, nqx2 = 2, nqx3 = 2\n  ecutfock = 120\n"
               "  exxdiv_treatment = 'gygi-baldereschi'\n  x_gamma_extrapolation = .true.\n")
    kgrid = "8 8 8 0 0 0" if functional == "pbe" else "6 6 6 0 0 0"
    txt = f"""&control
  calculation = 'scf'
  prefix = '{name}_{functional}'
  outdir = './tmp'
  pseudo_dir = '{PSEUDO}'
/
&system
  ibrav = 2
  celldm(1) = {alat / BOHR:.5f}
  nat = 2
  ntyp = 2
  ecutwfc = 80
  nbnd = {nbnd}
{hyb}/
&electrons
  conv_thr = 1.0d-9
/
ATOMIC_SPECIES
  {c} {mc} {c}.upf
  {a} {ma} {a}.upf
ATOMIC_POSITIONS crystal
  {c} 0.00 0.00 0.00
  {a} 0.25 0.25 0.25
K_POINTS automatic
  {kgrid}
"""
    f = d / f"scf_{functional}.in"; f.write_text(txt); return f

def run(f, np=8, nk=4):
    t = time.time()
    out = f.with_suffix(".out")
    with open(out, "w") as fh:
        subprocess.run([str(QE / "mpirun"), "-np", str(np), str(QE / "pw.x"), "-nk", str(nk), "-in", f.name],
                       cwd=f.parent, stdout=fh, stderr=subprocess.STDOUT)
    txt = out.read_text()
    ms = re.findall(r"highest occupied, lowest unoccupied level \(ev\):\s+([-\d.]+)\s+([-\d.]+)", txt)
    gap = float(ms[-1][1]) - float(ms[-1][0]) if ms else float("nan")   # last value = final (EXX) result
    return gap, time.time() - t, ("JOB DONE" in txt)

if __name__ == "__main__":
    rows = []
    for name in COMPOUNDS:
        gap, sec, ok = run(write(name, "pbe"))
        rows.append((name, "PBE", gap, sec, ok)); print(f"{name:5s} PBE   gap {gap:6.3f} eV  {sec:6.0f} s  {'ok' if ok else 'FAILED'}", flush=True)
    gap, sec, ok = run(write("CdTe", "hse"), np=8, nk=4)
    rows.append(("CdTe", "HSE06 (nq 2)", gap, sec, ok)); print(f"CdTe  HSE06 gap {gap:6.3f} eV  {sec:6.0f} s  {'ok' if ok else 'FAILED'}", flush=True)
    with open(HERE / "bulk_gaps_summary.csv", "w") as fh:
        fh.write("compound,functional,gap_Gamma_eV,wall_s,ok\n")
        for r in rows: fh.write(",".join(str(x) for x in r) + "\n")
