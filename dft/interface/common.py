"""Shared settings and helpers for the II-VI band-offset workflow (QE 7.6, PseudoDojo NC PBE v0.4).

Conventions used everywhere in this directory
  * energies in eV, lengths in Angstrom unless a name says otherwise
  * V-bar = cell (macroscopic) average of V_bare + V_Hartree from pp.x plot_num=11 (no xc)
  * for a pair "X/CdY" the offsets are reported as
        dEv = Ev(Cd compound) - Ev(X)      (Li et al. 2009 / Wei-Zunger sign: dEv(X/CdY) = Ev(CdY) - Ev(X))
        dEc = Ec(X) - Ec(Cd compound) = [Eg(X) - Eg(CdY)] - dEv
    so dEc > 0 means the partner's conduction band lies above the Cd compound's (a spike seen from CdY).
"""
import re, subprocess, time, os
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]                       # cdte-device-model
QE = ROOT / "tools/qe-env/bin"
PSEUDO_SR = HERE.parent / "pseudo/sr"
PSEUDO_FR = HERE.parent / "pseudo/fr/nc-fr-04_pbe_standard"
BOHR = 0.529177210903
RY = 13.605693122994
NP_MAX = 4                                   # hard cap (SCAPS shares the machine)

# zinc-blende experimental lattice constants (A), identical to ../bulk/make_and_run_bulk.py
MAT = {  # name: (cation, anion, a_exp)
    "CdTe": ("Cd", "Te", 6.481),
    "CdSe": ("Cd", "Se", 6.077),
    "ZnSe": ("Zn", "Se", 5.668),
    "ZnTe": ("Zn", "Te", 6.101),
    "CdS":  ("Cd", "S",  5.818),
}
MASS = {"Cd": 112.414, "Zn": 65.38, "Te": 127.60, "Se": 78.971, "S": 32.06}
EG_EXP = {"CdTe": 1.50, "ZnSe": 2.70, "ZnTe": 2.26, "CdS": 2.42, "CdSe": 1.74}  # CdSe: zb ~1.74 (only used for ZnSe/CdSe)

# semicore groups in band order at Gamma (lowest first), counted per formula unit, no SOC
SEMICORE = {
    "Cd": [("Cd4s", 1), ("Cd4p", 3)],
    "Zn": [("Zn3s", 1), ("Zn3p", 3)],
    "Te": [("Te4d", 5)], "Se": [("Se3d", 5)], "S": [],
}
ZVAL = {"Cd": 20, "Zn": 20, "Te": 16, "Se": 16, "S": 6}


def a_avg(A, B):
    return 0.5 * (MAT[A][2] + MAT[B][2])


def run_qe(exe, inp, cwd, np=NP_MAX, extra=(), log=None):
    """Run a QE executable under mpirun; returns (wall seconds, output text)."""
    assert np <= NP_MAX
    cwd = Path(cwd); out = cwd / (log or (Path(inp).stem + ".out"))
    t = time.time()
    cmd = [str(QE / "mpirun"), "-np", str(np), str(QE / exe), *extra, "-in", str(inp)]
    if np == 1:
        cmd = [str(QE / exe), *extra, "-in", str(inp)]
    env = dict(os.environ, OMP_NUM_THREADS="1")
    with open(out, "w") as fh:
        subprocess.run(cmd, cwd=cwd, stdout=fh, stderr=subprocess.STDOUT, env=env)
    return time.time() - t, out.read_text()


def parse_bands(txt):
    """Return list of (k-vector, eigenvalues array) from the last band printout of a pw.x output."""
    blk = txt.split("End of self-consistent calculation")[-1].split("End of band structure calculation")[-1]
    out, cur, k = [], None, None
    for line in blk.splitlines():
        if "bands (ev)" in line and "k =" in line:
            if cur is not None:
                out.append((k, np.array(cur)))
            ks = re.findall(r"-?\d+\.\d+", line.split("k =")[1].split("(")[0].replace("-", " -"))
            k, cur = tuple(float(x) for x in ks[:3]), []
            continue
        if cur is None:
            continue
        s = line.strip()
        if s.startswith(("occupation", "highest", "the Fermi", "Writing", "total energy", "!")) or "SPIN" in s:
            out.append((k, np.array(cur))); cur = None; continue
        cur += [float(x) for x in re.findall(r"-?\d+\.\d+", line.replace("-", " -"))]
    if cur:
        out.append((k, np.array(cur)))
    return out


def vbm_cbm(txt):
    m = re.findall(r"highest occupied, lowest unoccupied level \(ev\):\s+([-\d.]+)\s+([-\d.]+)", txt)
    if m:
        return float(m[-1][0]), float(m[-1][1])
    m = re.findall(r"highest occupied level \(ev\):\s+([-\d.]+)", txt)
    return float(m[-1]), float("nan")


def read_cube(path):
    """Read a Gaussian cube written by pp.x; returns (data[n1,n2,n3] in file units, cell vectors in bohr)."""
    with open(path) as fh:
        fh.readline(); fh.readline()
        nat = int(fh.readline().split()[0])
        n, v = [], []
        for _ in range(3):
            p = fh.readline().split(); n.append(int(p[0])); v.append([float(x) * int(p[0]) for x in p[1:4]])
        for _ in range(abs(nat)):
            fh.readline()
        data = np.array(fh.read().split(), dtype=float)
    return data.reshape(n), np.array(v)


def wall(sec):
    return f"{sec/60:.1f} min" if sec < 3600 else f"{sec/3600:.2f} h"
