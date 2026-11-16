"""Voc(T) calibration of the rebuilt Kujovic 21.4% cell: back barrier x front offset x interface S.

Front recombination: interface states coupling the ZnO conduction band to the absorber valence band
(sesame_cell.add_interface_defect); the IL keeps only the bulk tau (10 ns). Front contact: stored Fi_m 4.10 eV
(SCAPS's rule, see ../README.md). Everything else as K_c_graded_flat. Back metal fixed in absolute energy at
VBM(300 K) - phi_b. Defs come from optionA/kujovic_vocT.build_T, redirected into ./defs and ../absorption.

Stages (each resumable; a curve is skipped when its CSV exists):
  python calibrate.py grid        36 curves: 11 temperatures at 1 sun and 0.5 sun, plus a 300 K 1-sun J-V
  python calibrate.py ext         extension: S 1e1 and 1e2 for dEc -0.10/-0.22/-0.32 (lower S than requested)
  python calibrate.py score       -> calib_scores.csv, calib_vocT_top.png
  python calibrate.py sens        top 3 with dEgdT -3e-4 and -4.5e-4
  python calibrate.py xcheck      top 3 rerun at the fitted light-intensity factor (checks the ln X linearisation)
  python calibrate.py dead        best candidate with FTO and ZnO tau 1e-12 s: J-V and EQE
"""
import csv
import itertools
import math
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np

HERE = Path(__file__).resolve().parent
KJ = HERE.parent
sys.path.insert(0, str(KJ)); sys.path.insert(0, str(KJ.parent))
import kj_sesame as kj  # noqa: E402
import sesame_cell as sc  # noqa: E402

REPO = kj.REPO
CURVES = HERE / "curves"
TEMPS = [216, 232, 248, 265, 282, 298, 316, 326, 336, 345, 355]
PHI = [0.45, 0.50, 0.55]
DEC = [0.10, -0.10, -0.22, -0.32]
SF = [1e3, 1e4, 1e5]
MEAS = np.array([[float(r["T_K"]), float(r["Voc_V"])] for r in csv.DictReader(open(REPO / "data/kujovic_family/curves/S1_fig3d_Voc_vs_T.csv"))])
J1SUN = dict(Voc=875.5, Jsc=30.43, FF=80.48, eta=21.44)
RAMPS = [None, [1e-3, 1e-2, 0.1, 0.3, 1.0], [1.0]]
VGRID = np.round(np.arange(0, 1.6001, 0.02), 6)


def tag(phi, dEc, S, dEgdT=-4e-4):
    t = f"phi{phi:.2f}_dEc{dEc:+.2f}_S{S:.0e}".replace("+", "p").replace("-", "m")
    return t if dEgdT == -4e-4 else t + f"_dEgdT{dEgdT:.1e}".replace("-", "m")


def make_def(phi, dEc, T, dEgdT=-4e-4):
    """Def for (phi_b, dEc, T) with kujovic_vocT.build_T; S is not in the def (it goes on the interface states)."""
    name = f"C_phi{phi:.2f}_dEc{dEc:+.2f}_g{-dEgdT * 1e4:.1f}_T{T}".replace("+", "p").replace("-", "m").replace(".", "p")
    path = HERE / "defs" / f"{name}.def"
    if path.exists():
        return path
    sys.path.insert(0, str(REPO / "optionA")); sys.path.insert(0, str(REPO / "scripts"))
    import scaps_tools
    import kujovic_model as k
    import kujovic_vocT as kv
    (HERE / "defs").mkdir(exist_ok=True); (KJ / "absorption").mkdir(exist_ok=True)
    scaps_tools.DEFS = HERE / "defs"
    k.ABS = KJ / "absorption"
    p, r = dict(k.AUTH), dict(k.RECON)          # RECON: graded, no window defects (= K_c_graded_*)
    p["dEc"] = dEc
    r["back"] = phi
    extra = {"dEgdT": dEgdT, "f_cb": 0.5, "phi_back": r["VBM_abs"] - phi}
    kv.build_T(p, r, extra, T, name)
    return path


def make_cell(phi, dEc, S, T, dEgdT=-4e-4, dead_window=False):
    layers, contacts = kj.parse_def(make_def(phi, dEc, T, dEgdT))
    assert [L["name"] for L in layers] == ["FTO", "ZnO", "IL", "abs3", "abs2", "abs1", "abs0"]
    layers[2]["tau"] = layers[3]["tau"]         # IL: bulk 10 ns only; S goes on the interface states
    if dead_window:
        layers[0]["tau"] = layers[1]["tau"] = 1e-12
    cell = kj.build_cell(layers, contacts, float(T))
    sc.add_interface_defect(cell, S, k_front=1)
    return cell


def voc_at(cell, jv, X):
    """Voc at intensity X (x 1 sun), starting from the stored 1-sun solution just below Voc(1)."""
    s = cell.system
    vt = s.scaling.energy
    vR = cell.v_eq[-1]
    Vs = sorted(v for v in jv.sols if v < jv.voc1)
    if not Vs:
        return float("nan")
    V = Vs[-1]
    sol = sc._copy(jv.sols[V])
    solver = sc._IFSolver(cell); solver.equilibrium = cell.v_eq
    for f in (0.75, X) if X < 0.75 else (X,):    # intensity step at fixed V
        s.g = cell.g_full * f
        g = sc._copy(sol); g["v"][-1] = vR + V / vt
        new = solver.solve(s, compute="all", guess=g, tol=1e-8, maxiter=80, verbose=False)
        if new is None:
            s.g = cell.g_full.copy(); return float("nan")
        sol = new
    J = sc.currents(cell, sol)["J"]
    prevV, prevJ = V, J
    step = -0.01 if J < 0 else 0.01
    for _ in range(40):
        V2 = round(prevV + step, 6)
        g = sc._copy(sol); g["v"][-1] = vR + V2 / vt
        new = solver.solve(s, compute="all", guess=g, tol=1e-8, maxiter=80, verbose=False)
        if new is None:
            break
        sol = new
        J2 = sc.currents(cell, sol)["J"]
        if (J2 > 0) != (prevJ > 0):
            s.g = cell.g_full.copy()
            return prevV + (V2 - prevV) * prevJ / (prevJ - J2)
        prevV, prevJ = V2, J2
    s.g = cell.g_full.copy()
    return float("nan")


def run_point(phi, dEc, S, T, dEgdT=-4e-4, X2=0.5, dV=0.02, intensity=1.0):
    for i_r, ramp in enumerate(RAMPS):
        cell = make_cell(phi, dEc, S, T, dEgdT)
        if intensity != 1.0:
            cell.g_full = cell.g_full * intensity; cell.system.g = cell.g_full.copy()
        jv = sc.run_jv(cell, dV=dV, tol=1e-8, keep=tuple(VGRID), time_limit=900, ramp=ramp, V_max=1.6)
        if jv.ok:
            break
    if not jv.ok:
        return dict(T_K=T, status=jv.note, ramp_variant=i_r, Voc1=float("nan"), Voc2=float("nan"), m_V=float("nan"),
                    Jsc=float("nan"), FF=float("nan"), seconds=round(jv.seconds, 1))
    m = sc.jv_metrics(jv.V, jv.J, 0.0)
    jv.voc1 = m["Voc"] / 1000
    v2 = voc_at(cell, jv, X2) if X2 else float("nan")
    return dict(T_K=T, status="ok", ramp_variant=i_r, Voc1=jv.voc1, Voc2=v2, m_V=(jv.voc1 - v2) / math.log(1 / X2) if X2 else float("nan"),
                Jsc=m["Jsc"], FF=m["FF"], seconds=round(jv.seconds, 1))


def write_csv(path, rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader()
        w.writerows([{k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in r.items()} for r in rows])
    tmp.replace(path)                            # atomic: a power cut never leaves a half-written curve


def run_curve(phi, dEc, S, dEgdT=-4e-4, intensity=1.0, suffix=""):
    t = tag(phi, dEc, S, dEgdT) + suffix
    out = CURVES / f"{t}_vocT.csv"
    if out.exists():
        return
    t0 = time.time()
    rows = [dict(phi_b=phi, dEc=dEc, S=S, dEgdT=dEgdT, intensity=intensity,
                 **run_point(phi, dEc, S, T, dEgdT, X2=0.5 if intensity == 1.0 else None, intensity=intensity)) for T in TEMPS]
    write_csv(out, rows)
    print(f"{t}: {sum(r['status'] == 'ok' for r in rows)}/11 ok, {time.time() - t0:.0f} s, Voc(298) {rows[5]['Voc1']:.4f}", flush=True)


def run_jv300(phi, dEc, S):
    t = tag(phi, dEc, S)
    out = CURVES / f"{t}_jv300.csv"
    if out.exists():
        return
    for ramp in RAMPS:
        cell = make_cell(phi, dEc, S, 300)
        jv = sc.run_jv(cell, dV=0.01, tol=1e-8, time_limit=900, ramp=ramp, V_max=1.6)
        if jv.ok:
            break
    m = sc.jv_metrics(jv.V, jv.J, 0.0) if jv.ok else {k: float("nan") for k in ("Voc", "Jsc", "FF", "eta")}
    rows = [dict(phi_b=phi, dEc=dEc, S=S, status=jv.note, Voc=m["Voc"], Jsc=m["Jsc"], FF=m["FF"], eta=m["eta"], V=v, J=j)
            for v, j in zip(jv.V, jv.J)] or [dict(phi_b=phi, dEc=dEc, S=S, status=jv.note)]
    write_csv(out, rows)


def grid():
    CURVES.mkdir(exist_ok=True)
    for phi, dEc, S in itertools.product(PHI, DEC, SF):
        run_jv300(phi, dEc, S)
        run_curve(phi, dEc, S)


# ------------------------------------------------------------------ scoring
def load_curve(path):
    d = list(csv.DictReader(open(path)))
    T = np.array([float(r["T_K"]) for r in d])
    V1 = np.array([float(r["Voc1"]) for r in d]); V2 = np.array([float(r["Voc2"]) if r["Voc2"] not in ("", "nan") else np.nan for r in d])
    mV = np.array([float(r["m_V"]) if r.get("m_V") not in (None, "", "nan") else np.nan for r in d])
    return T, V1, V2, mV


def linfit(T, V, lo, hi):
    m = (T >= lo) & (T <= hi) & np.isfinite(V)
    return tuple(np.polyfit(T[m], V[m], 1)) if m.sum() >= 2 else (np.nan, np.nan)


def score_curve(T, V1, mV):
    ok = np.isfinite(V1)
    model = np.interp(MEAS[:, 0], T[ok], V1[ok])
    res = MEAS[:, 1] - model
    c = res.mean()
    rms_i = float(np.sqrt(np.mean((res - c) ** 2)))
    out = dict(rms_shape_mV=1000 * rms_i, offset_mV=1000 * c)
    if np.isfinite(mV).sum() == len(mV):
        mm = np.interp(MEAS[:, 0], T, mV)
        lnX = np.linspace(math.log(0.02), math.log(5), 2001)
        r = np.array([np.sqrt(np.mean((MEAS[:, 1] - (model + mm * x)) ** 2)) for x in lnX])
        k = int(np.argmin(r))
        out.update(rms_intensity_mV=1000 * float(r[k]), X_fit=float(math.exp(lnX[k])))
    s_hi, b_hi = linfit(T, V1, 315, 356); s_lo, _ = linfit(T, V1, 215, 249)
    out.update(slope_hi_mVK=1000 * s_hi, intercept_eV=b_hi, slope_lo_mVK=1000 * s_lo, Voc298_mV=1000 * float(np.interp(298, T[ok], V1[ok])))
    return out


EXT_S = [1e1, 1e2]          # extension: lower interface S for the measured cliffs (not in the requested grid)


def ext():
    for phi, dEc, S in itertools.product(PHI, [-0.10, -0.22, -0.32], EXT_S):
        run_jv300(phi, dEc, S)
        run_curve(phi, dEc, S)


def score():
    rows = []
    combos = list(itertools.product(PHI, DEC, SF)) + list(itertools.product(PHI, [-0.10, -0.22, -0.32], EXT_S))
    for phi, dEc, S in combos:
        t = tag(phi, dEc, S)
        f, g = CURVES / f"{t}_vocT.csv", CURVES / f"{t}_jv300.csv"
        if not (f.exists() and g.exists()):
            continue
        T, V1, V2, mV = load_curve(f)
        j = list(csv.DictReader(open(g)))[0]
        r = dict(tag=t, phi_b=phi, dEc=dEc, S=S, n_ok=int(np.isfinite(V1).sum()), **score_curve(T, V1, mV),
                 Voc300=float(j["Voc"]), Jsc300=float(j["Jsc"]), FF300=float(j["FF"]), eta300=float(j["eta"]))
        r["dVoc300_vs_JV"] = r["Voc300"] - J1SUN["Voc"]
        r["passes_1sun"] = bool(r["FF300"] >= 78 and abs(r["dVoc300_vs_JV"]) <= 20)
        r["in_requested_grid"] = S in SF
        rows.append(r)
    ms = score_measured()
    # rank: 1-sun criteria first, then a plausible JVT offset (|offset| <= 60 mV; the JVT/J-V gap itself is 25 mV),
    # then the shape rms. No curve passes the 1-sun criteria, so in practice: plausible offset, then shape.
    for r in rows:
        r["plausible_offset"] = bool(abs(r["offset_mV"]) <= 60)
    rows.sort(key=lambda r: (not r["passes_1sun"], not r["plausible_offset"], r["rms_shape_mV"]))
    for i, r in enumerate(rows):
        r["rank"] = i + 1
    write_csv(HERE / "calib_scores.csv", rows)
    print("measured:", {k: round(v, 3) for k, v in ms.items()})
    for r in rows[:12]:
        print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})
    plot_top(rows)
    return rows


def score_measured():
    s_hi, b_hi = linfit(MEAS[:, 0], MEAS[:, 1], 315, 356); s_lo, _ = linfit(MEAS[:, 0], MEAS[:, 1], 215, 249)
    return dict(slope_hi_mVK=1000 * s_hi, intercept_eV=b_hi, slope_lo_mVK=1000 * s_lo, Voc298_mV=1000 * float(np.interp(298, MEAS[:, 0], MEAS[:, 1])))


def top(n=3):
    return [r for r in csv.DictReader(open(HERE / "calib_scores.csv"))][:n]


SENS_EXTRA = "phi0.55_dEcm0.22_S1ep02"     # best intercept match (1.364 eV) among plausible offsets, added to the top 3


def sens_set():
    rows = list(csv.DictReader(open(HERE / "calib_scores.csv")))
    return top(3) + [r for r in rows if r["tag"] == SENS_EXTRA and r["tag"] not in [t["tag"] for t in top(3)]]


def sens():
    for r in sens_set():
        for g in (-3e-4, -4.5e-4):
            run_curve(float(r["phi_b"]), float(r["dEc"]), float(r["S"]), dEgdT=g)
    rows = []
    for r in sens_set():
        for g in (-3e-4, -4e-4, -4.5e-4):
            T, V1, V2, mV = load_curve(CURVES / f"{tag(float(r['phi_b']), float(r['dEc']), float(r['S']), g)}_vocT.csv")
            rows.append(dict(tag=r["tag"], dEgdT=g, **score_curve(T, V1, mV)))
            print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in rows[-1].items()})
    write_csv(HERE / "calib_dEgdT_sensitivity.csv", rows)


def xcheck():
    rows = []
    for r in top(3):
        X = float(r["X_fit"])
        run_curve(float(r["phi_b"]), float(r["dEc"]), float(r["S"]), intensity=X, suffix=f"_X{X:.3f}")
        T, V1, _, _ = load_curve(CURVES / f"{r['tag']}_X{X:.3f}_vocT.csv")
        model = np.interp(MEAS[:, 0], T, V1)
        rms = float(np.sqrt(np.mean((MEAS[:, 1] - model) ** 2)))
        rows.append(dict(tag=r["tag"], X_fit=X, rms_intensity_linearised_mV=float(r["rms_intensity_mV"]), rms_intensity_direct_mV=1000 * rms,
                         Voc298_direct_mV=1000 * float(np.interp(298, T, V1))))
        print(rows[-1])
    write_csv(HERE / "calib_intensity_check.csv", rows)


def dead():
    r = top(1)[0]
    phi, dEc, S = float(r["phi_b"]), float(r["dEc"]), float(r["S"])
    lams = np.arange(300, 911, 10.0)
    rows, eq = [], []
    for dw in (False, True):
        cell = make_cell(phi, dEc, S, 300, dead_window=dw)
        jv = sc.run_jv(cell, dV=0.01, tol=1e-8, keep=(0.0,), V_max=1.6)
        m = sc.jv_metrics(jv.V, jv.J, 0.0)
        cell_e = cell
        e = eqe_if(cell_e, jv.sols[0.0], lams)
        rows.append(dict(tag=r["tag"], dead_window=dw, Voc=m["Voc"], Jsc=m["Jsc"], FF=m["FF"], eta=m["eta"],
                         EQE_320=float(np.interp(320, lams, e)), EQE_350=float(np.interp(350, lams, e)), EQE_370=float(np.interp(370, lams, e)),
                         EQE_400=float(np.interp(400, lams, e))))
        eq += [dict(dead_window=dw, wavelength_nm=l_, EQE_pct=float(x)) for l_, x in zip(lams, e)]
        print(rows[-1], flush=True)
    write_csv(HERE / "calib_dead_window.csv", rows); write_csv(HERE / "calib_dead_window_eqe.csv", eq)


def eqe_if(cell, sol0, lams, flux=2e16):
    """kj.eqe with the interface-state solver."""
    s = cell.system
    J0 = sc.currents(cell, sol0)["J"]
    solver = sc._IFSolver(cell); solver.equilibrium = cell.v_eq
    out = []
    for lam in lams:
        s.g = cell.g_full + kj.mono_generation(cell, lam, flux) / s.scaling.generation
        new = solver.solve(s, compute="all", guess=sc._copy(sol0), tol=1e-8, maxiter=60, verbose=False)
        out.append(float("nan") if new is None else (sc.currents(cell, new)["J"] - J0) / (sc.Q * flux * 1e3) * 100)
    s.g = cell.g_full.copy()
    return np.array(out)


def plot_top(rows, n=5):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    cols = ["#2a78d6", "#eb6834", "#1baf7a", "#6250d6", "#e87ba4"]
    fig, ax = plt.subplots(1, 2, figsize=(15, 5.2))
    for a, shift in zip(ax, (True, False)):
        a.plot(MEAS[:, 0], MEAS[:, 1], "o", ms=5, mfc="white", mec="#0b0b0b", mew=1.1, label="measured (JVT)", zorder=5)
        for c, r in zip(cols, rows[:n]):
            T, V1, _, _ = load_curve(CURVES / f"{r['tag']}_vocT.csv")
            off = r["offset_mV"] / 1000 if shift else 0.0
            a.plot(T, V1 + off, "-s", ms=4, lw=1.6, color=c,
                   label=f"#{r['rank']} phi_b {r['phi_b']:.2f}, dEc {r['dEc']:+.2f}, S {r['S']:.0e}: rms {r['rms_shape_mV']:.1f} mV"
                         f" (offset {r['offset_mV']:+.0f}), 1 sun {r['Voc300']:.0f} mV / FF {r['FF300']:.1f}")
        a.set_xlabel("Temperature (K)"); a.set_ylabel("Voc (V)")
        a.grid(color="#e4e3df", lw=0.6)
        for s_ in ("top", "right"):
            a.spines[s_].set_visible(False)
    ax[0].set_title("model + best constant offset (score i)", fontsize=9, loc="left")
    ax[1].set_title("model as computed (1 sun)", fontsize=9, loc="left")
    ax[0].legend(frameon=False, fontsize=7.2, loc="lower left")
    fig.suptitle("Kujovic cell Voc(T): top 5 of the barrier x offset x interface-S grid (interface states, stored front Fi_m)", fontsize=10.5)
    fig.tight_layout(); fig.savefig(HERE / "calib_vocT_top.png", dpi=150)


if __name__ == "__main__":
    {"grid": grid, "ext": ext, "score": score, "sens": sens, "xcheck": xcheck, "dead": dead}[sys.argv[1]]()
