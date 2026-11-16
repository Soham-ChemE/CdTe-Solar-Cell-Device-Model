"""Tables, choices, EQE, SQ checks, figures and SCAPS exports for design.py."""
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

import design as D

sc, kj = D.sc, D.kj
HERE = D.HERE
sys.path.insert(0, str(D.REPO / "physics"))
import sq_limit  # noqa: E402

EG_FRONT = 1.41
JSC_MEAS_JV = 30.43
JSC_MEAS_EQE = 27.69          # measured EQE (S1_fig3b, 320-960 nm) integrated over the SCAPS AM1.5G spectrum
ETA_EQE_ANCHOR = 0.8755 * JSC_MEAS_EQE * 0.8048        # 19.51%
LAMS = np.arange(300, 901, 10)


def sq_front():
    return sq_limit.sq(EG_FRONT)


def table():
    sq = sq_front()
    base_m = {br: D.metrics(b) for br, b in D.BRANCHES.items()}
    rows = []
    for lab, d, ref in D.all_designs():
        m = D.metrics(d)
        mr = D.metrics(ref)
        br = next((b for b in D.BRANCHES if f"[{b}]" in lab), "base")
        mb = base_m[br]
        row = dict(design=lab, branch=br, params=D.label_params(d), key=D.key(d))
        if m is None or mb is None:
            row["status"] = "not simulated / failed"
            rows.append(row); continue
        row.update(status="ok", Voc_mV=m["Voc"], Jsc=m["Jsc"], FF=m["FF"], eta=m["eta"],
                   dVoc_mV=m["Voc"] - mb["Voc"], dJsc=m["Jsc"] - mb["Jsc"], dFF=m["FF"] - mb["FF"], deta=m["eta"] - mb["eta"],
                   projected_eta=D.ETA_MEAS * m["eta"] / mb["eta"],
                   # the same scaling applied to Jsc alone (J-V Jsc 30.43 against the model baseline) -> SQ check
                   projected_Jsc=m["Jsc"] * JSC_MEAS_JV / mb["Jsc"],
                   # EQE-anchored projection: baseline = measured Voc x FF x EQE-integrated Jsc (27.69 mA/cm2)
                   projected_eta_EQE=ETA_EQE_ANCHOR * m["eta"] / mb["eta"],
                   projected_Jsc_EQE=m["Jsc"] * JSC_MEAS_EQE / mb["Jsc"])
        if mr is not None:
            row.update(lever_ref=D.label_params(ref), lever_dVoc_mV=m["Voc"] - mr["Voc"], lever_dJsc=m["Jsc"] - mr["Jsc"],
                       lever_dFF=m["FF"] - mr["FF"], lever_deta=m["eta"] - mr["eta"],
                       lever_projected_gain=D.ETA_MEAS * (m["eta"] - mr["eta"]) / mb["eta"])
        row.update(Voc_over_SQ=m["Voc"] / (1000 * sq["Voc_V"]), Jsc_over_SQ=m["Jsc"] / sq["Jsc_mA_cm2"],
                   flag_Voc_above_90pct_SQ=m["Voc"] > 900 * sq["Voc_V"],
                   flag_projected_Jsc_above_SQ=row["projected_Jsc"] > sq["Jsc_mA_cm2"],
                   projected_eta_over_SQ=row["projected_eta"] / sq["eta_pct"])
        rows.append(row)
    return rows, sq


def write_choices(rows):
    """Step-2 inputs from step 1: realistic dEc = best eta at S 52 within [-0.10, +0.20]; aggressive dEc = best eta
    at S 5.2 (any dEc); NA scale = best eta of the NA scan."""
    get = lambda pre: [r for r in rows if r["design"].startswith(pre) and r.get("status") == "ok"]
    a52 = [r for r in get("1a ") if "S 52" in r["design"]]
    a5 = [r for r in get("1a ") if "S 5.2" in r["design"]]
    dec = lambda r: float(r["design"].split("dEc ")[1].split(",")[0])
    real = [r for r in a52 if -0.10 - 1e-9 <= dec(r) <= 0.20 + 1e-9]
    nd = get("1d ")
    if not (real and a5 and nd):
        return None
    ch = dict(dEc_realistic=dec(max(real, key=lambda r: r["eta"])), dEc_aggressive=dec(max(a5, key=lambda r: r["eta"])),
              nas=float(max(nd, key=lambda r: r["eta"])["design"].split("NA x")[1].split(" ")[0]))
    (HERE / "design_choices.json").write_text(json.dumps(ch, indent=1))
    return ch


def eqe_if(cell, sol0, lams, flux=2e16, tol=1e-8):
    """Small-signal EQE at short circuit under 1 sun, with the interface-state solver (kj.eqe uses the plain one)."""
    s = cell.system
    J0 = sc.currents(cell, sol0)["J"]
    solver = sc._IFSolver(cell)
    solver.equilibrium = cell.v_eq
    out = []
    for lam in lams:
        s.g = cell.g_full + kj.mono_generation(cell, lam, flux) / s.scaling.generation
        new = solver.solve(s, compute="all", guess=sc._copy(sol0), tol=tol, maxiter=60, verbose=False)
        out.append(float("nan") if new is None else (sc.currents(cell, new)["J"] - J0) / (sc.Q * flux * 1e3) * 100)
    s.g = cell.g_full.copy()
    return np.array(out)


def eqe_rows():
    f = HERE / "design_eqe.csv"
    have = {}
    if f.exists():
        for r in csv.DictReader(open(f)):
            have.setdefault(r["key"], []).append(r)
    todo = [("baseline", D.BASE)] + [(lab, d) for lab, d in D.combined("base")]
    rows = []
    lam_sp, P = sq_limit.load_spectrum()
    for lab, d in todo:
        k = D.key(d)
        if k in have:
            rows += have[k]; continue
        cell = D.make_cell(d)
        jv = sc.run_jv(cell, vlist=[], tol=1e-8, keep=(0.0,))
        q = eqe_if(cell, jv.sols[0.0], LAMS)
        # J from EQE x AM1.5G photon flux (SCAPS spectrum bins), for comparison with the J-V Jsc
        E = 6.62607015e-34 * 2.99792458e8 / (lam_sp * 1e-9)
        flux = P / E
        J_eqe = float((np.interp(lam_sp, LAMS, q, left=0, right=0) / 100 * flux).sum() * 1.602176634e-19 / 10)
        for lam, v in zip(LAMS, q):
            rows.append(dict(design=lab, key=k, wavelength_nm=float(lam), EQE_pct=float(v), J_from_EQE=J_eqe))
        print(f"EQE {lab}: J_EQE {J_eqe:.2f} mA/cm2", flush=True)
        D.write_csv(f, rows + [r for kk, rr in have.items() for r in rr if kk not in {D.key(dd) for _, dd in todo}])
    return rows


def plots(rows, eq):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ink, ink2 = "#0b0b0b", "#52514e"
    ok = [r for r in rows if r.get("status") == "ok"]
    fig, ax = plt.subplots(1, 2, figsize=(16, 7), gridspec_kw=dict(width_ratios=[1.6, 1]))
    a = ax[0]
    y = np.arange(len(ok))
    cols = ["#2a78d6" if r["design"].startswith("1") else ("#eb6834" if r["design"].startswith("2") else ink2) for r in ok]
    a.barh(y, [r["projected_eta"] for r in ok], color=cols)
    a.axvline(D.ETA_MEAS, color=ink, lw=0.8, ls="--")
    sqe = sq_front()["eta_pct"]
    a.axvline(sqe, color="#d03b3b", lw=1.0, ls=":")
    a.text(sqe, -1.2, f" SQ limit at 1.41 eV: {sqe:.1f}%", color="#d03b3b", fontsize=7, va="bottom")
    a.set_yticks(y); a.set_yticklabels([r["design"] for r in ok], fontsize=6.5); a.invert_yaxis()
    a.set_xlim(min(r["projected_eta"] for r in ok) - 1, max(max(r["projected_eta"] for r in ok), sq_front()["eta_pct"]) + 1)
    a.set_xlabel("projected efficiency (%) = 21.44 × eta_design / eta_branch-baseline")
    for yi, r in zip(y, ok):
        a.text(r["projected_eta"] + 0.05, yi, f"{r['projected_eta']:.2f}", va="center", fontsize=6)
    a = ax[1]
    for lab, c in (("baseline", ink), ("2 realistic [base]", "#2a78d6"), ("2 aggressive [base]", "#eb6834")):
        rr = [r for r in eq if r["design"] == lab]
        if rr:
            a.plot([float(r["wavelength_nm"]) for r in rr], [float(r["EQE_pct"]) for r in rr], color=c,
                   label=f"{lab}: J_EQE {float(rr[0]['J_from_EQE']):.2f} mA/cm²")
    meas = REPO_MEAS()
    if meas is not None:
        a.plot(*meas, "o", ms=2.5, mfc="none", color=ink2, label="measured (digitised)")
    a.set_xlabel("wavelength (nm)"); a.set_ylabel("EQE (%)"); a.set_ylim(0, 100); a.legend(frameon=False, fontsize=7.5, loc="lower center")
    for a_ in ax:
        a_.grid(color="#e4e3df", lw=0.6)
        for s_ in ("top", "right"):
            a_.spines[s_].set_visible(False)
    fig.tight_layout(); fig.savefig(HERE / "design_results.png", dpi=140)


def REPO_MEAS():
    f = D.REPO / "data/kujovic_family/curves/S1_fig3b_EQE.csv"
    if not f.exists():
        return None
    rr = list(csv.DictReader(open(f)))
    return [float(r["wavelength_nm"]) for r in rr], [float(r["EQE_pct"]) for r in rr]


def main():
    rows, sq = table()
    ch = write_choices(rows)
    D.write_csv(HERE / "design_results.csv", rows)
    print(f"SQ at Eg {EG_FRONT} eV: Voc {1000 * sq['Voc_V']:.1f} mV, Jsc {sq['Jsc_mA_cm2']:.2f} mA/cm2, eta {sq['eta_pct']:.2f}%  "
          f"(90% Voc_SQ = {900 * sq['Voc_V']:.1f} mV)")
    print("choices:", ch)
    for r in rows:
        if r.get("status") != "ok":
            print(f"{r['design']:48s} {r.get('status')}"); continue
        lv = f" | lever: dVoc {r['lever_dVoc_mV']:+6.1f} dJsc {r['lever_dJsc']:+5.2f} dFF {r['lever_dFF']:+5.2f} deta {r['lever_deta']:+5.2f} (proj {r['lever_projected_gain']:+5.2f})" if "lever_deta" in r else ""
        print(f"{r['design']:48s} {r['Voc_mV']:6.1f} {r['Jsc']:6.2f} {r['FF']:6.2f} {r['eta']:6.2f} | dVoc {r['dVoc_mV']:+6.1f} dJsc {r['dJsc']:+5.2f} "
              f"dFF {r['dFF']:+5.2f} deta {r['deta']:+5.2f} | proj {r['projected_eta']:6.2f}{lv}{'  >90% SQ Voc' if r['flag_Voc_above_90pct_SQ'] else ''}")
    eq = eqe_rows() if ch else []
    plots(rows, eq)


# ------------------------------------------------------------------ SCAPS exports
SIG_IF, VTH_IF = 1e-16, 1e5          # m^2, m/s (as optionA/scaps_if_xcheck.py)
IFBLOCK = """interface recombination

type : neutral
sigma_nleft : 1.000e-25 [m^2]
sigma_nright : {sig:.3e} [m^2]
sigma_pleft : {sig:.3e} [m^2]
sigma_pright : 1.000e-25 [m^2]
Tunneling to trap: 0 (0: no tunneling, 1: with tunneling)
Relative electron mass :  1.00e+00
Relative hole mass :  1.00e+00
energy distribution : single
Reference for defect energy :  9 ; 3 = above highest EV; 4 = below lowest EC; 5 = above Ei left; 6 = above Ei right; 7 = above EV left (= SCAPS%<2.7 reference); 8 = above EV right; 9 = above middle of interface gap
Et :  0.00 [eV]
Ekar :  0.10 [eV]
N : {N:.3e} [/m^2]
"""


def scaps_defs():
    sys.path.insert(0, str(D.REPO / "scripts")); sys.path.insert(0, str(D.REPO / "optionA"))
    from scaps_tools import DefFile
    from mzo_model import defect_block
    out = HERE / "defs_scaps"
    out.mkdir(exist_ok=True)
    (out / "3%mirror.ftr").write_text("/ optical filter representing 3% Transmission or Reflection for all lambda\n"
                                     "/ if used at the illuminated side: the data are interpreted as transmission\n"
                                     "/ if used at the rear side       : the data are interpreted as reflection\n"
                                     "/ lambda[nm]\toptical T or R [%]\n0\t3\n10000\t3\n")
    notes = []
    for lab, d in [("baseline", D.BASE)] + D.combined("base"):
        nm = ("Design_" + lab.replace("2 ", "").replace(" [base]", "")).replace(" ", "_")
        src = D.make_def(d, 0.0, out_dir=out, name=nm + "_src")
        dd = DefFile.load(src)
        bl = dd.defect_blocks("IL")
        dd.remove_defects("IL").add_defect_block("IL", bl[0])            # IL: bulk SRH only
        i = dd.idx("IL")
        N = (d["S"] / 100.0) / (SIG_IF * VTH_IF)
        dd.layers[i] = dd.layers[i].rstrip("\n") + "\n\n" + IFBLOCK.format(sig=SIG_IF, N=N) + "\n\n"
        # dead window (Sesame tau 1e-12 s): Nt 1e18 cm-3, sigma 1e-13 cm2, vth 1e7 cm/s, midgap
        dd.remove_defects("ZnO").add_defect_block("ZnO", defect_block(1e18, 1e-13, 3.4 / 2))
        dd.remove_defects("FTO").add_defect_block("FTO", defect_block(1e18, 1e-13, 3.6 / 2))
        if d["Tf"] != 0.90:
            # front filter: 3% reflection (MAR); copy 3%mirror.ftr into SCAPS's filter folder before running
            for attr in ("tail", "front", "head"):
                if hasattr(dd, attr) and "10%mirror.ftr" in getattr(dd, attr):
                    setattr(dd, attr, getattr(dd, attr).replace("10%mirror.ftr", "3%mirror.ftr"))
        import scaps_tools
        scaps_tools.DEFS = out
        dd.save(nm)
        (out / f"{nm}_src.def").unlink(missing_ok=True)
        txt = (out / f"{nm}.def").read_text(encoding="latin-1")
        notes.append(f"{nm}.def: {D.label_params(d)}\n"
                     f"  interface block on IL/ZnO: neutral, sigma_n(ZnO side) = sigma_p(absorber side) = {SIG_IF:.0e} m^2, "
                     f"vth {VTH_IF:.0e} m/s, level at the middle of the interface gap (reference 9, Et 0), N = {N:.3e} m^-2 (S = {d['S']:.3g} cm/s)\n"
                     f"  IL keeps only the bulk SRH block (tau {d['tau'] * 1e9:g} ns); ZnO and FTO carry a dead-window block "
                     f"(Nt 1e18 cm^-3, sigma 1e-13 cm^2: tau 1e-12 s) to mimic Sesame's dead window\n"
                     f"  front filter: {'3%mirror.ftr (copy it into SCAPS filter/)' if '3%mirror.ftr' in txt else '10%mirror.ftr'}; "
                     f"back: {'flat band (flatband 1, recalculate 1)' if d['back'] == 'ohm' else 'Fi_m = ' + format(5.81 - float(d['back'][1:]), '.2f') + ' eV'}; "
                     f"front Fi_m stored 4.10 eV (flatband 1, recalculate 0, as the baseline); Rs 0\n")
    (out / "README_scaps_crosscheck.txt").write_text(
        "SCAPS cross-check inputs for the design study (written by design.py defs; not run here).\n"
        "Sesame numbers for comparison: ../design_results.csv (rows '0 baseline' and '2 ... [base]').\n\n" + "\n".join(notes))
    print("\n".join(notes))
