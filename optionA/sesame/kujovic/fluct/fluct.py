"""Can absorber band-gap fluctuations mimic the cliff + back-barrier signature in the Kujovic cell's Voc(T)?

Parallel-domain (multi-diode) model after Grabitz, Rau & Werner 2005: the 1D cell (ident model: interface states
ZnO-CB <-> absorber-VB, dead FTO, bulk tau 100 ns, stored front Fi_m 4.10 eV, metal fixed in absolute energy) is
simulated with the whole absorber gap shifted by delta (split f_cb 0.5; buffer/IL offsets follow the shifted edges;
absorption shifted with the gap). Domain J-V curves are combined with Gaussian weights of width sigma.

Domains are simulated on a fixed delta grid (DELTAS) and combined in post-processing: each domain's J = Jsc - Jd(V);
ln Jd and Jsc are interpolated linearly in delta onto a fine grid (5 meV) and summed with normalised Gaussian
weights. This (a) lets sigma vary continuously without new runs and (b) integrates the low-gap tail that dominates
the dark current more accurately than 7-point Gauss-Hermite (also reported as a check). Light-intensity factor X:
superposition, Voc(X) solves Jd_total(V) = X Jsc_total.

  python fluct.py run A|B|C   simulate at 1 sun (resumable; one CSV per combo and temperature, written atomically)
  python fluct.py half A|B|C  the same domains at 0.5 sun near Voc (light-factor slope m(T), as in ident)
  python fluct.py analyze      -> fluct_scores.csv, fluct_profile.csv, fluct_summary.csv, fluct_*.png
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
KJ = HERE.parent
sys.path.insert(0, str(KJ)); sys.path.insert(0, str(KJ.parent))
import kj_sesame as kj  # noqa: E402
import sesame_cell as sc  # noqa: E402

REPO = kj.REPO
CURVES = HERE / "curves"
TEMPS = [216, 248, 282, 298, 316, 336, 355, 300]          # 7 for Voc(T) + the 300 K 1-sun J-V
DELTAS = [-0.30, -0.24, -0.18, -0.12, -0.06, 0.0, 0.06, 0.12, 0.18, 0.30]
TAU, NT_BULK, DEGDT, VBM0 = 100e-9, 5e11, -4e-4, 5.81
RAMPS = [None, [1e-3, 1e-2, 0.1, 0.3, 1.0], [1.0]]
MEAS = np.array([[float(r["T_K"]), float(r["Voc_V"])] for r in csv.DictReader(open(REPO / "data/kujovic_family/curves/S1_fig3d_Voc_vs_T.csv"))])
SIG_VT, SIG_VOC, SIG_FF, VOC_1SUN, FF_1SUN = 0.004, 8.0, 1.5, 875.5, 80.48
PRIOR = (0.052, 0.008)                                     # Kuciauskas 2023: sigma 52 +- 8 meV
DEC_B = [-0.54, -0.50, -0.46, -0.42, -0.38, -0.34, -0.30, -0.26, -0.22, -0.14, -0.06, 0.06]   # -0.38 .. -0.54 added: the sigma-free optimum kept moving to the deep edge
# back-contact trade-off reference points (stage C): the sigma-free best on the original grid (-0.34 eV, sigma 15 meV,
# XPS-compatible) and the deep-cliff branch best found after extending the grid (-0.46 eV, sigma 60 meV)
REF_POINTS = [(-0.34, 1.8323144223712118)]   # the -0.46 eV reference was dropped unrun (coordinator: stop extending)
BACKS_C = ("ohm", "b0.45", "b0.50", "b0.55")


def ridge_logS(dEc):
    rp = {float(r["dEc"]): float(r["logS"]) for r in csv.DictReader(open(KJ / "ident/ridge_points.csv"))}
    ks = sorted(rp)
    if dEc < ks[0]:                                        # linear extrapolation beyond the deepest ident ridge point
        return float(rp[ks[0]] + (dEc - ks[0]) * (rp[ks[1]] - rp[ks[0]]) / (ks[1] - ks[0]))
    return float(np.interp(dEc, ks, [rp[k] for k in ks]))


def scan_center(dEc):
    """log10 S at the centre of the +-0.5 decade S scan: the ident ridge, shifted up 0.3 decade beyond -0.47 eV because
    the sigma-free optimum at -0.46 eV already sat 0.3 decade above the extrapolated ridge."""
    return round(ridge_logS(dEc) + (0.3 if dEc < -0.47 else 0.0), 3)


def combos(stage):
    if stage == "A":
        return [(back, 0.10, S) for back in ("ohm", "b0.50") for S in (1e3, 1e4)]
    if stage == "B":
        base = [("b0.50", d, scan_center(d)) for d in DEC_B]
        out = [(b, d, 10 ** l) for b, d, l in base]
        out += [(b, d, 10 ** (l + o)) for b, d, l in base for o in (-0.5, 0.5)]
        return out
    if stage == "C":                                       # back-contact trade-off at the fixed reference points
        return [(back, d, S) for d, S in REF_POINTS for back in BACKS_C]
    raise KeyError(stage)


def ctag(back, dEc, S):
    return f"{back}_dEc{dEc:+.2f}_lS{math.log10(S):.3f}".replace("+", "p").replace("-", "m")


# ------------------------------------------------------------------ defs and cells
def make_def(back, dEc, T, delta):
    name = f"F_{back}_dEc{dEc:+.2f}_T{T}_d{delta:+.3f}".replace("+", "p").replace("-", "m")
    path = HERE / "defs" / f"{name}.def"
    if path.exists():
        return path
    sys.path.insert(0, str(REPO / "optionA")); sys.path.insert(0, str(REPO / "scripts"))
    import scaps_tools
    import kujovic_model as k
    (HERE / "defs").mkdir(exist_ok=True)
    scaps_tools.DEFS = HERE / "defs"
    k.ABS = KJ / "absorption"
    p, r = dict(k.AUTH), dict(k.RECON)
    p.update(tau=TAU, Nt_bulk=NT_BULK, dEc=dEc)
    dt = DEGDT * (T - 300.0) + delta                       # temperature shift + domain gap shift
    p["Eg_back"] += dt; p["Eg_front"] += dt
    r["VBM_abs"] = VBM0 + 0.5 * dt                         # f_cb 0.5
    if back == "ohm":
        r["back"] = "flatband"
    else:
        phi_metal = VBM0 - float(back[1:])                 # metal fixed in absolute energy (barrier at 300 K, delta 0)
        r["back"] = r["VBM_abs"] - phi_metal
    k.build(p, r, name=name)
    return path


def make_cell(back, dEc, S, T, delta):
    layers, contacts = kj.parse_def(make_def(back, dEc, T, delta))
    assert [L["name"] for L in layers] == ["FTO", "ZnO", "IL", "abs3", "abs2", "abs1", "abs0"]
    layers[2]["tau"] = layers[3]["tau"]                    # IL: bulk only; S on the interface states
    layers[0]["tau"] = layers[1]["tau"] = 1e-12            # dead FTO and ZnO (as in calib2/ident)
    cell = kj.build_cell(layers, contacts, float(T))
    sc.add_interface_defect(cell, S, k_front=1)
    return cell


def sweep(back, dEc, S, T, delta, dV, V_max, stop_after):
    for ramp in RAMPS:
        cell = make_cell(back, dEc, S, T, delta)
        jv = sc.run_jv(cell, dV=dV, tol=1e-8, time_limit=900, ramp=ramp, V_max=V_max, stop_after_voc=stop_after, keep=())
        if len(jv.V) > 3:
            break
    return jv


def write_csv(path, rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader()
        w.writerows([{k: (f"{v:.7g}" if isinstance(v, float) else v) for k, v in r.items()} for r in rows])
    tmp.replace(path)


def run_combo_T(back, dEc, S, T):
    out = CURVES / f"{ctag(back, dEc, S)}_T{T}.csv"
    if out.exists():
        return
    dV = 0.02 if T == 300 else 0.03
    rows = []
    jv0 = sweep(back, dEc, S, T, 0.0, dV, 1.6, 6)
    m0 = sc.jv_metrics(jv0.V, jv0.J, 0.0)
    vcap = (m0["Voc"] / 1000 if np.isfinite(m0["Voc"]) else 1.2) + 0.15
    for delta in DELTAS:
        jv = jv0 if delta == 0.0 else sweep(back, dEc, S, T, delta, dV, vcap, 10 ** 6)
        rows += [dict(back=back, dEc=dEc, S=S, T=T, delta=delta, status=jv.note, V=v, J=j) for v, j in zip(jv.V, jv.J)]
        if not len(jv.V):
            rows.append(dict(back=back, dEc=dEc, S=S, T=T, delta=delta, status=jv.note, V="", J=""))
    write_csv(out, rows)
    bad = sorted({r["delta"] for r in rows if r["status"] != "ok"})
    print(f"{ctag(back, dEc, S)} T{T}: Voc0 {m0['Voc']:.1f}  domains not fully swept: {bad}", flush=True)


def run_combo_T_half(back, dEc, S, T, X=0.5):
    """Domain J-V at X suns over the window where the composite Voc(X) can lie (for the light-factor slope m(T)).
    Superposition (Jd independent of light) fails for the back-barrier cells, so X is simulated directly."""
    out = CURVES / f"{ctag(back, dEc, S)}_T{T}_X{X}.csv"
    if out.exists():
        return
    dom = load_domains(back, dEc, S, T)
    V0, J0 = dom[0.0]
    m0 = sc.jv_metrics(V0, J0, 0.0)
    voc0 = m0["Voc"] / 1000 if np.isfinite(m0["Voc"]) else float(V0[-1]) - 0.15
    vlist = [0.2, 0.4] + [round(v, 4) for v in np.arange(max(0.5, voc0 - 0.42), voc0 + 0.0601, 0.025)]
    rows = []
    for delta in DELTAS:
        for ramp in RAMPS:
            cell = make_cell(back, dEc, S, T, delta)
            cell.g_full = cell.g_full * X; cell.system.g = cell.g_full.copy()
            jv = sc.run_jv(cell, tol=1e-8, time_limit=900, ramp=ramp, V_max=vlist[-1], stop_after_voc=10 ** 6, keep=(), vlist=vlist)
            if len(jv.V) > 3:
                break
        rows += [dict(back=back, dEc=dEc, S=S, T=T, X=X, delta=delta, status=jv.note, V=v, J=j) for v, j in zip(jv.V, jv.J)]
    write_csv(out, rows)
    print(f"{ctag(back, dEc, S)} T{T} X{X}: done", flush=True)


def run_half(stage):
    for c in combos(stage):
        for T in TEMPS[:7]:
            run_combo_T_half(*c, T)


def run(stage):
    CURVES.mkdir(exist_ok=True)
    cs = combos(stage)
    if stage == "B":                                       # ridge points first, then the +-0.5 decade S neighbours
        cs = cs[:len(DEC_B)] + cs[len(DEC_B):]
    for c in cs:
        for T in TEMPS:
            run_combo_T(*c, T)


# ------------------------------------------------------------------ composite (parallel domains)
FINE = np.round(np.arange(-0.30, 0.3001, 0.005), 4)


def load_domains(back, dEc, S, T, X=None):
    f = CURVES / (f"{ctag(back, dEc, S)}_T{T}.csv" if X is None else f"{ctag(back, dEc, S)}_T{T}_X{X}.csv")
    if not f.exists():
        return None
    d = {}
    for r in csv.DictReader(open(f)):
        if r["V"] == "":
            continue
        d.setdefault(float(r["delta"]), ([], []))
        d[float(r["delta"])][0].append(float(r["V"])); d[float(r["delta"])][1].append(float(r["J"]))
    return {k: (np.array(v[0]), np.array(v[1])) for k, v in d.items()}


def lnJd_on(V, J, Vg):
    """ln of the dark-like current Jd = Jsc - J on grid Vg; linear in V where Jd is resolved, linear extrapolation of
    ln Jd beyond the last simulated point (exponential diode branch); tiny floor below the resolved range."""
    jsc = J[0]
    jd = jsc - J
    ok = jd > 1e-6 * max(abs(jsc), 1e-3)
    if ok.sum() < 3:
        return jsc, np.full_like(Vg, -30.0)
    Vk, Lk = V[ok], np.log(jd[ok])
    out = np.interp(Vg, Vk, Lk, left=-30.0)
    hi = Vg > Vk[-1]
    if hi.any():
        s = np.polyfit(Vk[-3:], Lk[-3:], 1)[0]
        out[hi] = Lk[-1] + max(s, 0.0) * (Vg[hi] - Vk[-1])
    lo = Vg < Vk[0]
    out[lo] = np.minimum(out[lo], Lk[0])
    return jsc, out


def domain_table(dom, Vg):
    ds = sorted(dom)
    JSC, L = [], []
    for dl in ds:
        jsc, lj = lnJd_on(*dom[dl], Vg)
        JSC.append(jsc); L.append(lj)
    return np.array(ds), np.array(JSC), np.array(L)


def composite(ds, JSC, L, sigma, gh=False):
    """Total Jsc and Jd(V) for Gaussian gap disorder sigma (eV)."""
    if sigma <= 0:
        i0 = int(np.argmin(np.abs(ds)))
        return JSC[i0], np.exp(L[i0])
    if gh:                                                 # 7-point Gauss-Hermite (probabilists'), nodes +-3.75 sigma
        x, w = np.polynomial.hermite_e.hermegauss(7); w = w / w.sum()
        dl = np.clip(sigma * x, ds.min(), ds.max())
    else:
        dl = FINE[(FINE >= max(ds.min(), -4.5 * sigma)) & (FINE <= min(ds.max(), 4.5 * sigma))]
        w = np.exp(-0.5 * (dl / sigma) ** 2); w /= w.sum()
    jsc = np.interp(dl, ds, JSC)
    Lf = np.array([np.interp(dl, ds, L[:, j]) for j in range(L.shape[1])]).T     # (n_delta, n_V)
    return float((w * jsc).sum()), (w[:, None] * np.exp(Lf)).sum(0)


def voc_of(Vg, Jd, target):
    """V where Jd(V) = target (Jd increasing)."""
    lt = np.log(max(target, 1e-12)); lj = np.log(np.maximum(Jd, 1e-300))
    i = int(np.argmax(lj >= lt))
    if i == 0:
        return float("nan")
    return float(Vg[i - 1] + (Vg[i] - Vg[i - 1]) * (lt - lj[i - 1]) / (lj[i] - lj[i - 1]))


LNX = np.linspace(math.log(0.05), math.log(5.0), 121)


def curve_outputs(back, dEc, S, sigma, gh=False):
    """Voc(T, X) for the 7 temperatures and X grid, plus 300 K 1-sun Voc/FF/eta for the composite."""
    Vg = np.arange(0.0, 1.75, 0.001)
    VX = np.full((7, len(LNX)), np.nan)
    for it, T in enumerate(TEMPS[:7]):
        dom = load_domains(back, dEc, S, T)
        if dom is None:
            return None
        jsc, jd = composite(*domain_table(dom, Vg), sigma, gh)
        VX[it] = [voc_of(Vg, jd, math.exp(x) * jsc) for x in LNX]
    dom = load_domains(back, dEc, S, 300)
    if dom is None:
        return None
    jsc, jd = composite(*domain_table(dom, Vg), sigma, gh)
    m = sc.jv_metrics(Vg, jsc - jd, 0.0)
    return dict(VX=VX, Voc300=m["Voc"], FF300=m["FF"], eta300=m["eta"], Jsc300=jsc)


def chi2_of(out, prior=False, sigma=None):
    T7 = np.array(TEMPS[:7], float)
    best = None
    for j, x in enumerate(LNX):
        v = out["VX"][:, j]
        if not np.isfinite(v).all():
            continue
        model = PchipInterpolator(T7, v, extrapolate=True)(MEAS[:, 0])
        c = float((((MEAS[:, 1] - model) / SIG_VT) ** 2).sum())
        if best is None or c < best[0]:
            best = (c, math.exp(x), v)
    if best is None:
        return None
    cv = ((out["Voc300"] - VOC_1SUN) / SIG_VOC) ** 2; cf = ((out["FF300"] - FF_1SUN) / SIG_FF) ** 2
    cp = ((sigma - PRIOR[0]) / PRIOR[1]) ** 2 if prior else 0.0
    v1 = out["VX"][:, int(np.argmin(np.abs(LNX)))]
    hi = np.polyfit(T7[4:], v1[4:], 1); lo = np.polyfit(T7[:2], v1[:2], 1)
    return dict(chi2=best[0] + cv + cf + cp, chi2_VocT=best[0], chi2_Voc=cv, chi2_FF=cf, chi2_prior=cp, X=best[1],
                Voc300=out["Voc300"], FF300=out["FF300"], eta300=out["eta300"],
                slope_hi_mVK=1000 * hi[0], intercept_eV=hi[1], slope_lo_mVK=1000 * lo[0], Voc298_1sun=1000 * v1[3])


def json_best():
    f = HERE / "best_B.csv"
    if not f.exists():
        return None
    r = list(csv.DictReader(open(f)))[0]
    return dict(dEc=float(r["dEc"]), S=float(r["S"]))


if __name__ == "__main__":
    if sys.argv[1] == "run":
        run(sys.argv[2])
    elif sys.argv[1] == "half":
        run_half(sys.argv[2])
    elif sys.argv[1] == "analyze":
        import fluct_analysis
        fluct_analysis.main()
