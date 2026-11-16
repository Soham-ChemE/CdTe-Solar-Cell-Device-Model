"""Identifiability map of the front offset dEc and interface S for the rebuilt Kujovic cell (calib2 model).

Model: interface states (ZnO CB <-> absorber VB), dead FTO/ZnO (tau 1e-12 s), stored front Fi_m 4.10 eV,
bulk tau 100 ns, dEg/dT -4e-4 eV/K, f_cb 0.5, back metal fixed at VBM(300 K) - phi_b.
Data and sigmas: 13 JVT Voc(T) points (4 mV, free light-intensity factor X), 1-sun J-V Voc 875.5 (8 mV) and
FF 80.48 % (1.5 points). chi2 = sum of squared normalised residuals.

Stages (resumable; every (phi_b, dEc, S) record is written atomically to curves/ when it finishes):
  python ident.py grid      phi_b 0.50: 10 dEc x 9 log10 S; 300 K J-V first, Voc(T) at 7 T unless Voc(1 sun) < 700 mV
  python ident.py extend    log S 4.5 ... 6.0 where the best S sits at the grid edge (brackets the minimum; not requested)
  python ident.py ridge     best log S per dEc (interpolated), then simulated at phi_b 0.50, 0.45, 0.55
  python ident.py analyze   -> ident_map.csv, ident_profile.csv, ident_summary.csv, ident_map.png
"""
import csv
import itertools
import math
import os
import sys
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np
from scipy.interpolate import PchipInterpolator

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "calib2")); sys.path.insert(0, str(HERE.parent / "calib"))
import calibrate2 as c2  # noqa: E402
from calibrate import sc, MEAS, RAMPS, write_csv  # noqa: E402

CURVES = HERE / "curves"
TAU = 100e-9
TEMPS7 = [216, 248, 282, 298, 316, 336, 355]
DEC = [-0.34, -0.30, -0.26, -0.22, -0.18, -0.14, -0.10, -0.02, 0.06, 0.10]
LOGS = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
LOGS_EXT = [4.5, 5.0, 5.5, 6.0]   # added only where the best S sits at the grid edge (so every minimum is bracketed)
SIG_VT, SIG_VOC, SIG_FF = 0.004, 8.0, 1.5
VOC_1SUN, FF_1SUN = 875.5, 80.48
LNX = (math.log(0.05), math.log(5.0))


def tag(phi, dEc, logS):
    return f"phi{phi:.2f}_dEc{dEc:+.3f}_lS{logS:.3f}".replace("+", "p").replace("-", "m")


def jv300(phi, dEc, S):
    for ramp in RAMPS:
        cell = c2.make_cell(TAU, phi, dEc, S, 300)
        jv = sc.run_jv(cell, dV=0.01, tol=1e-8, time_limit=900, ramp=ramp, V_max=1.6)
        if jv.ok:
            break
    return sc.jv_metrics(jv.V, jv.J, 0.0) if jv.ok else None, jv.note


def run_record(phi, dEc, logS, skip_below=700.0):
    out = CURVES / f"{tag(phi, dEc, logS)}.csv"
    if out.exists():
        return
    S = 10 ** logS
    m, note = jv300(phi, dEc, S)
    base = dict(phi_b=phi, dEc=dEc, logS=logS, S=S, jv_status=note,
                Voc300=m["Voc"] if m else float("nan"), FF300=m["FF"] if m else float("nan"),
                Jsc300=m["Jsc"] if m else float("nan"), eta300=m["eta"] if m else float("nan"))
    rows = []
    if m is None or m["Voc"] < skip_below:
        rows.append(dict(**base, T_K="", status="skipped (1-sun Voc < 700 mV)" if m else "J-V failed"))
    else:
        for T in TEMPS7:
            r = c2.run_point(TAU, phi, dEc, S, T)
            rows.append(dict(**base, T_K=T, status=r["status"], Voc1=r["Voc1"], Voc2=r["Voc2"], m_V=r["m_V"]))
    write_csv(out, rows)
    print(f"{tag(phi, dEc, logS)}: Voc300 {base['Voc300']:.1f} FF {base['FF300']:.2f} -> {rows[-1]['status']}", flush=True)


def grid():
    CURVES.mkdir(exist_ok=True)
    # 300 K J-V for the whole map first would double the cell builds; do record by record instead
    for dEc, logS in itertools.product(DEC, LOGS):
        run_record(0.50, dEc, logS)


# ------------------------------------------------------------------ chi-square
def load(phi, dEc, logS):
    f = CURVES / f"{tag(phi, dEc, logS)}.csv"
    if not f.exists():
        return None
    d = list(csv.DictReader(open(f)))
    r0 = d[0]
    out = dict(phi_b=phi, dEc=dEc, logS=logS, Voc300=float(r0["Voc300"]), FF300=float(r0["FF300"]),
               Jsc300=float(r0["Jsc300"]), eta300=float(r0["eta300"]), skipped=r0["T_K"] == "")
    if not out["skipped"]:
        out["T"] = np.array([float(r["T_K"]) for r in d])
        out["V1"] = np.array([float(r["Voc1"]) for r in d]); out["m"] = np.array([float(r["m_V"]) for r in d])
        out["ok"] = all(r["status"] == "ok" for r in d) and np.isfinite(out["V1"]).all() and np.isfinite(out["m"]).all()
    return out


def chi2_parts(T, V1, m, Voc300, FF300):
    """chi2 with X profiled analytically (Voc_X = V1 + m ln X is linear in ln X), ln X clipped to [0.05, 5] suns."""
    v = PchipInterpolator(T, V1, extrapolate=True)(MEAS[:, 0])
    mm = np.interp(MEAS[:, 0], T, m)
    r0 = MEAS[:, 1] - v
    lnx = float(np.clip((mm * r0).sum() / (mm * mm).sum(), *LNX))
    c_vt = float((((r0 - mm * lnx) / SIG_VT) ** 2).sum())
    c_voc = ((Voc300 - VOC_1SUN) / SIG_VOC) ** 2
    c_ff = ((FF300 - FF_1SUN) / SIG_FF) ** 2
    return dict(chi2=c_vt + c_voc + c_ff, chi2_VocT=c_vt, chi2_Voc1sun=c_voc, chi2_FF1sun=c_ff, X=math.exp(lnx))


def fine_scan(phi, dEc, n=241):
    """Interpolate the per-(dEc) model quantities in log S (PCHIP over simulated points) and scan chi2 finely."""
    recs = [r for r in (load(phi, dEc, s) for s in LOGS + LOGS_EXT) if r and not r["skipped"] and r["ok"]]
    if len(recs) < 2:
        return None
    ls = np.array([r["logS"] for r in recs])
    T = recs[0]["T"]
    V1 = np.array([r["V1"] for r in recs]); M = np.array([r["m"] for r in recs])
    voc = np.array([r["Voc300"] for r in recs]); ff = np.array([r["FF300"] for r in recs])
    grid_ = np.linspace(ls.min(), ls.max(), n)
    iV = PchipInterpolator(ls, V1, axis=0); iM = PchipInterpolator(ls, M, axis=0)
    iVoc = PchipInterpolator(ls, voc); iFF = PchipInterpolator(ls, ff)
    res = [dict(logS=float(g), Voc300=float(iVoc(g)), FF300=float(iFF(g)), **chi2_parts(T, iV(g), iM(g), float(iVoc(g)), float(iFF(g))))
           for g in grid_]
    return res


def extend():
    """Bracket edge minima: add log S 4.5, 5.0, ... for a dEc while its best S is at the largest simulated S."""
    for dEc in DEC:
        for ls in LOGS_EXT:
            sc_ = fine_scan(0.50, dEc)
            if not sc_:
                break
            best = min(sc_, key=lambda r: r["chi2"])
            if best["logS"] < max(r["logS"] for r in sc_) - 0.26:
                break
            run_record(0.50, dEc, ls)
            if load(0.50, dEc, ls)["skipped"]:
                break


def ridge():
    pts_file = HERE / "ridge_points.csv"
    if pts_file.exists():
        pts = {float(r["dEc"]): float(r["logS"]) for r in csv.DictReader(open(pts_file))}
    else:
        pts = {}
        for dEc in DEC:
            sc_ = fine_scan(0.50, dEc)
            if sc_:
                pts[dEc] = round(min(sc_, key=lambda r: r["chi2"])["logS"], 3)
        write_csv(pts_file, [dict(dEc=k, logS=v) for k, v in pts.items()])
    for phi in (0.50, 0.45, 0.55):
        for dEc, ls in pts.items():
            run_record(phi, dEc, ls, skip_below=0.0)


def ridge_logS():
    f = HERE / "ridge_points.csv"
    return {float(r["dEc"]): float(r["logS"]) for r in csv.DictReader(open(f))} if f.exists() else {}


def interp_check():
    """Error of the 7-temperature PCHIP against the 11-temperature curve, at the 13 measured T (calib2 curve)."""
    f = HERE.parent / "calib2/curves/tau100ns_phi0.50_dEcm0.22_S3ep01_vocT.csv"
    d = list(csv.DictReader(open(f)))
    T = np.array([float(r["T_K"]) for r in d]); V = np.array([float(r["Voc1"]) for r in d])
    full = PchipInterpolator(T, V)(MEAS[:, 0])
    m7 = np.isin(T, TEMPS7)
    sub = PchipInterpolator(T[m7], V[m7])(MEAS[:, 0])
    return 1000 * float(np.max(np.abs(full - sub))), 1000 * float(np.sqrt(np.mean((full - sub) ** 2)))


def analyze():
    rows, prof = [], []
    for dEc, ls in itertools.product(DEC, LOGS + LOGS_EXT):
        r = load(0.50, dEc, ls)
        if r is None:
            continue
        row = dict(dEc=dEc, logS=ls, Voc300=r["Voc300"], FF300=r["FF300"], eta300=r["eta300"], skipped=r["skipped"])
        if not r["skipped"]:
            row.update(chi2_parts(r["T"], r["V1"], r["m"], r["Voc300"], r["FF300"]))
        rows.append(row)
    fine = {dEc: fine_scan(0.50, dEc) for dEc in DEC}
    allmin = min(min(x["chi2"] for x in fs) for fs in fine.values() if fs)
    rl = ridge_logS()
    for dEc in DEC:
        fs = fine[dEc]
        if not fs:
            continue
        b = min(fs, key=lambda x: x["chi2"])
        p = dict(dEc=dEc, logS_best_interp=b["logS"], chi2_interp=b["chi2"], X_interp=b["X"], Voc300_interp=b["Voc300"], FF300_interp=b["FF300"])
        if dEc in rl:
            for phi in (0.50, 0.45, 0.55):
                r = load(phi, dEc, rl[dEc])
                if r and not r["skipped"] and r["ok"]:
                    c = chi2_parts(r["T"], r["V1"], r["m"], r["Voc300"], r["FF300"])
                    p.update({f"chi2_sim_phi{phi:.2f}": c["chi2"], f"chi2VocT_sim_phi{phi:.2f}": c["chi2_VocT"],
                              f"chi2Voc_sim_phi{phi:.2f}": c["chi2_Voc1sun"], f"chi2FF_sim_phi{phi:.2f}": c["chi2_FF1sun"],
                              f"X_sim_phi{phi:.2f}": c["X"], f"Voc300_sim_phi{phi:.2f}": r["Voc300"], f"FF300_sim_phi{phi:.2f}": r["FF300"]})
        prof.append(p)
    ref = min(min(p.get("chi2_sim_phi0.50", np.inf), p["chi2_interp"]) for p in prof)
    for p in prof:
        p["dchi2_interp"] = p["chi2_interp"] - ref
        if "chi2_sim_phi0.50" in p:
            p["dchi2_sim_phi0.50"] = p["chi2_sim_phi0.50"] - ref
    write_csv(HERE / "ident_map.csv", rows)
    write_csv(HERE / "ident_profile.csv", prof)
    fmap = [dict(dEc=dEc, **x) for dEc, fs in fine.items() if fs for x in fs]
    write_csv(HERE / "ident_fine_scan.csv", fmap)
    best_sp = min((p for p in prof if p["dEc"] >= 0.06), key=lambda p: p.get("chi2_sim_phi0.50", p["chi2_interp"]))
    best_cl = min((p for p in prof if p["dEc"] <= -0.10), key=lambda p: p.get("chi2_sim_phi0.50", p["chi2_interp"]))
    xps = [p for p in prof if -0.32 <= p["dEc"] <= -0.22]
    summ = dict(chi2_min=ref, n_data=15, n_free=3, dof=12,
                best_cliff_dEc=best_cl["dEc"], best_cliff_chi2=best_cl.get("chi2_sim_phi0.50", best_cl["chi2_interp"]),
                best_spike_dEc=best_sp["dEc"], best_spike_chi2=best_sp.get("chi2_sim_phi0.50", best_sp["chi2_interp"]),
                dchi2_spike_vs_cliff=best_sp.get("chi2_sim_phi0.50", best_sp["chi2_interp"]) - best_cl.get("chi2_sim_phi0.50", best_cl["chi2_interp"]),
                xps_range_min_dchi2=min(min(p.get("dchi2_sim_phi0.50", np.inf), p["dchi2_interp"]) for p in xps),
                xps_range_max_dchi2=max(min(p.get("dchi2_sim_phi0.50", np.inf), p["dchi2_interp"]) for p in xps))
    summ["interp7_vs_11T_max_mV"], summ["interp7_vs_11T_rms_mV"] = interp_check()
    # dEc interval: parabola through the simulated profile at the best dEc and its two neighbours
    sim = sorted([(p["dEc"], p["chi2_sim_phi0.50"]) for p in prof if "chi2_sim_phi0.50" in p])
    k = int(np.argmin([c for _, c in sim])); k = min(max(k, 1), len(sim) - 2)
    xs, ys = np.array([sim[k - 1][0], sim[k][0], sim[k + 1][0]]), np.array([sim[k - 1][1], sim[k][1], sim[k + 1][1]])
    a2, a1, a0 = np.polyfit(xs, ys, 2)
    x0 = -a1 / (2 * a2); y0 = a0 - a1 ** 2 / (4 * a2)
    for lev, nm in ((2.3, "68"), (6.2, "95")):
        h = math.sqrt(max(lev - (y0 - ref), 0) / a2) if a2 > 0 else float("nan")
        summ[f"dEc_{nm}_lo"], summ[f"dEc_{nm}_hi"] = x0 - h, x0 + h
    summ["dEc_best_parabola"], summ["chi2_best_parabola"] = x0, y0
    # S interval at the best simulated dEc (fine scan in log S)
    bd = sim[int(np.argmin([c for _, c in sim]))][0]
    fs = fine[bd]
    for lev, nm in ((2.3, "68"), (6.2, "95")):
        inside = [x["logS"] for x in fs if x["chi2"] - ref <= lev]
        summ[f"logS_{nm}_at_best_dEc"] = f"{min(inside):.2f}..{max(inside):.2f}" if inside else "none"
    rl_ = ridge_logS()
    summ["ridge_logS_at_dEc_lo95"] = float(np.interp(summ["dEc_95_lo"], sorted(rl_), [rl_[k_] for k_ in sorted(rl_)]))
    summ["ridge_logS_at_dEc_hi95"] = float(np.interp(summ["dEc_95_hi"], sorted(rl_), [rl_[k_] for k_ in sorted(rl_)]))
    # local quadratic approximation of the 2-D valley (the dEc grid step, 0.04 eV, is wider than the 95% region):
    # Dchi2 = A (logS - ridge(dEc))^2 + P (dEc - dEc0)^2, A from the log-S scan at the best dEc, P from the profile
    near = [x for x in fs if x["chi2"] - ref < 30]
    A = float(np.polyfit([x["logS"] for x in near], [x["chi2"] for x in near], 2)[0])
    ks = sorted(rl_)
    kslope = float(np.polyfit(ks[:3], [rl_[k_] for k_ in ks[:3]], 1)[0])
    summ.update(quad_A_per_dec2=A, quad_P_per_eV2=float(a2), ridge_dlogS_ddEc=kslope)
    write_csv(HERE / "ident_summary.csv", [summ])
    plot.quad = dict(A=A, P=float(a2), d0=float(x0), l0=float(np.interp(x0, ks, [rl_[k_] for k_ in ks])), k=kslope, y0=float(y0 - ref))
    for p in prof:
        print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in p.items()})
    print(summ)
    plot(fmap, prof, ref, rl)


def plot(fmap, prof, ref, rl):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm
    ink, ink2 = "#0b0b0b", "#52514e"
    dE = sorted({r["dEc"] for r in fmap})
    LL = np.linspace(-0.2, 6.2, 321)
    Z = np.full((len(LL), len(dE)), np.nan)
    for j, d in enumerate(dE):
        rr = sorted([r for r in fmap if r["dEc"] == d], key=lambda r: r["logS"])
        ls = np.array([r["logS"] for r in rr]); ch = np.array([r["chi2"] for r in rr])
        m = (LL >= ls.min()) & (LL <= ls.max())
        Z[m, j] = np.interp(LL[m], ls, ch)
    D = np.clip(Z - ref, 0.05, None)
    fig, ax = plt.subplots(1, 3, figsize=(19, 5.6), gridspec_kw={"width_ratios": [1.15, 1, 1]})
    for a, (xl, yl, ttl) in zip(ax[:2], (((-0.36, 0.12), (-0.2, 6.2), "full map"), ((-0.36, -0.16), (-0.2, 3.2), "zoom on the cliff side"))):
        pc = a.pcolormesh(dE, LL, D, shading="gouraud", cmap="Blues_r", norm=LogNorm(vmin=0.3, vmax=3000))
        cs = a.contour(dE, LL, D, levels=[2.3, 6.2, 25, 100, 400], colors=["#eb6834", "#eb6834", ink2, ink2, ink2],
                       linewidths=[2.2, 1.4, 0.8, 0.8, 0.8], linestyles=["-", "--", ":", ":", ":"])
        a.clabel(cs, fmt={2.3: "2.3", 6.2: "6.2", 25: "25", 100: "100", 400: "400"}, fontsize=7)
        a.axvspan(-0.32, -0.22, ymin=0, ymax=0.04, color="#1baf7a", alpha=0.9, lw=0)
        a.text(-0.27, yl[0] + 0.07 * (yl[1] - yl[0]), "XPS range", ha="center", fontsize=7.5, color=ink)
        a.plot([p["dEc"] for p in prof], [p["logS_best_interp"] for p in prof], "o-", color="#e87ba4", ms=4, lw=1.2, label="best S for each dEc (ridge)")
        bp = min(prof, key=lambda p: p.get("chi2_sim_phi0.50", np.inf))
        a.plot([bp["dEc"]], [rl.get(bp["dEc"], bp["logS_best_interp"])], "*", ms=14, color="#eb6834", mec=ink, label="best fit")
        q = getattr(plot, "quad", None)
        if q and xl[1] < 0:      # zoom panel: local quadratic 68/95% region
            dd, ll = np.meshgrid(np.linspace(-0.36, -0.24, 400), np.linspace(-0.2, 1.8, 400))
            Q = q["A"] * (ll - (q["l0"] + q["k"] * (dd - q["d0"]))) ** 2 + q["P"] * (dd - q["d0"]) ** 2 + q["y0"]
            cq = a.contour(dd, ll, Q, levels=[2.3, 6.2], colors=["#eb6834", "#eb6834"], linewidths=[2.2, 1.4], linestyles=["-", "--"])
            a.plot([], [], color="#eb6834", lw=2.2, label="Δχ² 2.3 / 6.2 (local quadratic)")
            a.legend(frameon=False, fontsize=8, loc="upper left")
        a.set_xlim(*xl); a.set_ylim(*yl)
        a.set_xlabel("front conduction-band offset dEc (eV; negative = cliff)"); a.set_ylabel("log10 interface S (cm/s)")
        a.set_title(f"Δχ² ({ttl}); φ_b 0.50, X profiled; χ²_min {ref:.1f}, 15 data, 3 free", fontsize=9, loc="left")
    fig.colorbar(pc, ax=ax[1], label="Δχ²")
    ax[0].legend(frameon=False, fontsize=8, loc="upper left")
    b = ax[2]
    b.plot([p["dEc"] for p in prof], [max(p["chi2_interp"] - ref, 0) for p in prof], "--", color="#8a8984", lw=1.2, label="φ_b 0.50, interpolated in S")
    for phi, c in {0.45: "#2a78d6", 0.50: ink, 0.55: "#eb6834"}.items():
        k = f"chi2_sim_phi{phi:.2f}"
        pts = [(p["dEc"], max(p[k] - ref, 0)) for p in prof if k in p]
        if pts:
            b.plot(*zip(*pts), "o-", color=c, ms=4.5, lw=1.6, label=f"φ_b {phi:.2f}, simulated on the φ_b 0.50 ridge")
    b.axhline(2.3, color="#eb6834", lw=1, ls="-"); b.axhline(6.2, color="#eb6834", lw=1, ls="--")
    b.axvspan(-0.32, -0.22, color="#1baf7a", alpha=0.15, lw=0)
    b.set_yscale("symlog", linthresh=1); b.set_ylim(0, 3000)
    b.set_xlabel("dEc (eV)"); b.set_ylabel("Δχ² (minimised over S and X)")
    b.set_title("profile Δχ² vs dEc (shaded: XPS -0.32 to -0.22 eV)", fontsize=9, loc="left"); b.legend(frameon=False, fontsize=8, loc="lower right")
    for a_ in ax:
        for s_ in ("top", "right"):
            a_.spines[s_].set_visible(False)
        a_.tick_params(colors=ink2, labelsize=8)
    fig.tight_layout(); fig.savefig(HERE / "ident_map.png", dpi=150)


if __name__ == "__main__":
    {"grid": grid, "extend": extend, "ridge": ridge, "analyze": analyze}[sys.argv[1]]()
