"""Validation against measured offsets and the calibrated ZnSe/CdTe (and ZnSe/CdSe) estimate.

For each pair the computed natural-offset candidates are (all PBE lineup + SOC):
  A : no volume correction (both materials at the SL average lattice constant)
  C : core-level reference with zero absolute deformation (Wei-Zunger 1998 / XPS-Kraut logic)
  L : C + absolute [001] deformation potential of the cation-s level from strained/unstrained homojunctions
      (approximation to Li et al. 2009, who angular-average [001],[110],[111]); only if homojunctions exist
Both A and C (and L) can carry the HSE06 bulk VBM correction.
Calibration: dEv = A + f (C - A); f fitted to the measured ranges of the validation pairs. f is the fraction of
the VBM-vs-semicore volume deformation that is treated as absolute. Writes calibration.json and results_extra.json.
"""
import json, math, glob
from common import MAT, EG_EXP, HERE, a_avg
from offsets import offsets_for, hj_D
from make_results import soc, hse_delta

EXP = {"ZnTe/CdTe": (-0.15, 0.0), "CdS/CdTe": (0.65, 0.94)}       # dEv = Ev(CdTe) - Ev(X), ranges given in the task
LI2009 = {"ZnTe/CdTe": 3.95 - 3.63, "CdS/CdTe": 3.95 - 2.78, "ZnSe/CdTe": 3.95 - 2.79, "ZnSe/CdSe": 3.26 - 2.79}


def candidates(tag):
    lin = json.loads((HERE / "sl" / tag / "lineup.json").read_text())
    X, C = lin["A"], lin["B"]
    o = offsets_for(lin)
    so = soc(C) / 3 - soc(X) / 3
    from make_results import hse_nq
    nq = min(hse_nq(X, MAT[X][2]), hse_nq(C, MAT[C][2]))
    hse_eq = hse_delta(C, MAT[C][2], nq)[0] - hse_delta(X, MAT[X][2], nq)[0]      # evaluated at each a_exp
    hse2 = hse_delta(C, MAT[C][2], 2)[0] - hse_delta(X, MAT[X][2], 2)[0]
    aav5 = round(a_avg(X, C), 5)
    hse = hse_delta(C, aav5, 2)[0] - hse_delta(X, aav5, 2)[0]                     # at a_avg: consistent with the SL
    nq = 2
    aav = a_avg(X, C)
    dlnC, dlnX = 3 * math.log(MAT[C][2] / aav), 3 * math.log(MAT[X][2] / aav)
    L = o["core"] + hj_D(C) * dlnC - hj_D(X) * dlnX
    out = dict(pair=f"{X}/{C}", tag=tag, n=lin["n"], dV=lin["dV_centre"], SO=so, HSE=hse, HSE_nq=nq, HSE_eq=hse_eq,
               HSE_eq_nq2=hse2,
               A=o["avg"] + so, C=o["core"] + so, L=L + so, D_C=hj_D(C), D_X=hj_D(X), dlnV_C=dlnC, dlnV_X=dlnX,
               dEg=EG_EXP[X] - EG_EXP[C], Li2009=LI2009.get(f"{X}/{C}"))
    for k in ("A", "C", "L"):
        out[k + "_HSE"] = out[k] + hse
    return out


def write_rows():
    """Append the calibrated (sensitivity) rows for the target pairs to results_extra.json."""
    d = json.loads((HERE / "calibration.json").read_text())
    cal, pairs = d["cal"], d["pairs"]
    rows = []
    for t, r in pairs.items():
        if r["pair"] not in ("ZnSe/CdTe", "ZnSe/CdSe"):
            continue
        for flav, lab in (("", "PBE"), ("_HSE", "PBE lineup + HSE06 bulk")):
            v = r.get("cal" + flav)
            if v is None or v != v:
                continue
            rows.append(dict(pair=r["pair"], method=f"calibrated A+f(C-A), f fitted to ZnTe/CdTe+CdS/CdTe XPS ({lab})",
                             n=r["n"], dV=f"{r['dV']:.3f}", dEv_PBE="", SO_correction=f"{r['SO']:.3f}",
                             dEv_final=f"{v:.3f}", dEc_final=f"{r['dEg'] - v:.3f}",
                             notes=(f"f={cal['f_best' + flav]:.2f} (per-pair f ranges {cal['f_ranges' + flav]}); "
                                    f"dEv range {r['cal_lo' + flav]:.2f}..{r['cal_hi' + flav]:.2f}; sensitivity check only")))
    ex = HERE / "results_extra.json"
    prev = json.loads(ex.read_text()) if ex.exists() else []
    prev = [x for x in prev if not x["method"].startswith("calibrated")] + rows
    ex.write_text(json.dumps(prev, indent=1, default=float))


if __name__ == "__main__":
    tags = ["ZnTe_CdTe_n3", "CdS_CdTe_n3", "ZnSe_CdTe_n3", "ZnSe_CdTe_n4", "ZnSe_CdSe_n3", "ZnTe_CdTe_n4"]
    res = {t: candidates(t) for t in tags if (HERE / "sl" / t / "lineup.json").exists()}
    cal = {}
    for flav in ("", "_HSE"):
        fr = {}
        for t, r in res.items():
            if r["pair"] in EXP and t.endswith("n3"):
                lo, hi = EXP[r["pair"]]
                A, C = r["A" + flav], r["C" + flav]
                f1, f2 = (lo - A) / (C - A), (hi - A) / (C - A)
                fr[r["pair"]] = (min(f1, f2), max(f1, f2), ((lo + hi) / 2 - A) / (C - A))
        cal["f_ranges" + flav] = fr
        if fr:
            mids = [v[2] for v in fr.values()]
            f_best = sum(mids) / len(mids)
            f_lo = min(v[0] for v in fr.values()); f_hi = max(v[1] for v in fr.values())
            cal["f_best" + flav] = f_best; cal["f_lo" + flav] = f_lo; cal["f_hi" + flav] = f_hi
            for t, r in res.items():
                A, C = r["A" + flav], r["C" + flav]
                r["cal" + flav] = A + f_best * (C - A)
                vals = [A + f * (C - A) for f in (f_lo, f_hi)]
                r["cal_lo" + flav], r["cal_hi" + flav] = min(vals), max(vals)
    (HERE / "calibration.json").write_text(json.dumps(dict(cal=cal, pairs=res), indent=1))
    print(json.dumps(cal, indent=1))
    for t, r in res.items():
        print(f"{t:14s} A={r['A']:+.3f} C={r['C']:+.3f} L={r['L']:+.3f} | HSE: A={r['A_HSE']:+.3f} C={r['C_HSE']:+.3f}"
              f" | cal={r.get('cal', float('nan')):+.3f} [{r.get('cal_lo', float('nan')):+.3f},{r.get('cal_hi', float('nan')):+.3f}]"
              f" cal_HSE={r.get('cal_HSE', float('nan')):+.3f}  Li2009={r['Li2009']}")
    write_rows()
