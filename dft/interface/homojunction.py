"""Absolute [001] uniaxial deformation potential of semicore levels from a strained/unstrained homojunction.

(M)n(M')n (001) superlattice of ONE compound: first half cubic at a_exp, second half strained uniaxially along
[001] (in-plane a_exp, c = a_exp (1 + eps)). The semicore lineup across this coherent homojunction is
    dE_c = dVbar(SL) + (E_c - Vbar)_strained bulk - (E_c - Vbar)_cubic bulk,
and D_c[001] = dE_c / ln(1 + eps) is the absolute deformation potential of level c for [001] uniaxial strain
(per unit dlnV). Li, Gong & Wei (PRB 73, 245206, 2006) angular-average such uniaxial values over [001],[110],[111];
only [001] is computed here, so this is an approximation to their hydrostatic a_c (stated in README).
Usage: python homojunction.py setup MAT | bulk MAT | analyse MAT
"""
import sys, json
from common import MAT, HERE
from make_superlattice import write_inputs
from bulk_refs import run

EPS = 0.05


def tag(m):
    return f"HJ_{m}_eps5_n2"


if __name__ == "__main__":
    what, m = sys.argv[1], sys.argv[2]
    a0 = MAT[m][2]
    if what == "setup":
        print(write_inputs(m, m, 2, 80, (6, 6, 1), a0, a0, a0 * (1 + EPS), tag=tag(m)))
    elif what == "bulk":
        for c in (a0, a0 * (1 + EPS)):
            r = run(m, a0, round(c, 5))
            print(m, c, r["ok"])
    elif what == "analyse":
        import math
        from bulk_refs import tag_of
        lin = json.loads((HERE / "sl" / tag(m) / "lineup.json").read_text())
        b0 = json.loads((HERE / "bulk" / tag_of(m, a0, round(a0, 5)) / "result.json").read_text())
        b1 = json.loads((HERE / "bulk" / tag_of(m, a0, round(a0 * (1 + EPS), 5)) / "result.json").read_text())
        out = dict(mat=m, eps=EPS, dV=lin["dV_centre"])
        for k in b0:
            if k.endswith("_minus_Vbar"):
                dE = lin["dV_centre"] + b1[k] - b0[k]
                out["D001_" + k.replace("_minus_Vbar", "")] = dE / math.log(1 + EPS)
        (HERE / "sl" / tag(m) / "homojunction.json").write_text(json.dumps(out, indent=1))
        print(json.dumps(out, indent=1))
