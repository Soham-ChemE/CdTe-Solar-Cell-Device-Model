"""Build the data and preview assets of the live page (docs/index.html) from the committed CSVs.

Every number the page draws or prints comes from here; nothing is typed into the page by hand except text that quotes
README.md and docs/CLAIMS.md.

Writes
  docs/assets/data.js            window.CDTE = {...}: hero profile, Voc(T) curves (F1), fluctuation gate (F3), ZnO paradox
                                 (F4), design staircase (F5), solver cross-check (F6), ZnSe collapse map (F7)
  docs/assets/cliff.json         the identifiability map and fine scan (F2), loaded lazily by "The cliff, live" and the valley
  docs/assets/social-preview.png 1280x640 card; embeds docs/assets/hero_dark.webp when it exists (rendered by tools/page_qa.py)

Run from anywhere:   python docs/build_assets.py          (numpy, scipy, matplotlib)
Renders and QA:      python docs/tools/page_qa.py --hero --qa   (Playwright for Python; see that file), then re-run this
                     script so the social preview picks up the new hero render.
"""
import csv
import json
import math
from pathlib import Path

import numpy as np
from scipy.interpolate import PchipInterpolator

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs/assets"
KJ = REPO / "optionA/sesame/kujovic"
IDENT, FLUCT, ZNSE = KJ / "ident", KJ / "fluct", KJ / "znse"
PANDEY = REPO / "optionA/sesame/pandey_oneS"
DESIGN = REPO / "optionA/sesame/design"
OUT.mkdir(parents=True, exist_ok=True)


def rows(p):
    with open(p, newline="") as fh:
        return list(csv.DictReader(fh))


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return float("nan")


def r(x, n=3):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(x, n)


# ------------------------------------------------------------------ identifiability (hero, F1, F2, the cliff live)
summary = rows(IDENT / "ident_summary.csv")[0]
chi2_min = f(summary["chi2_min"])
prof_rows = {round(f(x["dEc"]), 3): x for x in rows(IDENT / "ident_profile.csv")}
ridge = {round(f(x["dEc"]), 3): f(x["logS"]) for x in rows(IDENT / "ridge_points.csv")}
ridge.setdefault(0.1, f(prof_rows[0.1]["logS_best_interp"]))
profile = []
for d in sorted(prof_rows, reverse=True):
    x = prof_rows[d]
    profile.append(dict(dEc=d, logS=r(ridge[d]), dchi2=r(f(x["dchi2_sim_phi0.50"]), 1), voc=r(f(x["Voc300_sim_phi0.50"]), 1),
                        ff=r(f(x["FF300_sim_phi0.50"]), 2), X=r(f(x["X_sim_phi0.50"]), 3)))

# F1: measured Voc(T) and the three front models at phi_b = 0.50 eV, light level X profiled (as scripts/make_figures.py)
meas = rows(REPO / "data/kujovic_family/curves/S1_fig3d_Voc_vs_T.csv")
vocT = dict(measured=[[r(f(m["T_K"]), 2), r(f(m["Voc_V"]) * 1000, 1)] for m in meas], models=[])
Tf = np.linspace(216, 355, 48)
for d, key in ((-0.30, "cliff"), (0.06, "spike"), (0.10, "published")):
    tag = f"phi0.50_dEc{'m' if d < 0 else 'p'}{abs(d):.3f}_lS{ridge[round(d, 3)]:.3f}.csv"
    cv = rows(IDENT / "curves" / tag)
    T = np.array([f(c["T_K"]) for c in cv]); v1 = np.array([f(c["Voc1"]) for c in cv]) * 1000; m = np.array([f(c["m_V"]) for c in cv]) * 1000
    X = f(prof_rows[round(d, 3)]["X_sim_phi0.50"]); vx = v1 + m * math.log(X)
    vocT["models"].append(dict(key=key, dEc=d, logS=r(ridge[round(d, 3)]), X=r(X, 2), dchi2=r(f(prof_rows[round(d, 3)]["dchi2_sim_phi0.50"]), 1),
                               sim=[[r(t, 1), r(v, 1)] for t, v in zip(T, vx)],
                               curve=[[r(t, 1), r(v, 1)] for t, v in zip(Tf, PchipInterpolator(T, vx)(Tf))]))

# the cliff, live + the valley: fine scan (PCHIP in log S between simulated points) and the simulated map
fine = rows(IDENT / "ident_fine_scan.csv")
offs = sorted({round(f(x["dEc"]), 3) for x in fine})
cliff = dict(source="optionA/sesame/kujovic/ident/ident_fine_scan.csv and ident_map.csv (phi_b 0.50 eV, light level X profiled)",
             chi2_min=chi2_min, dof=int(summary["dof"]), voc_measured=875.5, ff_measured=80.48, offsets=[])
imap = rows(IDENT / "ident_map.csv")
for d in offs:
    fr = sorted([x for x in fine if round(f(x["dEc"]), 3) == d], key=lambda x: f(x["logS"]))
    keep = fr[::2] + ([fr[-1]] if len(fr) % 2 == 0 else [])
    mp = sorted([x for x in imap if round(f(x["dEc"]), 3) == d], key=lambda x: f(x["logS"]))
    cliff["offsets"].append(dict(
        dEc=d, ridge=r(ridge[d]), dchi2_profile=r(f(prof_rows[d]["dchi2_sim_phi0.50"]), 1),
        ridge_sim=[r(f(prof_rows[d]["Voc300_sim_phi0.50"]), 1), r(f(prof_rows[d]["FF300_sim_phi0.50"]), 2), r(f(prof_rows[d]["dchi2_sim_phi0.50"]), 1)],
        fine=[[r(f(x["logS"]), 4), r(f(x["Voc300"]), 1), r(f(x["FF300"]), 2), r(f(x["chi2"]) - chi2_min, 2)] for x in keep],
        map=[[r(f(x["logS"]), 2), r(f(x["Voc300"]), 1), r(f(x["FF300"]), 2), r(f(x["eta300"]), 2),
              None if x["skipped"] == "True" else r(f(x["chi2"]) - chi2_min, 1)] for x in mp]))

ident = dict(chi2_min=chi2_min, dof=int(summary["dof"]), best=dict(dEc=f(summary["best_cliff_dEc"]), logS=r(ridge[-0.3])),
             ci68=[r(f(summary["dEc_68_lo"])), r(f(summary["dEc_68_hi"]))], ci95=[r(f(summary["dEc_95_lo"])), r(f(summary["dEc_95_hi"]))],
             ridge95=[r(f(summary["ridge_logS_at_dEc_lo95"])), r(f(summary["ridge_logS_at_dEc_hi95"]))],
             ridge_slope=r(f(summary["ridge_dlogS_ddEc"]), 1), xps=[-0.32, -0.22], voc_measured=875.5, ff_measured=80.48)

# ------------------------------------------------------------------ fluctuation gate (F3)
sv = rows(FLUCT / "fluct_sigma_vs_dEc.csv")
fsum = rows(FLUCT / "fluct_summary.csv")[0]
ref = f(fsum["B_noprior_s60_chi2min"])  # global best with sigma free and S free, no prior (-0.46 eV, sigma 60 meV)
sig = sorted({f(x["sigma_meV"]) for x in sv}); fd = sorted({round(f(x["dEc"]), 3) for x in sv})
grid = {(round(f(x["dEc"]), 3), f(x["sigma_meV"])): x for x in sv}
fprof, fsb = rows(FLUCT / "fluct_profile.csv"), rows(FLUCT / "fluct_profile_Sbound.csv")


def spike_dchi2(rr, **kw):
    return [f(x["dchi2"]) for x in rr if all(x[k] == v for k, v in kw.items()) and abs(f(x["dEc"]) - 0.06) < 1e-6][0]


fluct = dict(source="optionA/sesame/kujovic/fluct/fluct_sigma_vs_dEc.csv (no sigma prior, S free, phi_b 0.50 eV)",
             chi2_ref=r(ref, 3), ref_point=dict(dEc=f(fsum["B_noprior_s60_best_dEc"]), sigma=f(fsum["B_noprior_s60_best_sigma"]),
                                               logS=f(fsum["B_noprior_s60_best_logS"])),
             sigma=sig, dEc=fd,
             dchi2=[[r(f(grid[(d, s)]["chi2"]) - ref, 1) for d in fd] for s in sig],
             logS=[[r(f(grid[(d, s)]["logS"]), 3) for d in fd] for s in sig],
             voc=[[r(f(grid[(d, s)]["Voc300"]), 1) for d in fd] for s in sig],
             spike=dict(free=[spike_dchi2(fprof, fit="noprior", sigma_max_meV="60"), spike_dchi2(fprof, fit="prior", sigma_max_meV="60")],
                        S1=[spike_dchi2(fsb, fit="noprior", logS_min="0"), spike_dchi2(fsb, fit="prior", logS_min="0")],
                        S10=[spike_dchi2(fsb, fit="noprior", logS_min="1"), spike_dchi2(fsb, fit="prior", logS_min="1")]),
             prior=[52, 8])
fluct["spike_min"] = r(min(min(v) for v in fluct["spike"].values()), 1)

# ------------------------------------------------------------------ ZnO paradox (F4)
pm = {x["mg_fraction"]: x for x in rows(REPO / "data/pandey2021/pandey2021_mzo_series.csv")}
best = [x for x in rows(PANDEY / "oneS_fits.csv") if x["case"] == "best|kscale|Rs fit" and x["fit"] == "shared S"][0]
xs = ["0.00", "0.10", "0.15", "0.20", "0.25"]
zno = dict(source="data/pandey2021/pandey2021_mzo_series.csv; optionA/sesame/pandey_oneS/oneS_fits.csv (best|kscale|Rs fit, shared S)",
           logS_cu=f(best["lS"]), logS_as=r(ridge[-0.3]), k=r(f(best["k"]), 3),
           series=[dict(x=f(x), dEc=f(pm[x]["dEc_XPS_eV"]), voc_best=f(pm[x]["Voc_best_mV"]), voc_avg=f(pm[x]["Voc_avg_mV"]),
                        ff_best=f(pm[x]["FF_best_pct"]), eta_best=f(pm[x]["eta_best_pct"]), eta_avg=f(pm[x]["eta_avg_pct"]),
                        voc_model=r(f(best[f"x{x}_Voc"]), 1), ff_model=r(f(best[f"x{x}_FF"]), 1)) for x in xs])

# ------------------------------------------------------------------ design staircase (F5, same arithmetic as make_figures.fig5)
res = {x["design"]: x for x in rows(DESIGN / "design_results.csv")}
pen = rows(DESIGN / "design_penalties.csv")
cons = [x for x in pen if x["branch"] == "base" and x["design"] == "conservative"][0]
basep = [x for x in pen if x["branch"] == "base" and x["design"] == "baseline (+B)"][0]
eta0 = f(res["0 baseline (ident best fit)"]["eta"])
steps = [("Remove the cliff", "ΔEc +0.20 eV, S ×10", f(res["1a dEc +0.20, S 52.1"]["eta"]) - eta0),
         ("Bulk lifetime", "τ 300 ns", f(res["1c tau 300 ns at dEc +0.00"]["lever_deta"])),
         ("Absorber doping", "N_A ×3", f(res["1d NA x3 at dEc 0, tau 300 ns"]["lever_deta"])),
         ("Back barrier", "0.30 eV", f(res["1e back b0.30 at dEc 0"]["lever_deta"])),
         ("Optics", "anti-reflection + 150 nm FTO", f(res["1f optics (c) at dEc 0"]["lever_deta"]))]
cum = eta0 + sum(s[2] for s in steps)
steps.append(("Non-additivity", "+ radiative B", f(cons["eta_no_RsRsh"]) - cum))
scaps_cons = rows(REPO / "optionA/scaps_design_conservative_RsRsh.csv")[0]
branches = [f(x["eta"]) for x in pen if x["design"] == "conservative"]
design = dict(source="optionA/sesame/design/design_results.csv, design_penalties.csv; optionA/scaps_design_conservative_RsRsh.csv",
              eta0=r(eta0, 2), steps=[dict(name=a, detail=b, d=r(c, 2)) for a, b, c in steps],
              cons_ideal=r(f(cons["eta_no_RsRsh"]), 2), penalty=r(f(cons["eta"]) - f(cons["eta_no_RsRsh"]), 2),
              cons=r(f(cons["eta"]), 2), cons_voc=r(f(cons["Voc_mV"]), 1), baseline_pen=r(f(basep["eta"]), 2),
              scaps=r(f(scaps_cons["eta"]), 2), scaps_voc=r(f(scaps_cons["Voc"]) * 1000, 1),
              branches=[r(min(branches), 2), r(max(branches), 2)])

# ------------------------------------------------------------------ solvers (F6): dark J-V and the light-case table (as fig6)
dark = rows(REPO / "optionA/scaps_if_dark.csv")
solv = dict(source="optionA/scaps_if_dark.csv (phi_b 0.50 eV, interface-state model)", dark=[], table=[])
for d in ("0.1", "-0.1", "-0.22", "-0.32"):
    rr = [x for x in dark if x["dEc"] == d and not math.isnan(f(x["J_scaps_mAcm2"]))]
    solv["dark"].append(dict(dEc=f(d), S=f(rr[0]["S"]), V=[f(x["V"]) for x in rr], scaps=[float(f"{f(x['J_scaps_mAcm2']):.5g}") for x in rr],
                             sesame=[float(f"{f(x['J_sesame_mAcm2']):.5g}") for x in rr]))
val = rows(REPO / "optionA/sesame/validation.csv"); kval = rows(KJ / "kujovic_validation.csv"); light = rows(REPO / "optionA/scaps_if_xcheck.csv")
zx = rows(REPO / "optionA/scaps_znse_xcheck.csv"); dx = rows(REPO / "optionA/scaps_design_xcheck.csv")
v = [x for x in val if x["optics"] == "scaps"]
solv["table"].append(["MgZnO/ZnO cells, absorber-side interface layer (8 cases)", "IL",
                      f"{min(f(x['dVoc_mV']) for x in v):+.1f} to {max(f(x['dVoc_mV']) for x in v):+.1f}",
                      f"{max(abs(f(x['dJsc_pct'])) for x in v):.2f}", f"{max(abs(f(x['dFF_abs'])) for x in v):.2f}"])
k = [x for x in kval if x["front_contact"].startswith("Schottky")]
solv["table"].append(["21.4 % stack rebuild, 300 K (2 cases)", "IL", " / ".join(f"{f(x['dVoc_mV']):+.1f}" for x in k),
                      f"{max(abs(f(x['dJsc_pct'])) for x in k):.2f}", f"{max(abs(f(x['dFF'])) for x in k):.2f}"])
s = [x for x in light if x["scaps_ok"] == "True"][0]
solv["table"].append(["Interface states, spike +0.10 eV, S 10⁴ cm/s", "IF", f"{f(s['Voc_sesame']) - f(s['Voc_scaps']):+.1f}",
                      f"{100 * abs(f(s['Jsc_sesame']) / f(s['Jsc_scaps']) - 1):.2f}", f"{abs(f(s['FF_sesame']) - f(s['FF_scaps'])):.2f}"])
solv["spike_light"] = dict(scaps=f(s["Voc_scaps"]), sesame=r(f(s["Voc_sesame"]), 1), ff=f(s["FF_scaps"]))
solv["n_fail_light"] = sum(x["scaps_ok"] != "True" for x in light)
z = [x for x in zx if abs(f(x["dEc"]) - 0.3) < 1e-6][0]; zs = [float(t) for t in z["sesame"].replace("mV", "").split("/")]
solv["table"].append(["ZnSe front, ΔEc +0.30 eV, interface states", "IF", f"{zs[0] - f(z['Voc_scaps']):+.1f}",
                      f"{100 * abs(zs[1] / f(z['J0_scaps']) - 1):.2f}", f"{abs(zs[2] - f(z['FF_scaps'])):.2f}"])
scv = {kk: f(scaps_cons[kk]) for kk in ("Voc", "Jsc", "FF", "eta")}
solv["table"].append(["Conservative design, Rs/Rsh applied", "IF", f"{f(cons['Voc_mV']) - 1000 * scv['Voc']:+.1f}",
                      f"{100 * abs(f(cons['Jsc']) / scv['Jsc'] - 1):.2f}", f"{abs(f(cons['FF']) - scv['FF']):.2f}"])
rz = [x for x in dx if x["design"] == "realistic" and x["resistance"] == "ideal"][0]; rs = res["2 realistic [base]"]
solv["table"].append(["N_A ×10 design (ideal)", "IF", f"{f(rs['Voc_mV']) - f(rz['Voc']):+.1f}",
                      f"{100 * abs(f(rs['Jsc']) / f(rz['Jsc']) - 1):.2f}", f"{abs(f(rs['FF']) - f(rz['FF'])):.2f}"])
ratios = [f(x["ratio"]) for x in dark if not math.isnan(f(x["ratio"])) and f(x["J_scaps_mAcm2"]) >= 1e-3]
solv["ratio_range"] = [r(min(ratios), 3), r(max(ratios), 3)]

# ------------------------------------------------------------------ ZnSe (F7)
zr = rows(ZNSE / "znse_results.csv")
sets = [("5.21195", "1e+15", "80", "S 5.2, N_D 10¹⁵, 80 nm"), ("5.21195", "1e+17", "80", "S 5.2, N_D 10¹⁷, 80 nm"),
        ("5.21195", "1e+15", "50", "S 5.2, N_D 10¹⁵, 50 nm"), ("5.21195", "1e+17", "50", "S 5.2, N_D 10¹⁷, 50 nm"),
        ("1000", "1e+15", "80", "S 10³, N_D 10¹⁵, 80 nm"), ("1000", "1e+17", "80", "S 10³, N_D 10¹⁷, 80 nm"),
        ("100000", "1e+15", "80", "S 10⁵, N_D 10¹⁵, 80 nm"), ("100000", "1e+17", "80", "S 10⁵, N_D 10¹⁷, 80 nm")]
znse = dict(source="optionA/sesame/kujovic/znse/znse_results.csv; DFT: dft/interface/results.csv", dft=[0.55, 0.3],
            dEc=sorted({f(x["dEc"]) for x in zr}), sets=[])
for S, ND, dnm, lab in sets:
    rr = sorted([x for x in zr if x["S"] == S and x["ND"] == ND and x["d_nm"] == dnm], key=lambda x: f(x["dEc"]))
    znse["sets"].append(dict(label=lab, eta=[r(f(x["eta"]), 2) if x["status"] == "ok" else None for x in rr],
                             j0=[r(f(x["J_V0"]), 2) if x["J_V0"] not in ("", "nan") else None for x in rr],
                             status=[x["status"] for x in rr]))

data = dict(source="Generated by docs/build_assets.py from the committed CSVs", ident=ident, profile=profile, vocT=vocT,
            fluct=fluct, zno=zno, design=design, solvers=solv, znse=znse)
js = "// Generated by docs/build_assets.py from the committed CSVs. Do not edit by hand.\n"
js += "window.CDTE = " + json.dumps(data, separators=(",", ":"), ensure_ascii=False) + ";\n"
(OUT / "data.js").write_text(js)
(OUT / "cliff.json").write_text(json.dumps(cliff, separators=(",", ":")))
print("wrote", OUT / "data.js", len(js), "bytes;", OUT / "cliff.json", (OUT / "cliff.json").stat().st_size, "bytes")
print("design", design)
print("fluct spike", fluct["spike"], "ref", ref)

# ------------------------------------------------------------------ social preview (1280x640)
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

BG, INK, MUT, CY, GR, OR = "#0b1220", "#e6edf3", "#8b98a9", "#22d3ee", "#34d399", "#f97316"
fig = plt.figure(figsize=(12.8, 6.4), dpi=100, facecolor=BG)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1280); ax.set_ylim(640, 0); ax.axis("off"); ax.set_facecolor(BG)
render = OUT / "hero_dark.webp"
if render.exists():  # the 3D hero, captured by docs/tools/page_qa.py --hero, on the right half with a fade into the text side
    from PIL import Image
    img = np.asarray(Image.open(render).convert("RGB")) / 255.0
    h, w = img.shape[:2]
    tw = 840; th = int(h * tw / w); y0 = (640 - th) // 2 + 20
    ax.imshow(img, extent=(1280 - tw, 1280, y0 + th, y0), zorder=0, interpolation="lanczos")
    bg = np.array([0x0b, 0x12, 0x20]) / 255
    fade = lambda n, flip=False: np.dstack([np.full((1, n, 3), bg), (np.linspace(0, 1, n) if flip else np.linspace(1, 0, n))[None, :, None]])
    ax.imshow(fade(256), extent=(1280 - tw, 1280 - tw + 360, y0 + th, y0), zorder=1)                      # left edge into the text
    ax.imshow(fade(64).transpose(1, 0, 2), extent=(1280 - tw, 1280, y0 + 60, y0), zorder=1)              # top edge
    ax.imshow(fade(64, True).transpose(1, 0, 2), extent=(1280 - tw, 1280, y0 + th, y0 + th - 60), zorder=1)  # bottom edge
kw = dict(family="DejaVu Sans", zorder=3)
ax.text(64, 92, "CdTe DEVICE MODELLING  ·  SCAPS-1D + NIST SESAME + DFT", color="#a78bfa", fontsize=13, fontweight="bold", **kw)
ax.text(64, 168, "A passivated cliff,", color=INK, fontsize=44, fontweight="bold", **kw)
ax.text(64, 230, "not a spike.", color=INK, fontsize=44, fontweight="bold", **kw)
ax.text(64, 276, "Calibrated, cross-validated model of the", color=MUT, fontsize=15, **kw)
ax.text(64, 300, "21.4 % ZnO/CdSeTe/CdTe solar cell", color=MUT, fontsize=15, **kw)
stats = [(f"Δχ² ≥ {fluct['spike_min']:.0f}", "published +0.10 eV spike, excluded"), ("−0.30 eV", "best-fit cliff, S ≈ 5 cm/s"),
         (f"{design['cons']:.1f} %", "design, in SCAPS and Sesame"), ("≈ 1 mV", "SCAPS–Sesame agreement")]
for i, (big, small) in enumerate(stats):
    x, y = 64 + (i % 2) * 300, 372 + (i // 2) * 92
    ax.text(x, y, big, color=CY, fontsize=26, fontweight="bold", **kw)
    ax.text(x, y + 28, small, color=MUT, fontsize=11, **kw)
ax.text(64, 590, "soham-cheme.github.io/CdTe-Solar-Cell-Device-Model", color="#5b6676", fontsize=12, **kw)
fig.savefig(OUT / "social-preview.png", facecolor=BG)
print("wrote", OUT / "social-preview.png", "(with hero render)" if render.exists() else "(no hero render yet)")
