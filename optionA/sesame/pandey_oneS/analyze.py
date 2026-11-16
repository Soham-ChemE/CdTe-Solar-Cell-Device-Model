"""Score the shared-parameter grid of oneS.py against the five best Pandey cells (averages for reference).

chi2 per cell = ((Voc - Voc_t)/10 mV)^2 + ((FF - FF_t)/2 pt)^2 + ((Jsc - Jsc_t)/0.5 mA/cm2)^2, summed over the five
cells (x = 0 ... 0.25). Rs is shared by the five cells: fitted on a 0-4 ohm cm2 grid (step 0.1) or fixed at 1.3.
Jsc treatments: 'abs' (as specified), 'kscale' (one shared optical factor k multiplies every model Jsc; fitted
analytically, clipped to 0.9-1.1; the ~1 mV Voc change from k is ignored), 'noJsc' (Voc and FF only).
Fits: one shared S; S free for x = 0 only (the four Mg cells share one S). Profiles over log10 S.
"""
import csv
import functools
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import oneS as o  # noqa: E402

sc = o.sc
SIG = dict(Voc=10.0, FF=2.0, Jsc=0.5)
RS_GRID = np.round(np.arange(0.0, 4.0001, 0.1), 3)
CELLS = o.cells()
XS = [c["x"] for c in CELLS]
MODES = ("abs", "kscale", "noJsc")


def load(x, c):
    f = o.CURVES / f"{o.tag(x, c)}.csv"
    if not f.exists():
        return None
    rows = list(csv.DictReader(open(f)))
    if not rows or rows[0]["status"] != "ok" or rows[0]["V_int"] == "":
        return "failed"
    return np.array([float(r["V_int"]) for r in rows]), np.array([float(r["J_mAcm2"]) for r in rows])


@functools.lru_cache(maxsize=None)
def metrics(x, c):
    """(len(RS_GRID), 3) array of Voc, Jsc, FF per Rs; None if missing, NaN if the curve failed."""
    d = load(x, c)
    if d is None:
        return None
    if isinstance(d, str):
        return np.full((len(RS_GRID), 3), np.nan)
    V, J = d
    return np.array([[m["Voc"], m["Jsc"], m["FF"]] for m in (sc.jv_metrics(V, J, rs) for rs in RS_GRID)])


@functools.lru_cache(maxsize=None)
def grid():
    """All parameter sets with all five cells present: list of (combo, M) with M of shape (5, nRs, 3)."""
    out = []
    for c in o.all_combos():
        ms = [metrics(x, c) for x in XS]
        if all(m is not None for m in ms):
            out.append((c, np.array(ms)))
    return out


def chi2_cells(M, target, mode):
    """(5, nRs) per-cell chi2, plus the optical factor k (nRs,) used."""
    T = np.array([[cd[target]["Voc"], cd[target]["Jsc"], cd[target]["FF"]] for cd in CELLS])[:, None, :]
    cv = ((M[..., 0] - T[..., 0]) / SIG["Voc"]) ** 2 + ((M[..., 2] - T[..., 2]) / SIG["FF"]) ** 2
    k = np.ones(M.shape[1])
    if mode == "noJsc":
        return cv, k
    if mode == "kscale":
        k = np.clip((M[..., 1] * T[..., 1]).sum(0) / (M[..., 1] ** 2).sum(0), 0.9, 1.1)
    return cv + ((k[None, :] * M[..., 1] - T[..., 1]) / SIG["Jsc"]) ** 2, k


def rows_for(target, mode, rs_fixed=None):
    rows = []
    for c, M in grid():
        ch, k = chi2_cells(M, target, mode)
        for i, rs in enumerate(RS_GRID):
            if rs_fixed is not None and abs(rs - rs_fixed) > 1e-9:
                continue
            if not np.all(np.isfinite(ch[:, i])):
                continue
            rows.append(dict(lS=c[0], tau_ns=round(c[1] * 1e9, 3), NA=c[2], phib=c[3], ND=c[4], Rs=float(rs), k=float(k[i]),
                             chi2=ch[:, i], m=M[:, i, :]))
    return rows


def s_range(prof, ref, lev=4.0):
    ls = sorted(prof)
    ys = [prof[l] - ref for l in ls]
    ins = [l for l, y in zip(ls, ys) if y <= lev]
    lo, hi, flag = min(ins), max(ins), ""
    i = ls.index(lo)
    if i > 0:
        lo = ls[i - 1] + (ls[i] - ls[i - 1]) * (ys[i - 1] - lev) / (ys[i - 1] - ys[i])
    else:
        flag += " (lower end at grid edge)"
    i = ls.index(hi)
    if i < len(ls) - 1:
        hi = ls[i] + (ls[i + 1] - ls[i]) * (lev - ys[i]) / (ys[i + 1] - ys[i])
    else:
        flag += " (upper end at grid edge)"
    return lo, hi, flag


def fits(rows):
    tot = lambda r: float(r["chi2"].sum())
    b = min(rows, key=tot)
    prof = {}
    for r in rows:
        if r["lS"] not in prof or tot(r) < tot(prof[r["lS"]]):
            prof[r["lS"]] = r
    # S free for x = 0: Mg cells share S_Mg; tau, NA, phi_b, ND, Rs (and k) shared by all five
    grp = {}
    for r in rows:
        grp.setdefault((r["tau_ns"], r["NA"], r["phib"], r["ND"], r["Rs"]), {})[r["lS"]] = r
    free, prof0, profM = None, {}, {}
    for key, d in grp.items():
        mg = min(d.values(), key=lambda r: float(r["chi2"][1:].sum()))
        z = min(d.values(), key=lambda r: float(r["chi2"][0]))
        t = float(mg["chi2"][1:].sum() + z["chi2"][0])
        if free is None or t < free["chi2"]:
            free = dict(chi2=t, rest=key, mg=mg, z=z)
        for lS, r in d.items():
            v0 = float(mg["chi2"][1:].sum() + r["chi2"][0])
            vm = float(r["chi2"][1:].sum() + z["chi2"][0])
            if lS not in prof0 or v0 < prof0[lS]:
                prof0[lS] = v0
            if lS not in profM or vm < profM[lS]:
                profM[lS] = vm
    return b, prof, free, prof0, profM


def describe(r):
    return (f"log10 S {r['lS']:g}, tau {r['tau_ns']:g} ns, NA {r['NA']:.0e}, phi_b {r['phib']:.2f}, ND_MZO {r['ND']:.0e}, "
            f"Rs {r['Rs']:.1f}, k {r['k']:.3f}")


def cells_str(r):
    return "; ".join(f"x{cd['x']:.2f} {m[0]:.0f}/{m[1]:.2f}/{m[2]:.1f} (chi2 {c:.1f})" for cd, m, c in zip(CELLS, r["m"], r["chi2"]))


def write_csv(name, rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    tmp = HERE / (name + ".tmp")
    with open(tmp, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader()
        w.writerows([{k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in r.items()} for r in rows])
    tmp.replace(HERE / name)


def flat(r, **extra):
    d = dict(extra, lS=r["lS"], tau_ns=r["tau_ns"], NA=r["NA"], phib=r["phib"], ND=r["ND"], Rs=r["Rs"], k=r["k"],
             chi2=float(r["chi2"].sum()))
    for cd, m, c in zip(CELLS, r["m"], r["chi2"]):
        d.update({f"x{cd['x']:.2f}_Voc": float(m[0]), f"x{cd['x']:.2f}_Jsc": float(m[1]), f"x{cd['x']:.2f}_FF": float(m[2]),
                  f"x{cd['x']:.2f}_chi2": float(c)})
    return d


def main():
    have = sum((o.CURVES / f"{o.tag(x, c)}.csv").exists() for c in o.all_combos() for x in XS)
    fail = sum(isinstance(load(x, c), str) for c in o.all_combos() for x in XS if (o.CURVES / f"{o.tag(x, c)}.csv").exists())
    print(f"curves present {have} of {len(o.all_combos()) * 5}, failed {fail}; complete parameter sets {len(grid())}")
    out_fit, out_prof, summ, plotdata = [], [], {}, {}
    cases = [("best", m, None) for m in MODES] + [("best", "abs", 1.3), ("avg", "abs", None)]
    for target, mode, rsf in cases:
        lab = f"{target}|{mode}|{'Rs fit' if rsf is None else 'Rs 1.3'}"
        rows = rows_for(target, mode, rsf)
        b, prof, free, prof0, profM = fits(rows)
        ref = float(b["chi2"].sum())
        lo, hi, fl = s_range({k: float(v["chi2"].sum()) for k, v in prof.items()}, ref)
        l0 = s_range(prof0, free["chi2"]); lm = s_range(profM, free["chi2"])
        print(f"\n[{lab}] shared S: {describe(b)} -> chi2 {ref:.1f} (n data {15 if mode != 'noJsc' else 10})")
        print("   " + cells_str(b))
        print(f"   shared log10 S, dchi2 <= 4: {lo:.2f} .. {hi:.2f}{fl}")
        print("   profile: " + ", ".join(f"{k:g}: {float(v['chi2'].sum()) - ref:.1f} (x0 {float(v['chi2'][0]):.1f})" for k, v in sorted(prof.items())))
        print(f"   S free for x=0: log10 S_Mg {free['mg']['lS']:g}, log10 S_0 {free['z']['lS']:g}; rest {free['rest']}; chi2 {free['chi2']:.1f}"
              f" -> improvement {ref - free['chi2']:.1f}")
        print(f"     x0 cell at its own S: {free['z']['m'][0][0]:.0f}/{free['z']['m'][0][1]:.2f}/{free['z']['m'][0][2]:.1f}")
        print(f"     log10 S_0 range {l0[0]:.2f}..{l0[1]:.2f}{l0[2]}; log10 S_Mg range {lm[0]:.2f}..{lm[1]:.2f}{lm[2]}")
        k_ = lab.replace("|", "_").replace(" ", "")
        summ.update({f"{k_}_shared": describe(b), f"{k_}_shared_chi2": ref, f"{k_}_shared_lS_range": f"{lo:.2f}..{hi:.2f}{fl}",
                     f"{k_}_free_lS_Mg": free["mg"]["lS"], f"{k_}_free_lS_0": free["z"]["lS"], f"{k_}_free_chi2": free["chi2"],
                     f"{k_}_free_improvement": ref - free["chi2"], f"{k_}_free_lS0_range": f"{l0[0]:.2f}..{l0[1]:.2f}{l0[2]}",
                     f"{k_}_free_lSMg_range": f"{lm[0]:.2f}..{lm[1]:.2f}{lm[2]}"})
        out_fit.append(flat(b, case=lab, fit="shared S"))
        out_fit.append(flat(free["mg"], case=lab, fit="S free for x=0: Mg-cell S"))
        out_fit.append(flat(free["z"], case=lab, fit="S free for x=0: x=0 S"))
        for lS in sorted(prof):
            out_prof.append(dict(case=lab, lS=lS, dchi2_shared=float(prof[lS]["chi2"].sum()) - ref,
                                 chi2_x0_at_shared=float(prof[lS]["chi2"][0]), dchi2_freeS_x0=prof0[lS] - free["chi2"],
                                 dchi2_freeS_Mg=profM[lS] - free["chi2"], **{f"{n}_at_shared": v for n, v in
                                 (("tau_ns", prof[lS]["tau_ns"]), ("NA", prof[lS]["NA"]), ("phib", prof[lS]["phib"]), ("ND", prof[lS]["ND"]), ("Rs", prof[lS]["Rs"]))}))
        plotdata[lab] = (b, prof, free, prof0, profM, ref)
    write_csv("oneS_fits.csv", out_fit)
    write_csv("oneS_profiles.csv", out_prof)
    write_csv("oneS_summary.csv", [summ])
    plots(plotdata)


def plots(pd):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ink, ink2, gridc = "#0b0b0b", "#52514e", "#e4e3df"
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.8))
    a = ax[0]
    for lab, c, ls in (("best|abs|Rs fit", ink, "-"), ("best|kscale|Rs fit", "#2a78d6", "-"), ("best|noJsc|Rs fit", "#eb6834", "-"),
                       ("best|abs|Rs 1.3", ink2, ":")):
        if lab not in pd:
            continue
        b, prof, free, prof0, profM, ref = pd[lab]
        ls_ = sorted(prof)
        a.plot(ls_, [max(float(prof[l]["chi2"].sum()) - ref, 0) for l in ls_], ls, marker="o", ms=4, color=c, label=lab.replace("best|", ""))
    a.axhline(4, color="#1baf7a", lw=0.9, ls="--")
    a.axvspan(np.log10(2), np.log10(20), color="#e87ba4", alpha=0.25, lw=0, label="As-doped 21.4% cell: S ≈ 2–20 cm/s")
    a.set_yscale("symlog", linthresh=1); a.set_ylim(0, 400); a.set_xlabel("log10 S_if (cm/s), shared by all five cells"); a.set_ylabel("Δχ² (profile)")
    a.set_title("One shared S: profile over the other parameters", fontsize=9, loc="left"); a.legend(frameon=False, fontsize=7)
    a = ax[1]
    for lab, c in (("best|abs|Rs fit", ink), ("best|noJsc|Rs fit", "#eb6834")):
        if lab not in pd:
            continue
        b, prof, free, prof0, profM, ref = pd[lab]
        ls_ = sorted(prof0)
        f0 = free["chi2"]
        a.plot(ls_, [max(prof0[l] - f0, 0) for l in ls_], "-o", ms=4, color=c, label=f"S of x = 0 ({lab.split('|')[1]})")
        a.plot(ls_, [max(profM[l] - f0, 0) for l in ls_], "--s", ms=4, color=c, mfc="white", label=f"S of the Mg cells ({lab.split('|')[1]})")
    a.axhline(4, color="#1baf7a", lw=0.9, ls="--")
    a.set_yscale("symlog", linthresh=1); a.set_ylim(0, 400); a.set_xlabel("log10 S_if (cm/s)"); a.set_ylabel("Δχ² (profile)")
    a.set_title("S free for x = 0 only: which cell pins which S", fontsize=9, loc="left"); a.legend(frameon=False, fontsize=7)
    a = ax[2]
    b = pd["best|kscale|Rs fit"][0]
    xs = [cd["x"] for cd in CELLS]
    a2 = a.twinx()
    a.plot(xs, [cd["best"]["Voc"] for cd in CELLS], "o", color=ink, mfc="white", label="Voc best cell")
    a.plot(xs, [cd["avg"]["Voc"] for cd in CELLS], "x", color=ink2, label="Voc average")
    a.plot(xs, [m[0] for m in b["m"]], "-", color=ink, label="Voc model (shared S)")
    a2.plot(xs, [cd["best"]["FF"] for cd in CELLS], "s", color="#eb6834", mfc="white", label="FF best cell")
    a2.plot(xs, [cd["avg"]["FF"] for cd in CELLS], "x", color="#eb6834", label="FF average")
    a2.plot(xs, [m[2] for m in b["m"]], "-", color="#eb6834", label="FF model (shared S)")
    a.set_xlabel("Mg fraction x"); a.set_ylabel("Voc (mV)"); a2.set_ylabel("FF (%)", color="#eb6834")
    h1, l1 = a.get_legend_handles_labels(); h2, l2 = a2.get_legend_handles_labels()
    a.legend(h1 + h2, l1 + l2, frameon=False, fontsize=6.5, loc="lower right")
    a.set_title("Best shared fit (Jsc with optical factor k):\n" + describe(b), fontsize=7.5, loc="left")
    for a_ in ax:
        a_.grid(color=gridc, lw=0.6)
        for s_ in ("top", "right"):
            a_.spines[s_].set_visible(False)
    fig.tight_layout(); fig.savefig(HERE / "oneS_fits.png", dpi=140)


if __name__ == "__main__":
    main()
