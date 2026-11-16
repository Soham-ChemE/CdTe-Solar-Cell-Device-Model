"""Assemble band offsets from superlattice lineups (lineup.json) and bulk references (bulk/*/result.json).

Sign convention (Li et al. 2009, Wei & Zunger 1998): for pair X/CdY
    dEv = Ev(CdY) - Ev(X)      dEc = Ec(X) - Ec(CdY) = [Eg(X) - Eg(CdY)] - dEv
Methods (all PBE lineups, scalar-relativistic, + SOC correction Delta_SO/3 per material):
  A  'avg'   : both materials at the SL's average lattice constant (hydrostatically strained). No assumption.
  V  'Vref'  : natural offset assuming V-bar has zero absolute volume deformation potential, i.e. bulk
               (E_VBM - Vbar) evaluated at each material's own a_exp.
  C  'core'  : natural offset assuming the semicore level has zero absolute deformation potential
               (Wei-Zunger 1998 core-level method; same assumption as an XPS Kraut-method measurement):
               Ev(M) = [Vbar_M(SL) + (E_c - Vbar)_M(a_avg)] + (E_VBM - E_c)_M(a_exp).
"""
import json, csv, sys
from pathlib import Path
import numpy as np
from common import MAT, EG_EXP, HERE, a_avg
from bulk_refs import tag_of

CORES = {"Cd": ["Cd4s", "Cd4p"], "Zn": ["Zn3s", "Zn3p"], "Te": ["Te4d"], "Se": ["Se3d"], "S": []}


def hj_D(m):
    """Absolute [001] deformation potential (eV per unit dlnV) of the cation-s level from homojunction.py, or nan."""
    f = HERE / "sl" / f"HJ_{m}_eps5_n2" / "homojunction.json"
    if not f.exists():
        return float("nan")
    h = json.loads(f.read_text())
    return h["D001_Cd4s" if MAT[m][0] == "Cd" else "D001_Zn3s"]


def bulk(m, a, ecut=80, soc=False):
    f = HERE / ("soc" if soc else "bulk") / tag_of(m, round(a, 5), None, ecut, soc) / "result.json"
    r = json.loads(f.read_text())
    assert r["ok"], f
    return r


def dso(m):
    try:
        return bulk(m, MAT[m][2], soc=True)["Delta_SO"]
    except Exception:
        return float("nan")


def offsets_for(lin):
    X, C = lin["A"], lin["B"]                  # SL built as (X)n(CdY)n
    aav = round(a_avg(X, C), 5)
    dV = lin["dV_centre"]                      # Vbar(CdY) - Vbar(X) in the SL, eV
    bx_av, bc_av = bulk(X, aav), bulk(C, aav)
    bx_eq, bc_eq = bulk(X, MAT[X][2]), bulk(C, MAT[C][2])
    so = dso(C) / 3 - dso(X) / 3
    dEg = EG_EXP[X] - EG_EXP[C]
    out = {}
    out["avg"] = dV + bc_av["VBM_minus_Vbar"] - bx_av["VBM_minus_Vbar"]
    out["Vref"] = dV + bc_eq["VBM_minus_Vbar"] - bx_eq["VBM_minus_Vbar"]
    core = {}
    for cx in CORES[MAT[X][0]] + CORES[MAT[X][1]]:
        for cc in CORES[MAT[C][0]] + CORES[MAT[C][1]]:
            ex = bx_av[cx + "_minus_Vbar"] + (bx_eq["E_VBM_gamma"] - bx_eq[cx])
            ec = bc_av[cc + "_minus_Vbar"] + (bc_eq["E_VBM_gamma"] - bc_eq[cc])
            core[f"{cx}|{cc}"] = dV + ec - ex
    cs = f"{MAT[X][0]}{'3s' if MAT[X][0]=='Zn' else '4s'}|{MAT[C][0]}{'3s' if MAT[C][0]=='Zn' else '4s'}"
    out["core"] = core[cs]
    out["core_all"] = core
    out["core_spread"] = (min(core.values()), max(core.values()))
    import math
    dlnC, dlnX = 3 * math.log(MAT[C][2] / aav), 3 * math.log(MAT[X][2] / aav)
    out["L"] = out["core"] + hj_D(C) * dlnC - hj_D(X) * dlnX
    out["SO"] = so; out["dEg"] = dEg; out["dV"] = dV
    return out


if __name__ == "__main__":
    for f in sys.argv[1:]:
        lin = json.loads((HERE / f / "lineup.json").read_text())
        print(json.dumps(offsets_for(lin), indent=1))
