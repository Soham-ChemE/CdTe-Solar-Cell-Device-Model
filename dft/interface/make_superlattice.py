"""Build pw.x / pp.x / average.x inputs for an (A)n(B)n (001) zinc-blende superlattice.

Cell: simple tetragonal (ibrav=6), in-plane vectors a_par/sqrt2 along [110] and [1-10],
c axis along [001]; 4 atoms (2 cation + 2 anion planes) per conventional-cell height and per material.
Default geometry = Li et al. (2009) protocol: unrelaxed, ideal zinc-blende positions, both
materials cubic at the average lattice constant a_avg = (a_A + a_B)/2.
Optional c_A, c_B give tetragonally distorted layers (pseudomorphic geometry).

Usage:  python make_superlattice.py ZnTe CdTe 3 [--ecut 80] [--k 6 6 1] [--apar A] [--cA A] [--cB A]
"""
import argparse, math
from pathlib import Path
from common import MAT, MASS, ZVAL, BOHR, PSEUDO_SR, HERE, a_avg

INPLANE = [(0.0, 0.0), (0.5, 0.0), (0.5, 0.5), (0.0, 0.5)]   # plane p -> in-plane crystal coords (p mod 4)


def planes(A, B, n, cA, cB):
    """List of (species, z in Angstrom, material) for the 8n atomic planes, starting with A's cation at z=0."""
    out, z = [], 0.0
    seq = [(A, cA)] * (4 * n) + [(B, cB)] * (4 * n)
    for p, (m, c) in enumerate(seq):
        cat, an, _ = MAT[m]
        out.append((cat if p % 2 == 0 else an, z, m))
        nxt = seq[(p + 1) % len(seq)][1]
        z += (c + nxt) / 8.0              # c/4 inside a layer, average of the two at an interface
    return out, z


def write_inputs(A, B, n, ecut=80, k=(6, 6, 1), apar=None, cA=None, cB=None, tag=None, disk_io="high",
                 conv_thr="1.0d-8", smearing=False):
    apar = apar or a_avg(A, B)
    cA = cA or apar; cB = cB or apar
    pl, L = planes(A, B, n, cA, cB)
    b = apar / math.sqrt(2)
    tag = tag or f"{A}_{B}_n{n}"
    d = HERE / "sl" / tag; d.mkdir(parents=True, exist_ok=True)
    species = sorted({s for s, _, _ in pl}, key=lambda s: (s not in ("Zn", "Cd"), s))
    nel = sum(ZVAL[s] for s, _, _ in pl)
    pos = "\n".join(f"  {s:2s} {INPLANE[p % 4][0]:.6f} {INPLANE[p % 4][1]:.6f} {z / L:.10f}"
                    for p, (s, z, _) in enumerate(pl))
    spec = "\n".join(f"  {s:2s} {MASS[s]:.3f} {s}.upf" for s in species)
    prefix = tag
    # strained cells can have a (PBE) broken gap: use small Gaussian smearing + extra bands so charge transfer is visible
    smear = (f"  occupations = 'smearing'\n  smearing = 'gaussian'\n  degauss = 0.005\n  nbnd = {nel // 2 + 24}\n"
             if smearing else "")
    (d / "scf.in").write_text(f"""&control
  calculation = 'scf'
  prefix = '{prefix}'
  outdir = './tmp'
  pseudo_dir = '{PSEUDO_SR}'
  disk_io = '{disk_io}'
/
&system
  ibrav = 6
  celldm(1) = {b / BOHR:.8f}
  celldm(3) = {L / b:.8f}
  nat = {len(pl)}
  ntyp = {len(species)}
  ecutwfc = {ecut}
{smear}/
&electrons
  conv_thr = {conv_thr}
  mixing_beta = 0.3
  mixing_ndim = 12
/
ATOMIC_SPECIES
{spec}
ATOMIC_POSITIONS crystal
{pos}
K_POINTS automatic
  {k[0]} {k[1]} {k[2]} 0 0 0
""")
    (d / "pp.in").write_text(f"""&inputpp
  prefix = '{prefix}'
  outdir = './tmp'
  filplot = 'vbh.pp'
  plot_num = 11
/
&plot
  iflag = 3
  output_format = 6
  fileout = 'vbh.cube'
/
""")
    # average.x: planar average along z, macroscopic average with one window = ML period a/2 (bohr)
    win = (apar / 2) / BOHR if (cA == apar and cB == apar) else (cA / 2) / BOHR
    (d / "average.in").write_text(f"1\nvbh.pp\n1.0\n3000\n3\n{win:.8f}\n")
    meta = dict(A=A, B=B, n=n, ecut=ecut, k=list(k), apar=apar, cA=cA, cB=cB, L=L, nel=nel,
                planes=[(s, z, m) for s, z, m in pl])
    import json
    (d / "meta.json").write_text(json.dumps(meta, indent=1))
    return d


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("A"); ap.add_argument("B"); ap.add_argument("n", type=int)
    ap.add_argument("--ecut", type=float, default=80); ap.add_argument("--k", type=int, nargs=3, default=[6, 6, 1])
    ap.add_argument("--apar", type=float); ap.add_argument("--cA", type=float); ap.add_argument("--cB", type=float)
    ap.add_argument("--tag")
    a = ap.parse_args()
    print(write_inputs(a.A, a.B, a.n, a.ecut, tuple(a.k), a.apar, a.cA, a.cB, a.tag))
