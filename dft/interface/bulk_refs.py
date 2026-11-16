"""Bulk reference calculations for the band-offset workflow.

For a zinc-blende compound at lattice constant a (cubic, 2-atom fcc cell) or a tetragonally strained
4-atom cell (a_par, c), compute with the same pseudopotentials / cutoff as the superlattices:
  E_VBM, E_CBM (Gamma), semicore levels at Gamma (cation s, cation p, anion d),
  V-bar = cell average of V_bare + V_H (pp.x plot_num=11), and with --soc the Gamma8-Gamma7 splitting.
Results are cached in bulk/<tag>/result.json (or soc/<tag>/result.json).

Usage examples:
  python bulk_refs.py CdTe 6.481                 # cubic, SR pseudos
  python bulk_refs.py ZnSe 6.481 --c 4.80        # tetragonal: a_par = 6.481, c = 4.80 (pseudomorphic)
  python bulk_refs.py CdTe 6.481 --soc           # fully relativistic, Delta_SO
"""
import argparse, json, math
from pathlib import Path
import numpy as np
from common import (MAT, MASS, ZVAL, BOHR, RY, PSEUDO_SR, PSEUDO_FR, HERE, NP_MAX,
                    run_qe, parse_bands, vbm_cbm, read_cube)


def tag_of(mat, a, c=None, ecut=80, soc=False, k=None, hse=False, nq=2):
    t = f"{mat}_a{a:.4f}" + (f"_c{c:.4f}" if c else "") + (f"_ec{ecut:g}" if ecut != 80 else "")
    return t + (f"_k{k}" if k else "") + ("_hse" if hse else "") + (f"_nq{nq}" if hse and nq != 2 else "")


def write_input(d, mat, a, c=None, ecut=80, soc=False, k=8, nbnd_extra=8, calc="scf", hse=False, nq=2):
    cat, an, _ = MAT[mat]
    nel = ZVAL[cat] + ZVAL[an]
    if c is None:      # 2-atom fcc cell
        cell = f"  ibrav = 2\n  celldm(1) = {a / BOHR:.8f}\n"
        pos = f"  {cat} 0.00 0.00 0.00\n  {an} 0.25 0.25 0.25\n"
        kp = f"  {k} {k} {k} 0 0 0"; nat = 2
    else:              # 4-atom simple tetragonal cell, a_par along [110]/[1-10], c along [001]
        b = a / math.sqrt(2)
        cell = f"  ibrav = 6\n  celldm(1) = {b / BOHR:.8f}\n  celldm(3) = {c / b:.8f}\n"
        pos = (f"  {cat} 0.0 0.0 0.0\n  {an} 0.5 0.0 0.25\n  {cat} 0.5 0.5 0.5\n  {an} 0.0 0.5 0.75\n")
        kz = max(4, round(k * a / c * 0.75))
        kp = f"  {k} {k} {kz} 0 0 0"; nat = 4; nel *= 2
    nbnd = (nel // 2 + nbnd_extra) * (2 if soc else 1)
    socl = "  noncolin = .true.\n  lspinorb = .true.\n" if soc else ""
    if hse:   # same HSE06 settings as ../bulk/make_and_run_bulk.py (nq 2x2x2, ecutfock 120 Ry)
        socl += (f"  input_dft = 'hse'\n  nqx1 = {nq}, nqx2 = {nq}, nqx3 = {nq}\n  ecutfock = 120\n"
                 "  exxdiv_treatment = 'gygi-baldereschi'\n  x_gamma_extrapolation = .true.\n")
        nbnd = nel // 2 + 4
    pdir = PSEUDO_FR if soc else PSEUDO_SR
    (d / "scf.in").write_text(f"""&control
  calculation = '{calc}'
  prefix = 'b'
  outdir = './tmp'
  pseudo_dir = '{pdir}'
/
&system
{cell}  nat = {nat}
  ntyp = 2
  ecutwfc = {ecut}
  nbnd = {nbnd}
{socl}/
&electrons
  conv_thr = 1.0d-10
/
ATOMIC_SPECIES
  {cat} {MASS[cat]} {cat}.upf
  {an} {MASS[an]} {an}.upf
ATOMIC_POSITIONS crystal
{pos}K_POINTS automatic
{kp}
""")
    (d / "pp.in").write_text("""&inputpp
  prefix = 'b'
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
    return nel, nat


def gamma_levels(evals, mat, nel, soc):
    """Group the deep Gamma eigenvalues into semicore levels by energy gaps (>2 eV)."""
    cat, an, _ = MAT[mat]
    e = np.sort(evals)
    groups, cur = [], [e[0]]
    for x in e[1:]:
        if x - cur[-1] > 2.0:
            groups.append(cur); cur = [x]
        else:
            cur.append(x)
    groups.append(cur)
    names = [f"{cat}{'3' if cat == 'Zn' else '4'}s", f"{cat}{'3' if cat == 'Zn' else '4'}p"]
    if an == "Te": names.append("Te4d")
    if an == "Se": names.append("Se3d")
    out = {}
    for nm, g in zip(names, groups):
        out[nm] = float(np.mean(g)); out[nm + "_nb"] = len(g); out[nm + "_spread"] = float(np.ptp(g))
    return out


def run(mat, a, c=None, ecut=80, soc=False, k=8, force=False, hse=False, nq=2):
    base = HERE / ("soc" if soc else ("hse" if hse else "bulk"))
    d = base / tag_of(mat, a, c, ecut, soc, None if k == 8 else k, hse, nq); d.mkdir(parents=True, exist_ok=True)
    rf = d / "result.json"
    if rf.exists() and not force:
        return json.loads(rf.read_text())
    nel, nat = write_input(d, mat, a, c, ecut, soc, k, hse=hse, nq=nq)
    t1, txt = run_qe("pw.x", "scf.in", d, NP_MAX, ["-nk", "4"])
    ok = "JOB DONE" in txt and "convergence has been achieved" in txt
    res = dict(mat=mat, a=a, c=c, ecut=ecut, soc=soc, hse=hse, k=k, ok=ok, pw_s=t1)
    if ok:
        vb, cb = vbm_cbm(txt)
        bands = parse_bands(txt)
        g = [e for kk, e in bands if max(abs(x) for x in kk) < 1e-6][0]
        nocc = nel if soc else nel // 2               # occupied bands per cell
        res.update(E_VBM=vb, E_CBM=cb, gap=cb - vb, E_VBM_gamma=float(g[nocc - 1]), E_CBM_gamma=float(g[nocc]))
        if soc:
            # top of valence at Gamma: Gamma8 (4-fold) above Gamma7 (2-fold) per formula unit
            nf = nat // 2
            res["E_G8"] = float(g[nocc - 1]); res["E_G7"] = float(g[nocc - 1 - 4 * nf])
            res["Delta_SO"] = res["E_G8"] - res["E_G7"]
            res["top6"] = [float(x) for x in g[nocc - 6 * nf:nocc]]
        else:
            res.update(gamma_levels(g[:9 * (nat // 2) + 1] if MAT[mat][1] != "S" else g[:4 * (nat // 2) + 1], mat, nel, soc))
            if nat == 4:   # tetragonal: report top 3 valence states at Gamma (split by strain)
                res["top_val_gamma"] = [float(x) for x in g[nocc - 6:nocc]]
        t2, _ = run_qe("pp.x", "pp.in", d, NP_MAX)
        data, _ = read_cube(d / "vbh.cube")
        res["Vbar"] = float(data.mean()) * RY
        res["pp_s"] = t2
        res["VBM_minus_Vbar"] = res["E_VBM_gamma"] - res["Vbar"]
        for kk in list(res):
            if kk[-1] in "spd" and kk[:2] in ("Cd", "Zn", "Te", "Se") and not kk.endswith(("_nb", "_spread")):
                res[f"{kk}_minus_Vbar"] = res[kk] - res["Vbar"]
        (d / "vbh.cube").unlink(missing_ok=True)
        for f in (d / "tmp").rglob("wfc*"):
            f.unlink()
    rf.write_text(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mat"); ap.add_argument("a", type=float)
    ap.add_argument("--c", type=float); ap.add_argument("--ecut", type=float, default=80)
    ap.add_argument("--soc", action="store_true"); ap.add_argument("--k", type=int, default=8)
    ap.add_argument("--force", action="store_true"); ap.add_argument("--hse", action="store_true")
    ap.add_argument("--nq", type=int, default=2)
    x = ap.parse_args()
    r = run(x.mat, x.a, x.c, x.ecut, x.soc, x.k, x.force, x.hse, x.nq)
    print(json.dumps(r, indent=1))
