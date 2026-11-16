"""Pseudomorphic (coherently strained) limits for ZnSe/CdTe.

P1: ZnSe strained in-plane to CdTe (a_par = 6.481 A), CdTe cubic.   P2: CdTe strained in-plane to ZnSe, ZnSe cubic.
Out-of-plane lattice constant of the strained layer from linear elasticity, eps_perp = -2 (C12/C11) eps_par,
with room-temperature experimental elastic constants (GPa): CdTe C11 53.5, C12 36.7 (McSkimin & Thomas 1962);
ZnSe C11 85.9, C12 50.6 (Lee 1970). At 12-14 % misfit this is an extrapolation (stated in README).

Two routes are computed:
  (i)  explicit pseudomorphic superlattice lineup + bulk references at exactly the same strained geometry
       (no deformation-potential assumption; SOC of the strained layer from an FR calculation of the same cell);
  (ii) natural offset + VBM shift of the strained bulk relative to the cation-s semicore level (core-level route).
Usage: python pseudomorphic.py setup|bulk
"""
import sys, json
from common import MAT, HERE
from make_superlattice import write_inputs
from bulk_refs import run

ELAST = {"CdTe": (53.5, 36.7), "ZnSe": (85.9, 50.6), "ZnTe": (71.7, 40.7), "CdS": (77.0, 54.0)}


def c_perp(mat, apar):
    a0 = MAT[mat][2]; C11, C12 = ELAST[mat]
    e = (apar - a0) / a0
    return a0 * (1 - 2 * C12 / C11 * e)


CASES = {
    "P1_ZnSe_on_CdTe": dict(A="ZnSe", B="CdTe", apar=MAT["CdTe"][2], cA=c_perp("ZnSe", MAT["CdTe"][2]), cB=MAT["CdTe"][2],
                            strained="ZnSe"),
    "P2_CdTe_on_ZnSe": dict(A="ZnSe", B="CdTe", apar=MAT["ZnSe"][2], cA=MAT["ZnSe"][2], cB=c_perp("CdTe", MAT["ZnSe"][2]),
                            strained="CdTe"),
}

if __name__ == "__main__":
    what = sys.argv[1]
    for name, c in CASES.items():
        cs = c["cA"] if c["strained"] == c["A"] else c["cB"]
        if what == "setup":
            # k 4x4x1: lineup k-error ~0.01 eV (ZnTe/CdTe test), negligible next to the strain effects here
            d = write_inputs(c["A"], c["B"], 3, 80, (4, 4, 1), c["apar"], c["cA"], c["cB"], tag=f"{name}_n3",
                             smearing=True)
            print(name, d, f"apar={c['apar']:.4f} c_strained={cs:.4f}")
        if what == "bulk":
            for soc in (False, True):
                r = run(c["strained"], c["apar"], cs, soc=soc)
                print(name, "soc" if soc else "sr", r.get("ok"), r.get("top_val_gamma") or r.get("top6"))
