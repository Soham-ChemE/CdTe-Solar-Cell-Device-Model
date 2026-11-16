"""Post-processing of the parallel-domain runs (see fluct.py)."""
import csv
import math
from functools import lru_cache

import numpy as np
from scipy.interpolate import PchipInterpolator

import fluct as f

VG = np.arange(0.0, 1.75, 0.001)
SIG_FINE = np.round(np.arange(0.0, 0.0801, 0.005), 3)
SIG_REQ = [0.0, 0.030, 0.045, 0.060, 0.080]


@lru_cache(maxsize=None)
def table(back, dEc, S, T, X=None):
    dom = f.load_domains(back, dEc, S, T, X)
    if dom is None:
        return None
    return f.domain_table(dom, VG)


def composite(tab, sigma, gh=False, nsig=4.5):
    ds, JSC, L = tab
    if sigma <= 0:
        i0 = int(np.argmin(np.abs(ds)))
        return JSC[i0], np.exp(L[i0])
    if gh:
        x, w = np.polynomial.hermite_e.hermegauss(7); w = w / w.sum()
        dl = np.clip(sigma * x, ds.min(), ds.max())
    else:
        dl = f.FINE[(f.FINE >= max(ds.min(), -nsig * sigma)) & (f.FINE <= min(ds.max(), nsig * sigma))]
        w = np.exp(-0.5 * (dl / sigma) ** 2); w /= w.sum()
    i = np.clip(np.searchsorted(ds, dl, side="right") - 1, 0, len(ds) - 2)
    t = ((dl - ds[i]) / (ds[i + 1] - ds[i]))[:, None]
    Lf = (1 - t) * L[i] + t * L[i + 1]
    jsc = np.interp(dl, ds, JSC)
    return float((w * jsc).sum()), (w[:, None] * np.exp(Lf)).sum(0)


def outputs(back, dEc, S, sigma, gh=False, nsig=4.5):
    # Voc at 1 sun and at 0.5 sun (both simulated), then Voc(X) = Voc1 + m ln X with m = (Voc1 - Voc0.5)/ln 2 (as ident)
    VX = np.full((7, len(f.LNX)), np.nan)
    for it, T in enumerate(f.TEMPS[:7]):
        tab, tab5 = table(back, dEc, S, T), table(back, dEc, S, T, 0.5)
        if tab is None or tab5 is None:
            return None
        jsc, jd = composite(tab, sigma, gh, nsig)
        jsc5, jd5 = composite(tab5, sigma, gh, nsig)
        v1, v5 = f.voc_of(VG, jd, jsc), f.voc_of(VG, jd5, jsc5)
        VX[it] = v1 + (v1 - v5) / math.log(2.0) * f.LNX
    tab = table(back, dEc, S, 300)
    if tab is None:
        return None
    jsc, jd = composite(tab, sigma, gh)
    m = f.sc.jv_metrics(VG, jsc - jd, 0.0)
    return dict(VX=VX, Voc300=m["Voc"], FF300=m["FF"], eta300=m["eta"], Jsc300=jsc)


def interp_S(outs, ls, lt):
    """Quadratic (Lagrange) interpolation of the outputs at three log S values ls onto lt."""
    a, b, c = ls
    la = (lt - b) * (lt - c) / ((a - b) * (a - c)); lb = (lt - a) * (lt - c) / ((b - a) * (b - c)); lc = (lt - a) * (lt - b) / ((c - a) * (c - b))
    o = {k: la * outs[0][k] + lb * outs[1][k] + lc * outs[2][k] for k in ("VX", "Voc300", "FF300", "eta300")}
    return o


def write_csv(name, rows):
    f.write_csv(f.HERE / name, rows)


def stageA():
    rows = []
    for back, dEc, S in f.combos("A"):
        for sg in SIG_FINE:
            out = outputs(back, dEc, S, sg)
            if out is None:
                continue
            c = f.chi2_of(out)
            rows.append(dict(stage="A", back=back, dEc=dEc, S=S, sigma_meV=1000 * sg, **c))
    return rows


def stageB(prior):
    """Profile over S (interpolated between ridge-0.5, ridge, ridge+0.5) and sigma for every dEc."""
    res = []
    for dEc in f.DEC_B:
        l0 = f.scan_center(dEc)
        ls = [l0 - 0.5, l0, l0 + 0.5]
        Ss = [10 ** l for l in ls]
        for sg in SIG_FINE:
            outs = [outputs("b0.50", dEc, S, sg) for S in Ss]
            if any(o is None for o in outs):
                continue
            for lt in np.linspace(ls[0], ls[2], 41):
                o = interp_S(outs, ls, lt)
                c = f.chi2_of(o, prior=prior, sigma=sg)
                if c:
                    res.append(dict(dEc=dEc, logS=float(lt), sigma_meV=1000 * sg, **c))
    return res


def profile(res, key="dEc", sigma_max=None):
    rr = [r for r in res if sigma_max is None or r["sigma_meV"] <= sigma_max + 1e-9]
    out = []
    for d in sorted({r[key] for r in rr}):
        b = min((r for r in rr if r[key] == d), key=lambda r: r["chi2"])
        out.append(b)
    return out


def bounded_profile(res, lmin, sigma_max):
    """Profile over dEc with log10 S >= lmin. Where the simulated S window lies wholly below lmin, the value at the
    window's upper edge is kept and flagged lower_bound (the S optimum there is below the window, so chi2 at S >= 10**lmin
    can only be higher)."""
    out = []
    for d in sorted({r["dEc"] for r in res}):
        rr = [r for r in res if r["dEc"] == d and r["sigma_meV"] <= sigma_max + 1e-9]
        ok = [r for r in rr if r["logS"] >= lmin - 1e-9]
        if ok:
            out.append(dict(min(ok, key=lambda r: r["chi2"]), lower_bound=False))
        else:
            top = max(r["logS"] for r in rr)
            out.append(dict(min((r for r in rr if abs(r["logS"] - top) < 1e-9), key=lambda r: r["chi2"]), lower_bound=True))
    return out


def interval(prof, ref, lev):
    xs = [p["dEc"] for p in prof]; ys = [p["chi2"] - ref for p in prof]
    inside = [x for x, y in zip(xs, ys) if y <= lev]
    if not inside:
        return float("nan"), float("nan")
    lo, hi = min(inside), max(inside)
    i = xs.index(lo)
    if i > 0:
        lo = xs[i - 1] + (xs[i] - xs[i - 1]) * (ys[i - 1] - lev) / (ys[i - 1] - ys[i])
    i = xs.index(hi)
    if i < len(xs) - 1:
        hi = xs[i] + (xs[i + 1] - xs[i]) * (lev - ys[i]) / (ys[i + 1] - ys[i])
    return lo, hi


def main():
    summ = {}
    # ---- A: fluctuations alone on the authors' spike
    A = stageA()
    if A:
        write_csv("fluct_A_scores.csv", A)
        bA = min(A, key=lambda r: r["chi2"])
        summ.update(A_best_back=bA["back"], A_best_S=bA["S"], A_best_sigma_meV=bA["sigma_meV"], A_best_chi2=bA["chi2"],
                    A_best_chi2_VocT=bA["chi2_VocT"], A_best_Voc300=bA["Voc300"], A_best_FF300=bA["FF300"], A_best_X=bA["X"])
        for back in ("ohm", "b0.50"):
            sub = [r for r in A if r["back"] == back]
            if sub:
                b = min(sub, key=lambda r: r["chi2"])
                summ[f"A_best_{back}_chi2"], summ[f"A_best_{back}_sigma"], summ[f"A_best_{back}_S"] = b["chi2"], b["sigma_meV"], b["S"]
    # ---- B: joint refit, with and without the Kuciauskas prior; sigma restricted to <= 60 meV (requested grid) and free to 80
    out_rows, bnd_rows = [], []
    for prior in (False, True):
        res = stageB(prior)
        if not res:
            continue
        lab = "prior" if prior else "noprior"
        if not prior:                                      # chi2 vs sigma at each dEc (min over S and X): the trade-off table
            tab_ = []
            for d in sorted({r["dEc"] for r in res}):
                for sg in sorted({r["sigma_meV"] for r in res}):
                    rr = [r for r in res if r["dEc"] == d and r["sigma_meV"] == sg]
                    if rr:
                        b = min(rr, key=lambda r: r["chi2"])
                        tab_.append(dict(dEc=d, sigma_meV=sg, logS=b["logS"], chi2=b["chi2"], chi2_VocT=b["chi2_VocT"], chi2_Voc=b["chi2_Voc"],
                                         chi2_FF=b["chi2_FF"], X=b["X"], Voc300=b["Voc300"], FF300=b["FF300"], intercept_eV=b["intercept_eV"],
                                         slope_hi_mVK=b["slope_hi_mVK"], slope_lo_mVK=b["slope_lo_mVK"]))
            write_csv("fluct_sigma_vs_dEc.csv", tab_)
        # scan saved at the three simulated S values of each dEc (every 20th point of the 41-point log-S scan)
        write_csv(f"fluct_B_scan_{lab}.csv", [r for i, r in enumerate(res) if i % 41 in (0, 20, 40)])
        for smax, sl in ((0, "s0"), (60, "s60"), (80, "s80")):
            prof = profile(res, sigma_max=smax)
            ref = min(p["chi2"] for p in prof)
            for p in prof:
                out_rows.append(dict(fit=lab, sigma_max_meV=smax, **{k: v for k, v in p.items()}, dchi2=p["chi2"] - ref))
            best = min(prof, key=lambda p: p["chi2"])
            sp = [p for p in prof if p["dEc"] > 0]; cl = [p for p in prof if p["dEc"] < 0]
            summ[f"B_{lab}_{sl}_best_dEc"] = best["dEc"]; summ[f"B_{lab}_{sl}_best_logS"] = best["logS"]
            summ[f"B_{lab}_{sl}_best_sigma"] = best["sigma_meV"]; summ[f"B_{lab}_{sl}_chi2min"] = ref
            summ[f"B_{lab}_{sl}_best_X"] = best["X"]
            if sp and cl:
                summ[f"B_{lab}_{sl}_dchi2_spike_vs_cliff"] = min(p["chi2"] for p in sp) - min(p["chi2"] for p in cl)
            for lev, nm in ((3.84, "95_1par"), (6.2, "95_2par")):
                lo, hi = interval(prof, ref, lev)
                xs_ = [p["dEc"] for p in prof]           # '<' / '>' marks an end that is still inside at the grid edge
                summ[f"B_{lab}_{sl}_dEc_{nm}"] = f"{'<=' if lo == xs_[0] else ''}{lo:.3f}..{hi:.3f}{'(edge)' if hi == xs_[-1] else ''}"
            if not prior and sl == "s60":
                with open(f.HERE / "best_B.csv", "w", newline="") as fh:
                    w = csv.writer(fh); w.writerow(["dEc", "S", "sigma_meV"]); w.writerow([best["dEc"], 10 ** best["logS"], best["sigma_meV"]])
        # physical lower bound on the front-interface S (coordinator, 2026-11-16: measured CdTe front S >= ~26 cm/s)
        for lmin in (0.0, 1.0):
            prof = bounded_profile(res, lmin, 60)
            ref = min(p["chi2"] for p in prof if not p["lower_bound"])
            for p in prof:
                bnd_rows.append(dict(fit=lab, logS_min=lmin, sigma_max_meV=60, **p, dchi2=p["chi2"] - ref))
            best = min((p for p in prof if not p["lower_bound"]), key=lambda p: p["chi2"])
            k = f"Bbound_{lab}_logSmin{lmin:g}"
            summ.update({f"{k}_best_dEc": best["dEc"], f"{k}_best_logS": best["logS"], f"{k}_best_sigma": best["sigma_meV"],
                         f"{k}_chi2min": ref, f"{k}_best_X": best["X"], f"{k}_Voc300": best["Voc300"], f"{k}_FF300": best["FF300"]})
            sp = [p for p in prof if p["dEc"] > 0]; cl = [p for p in prof if p["dEc"] < 0 and not p["lower_bound"]]
            if sp and cl:
                summ[f"{k}_dchi2_spike_vs_cliff"] = min(p["chi2"] for p in sp) - min(p["chi2"] for p in cl)
            for lev, nm in ((3.84, "95_1par"), (6.2, "95_2par")):
                # a lower-bound point counts as outside when its bound already exceeds the level; below the level it is
                # unknown (not simulated at S >= bound) and is left out of the interval
                pv = [p for p in prof if not (p["lower_bound"] and p["chi2"] - ref < lev)]
                lo, hi = interval(pv, ref, lev)
                xs_ = [p["dEc"] for p in pv]
                unk = [p["dEc"] for p in prof if p["lower_bound"] and p["chi2"] - ref < lev]
                summ[f"{k}_dEc_{nm}"] = (f"{'<=' if lo == xs_[0] else ''}{lo:.3f}..{hi:.3f}"
                                         + (f" (not simulated at this S bound: {unk})" if unk else ""))
    if out_rows:
        write_csv("fluct_profile.csv", out_rows)
    if bnd_rows:
        write_csv("fluct_profile_Sbound.csv", bnd_rows)
    # ---- checks: sigma = 0 at the ident ridge against ident; GH-7 against the fine integration
    chk = []
    for dEc in f.DEC_B:
        S = 10 ** round(f.ridge_logS(dEc), 3)
        o = outputs("b0.50", dEc, S, 0.0)
        if o is None:
            continue
        c = f.chi2_of(o)
        row = dict(dEc=dEc, logS=math.log10(S), chi2_sigma0=c["chi2"], Voc300=c["Voc300"], FF300=c["FF300"])
        for sg in (0.045, 0.060):
            a = f.chi2_of(outputs("b0.50", dEc, S, sg)); g = f.chi2_of(outputs("b0.50", dEc, S, sg, gh=True))
            row[f"chi2_fine_s{int(sg*1000)}"] = a["chi2"]; row[f"chi2_GH7_s{int(sg*1000)}"] = g["chi2"]
            row[f"Voc300_fine_s{int(sg*1000)}"] = a["Voc300"]; row[f"Voc300_GH7_s{int(sg*1000)}"] = g["Voc300"]
            t35 = f.chi2_of(outputs("b0.50", dEc, S, sg, nsig=3.5))
            row[f"chi2_trunc3.5sig_s{int(sg*1000)}"] = t35["chi2"]
            row[f"Voc216_X1_fine_s{int(sg*1000)}"] = float(outputs("b0.50", dEc, S, sg)["VX"][0, int(np.argmin(np.abs(f.LNX)))])
            row[f"Voc216_X1_trunc3.5_s{int(sg*1000)}"] = float(outputs("b0.50", dEc, S, sg, nsig=3.5)["VX"][0, int(np.argmin(np.abs(f.LNX)))])
        chk.append(row)
    if chk:
        write_csv("fluct_checks.csv", chk)
    # ---- C: phi_b trade-off at the best B point
    C = []
    for dEc_r, S_r in f.REF_POINTS:
        for back in f.BACKS_C:
            for sg in SIG_FINE:
                o = outputs(back, dEc_r, S_r, sg)
                if o is not None:
                    C.append(dict(back=back, dEc=dEc_r, S=S_r, sigma_meV=1000 * sg, **f.chi2_of(o)))
    if C:
        write_csv("fluct_C_phib.csv", C)
        for dEc_r, S_r in f.REF_POINTS:
            for back in f.BACKS_C:
                sub = [r for r in C if r["back"] == back and r["dEc"] == dEc_r]
                if sub:
                    b = min(sub, key=lambda r: r["chi2"])
                    k = f"C_{dEc_r:+.2f}_{back}"
                    summ[f"{k}_best_sigma"], summ[f"{k}_chi2min"] = b["sigma_meV"], b["chi2"]
                    summ[f"{k}_slope_lo_at_best"], summ[f"{k}_X_at_best"] = b["slope_lo_mVK"], b["X"]
                    summ[f"{k}_Voc300_at_best"] = b["Voc300"]
                    bp = min(sub, key=lambda r: r["chi2"] + ((r["sigma_meV"] / 1000 - f.PRIOR[0]) / f.PRIOR[1]) ** 2)
                    summ[f"{k}_withprior_best_sigma"] = bp["sigma_meV"]
                    summ[f"{k}_withprior_chi2min"] = bp["chi2"] + ((bp["sigma_meV"] / 1000 - f.PRIOR[0]) / f.PRIOR[1]) ** 2
    write_csv("fluct_summary.csv", [summ])
    for k, v in summ.items():
        print(k, v)
    plots(A, out_rows, C, bnd_rows)


def plots(A, prof_rows, C, bnd_rows=()):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    ink, ink2 = "#0b0b0b", "#52514e"
    T7 = np.array(f.TEMPS[:7], float)
    cols = ["#2a78d6", "#eb6834", "#1baf7a", "#6250d6", "#e87ba4"]
    fig, ax = plt.subplots(2, 3, figsize=(18, 10))
    # A: Voc(T) for each combo at the requested sigmas (best X)
    for a, (back, dEc, S) in zip([ax[0, 0], ax[0, 1], ax[1, 0], ax[1, 1]], f.combos("A")):
        a.plot(f.MEAS[:, 0], f.MEAS[:, 1], "o", ms=5, mfc="white", mec=ink, mew=1.1, label="measured (JVT)", zorder=5)
        for c, sg in zip(cols, SIG_REQ):
            o = outputs(back, dEc, S, sg)
            if o is None:
                continue
            r = f.chi2_of(o)
            j = int(np.argmin(np.abs(f.LNX - math.log(r["X"]))))
            a.plot(T7, o["VX"][:, j], "-s", ms=3.5, color=c, lw=1.5,
                   label=f"σ {1000*sg:.0f} meV: χ² {r['chi2']:.0f} (Voc(T) {r['chi2_VocT']:.0f}), X {r['X']:.2f}, 1 sun {r['Voc300']:.0f} mV / {r['FF300']:.1f}%")
        a.set_title(f"(A) spike +0.10 eV, S {S:.0e} cm/s, back {'ohmic' if back == 'ohm' else '0.50 eV barrier'}", fontsize=9, loc="left")
        a.set_xlabel("T (K)"); a.set_ylabel("Voc (V)"); a.legend(frameon=False, fontsize=6.8, loc="lower left")
    # B: profile
    b = ax[0, 2]
    for (lab, smax), c, ls in ((("noprior", 0), "#8a8984", "--"), (("noprior", 60), ink, "-"), (("prior", 60), "#eb6834", "-"),
                               (("noprior", 80), ink2, ":")):
        pr = sorted([r for r in prof_rows if r["fit"] == lab and r["sigma_max_meV"] == smax], key=lambda r: r["dEc"])
        if pr:
            b.plot([r["dEc"] for r in pr], [max(r["dchi2"], 0) for r in pr], ls, marker="o", color=c, ms=4.5, lw=1.6,
                   label=("σ fixed at 0 (no fluctuations)" if smax == 0 else
                          f"{'with σ prior 52±8 meV' if lab == 'prior' else 'σ free'} (σ ≤ {smax} meV)"))
    for lab, c in (("noprior", "#1baf7a"), ("prior", "#e87ba4")):
        pr = sorted([r for r in bnd_rows if r["fit"] == lab and r["logS_min"] == 0.0], key=lambda r: r["dEc"])
        if pr:
            b.plot([r["dEc"] for r in pr], [max(r["dchi2"], 0) for r in pr], "-", color=c, lw=1.2, zorder=1,
                   label=f"S ≥ 1 cm/s{', σ prior' if lab == 'prior' else ''} (open: lower bound)")
            b.scatter([r["dEc"] for r in pr], [max(r["dchi2"], 0) for r in pr], s=22, zorder=2,
                      facecolors=["none" if r["lower_bound"] else c for r in pr], edgecolors=c)
    b.axhline(3.84, color="#2a78d6", lw=0.9, ls="--"); b.axhline(6.2, color="#2a78d6", lw=0.9, ls=":")
    b.axvspan(-0.32, -0.22, color="#1baf7a", alpha=0.15, lw=0, label="XPS cliff range (−0.32 to −0.22 eV)")
    b.set_yscale("symlog", linthresh=1); b.set_ylim(0, 2000); b.set_xlabel("dEc (eV)"); b.set_ylabel("Δχ² (min over S, σ, X)")
    b.set_title("(B) profile Δχ² vs dEc with gap fluctuations free", fontsize=9, loc="left"); b.legend(frameon=False, fontsize=6.5, loc="lower right")
    # B: best sigma per dEc
    c_ = ax[1, 2]
    for (lab, smax), c, mk in ((("noprior", 60), ink, "o"), (("prior", 60), "#eb6834", "s")):
        pr = sorted([r for r in prof_rows if r["fit"] == lab and r["sigma_max_meV"] == smax], key=lambda r: r["dEc"])
        if pr:
            c_.plot([r["dEc"] for r in pr], [r["sigma_meV"] for r in pr], "-", marker=mk, color=c, label=("best σ with prior 52±8 meV" if lab == "prior" else "best σ, σ free"))
    c_.set_title("(B) best-fit σ for each dEc", fontsize=9, loc="left")
    c_.set_xlabel("dEc (eV)"); c_.set_ylabel("best-fit σ (meV)"); c_.legend(frameon=False, fontsize=8)
    for a_ in ax.flat:
        a_.grid(color="#e4e3df", lw=0.6)
        for s_ in ("top", "right"):
            a_.spines[s_].set_visible(False)
        a_.tick_params(colors=ink2, labelsize=8)
    fig.suptitle("Absorber band-gap fluctuations (parallel domains) against the cliff + back-barrier fit of the Kujovic cell's Voc(T)", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.96)); fig.savefig(f.HERE / "fluct_results.png", dpi=140)
    if C:
        fig, axs = plt.subplots(1, len(f.REF_POINTS), figsize=(6.0 * len(f.REF_POINTS), 4.6), sharey=True)
        for a, (dEc_r, S_r) in zip(np.atleast_1d(axs), f.REF_POINTS):
            for back, cc in (("ohm", "#8a8984"), ("b0.45", "#2a78d6"), ("b0.50", ink), ("b0.55", "#e87ba4")):
                sub = sorted([r for r in C if r["back"] == back and r["dEc"] == dEc_r], key=lambda r: r["sigma_meV"])
                if sub:
                    a.plot([r["sigma_meV"] for r in sub], [r["chi2"] for r in sub], "-o", ms=3.5, color=cc,
                           label="ohmic back" if back == "ohm" else f"φ_b {back[1:]} eV")
            a.set_yscale("log"); a.set_xlabel("σ (meV)"); a.set_ylabel("χ² (X free; S fixed)")
            a.set_title(f"back contact against σ at dEc {dEc_r:+.2f} eV, S {S_r:.3g} cm/s", fontsize=9, loc="left")
            a.legend(frameon=False, fontsize=8); a.grid(color="#e4e3df", lw=0.6)
            for s_ in ("top", "right"):
                a.spines[s_].set_visible(False)
        fig.tight_layout(); fig.savefig(f.HERE / "fluct_sigma_vs_phib.png", dpi=140)


if __name__ == "__main__":
    main()
