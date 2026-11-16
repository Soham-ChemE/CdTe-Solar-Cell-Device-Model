"""Collect every computed offset into results.csv (and results_detail.json).

Sign convention: pair 'X/CdY':  dEv = Ev(CdY) - Ev(X);  dEc = Ec(X) - Ec(CdY) = (Eg_X - Eg_CdY)_exp - dEv.
dV column = Vbar(CdY) - Vbar(X) in the superlattice (V_bare + V_H, eV; includes pseudopotential G=0 terms,
so it is only meaningful together with the bulk references computed with the same pseudopotentials).
"""
import json, csv, glob, math
from pathlib import Path
from common import MAT, EG_EXP, HERE, a_avg
from bulk_refs import tag_of
from offsets import offsets_for, bulk

NAN = float("nan")


def soc(m):
    f = HERE / "soc" / tag_of(m, MAT[m][2], soc=True) / "result.json"
    return json.loads(f.read_text())["Delta_SO"] if f.exists() else NAN


def hse_nq(m, a):
    """Best available HSE q-mesh for material m at a (3 if computed, else 2)."""
    return 3 if (HERE / "hse" / tag_of(m, round(a, 5), k=6, hse=True, nq=3) / "result.json").exists() else 2


def hse_delta(m, a, nq=None):
    """VBM shift HSE06 - PBE relative to Vbar (and to the cation-s level) for material m at lattice constant a."""
    nq = nq or hse_nq(m, a)
    f = HERE / "hse" / tag_of(m, round(a, 5), k=6, hse=True, nq=nq) / "result.json"
    if not f.exists():
        return NAN, NAN
    h = json.loads(f.read_text())
    if not h.get("ok"):
        return NAN, NAN
    p = bulk(m, a)
    cs = "Cd4s" if MAT[m][0] == "Cd" else "Zn3s"
    return (h["VBM_minus_Vbar"] - p["VBM_minus_Vbar"],
            (h["E_VBM_gamma"] - h[cs]) - (p["E_VBM_gamma"] - p[cs]))


def fmt(x, nd=3):
    return "" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{nd}f}"


def main():
    rows, detail = [], {}
    for lf in sorted(glob.glob(str(HERE / "sl" / "*" / "lineup.json"))):
        lin = json.loads(open(lf).read())
        tag = lin["tag"]
        if tag.startswith(("P1", "P2", "HJ_")):   # pseudomorphic / homojunction cases are handled separately
            continue
        X, C = lin["A"], lin["B"]
        pair = f"{X}/{C}"
        o = offsets_for(lin)
        so = soc(C) / 3 - soc(X) / 3
        dEg = EG_EXP[X] - EG_EXP[C]
        kstr = "x".join(map(str, lin["k"]))
        flat = max(abs(lin["slope_A_eV_per_A"]), abs(lin["slope_B_eV_per_A"])) * 3 * MAT[C][2]
        note_conv = f"k {kstr}; plateau ripple {1000*max(lin['ripple_A'], lin['ripple_B']):.1f} meV"
        nq = min(hse_nq(X, MAT[X][2]), hse_nq(C, MAT[C][2]))
        hx, hc = hse_delta(X, MAT[X][2], nq), hse_delta(C, MAT[C][2], nq)
        hse_eq = hc[0] - hx[0]                                   # HSE-PBE shift of E_VBM - Vbar at each a_exp
        aav5 = round(a_avg(X, C), 5)
        hse_corr = hse_delta(C, aav5, 2)[0] - hse_delta(X, aav5, 2)[0]   # at a_avg, consistent with the SL geometry
        detail[tag] = dict(lineup=lin, offsets=o, so=so, hse_V=(hx[0], hc[0]), hse_core=(hx[1], hc[1]))
        for meth, val, note in [
            ("A: both at a_avg (strained, no volume correction)", o["avg"], "rigorous for the unrelaxed SL geometry"),
            ("C: core-level natural (cation-s ref, zero core deformation)", o["core"],
             f"spread over 9 semicore-ref choices {o['core_spread'][0]:.3f}..{o['core_spread'][1]:.3f}"),
            ("L: C + absolute [001] core deformation potential (homojunction)", o["L"],
             "approximates Li et al. 2009 (they angular-average [001],[110],[111]); D001 linear in strain"),
            ("V: Vbar natural (zero Vbar deformation) - INVALID", o["Vref"],
             "fails: Vbar contains pseudopotential G=0 term ~1/Omega; shown only to document the failure"),
        ]:
            rows.append(dict(pair=pair, method=meth, n=lin["n"], dV=fmt(lin["dV_centre"]), dEv_PBE=fmt(val),
                             SO_correction=fmt(so), dEv_final=fmt(val + so), dEc_final=fmt(dEg - (val + so)),
                             notes=f"{note}; {note_conv}"))
            if math.isnan(val):
                rows.pop(); continue
            if not math.isnan(hse_corr) and not meth.startswith("V"):
                rows.append(dict(pair=pair, method=meth.split(":")[0] + "+HSE06 bulk VBM correction", n=lin["n"],
                                 dV=fmt(lin["dV_centre"]), dEv_PBE=fmt(val), SO_correction=fmt(so),
                                 dEv_final=fmt(val + so + hse_corr), dEc_final=fmt(dEg - (val + so + hse_corr)),
                                 notes=(f"HSE06-PBE shift of E_VBM-Vbar at a_avg (nq 2, k 6) applied: {hse_corr:+.3f} eV; "
                                        f"same evaluated at a_exp (nq {nq}) would be {hse_eq:+.3f} eV; {note_conv}")))

    extra = HERE / "results_extra.json"     # pseudomorphic and calibrated rows, written by other scripts
    if extra.exists():
        rows += json.loads(extra.read_text())
    # best-estimate row: mean of method L (largest n available) with and without the HSE06 a_avg correction
    for pair in ("ZnSe/CdTe", "ZnSe/CdSe", "ZnTe/CdTe", "CdS/CdTe"):
        cand = [r for r in rows if r["pair"] == pair and r["method"].startswith("L") and "k 4x4x1" not in r["notes"]]
        if not cand:
            continue
        nmax = max(int(r["n"]) for r in cand)
        l0 = [r for r in cand if int(r["n"]) == nmax and r["method"].startswith("L:")]
        lh = [r for r in cand if int(r["n"]) == nmax and r["method"].startswith("L+HSE")]
        if l0 and lh:
            ev = 0.5 * (float(l0[0]["dEv_final"]) + float(lh[0]["dEv_final"]))
            ec = 0.5 * (float(l0[0]["dEc_final"]) + float(lh[0]["dEc_final"]))
            rows.append(dict(pair=pair, method="BEST ESTIMATE (mean of L and L+HSE06)", n=nmax, dV=l0[0]["dV"],
                             dEv_PBE="", SO_correction=l0[0]["SO_correction"], dEv_final=f"{ev:.2f}", dEc_final=f"{ec:.2f}",
                             notes=("1-sigma ~0.3 eV (validation residuals scaled to misfit, functional, [001]-only DP, "
                                    "interface type, n); see README section 5" if pair.startswith("ZnSe")
                                    else "validation pair; compare with measured dEv in README section 4")))
    with open(HERE / "results.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, ["pair", "method", "n", "dV", "dEv_PBE", "SO_correction", "dEv_final", "dEc_final", "notes"])
        w.writeheader(); [w.writerow(r) for r in rows]
    (HERE / "results_detail.json").write_text(json.dumps(detail, indent=1, default=str))
    for r in rows:
        print(f"{r['pair']:10s} n={r['n']} {r['method'][:58]:58s} dV={r['dV']:>7s} dEv={r['dEv_final']:>7s} dEc={r['dEc_final']:>7s}")


if __name__ == "__main__":
    main()
