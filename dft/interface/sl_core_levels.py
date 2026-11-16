"""Atom-resolved semicore ('core') levels in a superlattice from projwfc.x (Lowdin projections).

Checks the bulk-likeness assumption used by the core-level method: for an atom in the centre of layer M,
E_core(atom) - Vbar_M(SL) should equal the bulk (E_core - Vbar) of M at the same lattice constant.
Usage: python sl_core_levels.py sl/ZnTe_CdTe_n3   (needs wavefunctions kept: run_superlattice.py --keepwfc)
"""
import json, re, sys
from pathlib import Path
import numpy as np
from common import run_qe, HERE, NP_MAX

d = (HERE / sys.argv[1]).resolve()
meta = json.loads((d / "meta.json").read_text())
if not (d / "projwfc.out").exists() or "JOB DONE" not in (d / "projwfc.out").read_text():
    (d / "projwfc.in").write_text(f"""&projwfc
  prefix = '{d.name}'
  outdir = './tmp'
  filpdos = 'pdos'
  lsym = .false.
  degauss = 0.01
  DeltaE = 0.05
/
""")
    t, _ = run_qe("projwfc.x", "projwfc.in", d, NP_MAX)
    print(f"projwfc {t:.0f} s")
txt = (d / "projwfc.out").read_text()
# map wfc index -> (atom index, species, l)
wmap = {}
for m in re.finditer(r"state #\s*(\d+): atom\s+(\d+) \((\w+)\s*\)\s*, wfc\s+(\d+) \(l=(\d)", txt):
    wmap[int(m.group(1))] = (int(m.group(2)), m.group(3), int(m.group(5)))
# k-point weights are not printed by projwfc; read them from scf.out
scf = (d / "scf.out").read_text()
wk = [float(x) for x in re.findall(r"k\(\s*\d+\) = \([^)]*\), wk =\s*([\d.]+)", scf.split("cryst. coord.")[0])]
blocks = txt.split(" k = ")[1:]
acc = {}  # (atom, l) -> [sum w*e, sum w]
for ik, b in enumerate(blocks):
    for m in re.finditer(r"==== e\(\s*\d+\) =\s*([-\d.]+) eV ====\s*\n(.*?)\|psi\|\^2", b, re.S):
        e = float(m.group(1))
        if e > -25:          # only semicore states (VBM is ~0 to +8 eV on this scale)
            continue
        for w, s in re.findall(r"([\d.]+)\*\[#\s*(\d+)\]", m.group(2)):
            at, sp, l = wmap[int(s)]
            key = (at, sp, l)
            a = acc.setdefault(key, [0.0, 0.0])
            a[0] += wk[ik] * float(w) * e; a[1] += wk[ik] * float(w)
planes = meta["planes"]
rows = []
for (at, sp, l), (we, w) in sorted(acc.items()):
    if w < 1e-3:
        continue
    z = planes[at - 1][1]
    rows.append(dict(atom=at, species=sp, l=l, z=z, layer=planes[at - 1][2], E=we / w, weight=w))
(d / "core_levels_sl.json").write_text(json.dumps(rows, indent=1))
for r in rows:
    print(f"{r['atom']:3d} {r['species']:2s} l={r['l']} z={r['z']:7.3f} {r['layer']:5s} E={r['E']:10.4f} w={r['weight']:.2f}")
