"""Does a longer bulk lifetime let the measured-cliff Voc(T) fits pass the 1-sun test? (calib2)

Same model as ../calib (interface states coupling the ZnO conduction band to the absorber valence band, stored
front Fi_m 4.10 eV, back metal fixed at VBM(300 K) - phi_b, dEg/dT -4e-4 eV/K, f_cb 0.5), plus from now on:
  * dead window: FTO and ZnO tau = 1e-12 s;
  * bulk tau (all absorber sublayers and the IL) set to tau_bulk (= changing Nt at fixed sigma).
Grid: main tau {30, 100, 300} ns x phi_b {0.50, 0.55} x dEc {-0.22, -0.32} x S {1e1, 1e2, 1e3}  (36)
      control: dEc +0.10, phi_b 0.55, tau {30, 100} ns, S {1e3, 1e4}                            (4)
Stages (resumable; each curve written atomically to curves/ as soon as it finishes):
  python calibrate2.py grid | ext | score | best | sens   (ext: S 3e1 / 3e0 between grid values, not requested)
"""
import csv
import itertools
import math
import os
import sys
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "calib"))
import calibrate as c1  # noqa: E402  (defs, Voc at 0.5 sun, scoring, CSV helpers)
from calibrate import kj, sc, MEAS, J1SUN, TEMPS, RAMPS, VGRID, write_csv, load_curve, score_curve  # noqa: E402

CURVES = HERE / "curves"
MAIN = list(itertools.product([30e-9, 100e-9, 300e-9], [0.50, 0.55], [-0.22, -0.32], [1e1, 1e2, 1e3]))
CONTROL = list(itertools.product([30e-9, 100e-9], [0.55], [0.10], [1e3, 1e4]))
LAYER_NAMES = ["FTO", "ZnO", "IL", "abs3", "abs2", "abs1", "abs0"]
# extension (not requested): S between the grid values, where the 1-sun Voc of the cliff cells crosses 875 mV
EXT = [(100e-9, 0.50, -0.22, 3e1), (100e-9, 0.55, -0.22, 3e1), (300e-9, 0.50, -0.22, 3e1), (300e-9, 0.55, -0.22, 3e1),
       (300e-9, 0.50, -0.32, 3e0), (300e-9, 0.55, -0.32, 3e0), (10e-9, 0.50, -0.22, 3e1)]


def tag(tau, phi, dEc, S):
    return f"tau{tau * 1e9:.0f}ns_phi{phi:.2f}_dEc{dEc:+.2f}_S{S:.0e}".replace("+", "p").replace("-", "m")


def make_cell(tau, phi, dEc, S, T, dead=True):
    layers, contacts = kj.parse_def(c1.make_def(phi, dEc, T))
    assert [L["name"] for L in layers] == LAYER_NAMES
    for L in layers[2:]:
        L["tau"] = tau                           # bulk SRH only (IL included); S sits on the interface states
    if dead:
        layers[0]["tau"] = layers[1]["tau"] = 1e-12
    cell = kj.build_cell(layers, contacts, float(T))
    sc.add_interface_defect(cell, S, k_front=1)
    return cell


def run_point(tau, phi, dEc, S, T):
    for i_r, ramp in enumerate(RAMPS):
        cell = make_cell(tau, phi, dEc, S, T)
        jv = sc.run_jv(cell, dV=0.02, tol=1e-8, keep=tuple(VGRID), time_limit=900, ramp=ramp, V_max=1.6)
        if jv.ok:
            break
    if not jv.ok:
        return dict(T_K=T, status=jv.note, ramp_variant=i_r, Voc1=float("nan"), Voc2=float("nan"), m_V=float("nan"),
                    Jsc=float("nan"), FF=float("nan"))
    m = sc.jv_metrics(jv.V, jv.J, 0.0)
    jv.voc1 = m["Voc"] / 1000
    v2 = c1.voc_at(cell, jv, 0.5)
    return dict(T_K=T, status="ok", ramp_variant=i_r, Voc1=jv.voc1, Voc2=v2, m_V=(jv.voc1 - v2) / math.log(2), Jsc=m["Jsc"], FF=m["FF"])


def run_jv300(tau, phi, dEc, S, dead=True, out=None):
    out = out or CURVES / f"{tag(tau, phi, dEc, S)}_jv300.csv"
    if out.exists():
        return
    for ramp in RAMPS:
        cell = make_cell(tau, phi, dEc, S, 300, dead)
        jv = sc.run_jv(cell, dV=0.01, tol=1e-8, time_limit=900, ramp=ramp, V_max=1.6)
        if jv.ok:
            break
    m = sc.jv_metrics(jv.V, jv.J, 0.0) if jv.ok else {k: float("nan") for k in ("Voc", "Jsc", "FF", "eta")}
    rows = [dict(tau=tau, phi_b=phi, dEc=dEc, S=S, status=jv.note, Voc=m["Voc"], Jsc=m["Jsc"], FF=m["FF"], eta=m["eta"], V=v, J=j)
            for v, j in zip(jv.V, jv.J)] or [dict(tau=tau, phi_b=phi, dEc=dEc, S=S, status=jv.note)]
    write_csv(out, rows)


def run_curve(tau, phi, dEc, S):
    out = CURVES / f"{tag(tau, phi, dEc, S)}_vocT.csv"
    if out.exists():
        return
    rows = [dict(tau=tau, phi_b=phi, dEc=dEc, S=S, **run_point(tau, phi, dEc, S, T)) for T in TEMPS]
    write_csv(out, rows)
    print(f"{tag(tau, phi, dEc, S)}: {sum(r['status'] == 'ok' for r in rows)}/11 ok, Voc(298) {rows[5]['Voc1']:.4f}", flush=True)


def grid():
    CURVES.mkdir(exist_ok=True)
    for args in MAIN + CONTROL:
        run_jv300(*args)
        run_curve(*args)


def ext():
    CURVES.mkdir(exist_ok=True)
    for args in EXT:
        run_jv300(*args)
        run_curve(*args)


def score():
    rows = []
    for tau, phi, dEc, S in MAIN + CONTROL + EXT:
        t = tag(tau, phi, dEc, S)
        f, g = CURVES / f"{t}_vocT.csv", CURVES / f"{t}_jv300.csv"
        if not (f.exists() and g.exists()):
            continue
        T, V1, V2, mV = load_curve(f)
        j = list(csv.DictReader(open(g)))[0]
        r = dict(tag=t, set="control" if dEc > 0 else ("extension" if (tau, phi, dEc, S) in EXT else "main"), tau_ns=tau * 1e9, phi_b=phi, dEc=dEc, S=S,
                 n_ok=int(np.isfinite(V1).sum()), **score_curve(T, V1, mV),
                 Voc300=float(j["Voc"]), Jsc300=float(j["Jsc"]), FF300=float(j["FF"]), eta300=float(j["eta"]))
        r["dVoc300_vs_JV"] = r["Voc300"] - J1SUN["Voc"]
        r["passes_1sun"] = bool(r["FF300"] >= 78 and abs(r["dVoc300_vs_JV"]) <= 20)
        r["plausible_offset"] = bool(abs(r["offset_mV"]) <= 60)
        # distance to the pass box in units of its half-widths (0 inside)
        r["miss_1sun"] = math.hypot(max(0.0, abs(r["dVoc300_vs_JV"]) - 20) / 20, max(0.0, 78 - r["FF300"]) / 2)
        rows.append(r)
    rows.sort(key=lambda r: (not r["passes_1sun"], not r["plausible_offset"], r["rms_shape_mV"]))
    for i, r in enumerate(rows):
        r["rank"] = i + 1
    write_csv(HERE / "calib2_scores.csv", rows)
    for r in rows[:10]:
        print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})
    return rows


def best_row():
    rows = list(csv.DictReader(open(HERE / "calib2_scores.csv")))
    return rows[0]


def solve_at(cell, jv, V):
    """Solution at exactly V (from the stored grid solution closest below V)."""
    s, vt = cell.system, cell.system.scaling.energy
    Vk = max(v for v in jv.sols if v <= V + 1e-12)
    g = sc._copy(jv.sols[Vk]); g["v"][-1] = cell.v_eq[-1] + V / vt
    solver = sc._IFSolver(cell); solver.equilibrium = cell.v_eq
    return solver.solve(s, compute="all", guess=g, tol=1e-9, maxiter=100, verbose=False)


def breakdown(cell, sol):
    d = sc.currents(cell, sol)
    rec = d["rec"]
    out = dict(J=d["J"], J_generated=d["gen"], bulk_SRH=sum(rec[n] for n in ("IL", "abs3", "abs2", "abs1", "abs0")),
               front_interface=rec.get("interface", 0.0), window_FTO_ZnO=rec["FTO"] + rec["ZnO"],
               back_contact_electrons=d["loss_back_minority"], front_contact_holes=d["loss_front_minority"])
    out["closure"] = out["J_generated"] - sum(out[k] for k in ("bulk_SRH", "front_interface", "window_FTO_ZnO",
                                                                 "back_contact_electrons", "front_contact_holes")) - out["J"]
    return out


def best():
    r = best_row()
    tau, phi, dEc, S = float(r["tau_ns"]) * 1e-9, float(r["phi_b"]), float(r["dEc"]), float(r["S"])
    cell = make_cell(tau, phi, dEc, S, 300)
    jv = sc.run_jv(cell, dV=0.01, tol=1e-8, keep=tuple(np.round(np.arange(0, 1.6001, 0.01), 6)), V_max=1.6)
    m = sc.jv_metrics(jv.V, jv.J, 0.0)
    rows = []
    for label, V in (("short circuit", 0.0), ("maximum power", m["Vmpp"]), ("open circuit", m["Voc"] / 1000)):
        sol = solve_at(cell, jv, V) if V > 0 else jv.sols[0.0]
        rows.append(dict(tag=r["tag"], point=label, V=V, **breakdown(cell, sol)))
        print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in rows[-1].items()}, flush=True)
    write_csv(HERE / "best_loss_breakdown.csv", rows)
    # EQE against the measurement
    lams = np.arange(300, 961, 10.0)
    e = c1.eqe_if(cell, jv.sols[0.0], lams)
    meas = list(csv.DictReader(open(c1.REPO / "data/kujovic_family/curves/S1_fig3b_EQE.csv")))
    ml = np.array([float(x["wavelength_nm"]) for x in meas]); me = np.array([float(x["EQE_pct"]) for x in meas])
    sl, flux = sc.spectrum_flux()
    msk = (sl >= ml.min()) & (sl <= ml.max())
    integ = lambda lam, q: float((np.interp(sl[msk], lam, q) / 100 * flux[msk]).sum() * sc.Q * 1e3)
    write_csv(HERE / "best_eqe.csv", [dict(wavelength_nm=l_, EQE_pct=float(x)) for l_, x in zip(lams, e)])
    summ = dict(tag=r["tag"], Jsc_JV=m["Jsc"], Jsc_from_model_EQE=integ(lams, e), Jsc_from_measured_EQE=integ(ml, me),
                EQE_rms_vs_measured=float(np.sqrt(np.nanmean((np.interp(ml, lams, e) - me) ** 2))),
                Voc=m["Voc"], FF=m["FF"], eta=m["eta"], Vmpp=m["Vmpp"], Jmpp=m["Jmpp"])
    write_csv(HERE / "best_summary.csv", [summ])
    print(summ)
    plot_best(r, lams, e, ml, me)


def sens():
    """1-sun Voc and FF response to one-parameter steps around the best case (300 K J-V only)."""
    r = best_row()
    tau, phi, dEc, S = float(r["tau_ns"]) * 1e-9, float(r["phi_b"]), float(r["dEc"]), float(r["S"])
    steps = [("tau x3", (tau * 3, phi, dEc, S)), ("tau /3", (tau / 3, phi, dEc, S)),
             ("phi_b +0.05", (tau, phi + 0.05, dEc, S)), ("phi_b -0.05", (tau, phi - 0.05, dEc, S)),
             ("S x3", (tau, phi, dEc, S * 3)), ("S /3", (tau, phi, dEc, S / 3)),
             ("dEc +0.05 (shallower)", (tau, phi, dEc + 0.05, S)), ("dEc -0.05 (deeper)", (tau, phi, dEc - 0.05, S))]
    rows = [dict(step="best", Voc=float(r["Voc300"]), FF=float(r["FF300"]), eta=float(r["eta300"]))]
    for name, args in steps:
        out = CURVES / f"sens_{tag(*args)}_jv300.csv"
        run_jv300(*args, out=out)
        j = list(csv.DictReader(open(out)))[0]
        rows.append(dict(step=name, Voc=float(j["Voc"]), FF=float(j["FF"]), eta=float(j["eta"])))
    for x in rows:
        x["dVoc_mV"] = x["Voc"] - rows[0]["Voc"]; x["dFF"] = x["FF"] - rows[0]["FF"]
        x["miss_1sun"] = math.hypot(max(0.0, abs(x["Voc"] - J1SUN["Voc"]) - 20) / 20, max(0.0, 78 - x["FF"]) / 2)
        print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in x.items()})
    write_csv(HERE / "best_sensitivity_1sun.csv", rows)


def plot_best(r, lams, e, ml, me):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    T, V1, _, mV = load_curve(CURVES / f"{r['tag']}_vocT.csv")
    off, X = float(r["offset_mV"]) / 1000, float(r["X_fit"])
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.8))
    a = ax[0]
    a.plot(MEAS[:, 0], MEAS[:, 1], "o", ms=5, mfc="white", mec="#0b0b0b", mew=1.1, label="measured (JVT)", zorder=5)
    a.plot(T, V1, "-s", ms=4, color="#2a78d6", lw=1.8, label="model, 1 sun")
    a.plot(T, V1 + off, "--", color="#2a78d6", lw=1.2, label=f"model + offset {1000 * off:+.0f} mV (rms {float(r['rms_shape_mV']):.1f} mV)")
    a.plot(T, V1 + mV * math.log(X), ":", color="#eb6834", lw=1.8, label=f"model at {X:.2f} sun (rms {float(r['rms_intensity_mV']):.1f} mV)")
    a.set_xlabel("Temperature (K)"); a.set_ylabel("Voc (V)"); a.legend(frameon=False, fontsize=8)
    a.set_title(f"best: tau {float(r['tau_ns']):.0f} ns, phi_b {float(r['phi_b']):.2f} eV, dEc {float(r['dEc']):+.2f} eV, S {float(r['S']):.0e} cm/s", fontsize=9, loc="left")
    b = ax[1]
    b.plot(ml, me, "o", ms=3.5, mfc="white", mec="#0b0b0b", mew=0.9, label="measured EQE")
    b.plot(lams, e, "-", color="#2a78d6", lw=1.8, label="model (dead FTO/ZnO)")
    b.set_xlabel("Wavelength (nm)"); b.set_ylabel("EQE (%)"); b.set_ylim(0, 100); b.legend(frameon=False, fontsize=8)
    for a_ in ax:
        a_.grid(color="#e4e3df", lw=0.6)
        for s_ in ("top", "right"):
            a_.spines[s_].set_visible(False)
    fig.tight_layout(); fig.savefig(HERE / "best_vocT_eqe.png", dpi=150)


if __name__ == "__main__":
    {"grid": grid, "ext": ext, "score": score, "best": best, "sens": sens}[sys.argv[1]]()
