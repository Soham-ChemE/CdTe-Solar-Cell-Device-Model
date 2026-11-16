"""Result figures F1-F7 (docs/figures/).

Reads only CSV files already in the repository and writes PNGs to docs/figures/ (or to the folder given as the
first argument). No SCAPS or Sesame run is needed. Run from anywhere:

    python scripts/make_figures.py [out_dir]

F1  Voc(T) of the 21.4% cell: measured, best cliff, best spike, published spike
F2  identifiability map and profile likelihood (dEc, S)
F3  fluctuation gate: profiles, spike exclusion, back contact vs sigma
F4  one-S fit of the Cu-doped MgZnO series
F5  design waterfall (isolated lever gains, closed by the simulated conservative design)
F6  SCAPS vs Sesame cross-validation (dark J-V, ratio, light-case table)
F7  (SI) ZnSe front-buffer collapse map
"""
import csv
import math
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LogNorm  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from scipy.interpolate import PchipInterpolator  # noqa: E402

import sys  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
OUT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else REPO / "docs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

KJ = REPO / "optionA/sesame/kujovic"
IDENT = KJ / "ident"
FLUCT = KJ / "fluct"
ZNSE = KJ / "znse"
PANDEY = REPO / "optionA/sesame/pandey_oneS"
DESIGN = REPO / "optionA/sesame/design"
DATA = REPO / "data"

# Categorical slots (validated reference palette, light mode), always in this order.
C1, C2, C3, C4, C5, C7 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#6250d6"
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df"
XPS_FILL = "#1baf7a"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 9,
    "axes.titlesize": 9,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 7.5,
    "axes.edgecolor": INK2,
    "axes.labelcolor": INK,
    "xtick.color": INK2,
    "ytick.color": INK2,
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "lines.linewidth": 1.6,
    "lines.markersize": 5,
    "legend.frameon": False,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "figure.dpi": 100,
})


def read_csv(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return float("nan")


def panel_label(ax, s, x=-0.14, y=1.04):
    ax.text(x, y, s, transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom", ha="left", color=INK)


def save(fig, name):
    fig.savefig(OUT / name)
    plt.close(fig)
    print("wrote", OUT / name)


# --------------------------------------------------------------------------- shared data
def measured_vocT():
    rows = read_csv(DATA / "kujovic_family/curves/S1_fig3d_Voc_vs_T.csv")
    T = np.array([f(r["T_K"]) for r in rows])
    V = np.array([f(r["Voc_V"]) for r in rows]) * 1000.0
    return T, V


def ident_curve(phi, dEc, lS):
    tag = f"phi{phi:.2f}_dEc{'m' if dEc < 0 else 'p'}{abs(dEc):.3f}_lS{lS:.3f}.csv"
    rows = read_csv(IDENT / "curves" / tag)
    T = np.array([f(r["T_K"]) for r in rows])
    v1 = np.array([f(r["Voc1"]) for r in rows]) * 1000.0
    m = np.array([f(r["m_V"]) for r in rows]) * 1000.0
    return T, v1, m


def ident_profile():
    return {round(f(r["dEc"]), 3): r for r in read_csv(IDENT / "ident_profile.csv")}


# --------------------------------------------------------------------------- F1
def fig1():
    Tm, Vm = measured_vocT()
    prof = ident_profile()
    ridge = {round(f(r["dEc"]), 3): f(r["logS"]) for r in read_csv(IDENT / "ridge_points.csv")}
    ridge[0.1] = f(prof[0.1]["logS_best_interp"])
    cases = [
        (-0.30, C1, "-", "o", "best cliff: $\\Delta E_c$ = $-$0.30 eV, S = 5.2 cm/s"),
        (0.06, C2, "--", "s", "best spike: $\\Delta E_c$ = +0.06 eV, S = 1.9$\\times$10$^5$ cm/s"),
        (0.10, C7, ":", "^", "published spike: $\\Delta E_c$ = +0.10 eV (S on ridge)"),
    ]
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 3.3), gridspec_kw=dict(width_ratios=[1.2, 1]))
    Tf = np.linspace(216, 355, 200)
    handles = []
    for dEc, col, ls, mk, lab in cases:
        T, v1, m = ident_curve(0.50, dEc, ridge[round(dEc, 3)])
        X = f(prof[round(dEc, 3)]["X_sim_phi0.50"])
        dchi = f(prof[round(dEc, 3)]["dchi2_sim_phi0.50"])
        vx = v1 + m * math.log(X)
        a.plot(Tf, PchipInterpolator(T, vx)(Tf), ls=ls, color=col, lw=1.6, zorder=2)
        a.plot(T, vx, mk, color=col, ms=4.5, mec="white", mew=0.8, zorder=3)
        vm = PchipInterpolator(T, v1)(Tm) + PchipInterpolator(T, m)(Tm) * math.log(X)
        b.plot(Tm, vm - Vm, ls=ls, marker=mk, color=col, ms=4.5, mec="white", mew=0.8)
        dtxt = f"{dchi:.1f}" if dchi < 10 else f"{dchi:.0f}"
        handles.append(Line2D([], [], color=col, ls=ls, marker=mk, ms=4.5, mec="white", mew=0.8,
                              label=f"{lab}; X = {X:.2f} sun, $\\Delta\\chi^2$ = {dtxt}"))
    a.plot(Tm, Vm, "o", mfc="white", mec=INK, mew=1.2, ms=6, zorder=4)
    handles.append(Line2D([], [], color=INK, ls="none", marker="o", mfc="white", mew=1.2, ms=6,
                          label="measured, JVT stage (13 points)"))
    a.set_xlabel("Temperature (K)")
    a.set_ylabel("$V_{oc}$ (mV)")
    a.set_xlim(210, 360)
    b.axhspan(-4, 4, color=GRID, alpha=0.8, lw=0, zorder=0)
    b.axhline(0, color=INK2, lw=0.8)
    b.set_xlabel("Temperature (K)")
    b.set_ylabel("model $-$ measured (mV)")
    b.text(0.03, 0.04, "grey band: $\\pm\\sigma$ = 4 mV", transform=b.transAxes, fontsize=7, color=INK2)
    panel_label(a, "(a)", x=-0.14)
    panel_label(b, "(b)", x=-0.2)
    fig.legend(handles=handles, loc="lower center", ncol=2, fontsize=6.8, bbox_to_anchor=(0.5, -0.02),
               handlelength=2.6, columnspacing=1.5)
    fig.tight_layout(rect=(0, 0.15, 1, 1))
    save(fig, "F1_vocT_cliff_vs_spike.png")


# --------------------------------------------------------------------------- F2
def fig2():
    summ = read_csv(IDENT / "ident_summary.csv")[0]
    chi2min = f(summ["chi2_min"])
    fine = read_csv(IDENT / "ident_fine_scan.csv")
    ridge = read_csv(IDENT / "ridge_points.csv")
    prof = read_csv(IDENT / "ident_profile.csv")
    dEcs = sorted({round(f(r["dEc"]), 3) for r in fine})
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 3.0), gridspec_kw=dict(width_ratios=[1.15, 1]))
    norm = LogNorm(vmin=0.3, vmax=1e3)
    cmap = plt.get_cmap("Blues_r")
    w = 0.034
    for d in dEcs:
        rr = [r for r in fine if round(f(r["dEc"]), 3) == d]
        ls = np.array([f(r["logS"]) for r in rr])
        dc = np.clip(np.array([f(r["chi2"]) for r in rr]) - chi2min, 0.3, 1e3)
        edges = np.concatenate([[ls[0] - (ls[1] - ls[0]) / 2], (ls[1:] + ls[:-1]) / 2, [ls[-1] + (ls[-1] - ls[-2]) / 2]])
        a.pcolormesh([d - w / 2, d + w / 2], edges, dc[:, None], cmap=cmap, norm=norm, shading="flat", rasterized=True)
    rx = [f(r["dEc"]) for r in ridge] + [0.10]
    ry = [f(r["logS"]) for r in ridge] + [f([p for p in prof if round(f(p["dEc"]), 3) == 0.1][0]["logS_best_interp"])]
    a.plot(rx, ry, "-", color=C5, lw=1.2, marker="o", ms=3.5, label="best S for each $\\Delta E_c$ (ridge)")
    x95 = [f(summ["dEc_95_lo"]), f(summ["dEc_95_hi"])]
    y95 = [f(summ["ridge_logS_at_dEc_lo95"]), f(summ["ridge_logS_at_dEc_hi95"])]
    a.plot(x95, y95, "-", color=C2, lw=4.0, solid_capstyle="round", alpha=0.9, label="95% region (thin valley)")
    a.plot([-0.30], [0.716667], marker="*", ms=12, color=C2, mec=INK, mew=0.7, ls="none", label="best fit")
    a.fill_between([-0.32, -0.22], -0.55, -0.35, color=XPS_FILL, lw=0)
    a.text(-0.21, -0.45, "XPS cliffs [Liu 2022]", ha="left", va="center", fontsize=7, color=INK2)
    a.set_xlabel("front offset $\\Delta E_c$ (eV; negative = cliff)")
    a.set_ylabel("log$_{10}$ interface S (cm/s)")
    a.set_xlim(-0.37, 0.13)
    a.set_ylim(-0.65, 6.3)
    a.grid(False)
    a.legend(loc="upper left", fontsize=7)
    sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    cb = fig.colorbar(sm, ax=a, pad=0.02, fraction=0.05)
    cb.set_label("$\\Delta\\chi^2$ ($\\varphi_b$ = 0.50 eV, X profiled)")
    # (b) profile
    x = np.array([f(r["dEc"]) for r in prof])
    for key, col, mk, lab in (("0.45", C1, "s", "$\\varphi_b$ = 0.45 eV"), ("0.50", INK, "o", "$\\varphi_b$ = 0.50 eV"),
                              ("0.55", C2, "^", "$\\varphi_b$ = 0.55 eV")):
        y = np.array([f(r[f"chi2_sim_phi{key}"]) for r in prof]) - chi2min
        b.plot(x, np.clip(y, 0.05, None), marker=mk, color=col, ms=4, lw=1.3, label=lab)
    b.axhline(2.3, color=MUTED, lw=0.9, ls="-")
    b.axhline(6.2, color=MUTED, lw=0.9, ls="--")
    b.text(0.115, 2.5, "68%", fontsize=7, color=INK2, ha="right")
    b.text(0.115, 6.8, "95%", fontsize=7, color=INK2, ha="right")
    b.axvspan(-0.32, -0.22, color=XPS_FILL, alpha=0.15, lw=0, label="XPS range ($-$0.32 to $-$0.22 eV)")
    b.set_yscale("log")
    b.set_ylim(0.05, 3e3)
    b.set_xlabel("$\\Delta E_c$ (eV)")
    b.set_ylabel("profile $\\Delta\\chi^2$ (min over S, X)")
    b.legend(loc="lower right", fontsize=7)
    panel_label(a, "(a)", x=-0.17)
    panel_label(b, "(b)", x=-0.2)
    fig.tight_layout()
    save(fig, "F2_identifiability.png")


# --------------------------------------------------------------------------- F3
def fig3():
    from matplotlib.ticker import FixedLocator, NullLocator, ScalarFormatter
    prof = read_csv(FLUCT / "fluct_profile.csv")
    sb = read_csv(FLUCT / "fluct_profile_Sbound.csv")
    phib = read_csv(FLUCT / "fluct_C_phib.csv")
    fig, (a, b, c) = plt.subplots(1, 3, figsize=(7.2, 3.7), gridspec_kw=dict(width_ratios=[1.15, 0.95, 1.0]))

    def series(rows, **kw):
        rr = [r for r in rows if all(r[k] == v for k, v in kw.items())]
        rr.sort(key=lambda r: f(r["dEc"]))
        return rr

    lines = [
        (series(prof, fit="noprior", sigma_max_meV="0"), MUTED, "--", "o", "$\\sigma$ = 0, S free"),
        (series(prof, fit="noprior", sigma_max_meV="60"), INK, "-", "o", "$\\sigma$ free ($\\leq$ 60 meV), S free"),
        (series(sb, fit="noprior", logS_min="0"), C1, "-", "s", "$\\sigma$ free, S $\\geq$ 1 cm/s"),
        (series(sb, fit="noprior", logS_min="1"), C3, "-", "D", "$\\sigma$ free, S $\\geq$ 10 cm/s"),
    ]
    floor = 0.3
    for rr, col, ls, mk, lab in lines:
        x = np.array([f(r["dEc"]) for r in rr])
        y = np.clip(np.array([f(r["dchi2"]) for r in rr]), floor, None)
        lb = np.array([r.get("lower_bound", "False") == "True" for r in rr])
        a.plot(x, y, ls=ls, color=col, lw=1.2, marker=mk, ms=3.8, mec=col, mfc=col, label=lab)
        if lb.any():
            a.plot(x[lb], y[lb], mk, mfc="white", mec=col, ms=3.8, mew=0.9, ls="none")
    a.axvspan(-0.32, -0.22, color=XPS_FILL, alpha=0.15, lw=0)
    a.axhline(3.84, color=MUTED, lw=0.8, ls=":")
    a.set_yscale("log")
    a.set_ylim(floor * 0.8, 1e3)
    a.set_xlabel("$\\Delta E_c$ (eV)")
    a.set_ylabel("profile $\\Delta\\chi^2$ (0 plotted at 0.3)")
    a.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), fontsize=6.6, handlelength=2.2)
    a.text(0.98, 0.03, "open markers: lower bounds\n(S window below the bound)\nshaded: XPS cliffs", transform=a.transAxes,
           fontsize=6.2, color=INK2, va="bottom", ha="right")

    def spike(rows, **kw):
        return [f(r["dchi2"]) for r in series(rows, **kw) if abs(f(r["dEc"]) - 0.06) < 1e-6][0]

    bars = [
        ("S free", spike(prof, fit="noprior", sigma_max_meV="60"), spike(prof, fit="prior", sigma_max_meV="60")),
        ("S $\\geq$ 1", spike(sb, fit="noprior", logS_min="0"), spike(sb, fit="prior", logS_min="0")),
        ("S $\\geq$ 10", spike(sb, fit="noprior", logS_min="1"), spike(sb, fit="prior", logS_min="1")),
    ]
    yy = np.arange(len(bars))[::-1]
    h = 0.36
    b.barh(yy + h / 2 + 0.01, [v[1] for v in bars], height=h, color=C1, label="no $\\sigma$ prior")
    b.barh(yy - h / 2 - 0.01, [v[2] for v in bars], height=h, color=C2, label="$\\sigma$ prior 52 $\\pm$ 8 meV")
    for i, (_, v1, v2) in zip(yy, bars):
        b.text(v1 + 8, i + h / 2 + 0.01, f"{v1:.0f}", va="center", fontsize=7, color=INK)
        b.text(v2 + 8, i - h / 2 - 0.01, f"{v2:.0f}", va="center", fontsize=7, color=INK)
    b.set_yticks(yy)
    b.set_yticklabels([v[0] for v in bars])
    b.set_xlim(0, 600)
    b.set_xlabel("$\\Delta\\chi^2$, best spike (+0.06 eV)\nvs best cliff, $\\sigma$ free")
    b.legend(loc="upper center", bbox_to_anchor=(0.5, -0.27), fontsize=6.6)
    b.grid(axis="y", visible=False)

    for back, col, mk, lab in (("ohm", C2, "o", "ohmic back"), ("b0.45", C1, "s", "$\\varphi_b$ = 0.45 eV"),
                               ("b0.50", INK, "D", "$\\varphi_b$ = 0.50 eV"), ("b0.55", C7, "^", "$\\varphi_b$ = 0.55 eV")):
        rr = sorted([r for r in phib if r["back"] == back], key=lambda r: f(r["sigma_meV"]))
        sg = np.array([f(r["sigma_meV"]) for r in rr])
        y = np.array([f(r["chi2"]) for r in rr])
        i = int(np.argmin(y))
        c.plot(sg, y, color=col, lw=1.3, label=f"{lab} (min {y[i]:.1f} at {sg[i]:.0f} meV)")
        c.plot(sg[i], y[i], mk, color=col, ms=6, mec="white", mew=0.8)
    c.set_yscale("log")
    c.yaxis.set_major_locator(FixedLocator([20, 50, 100, 200, 500]))
    c.yaxis.set_major_formatter(ScalarFormatter())
    c.yaxis.set_minor_locator(NullLocator())
    c.set_xlabel("fluctuation width $\\sigma$ (meV)")
    c.set_ylabel("$\\chi^2$")
    c.set_title("$\\Delta E_c$ = $-$0.34 eV, S = 1.83 cm/s", fontsize=7.5, color=INK2)
    c.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), fontsize=6.6)
    panel_label(a, "(a)", x=-0.22)
    panel_label(b, "(b)", x=-0.3)
    panel_label(c, "(c)", x=-0.22)
    fig.tight_layout(w_pad=1.2)
    save(fig, "F3_fluctuation_gate.png")


# --------------------------------------------------------------------------- F4
def fig4():
    meas = read_csv(DATA / "pandey2021/pandey2021_mzo_series.csv")
    fits = read_csv(PANDEY / "oneS_fits.csv")
    best = [r for r in fits if r["case"] == "best|kscale|Rs fit" and r["fit"] == "shared S"][0]
    xs = ["0.00", "0.10", "0.15", "0.20", "0.25"]
    xv = np.array([float(x) for x in xs])
    mrow = {r["mg_fraction"]: r for r in meas}
    ticklab = ["0", "0.10", "0.15", "0.20", "0.25"]
    fig, (a, b, c) = plt.subplots(1, 3, figsize=(7.2, 3.5), gridspec_kw=dict(width_ratios=[1, 1, 1.15]))
    for ax, q, lab in ((a, "Voc", "$V_{oc}$ (mV)"), (b, "FF", "FF (%)")):
        unit = "mV" if q == "Voc" else "pct"
        mb = np.array([f(mrow[x][f"{q}_best_{unit}"]) for x in xs])
        ma = np.array([f(mrow[x][f"{q}_avg_{unit}"]) for x in xs])
        mod = np.array([f(best[f"x{x}_{q}"]) for x in xs])
        ax.plot(xv, ma, "x", color=MUTED, ms=5, mew=1.2, ls="none", label="measured average (25 cells)")
        ax.plot(xv, mb, "o", mfc="white", mec=INK, mew=1.2, ms=6, ls="none", label="measured best cell")
        ax.plot(xv, mod, "-", color=C1, marker="s", ms=4.5, mec="white", mew=0.7, label="model, one shared S = 10$^5$ cm/s")
        ax.set_xlabel("Mg fraction x in Mg$_x$Zn$_{1-x}$O")
        ax.set_ylabel(lab)
        ax.set_xticks(xv)
        ax.set_xticklabels(ticklab, fontsize=7)
    ha, la = a.get_legend_handles_labels()
    prof = read_csv(PANDEY / "oneS_profiles.csv")
    for case, col, mk, lab in (("best|kscale|Rs fit", C1, "s", "Cu-series profile, Jsc scaled (k fitted)"),
                               ("best|noJsc|Rs fit", C3, "D", "Cu-series profile, Voc and FF only"),
                               ("best|abs|Rs fit", C2, "o", "Cu-series profile, absolute Jsc")):
        rr = sorted([r for r in prof if r["case"] == case], key=lambda r: f(r["lS"]))
        c.plot([f(r["lS"]) for r in rr], np.clip([f(r["dchi2_shared"]) for r in rr], 0.05, None), color=col, marker=mk,
               ms=4, lw=1.3, label=lab)
    c.axvspan(0.3, 1.3, color=C4, alpha=0.3, lw=0, label="As-doped 21.4% cell (cliff $-$0.26 to $-$0.35 eV)")
    c.axhline(4, color=MUTED, lw=0.8, ls=":")
    c.set_yscale("log")
    c.set_ylim(0.04, 400)
    c.set_xlim(0, 6.3)
    c.set_xlabel("log$_{10}$ interface S (cm/s)")
    c.set_ylabel("$\\Delta\\chi^2$ (0 plotted at 0.05)")
    hc, lc = c.get_legend_handles_labels()
    fig.legend(ha + hc, la + lc, loc="lower center", ncol=2, fontsize=6.6, bbox_to_anchor=(0.5, 0.0),
               columnspacing=2.0)
    panel_label(a, "(a)", x=-0.27)
    panel_label(b, "(b)", x=-0.25)
    panel_label(c, "(c)", x=-0.25)
    fig.tight_layout(rect=(0, 0.2, 1, 1))
    save(fig, "F4_pandey_oneS.png")


# --------------------------------------------------------------------------- F5
def fig5():
    res = {r["design"]: r for r in read_csv(DESIGN / "design_results.csv")}
    pen = read_csv(DESIGN / "design_penalties.csv")
    cons = [r for r in pen if r["branch"] == "base" and r["design"] == "conservative"][0]
    basep = [r for r in pen if r["branch"] == "base" and r["design"] == "baseline (+B)"][0]
    eta0 = f(res["0 baseline (ident best fit)"]["eta"])
    steps = [
        ("remove cliff\n$\\Delta E_c$ +0.20 eV,\nS $\\times$10", f(res["1a dEc +0.20, S 52.1"]["eta"]) - eta0),
        ("bulk $\\tau$\n300 ns", f(res["1c tau 300 ns at dEc +0.00"]["lever_deta"])),
        ("$N_A$ $\\times$3", f(res["1d NA x3 at dEc 0, tau 300 ns"]["lever_deta"])),
        ("back barrier\n0.30 eV", f(res["1e back b0.30 at dEc 0"]["lever_deta"])),
        ("MAR +\nFTO 150 nm", f(res["1f optics (c) at dEc 0"]["lever_deta"])),
    ]
    eta_cons_ideal = f(cons["eta_no_RsRsh"])
    eta_cons = f(cons["eta"])
    cum = eta0 + sum(s[1] for s in steps)
    steps.append(("non-additivity\n+ radiative B", eta_cons_ideal - cum))
    fig, ax = plt.subplots(figsize=(7.0, 3.1))
    W, TH = 0.62, 0.12  # bar width; thickness of the level markers used for totals (no implied zero baseline)

    def level(x, y, col, txt, bold=False):
        ax.bar(x, TH, bottom=y - TH / 2, width=W, color=col)
        ax.text(x, y + 0.2, txt, ha="center", fontsize=7.5, color=INK, fontweight="bold" if bold else "normal")

    level(0, eta0, INK2, f"{eta0:.2f}")
    level_y = eta0
    labels = ["model baseline\n(calibrated fit,\nRs 0, B 0)"]
    for i, (lab, d) in enumerate(steps, start=1):
        col = C1 if d >= 0 else C2
        lo = level_y if d >= 0 else level_y + d
        ax.bar(i, max(abs(d), 0.04), bottom=lo, width=W, color=col)
        ax.plot([i - 1 + W / 2, i - W / 2], [level_y, level_y], color=MUTED, lw=0.8)
        ax.text(i, max(level_y, level_y + d) + 0.2, f"{d:+.2f}", ha="center", fontsize=7.5, color=INK)
        level_y += d
        labels.append(lab)
    n = len(steps) + 1
    ax.plot([n - 1 + W / 2, n - W / 2], [level_y, level_y], color=MUTED, lw=0.8)
    level(n, eta_cons_ideal, C3, f"{eta_cons_ideal:.2f}")
    labels.append("conservative\n(simulated,\nno $R_s$/$R_{sh}$)")
    dR = eta_cons - eta_cons_ideal
    ax.bar(n + 1, abs(dR), bottom=eta_cons, width=W, color=C2)
    ax.plot([n + W / 2, n + 1 - W / 2], [eta_cons_ideal, eta_cons_ideal], color=MUTED, lw=0.8)
    ax.text(n + 1, eta_cons_ideal + 0.2, f"{dR:+.2f}", ha="center", fontsize=7.5, color=INK)
    labels.append("$R_s$ 0.45,\n$R_{sh}$ 2500\n$\\Omega$ cm$^2$")
    ax.plot([n + 1 + W / 2, n + 2 - W / 2], [eta_cons, eta_cons], color=MUTED, lw=0.8)
    level(n + 2, eta_cons, C3, f"{eta_cons:.2f}", bold=True)
    labels.append("conservative\n(penalised)")
    yb = f(basep["eta"])
    ax.axhline(yb, color=INK2, lw=0.9, ls="--")
    ax.text(0.45, yb - 0.55, f"model baseline with the same penalties: {yb:.2f}%", ha="left", fontsize=7, color=INK2)
    ax.set_xticks(range(n + 3))
    ax.set_xticklabels(labels, fontsize=6.6)
    ax.set_ylim(16.5, 27.0)
    ax.set_ylabel("model efficiency (%)")
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    save(fig, "F5_design_waterfall.png")


# --------------------------------------------------------------------------- F6
def fig6():
    dark = read_csv(REPO / "optionA/scaps_if_dark.csv")
    light = read_csv(REPO / "optionA/scaps_if_xcheck.csv")
    val = read_csv(REPO / "optionA/sesame/validation.csv")
    kval = read_csv(KJ / "kujovic_validation.csv")
    zx = read_csv(REPO / "optionA/scaps_znse_xcheck.csv")
    dx = read_csv(REPO / "optionA/scaps_design_xcheck.csv")
    pen = read_csv(DESIGN / "design_penalties.csv")
    res = {r["design"]: r for r in read_csv(DESIGN / "design_results.csv")}

    fig = plt.figure(figsize=(7.2, 5.4))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 0.9], hspace=0.38, wspace=0.3)
    a = fig.add_subplot(gs[0, 0])
    b = fig.add_subplot(gs[0, 1])
    t = fig.add_subplot(gs[1, :])
    cols = {"0.1": C2, "-0.1": C1, "-0.22": C3, "-0.32": C7}
    mks = {"0.1": "s", "-0.1": "o", "-0.22": "D", "-0.32": "^"}
    for d in ("0.1", "-0.1", "-0.22", "-0.32"):
        rr = [r for r in dark if r["dEc"] == d]
        V = np.array([f(r["V"]) for r in rr])
        Js = np.array([f(r["J_scaps_mAcm2"]) for r in rr])
        Je = np.array([f(r["J_sesame_mAcm2"]) for r in rr])
        lab = f"$\\Delta E_c$ = {float(d):+.2f} eV"
        a.plot(V, Je, "-", color=cols[d], lw=1.4)
        a.plot(V, Js, mks[d], mfc="white", mec=cols[d], mew=1.0, ms=4.5, ls="none", label=lab)
        b.plot(V, Je / Js, "-", color=cols[d], marker=mks[d], ms=3.5, lw=1.2, label=lab)
    a.set_yscale("log")
    a.set_xlabel("voltage (V)")
    a.set_ylabel("dark current density (mA/cm$^2$)")
    a.legend(loc="lower right", fontsize=6.6, title="markers SCAPS, lines Sesame", title_fontsize=6.6)
    b.axhspan(0.96, 0.975, color=GRID, lw=0)
    b.set_ylim(0.94, 1.008)
    b.axhline(1.0, color=INK2, lw=0.8)
    b.set_xlabel("voltage (V)")
    b.set_ylabel("$J_{Sesame}/J_{SCAPS}$")
    b.text(0.97, 0.95, "colours and offsets as in (a)", transform=b.transAxes, ha="right", va="top", fontsize=6.8,
           color=INK2)

    # light-case table (all from CSVs)
    rows = []
    v = [r for r in val if r["optics"] == "scaps"]
    rows.append(["MgZnO/ZnO cells, absorber-side IL (8 cases)", "IL",
                 f"{min(f(r['dVoc_mV']) for r in v):+.1f} to {max(f(r['dVoc_mV']) for r in v):+.1f}",
                 f"{max(abs(f(r['dJsc_pct'])) for r in v):.2f}", f"{max(abs(f(r['dFF_abs'])) for r in v):.2f}"])
    k = [r for r in kval if r["front_contact"].startswith("Schottky")]
    rows.append(["21.4% stack rebuild, 300 K (2 cases)", "IL",
                 " / ".join(f"{f(r['dVoc_mV']):+.1f}" for r in k),
                 f"{max(abs(f(r['dJsc_pct'])) for r in k):.2f}", f"{max(abs(f(r['dFF'])) for r in k):.2f}"])
    s = [r for r in light if r["scaps_ok"] == "True"][0]
    rows.append([f"interface states, spike +0.10 eV, S 1e4 cm/s", "IF",
                 f"{f(s['Voc_sesame']) - f(s['Voc_scaps']):+.1f}",
                 f"{100 * abs(f(s['Jsc_sesame']) / f(s['Jsc_scaps']) - 1):.2f}",
                 f"{abs(f(s['FF_sesame']) - f(s['FF_scaps'])):.2f}"])
    nfail = sum(r["scaps_ok"] != "True" for r in light)
    z = [r for r in zx if abs(f(r["dEc"]) - 0.3) < 1e-6][0]
    zs = [float(x) for x in z["sesame"].replace("mV", "").split("/")]
    rows.append(["ZnSe front, $\\Delta E_c$ +0.30 eV, interface states", "IF",
                 f"{zs[0] - f(z['Voc_scaps']):+.1f}", f"{100 * abs(zs[1] / f(z['J0_scaps']) - 1):.2f}",
                 f"{abs(zs[2] - f(z['FF_scaps'])):.2f}"])
    cs = [r for r in pen if r["branch"] == "base" and r["design"] == "conservative"][0]
    # SCAPS conservative (penalised) values: from the SCAPS output file when it exists locally, otherwise from its
    # summary lines committed in optionA/scaps_design_conservative_RsRsh.csv (raw SCAPS outputs are not distributed)
    iv = REPO / "scaps/results/X_design_conservative_RsRsh.iv"
    scv = {}
    if iv.exists():
        for line in open(iv, errors="replace"):
            for key in ("Voc", "Jsc", "FF", "eta"):
                if line.strip().startswith(key + " ="):
                    scv[key] = float(line.split("=")[1].split()[0])
    else:
        row = read_csv(REPO / "optionA/scaps_design_conservative_RsRsh.csv")[0]
        scv = {k: f(row[k]) for k in ("Voc", "Jsc", "FF", "eta")}
    rows.append(["conservative design, $R_s$/$R_{sh}$ applied", "IF",
                 f"{f(cs['Voc_mV']) - 1000 * scv['Voc']:+.1f}", f"{100 * abs(f(cs['Jsc']) / scv['Jsc'] - 1):.2f}",
                 f"{abs(f(cs['FF']) - scv['FF']):.2f}"])
    rz = [r for r in dx if r["design"] == "realistic" and r["resistance"] == "ideal"][0]
    rs = res["2 realistic [base]"]
    rows.append(["NA$\\times$10 design (ideal)", "IF", f"{f(rs['Voc_mV']) - f(rz['Voc']):+.1f}",
                 f"{100 * abs(f(rs['Jsc']) / f(rz['Jsc']) - 1):.2f}", f"{abs(f(rs['FF']) - f(rz['FF'])):.2f}"])
    t.axis("off")
    tab = t.table(cellText=rows, colLabels=["light (1 sun, 300 K) case", "front model", "$\\Delta V_{oc}$ (mV)",
                                            "|$\\Delta J_{sc}$| (%)", "|$\\Delta$FF| (pts)"],
                  colWidths=[0.47, 0.11, 0.17, 0.13, 0.12], loc="upper center", cellLoc="center",
                  bbox=[0.0, 0.08, 1.0, 0.92])
    tab.auto_set_font_size(False)
    tab.set_fontsize(7.2)
    for (r_, c_), cell in tab.get_celld().items():
        cell.set_edgecolor(GRID)
        if r_ == 0:
            cell.set_facecolor("#f3f2ef")
            cell.set_text_props(fontweight="bold")
        if c_ == 0 and r_ > 0:
            cell.set_text_props(ha="left")
            cell._loc = "left"
    t.text(0.0, -0.02, f"$\\Delta$ = Sesame $-$ SCAPS. IL: absorber-side defect layer; IF: buffer-CB/absorber-VB interface "
           f"states. The {nfail} cliff cases of the IF check did not converge in SCAPS under light (see a, b).",
           transform=t.transAxes, fontsize=6.6, color=INK2, va="top")
    panel_label(a, "(a)", x=-0.2)
    panel_label(b, "(b)", x=-0.2)
    panel_label(t, "(c)", x=-0.02, y=0.95)
    save(fig, "F6_solver_crossvalidation.png")


# --------------------------------------------------------------------------- F7 (SI)
def fig7():
    rows = read_csv(ZNSE / "znse_results.csv")
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 2.9))
    sets = [
        (("5.21195", "1e+15", "80"), C1, "-", "o", "N$_D$ 1e15, 80 nm, S 5.2"),
        (("5.21195", "1e+17", "80"), C2, "-", "s", "N$_D$ 1e17, 80 nm, S 5.2"),
        (("5.21195", "1e+15", "50"), C1, ":", "o", "N$_D$ 1e15, 50 nm, S 5.2"),
        (("5.21195", "1e+17", "50"), C2, ":", "s", "N$_D$ 1e17, 50 nm, S 5.2"),
        (("100000", "1e+15", "80"), C3, "--", "D", "N$_D$ 1e15, 80 nm, S 1e5"),
        (("100000", "1e+17", "80"), C7, "--", "^", "N$_D$ 1e17, 80 nm, S 1e5"),
    ]
    for (S, ND, dnm), col, ls, mk, lab in sets:
        rr = sorted([r for r in rows if r["S"] == S and r["ND"] == ND and r["d_nm"] == dnm], key=lambda r: f(r["dEc"]))
        x = np.array([f(r["dEc"]) for r in rr])
        eta = np.array([f(r["eta"]) if r["status"] == "ok" else np.nan for r in rr])
        j0 = np.array([f(r["J_V0"]) if r["status"] != "" else np.nan for r in rr])
        mfc = "white" if dnm == "50" else col
        a.plot(x, eta, ls=ls, color=col, marker=mk, ms=4, mfc=mfc, mec=col, lw=1.2, label=lab)
        b.plot(x, j0, ls=ls, color=col, marker=mk, ms=4, mfc=mfc, mec=col, lw=1.2, label=lab)
    for ax in (a, b):
        ax.axvspan(0.25, 0.85, color=C4, alpha=0.18, lw=0)
        ax.axvline(0.55, color=C4, lw=1.4)
        ax.set_xlabel("ZnSe/absorber $\\Delta E_c$ (eV; positive = spike)")
    a.text(0.565, 24.3, "DFT +0.55 $\\pm$ 0.3 eV", fontsize=6.8, color=INK2)
    for v, lab in ((11.3, "USF 1998, ZnSe consumed: 11.3%"), (9.0, "USF 1997, ZnSe consumed: 9.0%"),
                   (5.6, "USF, ZnSe intact: 5.6%"), (1.8, "USF, ZnSe intact: 1.8%")):
        a.axhline(v, color=MUTED, lw=0.7, ls=(0, (2, 2)))
        a.text(-0.06, v + 0.3, lab, fontsize=6.0, color=INK2, ha="left")
    a.set_ylabel("efficiency (%)")
    a.set_ylim(0, 26)
    a.set_xlim(-0.13, 0.88)
    b.legend(loc="lower left", fontsize=6.4)
    b.set_ylabel("$J$ at $V$ = 0 (mA/cm$^2$)")
    b.set_ylim(0, 29)
    panel_label(a, "(a)", x=-0.15)
    panel_label(b, "(b)", x=-0.15)
    fig.tight_layout()
    save(fig, "F7_SI_znse_collapse.png")


if __name__ == "__main__":
    fig1()
    fig2()
    fig3()
    fig4()
    fig5()
    fig6()
    fig7()
