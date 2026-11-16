"""Sesame runs of the rebuilt Loughborough 21.4% cell (Kujovic 2024). SCAPS is not run.

  python run_kujovic.py validate  -> kujovic_validation.csv       (Step 0: K_u_backPhi581, K_u_base against SCAPS .iv)
  python run_kujovic.py configs   -> kujovic_configs.csv, kujovic_configs_jv.csv, kujovic_eqe.csv, kujovic_configs.png
  python run_kujovic.py vocT      -> kujovic_vocT.csv, kujovic_vocT_fits.csv, kujovic_vocT.png (Step B)
  python run_kujovic.py plot      -> redraw the figures from the CSVs
Defs for Voc(T) come from optionA/kujovic_vocT.build_T, redirected into ./defs and ./absorption (nothing is written
under scaps/). Optics: T_front 0.9, R_back 0.2 (SCAPS's own generation, see ../README.md). Rs = 0, as in the SCAPS runs.
"""
import csv
import os
import re
import sys
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kj_sesame as kj  # noqa: E402
import sesame_cell as sc  # noqa: E402

REPO = kj.REPO
CURVES = REPO / "data/kujovic_family/curves"
CONFIGS = ["K_c_graded_flat", "K_c_graded_bar0655", "K_c_uniform_bar0655", "K_c_uniform_flat", "K_c_graded_bar0655_win"]
AUTHORS_SCAPS = dict(Voc=872.0, Jsc=30.8, FF=79.6, eta=21.4)
MEASURED = dict(Voc=875.5, Jsc=30.43, FF=80.48, eta=21.44)
TEMPS = [216, 232, 248, 265, 282, 298, 316, 326, 336, 345, 355]
HYP = {  # label: (description, AUTH overrides, RECON 'back')
    "a": ("back barrier 0.655 eV (metal 5.155 eV)", {}, 0.655),
    "b": ("ohmic (flat-band) back", {}, "flatband"),
    "c": ("ohmic back + S_front 1e5 cm/s", {"S_front": 1e5}, "flatband"),
    "d": ("back barrier 0.655 eV + S_front 1e5 cm/s", {"S_front": 1e5}, 0.655),
    "e": ("ohmic back + front spike dEc +0.30 eV", {"dEc": 0.30}, "flatband"),
    # extra (not in the requested set): smaller back barriers, metal fixed at VBM - barrier
    "a055": ("extra: back barrier 0.55 eV", {}, 0.55),
    "a050": ("extra: back barrier 0.50 eV", {}, 0.50),
}


def read_iv(path):
    t = Path(path).read_text(encoding="latin-1").replace("\r", "")
    out = {k: float(re.search(rf"{k}\s*=\s*([-\d.eE+]+)", t).group(1)) for k in ("Voc", "Jsc", "FF", "eta")}
    out["Voc"] *= 1000
    lines = t.split("\n")
    i = next(k for k, l in enumerate(lines) if l.strip().startswith("v(V)"))
    cols = [c.strip() for c in lines[i].split("\t")]
    row0 = [float(v) for v in lines[i + 2].split()] if not lines[i + 1].split() else [float(v) for v in lines[i + 1].split()]
    out["row0"] = dict(zip(cols, row0))
    return out


RAMPS = [None, [1e-3, 1e-2, 0.1, 0.3, 1.0], [1.0]]     # default ramp, then two fallbacks for low-T starts


def run(cell, dV=0.01, keep=(0.0,), ramp=None):
    jv = sc.run_jv(cell, dV=dV, tol=1e-8, keep=keep, time_limit=1500, ramp=ramp, V_max=1.6)
    m = sc.jv_metrics(jv.V, jv.J, 0.0) if jv.ok else {k: float("nan") for k in ("Voc", "Jsc", "FF", "eta", "Vmpp", "Jmpp")}
    return jv, m


def fmt(rows):
    return [{k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in r.items()} for r in rows]


def write(name, rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(HERE / name, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(fmt(rows))


def validate():
    rows = []
    for name in ("K_u_backPhi581", "K_u_base"):
        s_iv = read_iv(REPO / f"scaps/results/{name}.iv")
        for rule in ("scaps", "ohmic"):
            layers, contacts = kj.parse_def(REPO / f"scaps/defs/{name}.def", front_rule=rule)
            cell = kj.build_cell(layers, contacts, 300.0)
            jv, m = run(cell)
            d0 = jv.detail[0]
            r0 = s_iv["row0"]
            rows.append(dict(case=name, front_contact=f"{contacts['front_type']} (Fi_m {contacts['phi_front']})" if rule == "scaps" else "Ohmic (flat band)",
                             back_contact=f"{contacts['back_type']} Fi_m {contacts['phi_back']}", status=jv.note,
                             Voc_sesame=m["Voc"], Jsc_sesame=m["Jsc"], FF_sesame=m["FF"], eta_sesame=m["eta"],
                             Voc_scaps=s_iv["Voc"], Jsc_scaps=s_iv["Jsc"], FF_scaps=s_iv["FF"], eta_scaps=s_iv["eta"],
                             dVoc_mV=m["Voc"] - s_iv["Voc"], dJsc_pct=100 * (m["Jsc"] / s_iv["Jsc"] - 1),
                             dFF=m["FF"] - s_iv["FF"], deta=m["eta"] - s_iv["eta"],
                             Jgen_sesame=d0["gen"], Jgen_scaps=r0["j_total_gen(mA/cm2)"],
                             Jrec_bulk_sesame=sum(d0["rec"].values()), Jrec_bulk_scaps=r0["jbulk(mA/cm2)"],
                             Jloss_front_sesame=d0["loss_front_minority"], Jloss_front_scaps=r0["jminor_right(mA/cm2)"],
                             Jloss_back_sesame=d0["loss_back_minority"], Jloss_back_scaps=r0["jminor_left(mA/cm2)"],
                             nodes=len(cell.x), seconds=round(jv.seconds, 1)))
            print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in rows[-1].items()}, flush=True)
    write("kujovic_validation.csv", rows)


def eqe_integral(lam, eqe_pct, lo, hi):
    """Jsc (mA/cm2) from an EQE curve with the SCAPS AM1.5G photon flux, over [lo, hi] nm."""
    sl, flux = sc.spectrum_flux()
    m = (sl >= lo) & (sl <= hi)
    return float((np.interp(sl[m], lam, eqe_pct) / 100 * flux[m]).sum() * sc.Q * 1e3)


def configs():
    meas = list(csv.DictReader(open(CURVES / "S1_fig3b_EQE.csv")))
    ml = np.array([float(r["wavelength_nm"]) for r in meas]); me = np.array([float(r["EQE_pct"]) for r in meas])
    lams = np.arange(300, 911, 10.0)
    rows, curves, eqrows = [], [], []
    for name in CONFIGS:
        layers, contacts = kj.parse_def(REPO / f"scaps/defs/{name}.def")
        cell = kj.build_cell(layers, contacts, 300.0)
        jv, m = run(cell)
        e = kj.eqe(cell, jv.sols[0.0], lams) if jv.ok else np.full(len(lams), np.nan)
        rms = float(np.sqrt(np.nanmean((np.interp(ml, lams, e) - me) ** 2)))
        rows.append(dict(config=name, front_contact=f"{contacts['front_type']} {contacts['phi_front']}",
                         back_contact=f"{contacts['back_type']} {contacts['phi_back'] if contacts['back_type'] == 'Schottky' else '(flat band)'}",
                         status=jv.note, Voc=m["Voc"], Jsc=m["Jsc"], FF=m["FF"], eta=m["eta"],
                         dVoc_vs_authors=m["Voc"] - AUTHORS_SCAPS["Voc"], dJsc_vs_authors=m["Jsc"] - AUTHORS_SCAPS["Jsc"],
                         dFF_vs_authors=m["FF"] - AUTHORS_SCAPS["FF"], deta_vs_authors=m["eta"] - AUTHORS_SCAPS["eta"],
                         dVoc_vs_measured=m["Voc"] - MEASURED["Voc"], dJsc_vs_measured=m["Jsc"] - MEASURED["Jsc"],
                         dFF_vs_measured=m["FF"] - MEASURED["FF"], deta_vs_measured=m["eta"] - MEASURED["eta"],
                         Jgen=jv.detail[0]["gen"] if jv.detail else float("nan"),
                         EQE_integral_meas_range=eqe_integral(lams, e, ml.min(), ml.max()),
                         EQE_rms_vs_measured_pct=rms, seconds=round(jv.seconds, 1)))
        for v, j in zip(jv.V, jv.J):
            curves.append(dict(config=name, V=round(v, 5), J_mAcm2=round(j, 5)))
        for l_, e_ in zip(lams, e):
            eqrows.append(dict(config=name, wavelength_nm=l_, EQE_pct=round(float(e_), 3)))
        print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in rows[-1].items()}, flush=True)
    print("measured EQE integral over", ml.min(), "-", ml.max(), "nm:", round(eqe_integral(ml, me, ml.min(), ml.max()), 2))
    write("kujovic_configs.csv", rows); write("kujovic_configs_jv.csv", curves); write("kujovic_eqe.csv", eqrows)
    plot_configs()


def build_T_defs(key, T):
    """Write the T-specific def with optionA/kujovic_vocT.build_T, redirected into ./defs and ./absorption."""
    sys.path.insert(0, str(REPO / "optionA")); sys.path.insert(0, str(REPO / "scripts"))
    import scaps_tools
    import kujovic_model as k
    import kujovic_vocT as kv
    (HERE / "defs").mkdir(exist_ok=True); (HERE / "absorption").mkdir(exist_ok=True)
    scaps_tools.DEFS = HERE / "defs"
    k.ABS = HERE / "absorption"
    desc, pov, back = HYP[key]
    p, r = dict(k.AUTH), dict(k.RECON)
    p.update(pov)
    r["back"] = back
    extra = {"dEgdT": -4.0e-4, "f_cb": 0.5, "phi_back": None}
    if back != "flatband":
        extra["phi_back"] = r["VBM_abs"] - float(back)
    name = kv.build_T(p, r, extra, T, f"K_T_{key}_{T}")
    return HERE / "defs" / f"{name}.def"


def vocT():
    rows = []
    out = HERE / "kujovic_vocT.csv"
    if out.exists():                       # resume: keep converged rows, recompute the rest
        rows = [dict(r) for r in csv.DictReader(open(out)) if r["status"] == "ok"]
    done = {(r["hyp"], int(r["T_K"])) for r in rows}
    for key in HYP:
        for T in TEMPS:
            if (key, T) in done:
                continue
            path = build_T_defs(key, T)
            layers, contacts = kj.parse_def(path)
            for i_r, ramp in enumerate(RAMPS):
                cell = kj.build_cell(layers, contacts, float(T))
                jv, m = run(cell, ramp=ramp)
                if jv.ok:
                    break
            rows.append(dict(hyp=key, description=HYP[key][0], T_K=T, status=jv.note, ramp_variant=i_r, Voc_V=m["Voc"] / 1000, Jsc=m["Jsc"],
                             FF=m["FF"], eta=m["eta"], back=f"{contacts['back_type']} {contacts['phi_back']}",
                             Eg_front=layers[2]["Eg"], Eg_back=layers[-1]["Eg"], seconds=round(jv.seconds, 1)))
            print({k_: (round(v, 4) if isinstance(v, float) else v) for k_, v in rows[-1].items()}, flush=True)
            write("kujovic_vocT.csv", sorted(rows, key=lambda r: (r["hyp"], int(r["T_K"]))))
    fits()
    plot_vocT()


def linfit(T, V, lo, hi):
    m = (T >= lo) & (T <= hi) & np.isfinite(V)
    if m.sum() < 2:
        return float("nan"), float("nan")
    s, b = np.polyfit(T[m], V[m], 1)
    return s * 1000, b


def fits():
    meas = np.array([[float(r["T_K"]), float(r["Voc_V"])] for r in csv.DictReader(open(CURVES / "S1_fig3d_Voc_vs_T.csv"))])
    rows = []
    s_hi, b_hi = linfit(meas[:, 0], meas[:, 1], 315, 356); s_lo, b_lo = linfit(meas[:, 0], meas[:, 1], 215, 249)
    rows.append(dict(hyp="measured", description="Kujovic JVT (S1 Fig. 3d)", slope_hi_mVK=s_hi, intercept_hi_eV=b_hi,
                     slope_lo_mVK=s_lo, intercept_lo_eV=b_lo, Voc_298_mV=1000 * np.interp(298, meas[:, 0], meas[:, 1]),
                     lo_over_hi_slope=s_lo / s_hi))
    data = list(csv.DictReader(open(HERE / "kujovic_vocT.csv")))
    for key in [k_ for k_ in HYP if any(r["hyp"] == k_ for r in data)]:
        d = sorted([r for r in data if r["hyp"] == key], key=lambda r: float(r["T_K"]))
        T = np.array([float(r["T_K"]) for r in d]); V = np.array([float(r["Voc_V"]) if r["Voc_V"] not in ("", "nan") else np.nan for r in d])
        s_hi, b_hi = linfit(T, V, 315, 356); s_lo, b_lo = linfit(T, V, 215, 249)
        rows.append(dict(hyp=key, description=HYP[key][0], slope_hi_mVK=s_hi, intercept_hi_eV=b_hi, slope_lo_mVK=s_lo,
                         intercept_lo_eV=b_lo, Voc_298_mV=1000 * float(np.interp(298, T[np.isfinite(V)], V[np.isfinite(V)])),
                         lo_over_hi_slope=s_lo / s_hi, n_converged=int(np.isfinite(V).sum())))
    write("kujovic_vocT_fits.csv", rows)
    for r in rows:
        print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})


def _style(ax):
    ax.grid(color="#e4e3df", lw=0.6); ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(colors="#52514e", labelsize=8)


def plot_configs():
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    cols = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
    jv = list(csv.DictReader(open(HERE / "kujovic_configs_jv.csv"))); eq = list(csv.DictReader(open(HERE / "kujovic_eqe.csv")))
    mj = list(csv.DictReader(open(CURVES / "S1_fig3a_JV_light.csv"))); me = list(csv.DictReader(open(CURVES / "S1_fig3b_EQE.csv")))
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.6))
    ax[0].plot([float(r["V_mV"]) / 1000 for r in mj], [-float(r["J_mA_cm2"]) for r in mj], "o", ms=3, mfc="white", mec="#0b0b0b", mew=0.8, label="measured 21.44% cell")
    ax[1].plot([float(r["wavelength_nm"]) for r in me], [float(r["EQE_pct"]) for r in me], "o", ms=3, mfc="white", mec="#0b0b0b", mew=0.8, label="measured")
    for c, name in zip(cols, CONFIGS):
        d = [r for r in jv if r["config"] == name]
        ax[0].plot([float(r["V"]) for r in d], [float(r["J_mAcm2"]) for r in d], color=c, lw=1.8, label=name.replace("K_c_", ""))
        e = [r for r in eq if r["config"] == name]
        ax[1].plot([float(r["wavelength_nm"]) for r in e], [float(r["EQE_pct"]) for r in e], color=c, lw=1.6, label=name.replace("K_c_", ""))
    ax[0].set_xlim(0, 0.95); ax[0].set_ylim(0, 33); ax[0].set_xlabel("Voltage (V)"); ax[0].set_ylabel("Current density (mA/cm$^2$)")
    ax[1].set_xlim(300, 920); ax[1].set_ylim(0, 100); ax[1].set_xlabel("Wavelength (nm)"); ax[1].set_ylabel("EQE (%)")
    for a in ax:
        _style(a); a.legend(frameon=False, fontsize=8)
    fig.suptitle("Rebuilt Kujovic 21.4% cell in Sesame: five SCAPS configurations (Rs 0, AM1.5G, 300 K)", fontsize=10.5)
    fig.tight_layout(); fig.savefig(HERE / "kujovic_configs.png", dpi=150)


def plot_vocT():
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    cols = {"a": "#2a78d6", "b": "#eb6834", "c": "#1baf7a", "d": "#6250d6", "e": "#e87ba4", "a055": "#8a8984", "a050": "#52514e"}
    meas = list(csv.DictReader(open(CURVES / "S1_fig3d_Voc_vs_T.csv")))
    data = list(csv.DictReader(open(HERE / "kujovic_vocT.csv")))
    fits_ = {r["hyp"]: r for r in csv.DictReader(open(HERE / "kujovic_vocT_fits.csv"))}
    fig, ax = plt.subplots(1, 2, figsize=(17, 5.0), gridspec_kw={"width_ratios": [1, 1.15]})
    for a, xlim in zip(ax, ((0, 370), (205, 365))):
        Tm = [float(r["T_K"]) for r in meas]; Vm = [float(r["Voc_V"]) for r in meas]
        a.plot(Tm, Vm, "o", ms=5, mfc="white", mec="#0b0b0b", mew=1.1, label="measured (JVT)", zorder=5)
        f = fits_["measured"]
        tt = np.linspace(0, 360, 50)
        a.plot(tt, float(f["intercept_hi_eV"]) + float(f["slope_hi_mVK"]) / 1000 * tt, color="#0b0b0b", lw=0.8, ls=":")
        for key, c in cols.items():
            d = sorted([r for r in data if r["hyp"] == key and r["Voc_V"] not in ("", "nan")], key=lambda r: float(r["T_K"]))
            if not d or key not in fits_:
                continue
            fk = fits_[key]
            a.plot([float(r["T_K"]) for r in d], [float(r["Voc_V"]) for r in d], "-" if len(key) == 1 else "--", marker="s", ms=4, color=c, lw=1.6,
                   label=f"({key}) {HYP[key][0]}: {float(fk['slope_hi_mVK']):.2f} mV/K, {float(fk['intercept_hi_eV']):.3f} eV; low-T {float(fk['slope_lo_mVK']):.2f} mV/K")
            if xlim[0] == 0:
                a.plot(tt, float(fk["intercept_hi_eV"]) + float(fk["slope_hi_mVK"]) / 1000 * tt, color=c, lw=0.7, ls=":")
        a.set_xlim(*xlim); a.set_xlabel("Temperature (K)"); a.set_ylabel("Voc (V)"); _style(a)
    ax[0].set_ylim(0.6, 1.75); ax[0].set_title("extrapolation of the 316-355 K fits to 0 K", fontsize=9, loc="left")
    ax[1].set_ylim(0.6, 1.1); ax[1].set_title("measured range", fontsize=9, loc="left")
    fm = fits_["measured"]
    ax[1].legend(frameon=False, fontsize=7.5, loc="upper left", bbox_to_anchor=(1.02, 1.0),
                 title=f"fits: 316-355 K slope, 0 K intercept; 216-248 K slope\nmeasured: {float(fm['slope_hi_mVK']):.2f} mV/K, {float(fm['intercept_hi_eV']):.3f} eV; low-T {float(fm['slope_lo_mVK']):.2f} mV/K", title_fontsize=7.5)
    fig.suptitle("Voc(T) of the rebuilt Kujovic cell in Sesame (dEg/dT -4e-4 eV/K, half in each band edge, back metal fixed)", fontsize=10.5)
    fig.tight_layout(); fig.savefig(HERE / "kujovic_vocT.png", dpi=150)


if __name__ == "__main__":
    stage = sys.argv[1]
    {"validate": validate, "configs": configs, "vocT": vocT,
     "plot": lambda: (plot_configs() if (HERE / "kujovic_configs.csv").exists() else None,
                      (fits(), plot_vocT()) if (HERE / "kujovic_vocT.csv").exists() else None)}[stage]()
