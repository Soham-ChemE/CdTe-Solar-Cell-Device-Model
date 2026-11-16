"""Option A, step 1: forward SCAPS model of the Pandey et al. 2021 MgZnO-series cell (Cu-doped CdSeTe/CdTe).

Stack (back -> front, light from the right): CdTe 3 um | CdSeTe 0.5 um | IL 10 nm | MgZnO 100 nm | FTO 0.5 um.
Every parameter is either measured in the paper, taken from the SCAPS CdTe baseline (Gloeckler 2003),
or a stated prior that the calibration step will fit. Nothing here is tuned to the data yet.

Usage: python optionA/mzo_model.py [tag]   -> runs the six Mg fractions, writes optionA/results_<tag>.csv
"""
import csv
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from scaps_tools import SCAPS_DIR, RESULTS, DefFile, Batch, read_iv, run_parallel  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
ABS = REPO / "scaps/absorption"
DATA = REPO / "data/pandey2021/pandey2021_mzo_series.csv"
HC = 1239.84198  # eV nm

# ---------------------------------------------------------------- priors (edit here; each has a source)
P = {
    "chi_CdTe": 3.90,          # SCAPS CdTe baseline (Gloeckler 2003)
    "Eg_CdTe": 1.50,           # measured
    "Eg_CdSeTe": 1.40,         # Pandey 2021: PL peak 885 nm -> 1.40 eV
    "dchi_CdSeTe": 0.10,       # gap narrowing mostly in the conduction band (Scarpulla 2023) -> chi = 3.90 + 0.10
    "NA": 1e15,                # cm-3, Cu doping; C-V depletion ~1 um (Pandey) -> ~1e15 (prior, to fit)
    "tau": 30e-9,              # s, TRPL at x = 0.15 (Pandey)
    "sigma": 1e-13,            # cm2, neutral midgap SRH centre (prior)
    "vth": 1e7,                # cm/s
    "S_front": 1e4,            # cm/s, front-interface recombination velocity (prior; Kujovic used 1e4)
    "d_IL": 10e-7,             # cm, 10 nm interface layer carrying the front recombination
    "ND_MZO": 1e17,            # cm-3, prior (Ablekim 2018: emitter needs >~1e17)
    "ND_FTO": 1e20,            # cm-3
    "phi_back": 5.10,          # eV, Te contact -> 0.30 eV hole barrier vs CdTe VBM (3.90 + 1.50 = 5.40)
    "Eg_cap": 3.50,            # eV, numerical: SCAPS fails to converge for MgZnO gaps >~3.6 eV (minority-carrier
                               # underflow; diag_convergence2.py). The electrical gap is capped here; the conduction
                               # band (chi, hence dEc) and the optics (absorption file shifted to the measured gap)
                               # keep the measured values. Holes are blocked either way (valence offset > 1.9 eV).
}


def shifted_abs(src: Path, dst: Path, shift_eV: float):
    """Write a red-shifted copy of an absorption file: alpha(E) -> alpha(E + shift)."""
    out = [f"/ {src.name} shifted by {-shift_eV:+.3f} eV in photon energy (option A model input)",
           "/ lambda (nm)\talpha (1/m)"]
    for line in src.read_text(encoding="latin-1").replace("\r", "").split("\n"):
        p = line.split()
        if len(p) == 2 and not line.startswith("/"):
            lam, a = float(p[0]), float(p[1])
            lam_new = HC / (HC / lam - shift_eV)
            out.append(f"{lam_new:.4f}\t{a:.6g}")
    dst.write_text("\r\n".join(out) + "\r\n", encoding="latin-1")


def defect_block(nt_cm3: float, sigma_cm2: float, et_above_ev: float) -> str:
    nt = nt_cm3 * 1e6
    s = sigma_cm2 * 1e-4
    return (
        "srhrecombination\n\n"
        "type : neutral ( 1 level(s) )\n"
        "energy distribution : single\n"
        "Reference for defect energy :  0 ; 0 = above EV (SCAPS<2.7); 1 = above Ei; 2 = below EC\n"
        "Ekar :  0.1000 [eV]\n"
        f"Nt(uniform) :\t {nt:.6e}\t {nt:.6e}\t {nt:.6e}\t 1.000000e+00\t 1.000000e+00\t {nt:.6e}\t {nt:.6e}\t 0\t 2\t[/m^3]\n"
        "profile : homogenous\n"
        "Lkar : 1.000e+00 [m]\n"
        f"Nleft : {nt:.3e} [/m^3]\n"
        f"Nright : {nt:.3e} [/m^3]\n"
        "leveltype : neutral\t\n"
        f"sigma_n : {s:.3e}\t[m^2]\n"
        f"sigma_p : {s:.3e}\t[m^2]\n"
        f"Et :   {et_above_ev:.3f}\t[eV]"
    )


def build(x: float, dEc: float, Eg_mzo: float, p=P, suffix: str = "") -> str:
    """Write the .def for Mg fraction x; returns its name."""
    ABS.mkdir(parents=True, exist_ok=True)
    shifted_abs(SCAPS_DIR / "absorption/CdTe-base.abs", ABS / "CdSeTe_from_CdTe_shift0p10.abs", 0.10)
    d = DefFile.load(SCAPS_DIR / "def/CdTe-base.def")          # layers: CdTe | CdS | SnOx
    d.duplicate_layer("CdTe", "CdSeTe", 1).duplicate_layer("CdTe", "IL", 2)
    d.rename_layer("CdS", "MgZnO").rename_layer("SnOx", "FTO")
    nt_bulk = 1.0 / (p["sigma"] * p["vth"] * p["tau"])       # cm-3
    nt_il = p["S_front"] / (p["sigma"] * p["vth"] * p["d_IL"])
    chi_se = p["chi_CdTe"] + p["dchi_CdSeTe"]
    for name, d_m, Eg, chi, nt in [("CdTe", 3.0e-6, p["Eg_CdTe"], p["chi_CdTe"], nt_bulk),
                                   ("CdSeTe", 0.49e-6, p["Eg_CdSeTe"], chi_se, nt_bulk),
                                   ("IL", 0.01e-6, p["Eg_CdSeTe"], chi_se, nt_il)]:
        d.set_thickness(name, d_m).set_param(name, "Eg", Eg).set_param(name, "chi", chi)
        d.set_param(name, "Na(uniform)", p["NA"] * 1e6).set_param(name, "Nd(uniform)", 0.0)
        d.remove_defects(name).add_defect_block(name, defect_block(nt, p["sigma"], Eg / 2))
        if name != "CdTe":
            d.set_absorption_file(name, "CdSeTe_from_CdTe_shift0p10.abs")
    zno_shift = Eg_mzo - 3.28                     # measured MgZnO gap relative to ZnO (3.28 eV, Pandey Table 1)
    mzo_abs = f"MgZnO_Eg{Eg_mzo:.2f}.abs".replace(".", "p", 1)
    shifted_abs(SCAPS_DIR / "absorption/ZnO.abs", ABS / mzo_abs, -zno_shift)
    d.set_thickness("MgZnO", 0.1e-6).set_param("MgZnO", "Eg", min(Eg_mzo, p["Eg_cap"]))
    d.set_param("MgZnO", "chi", chi_se - dEc)
    d.set_param("MgZnO", "Nd(uniform)", p["ND_MZO"] * 1e6).set_param("MgZnO", "Na(uniform)", 0.0)
    d.set_param("MgZnO", "eps", 9.0).remove_defects("MgZnO").set_absorption_file("MgZnO", mzo_abs)
    d.set_param("FTO", "Nd(uniform)", p["ND_FTO"] * 1e6).remove_defects("FTO")
    if p.get("chi_FTO") is not None:
        d.set_param("FTO", "chi", p["chi_FTO"])
    d.set_back_workfunction(p["phi_back"]).set_front_workfunction(None)
    name = f"A_mzo_x{x:.2f}".replace(".", "p") + suffix
    d.save(name)
    return name


def main(tag="nominal"):
    rows = list(csv.DictReader(open(DATA)))
    cases = []
    for r in rows:
        x = float(r["mg_fraction"])
        name = build(x, float(r["dEc_XPS_eV"]), float(r["Eg_MZO_eV"]))
        cases.append(dict(deffile=f"{name}.def", out=f"{name}_{tag}", step=0.01, stopV=1.2))
    for res in run_parallel(f"A_mzo_{tag}", cases, timeout=1800):
        if "error" in res.stdout.lower():
            print(res.stdout[-400:])
    out = []
    for r in rows:
        x = float(r["mg_fraction"])
        name = f"A_mzo_x{x:.2f}".replace(".", "p")
        f = RESULTS / f"{name}_{tag}.iv"
        iv = read_iv(f) if f.exists() else {"Voc": float("nan"), "Jsc": float("nan"), "FF": float("nan"), "eta": float("nan"), "deffile": ""}
        out.append({"x": x, "dEc": float(r["dEc_XPS_eV"]),
                    "Voc_sim": iv["Voc"] * 1000, "Voc_avg": float(r["Voc_avg_mV"]),
                    "Jsc_sim": iv["Jsc"], "Jsc_avg": float(r["Jsc_avg_mAcm2"]),
                    "FF_sim": iv["FF"], "FF_avg": float(r["FF_avg_pct"]),
                    "eta_sim": iv["eta"], "eta_avg": float(r["eta_avg_pct"]), "def_ok": iv["deffile"] == f"{name}.def"})
    with open(REPO / f"optionA/results_{tag}.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    print(f"{'x':>5} {'dEc':>6} | {'Voc sim/avg':>14} | {'Jsc sim/avg':>13} | {'FF sim/avg':>12} | {'eta sim/avg':>12} | file")
    for o in out:
        print(f"{o['x']:5.2f} {o['dEc']:6.2f} | {o['Voc_sim']:6.0f} / {o['Voc_avg']:4.0f} | {o['Jsc_sim']:5.2f} / {o['Jsc_avg']:5.1f} | "
              f"{o['FF_sim']:5.1f} / {o['FF_avg']:4.1f} | {o['eta_sim']:5.2f} / {o['eta_avg']:4.1f} | {'ok' if o['def_ok'] else 'MISMATCH'}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "nominal")
