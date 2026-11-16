"""Rebuild of the Loughborough SCAPS model of the 21.4% ZnO/CdSeTe/CdTe cell (Kujovic thesis Table 3.1, 2024 paper).

Authors' inputs (data/kujovic_family/params_from_authors.csv):
  FTO 350 nm, Eg 3.6, ND 1e20, mu 100/25 | ZnO 50 nm, Eg 3.4, ND 1e11, mu 50/20 |
  absorber 3.5 um, Eg 1.50 (back, CdTe) -> 1.41 (front, CdSeTe) linear, NA 3e16 -> 1e16 linear, mu 320/80,
  bulk Nt 5e12 cm-3 with tau 10 ns | ZnO/CdSeTe interface defects 1e9 cm-2 = S 1e4 cm/s | CBO +0.1 eV (assumed).
  Their SCAPS output: 21.4% (Voc 872 mV, Jsc 30.8 mA/cm2, FF 79.6%).
Not stated by the authors, chosen here (each is labelled in RECON):
  electron affinities from the authors' band diagram (thesis Fig. 5.4: CdSeTe CBM -4.40, VBM -5.81 eV) with the
  VBM held at 5.81 eV across the graded absorber; Nc/Nv/eps from the SCAPS CdTe baseline; neutral midgap SRH
  centres; flat-band front and back contacts; SCAPS baseline optical filters; grading as 4 sublayers (SCAPS
  allows at most 7 layers in total).
Usage: python optionA/kujovic_model.py [tag] [key=value ...]   (overrides, e.g. dEc=-0.1 S_front=1e5)
"""
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from mzo_model import shifted_abs, defect_block  # noqa: E402
from scaps_tools import SCAPS_DIR, RESULTS, DefFile, Batch, read_iv, read_qe  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
ABS = REPO / "scaps/absorption"
AUTH = {"d_abs_um": 3.5, "Eg_back": 1.50, "Eg_front": 1.41, "NA_back": 3e16, "NA_front": 1e16, "tau": 10e-9,
        "Nt_bulk": 5e12, "S_front": 1e4, "dEc": 0.10, "ND_ZnO": 1e11, "Eg_ZnO": 3.4, "d_ZnO_nm": 50,
        "ND_FTO": 1e20, "d_FTO_nm": 350, "mu_abs": (320, 80), "mu_ZnO": (50, 20), "mu_FTO": (100, 25)}
RECON = {"VBM_abs": 5.81, "chi_FTO": 4.50, "n_sub": 4,   # SCAPS allows at most 7 layers: 4 absorber + IL + ZnO + FTO
         "d_IL_nm": 10, "vth": 1e7, "back": "flatband", "Rs": 0.0,
         # Switches added 2026-11-16 after reading the authors' own SCAPS band diagram (thesis Fig. 3.11,
         # data/kujovic_family/curves/S4_fig3.11_*): their absorber gap is 1.50 eV at every depth and the back
         # contact sits 0.655 eV above the valence band (a hole barrier), although the text states a 1.41-1.50 eV grading.
         "Eg_mode": "graded",        # "graded": electrical gap 1.50 -> 1.41 eV; "uniform": 1.50 eV everywhere (optics stay graded)
         "window_defects": False,    # True: ZnO Nt 1e13, FTO Nt 1e14 cm-3 (authors' Table 3.1; type and cross-section unstated)
         "sigma_window": 1e-12}      # cm2, assumed cross-section of the window defects


def build(p=AUTH, r=RECON, name="K_kujovic"):
    d = DefFile.load(SCAPS_DIR / "def/CdTe-base.def")          # CdTe | CdS | SnOx
    n = r["n_sub"]
    for k in range(1, n):
        d.duplicate_layer("CdTe", f"abs{k}", k)
    d.rename_layer("CdTe", "abs0")
    d.duplicate_layer(f"abs{n - 1}", "IL", n)
    d.rename_layer("CdS", "ZnO").rename_layer("SnOx", "FTO")
    sigma_bulk = 1.0 / (p["tau"] * r["vth"] * p["Nt_bulk"])
    t_sub = p["d_abs_um"] * 1e-6 / n
    for k in range(n):                                    # k = 0 at the back (CdTe) ... n-1 at the front (CdSeTe)
        f = (k + 0.5) / n
        Eg = p["Eg_back"] + f * (p["Eg_front"] - p["Eg_back"])
        NA = p["NA_back"] + f * (p["NA_front"] - p["NA_back"])
        L = f"abs{k}"
        thick = t_sub - (r["d_IL_nm"] * 1e-9 if k == n - 1 else 0.0)
        Eg_el = p["Eg_back"] if r.get("Eg_mode") == "uniform" else Eg     # electrical gap
        d.set_thickness(L, thick).set_param(L, "Eg", Eg_el).set_param(L, "chi", r["VBM_abs"] - Eg_el)
        d.set_param(L, "Na(uniform)", NA * 1e6).set_param(L, "Nd(uniform)", 0.0)
        d.set_param(L, "mu_n", p["mu_abs"][0] * 1e-4).set_param(L, "mu_p", p["mu_abs"][1] * 1e-4)
        d.remove_defects(L).add_defect_block(L, defect_block(p["Nt_bulk"], sigma_bulk, Eg_el / 2))
        fn = f"CdTe_shift_{1.50 - Eg:.3f}.abs".replace("0.", "0p", 1)
        shifted_abs(SCAPS_DIR / "absorption/CdTe-base.abs", ABS / fn, 1.50 - Eg)
        d.set_absorption_file(L, fn)
    Egf = p["Eg_front"]; Egf_el = p["Eg_back"] if r.get("Eg_mode") == "uniform" else Egf
    chi_front = r["VBM_abs"] - Egf_el
    nt_il = p["S_front"] / (1e-12 * r["vth"] * r["d_IL_nm"] * 1e-7)
    d.set_thickness("IL", r["d_IL_nm"] * 1e-9).set_param("IL", "Eg", Egf_el).set_param("IL", "chi", chi_front)
    d.set_param("IL", "Na(uniform)", p["NA_front"] * 1e6).remove_defects("IL")
    d.set_param("IL", "mu_n", p["mu_abs"][0] * 1e-4).set_param("IL", "mu_p", p["mu_abs"][1] * 1e-4)
    fn_front = f"CdTe_shift_{1.50 - Egf:.3f}.abs".replace("0.", "0p", 1)
    shifted_abs(SCAPS_DIR / "absorption/CdTe-base.abs", ABS / fn_front, 1.50 - Egf)
    d.set_absorption_file("IL", fn_front)
    d.add_defect_block("IL", defect_block(p["Nt_bulk"], sigma_bulk, Egf_el / 2))
    d.add_defect_block("IL", defect_block(nt_il, 1e-12, Egf_el / 2))
    d.set_thickness("ZnO", p["d_ZnO_nm"] * 1e-9).set_param("ZnO", "Eg", p["Eg_ZnO"]).set_param("ZnO", "chi", chi_front - p["dEc"])
    d.set_param("ZnO", "Nd(uniform)", p["ND_ZnO"] * 1e6).set_param("ZnO", "Na(uniform)", 0.0).set_param("ZnO", "eps", 9.0)
    d.set_param("ZnO", "mu_n", p["mu_ZnO"][0] * 1e-4).set_param("ZnO", "mu_p", p["mu_ZnO"][1] * 1e-4)
    d.remove_defects("ZnO").set_absorption_file("ZnO", "ZnO.abs")
    d.set_thickness("FTO", p["d_FTO_nm"] * 1e-9).set_param("FTO", "Nd(uniform)", p["ND_FTO"] * 1e6).set_param("FTO", "chi", r["chi_FTO"])
    d.set_param("FTO", "mu_n", p["mu_FTO"][0] * 1e-4).set_param("FTO", "mu_p", p["mu_FTO"][1] * 1e-4).remove_defects("FTO")
    if r.get("window_defects"):
        d.add_defect_block("ZnO", defect_block(1e13, r["sigma_window"], p["Eg_ZnO"] / 2))
        d.add_defect_block("FTO", defect_block(1e14, r["sigma_window"], 3.6 / 2))
    d.set_front_workfunction(None)
    if r["back"] == "flatband":
        # 'flatband : 1' alone is NOT honoured when SCAPS loads a .def from a script: with 'recalculate : 0'
        # (as in the CdTe baseline) SCAPS keeps the stored Fi_m (5.0 eV here, a 0.81 eV hole barrier). Found
        # 2026-11-16 from the equilibrium band diagram (optionA/kujovic_eb.py). Both flags must be set.
        d.head = re.sub(r"^flatband : \d", "flatband : 1", d.head, count=1, flags=re.M)
        d.head = re.sub(r"^recalculate : \d", "recalculate : 1", d.head, count=1, flags=re.M)
    else:                                   # float: hole barrier in eV (metal Fermi level above the back VBM)
        d.set_back_workfunction(r["VBM_abs"] - float(r["back"]))
    if len(d.layers) > 7:
        raise ValueError(f"SCAPS allows at most 7 layers; this structure has {len(d.layers)}")
    d.save(name)
    return name


def compare(tag, iv, qe):
    import numpy as np
    meas_jv = list(csv.DictReader(open(REPO / "data/kujovic_family/curves/S1_fig3a_JV_light.csv")))
    meas_qe = list(csv.DictReader(open(REPO / "data/kujovic_family/curves/S1_fig3b_EQE.csv")))
    lam = np.array([float(r["wavelength_nm"]) for r in meas_qe]); eqe = np.array([float(r["EQE_pct"]) for r in meas_qe])
    sl, sq = np.array(qe["lambda_nm"]), np.array(qe["qe_pct"])
    m = (lam >= sl.min()) & (lam <= sl.max())
    rms = float(np.sqrt(np.mean((np.interp(lam[m], sl, sq) - eqe[m]) ** 2)))
    print(f"[{tag}] SCAPS: Voc {iv['Voc']*1000:.1f} mV  Jsc {iv['Jsc']:.2f}  FF {iv['FF']:.2f}  eta {iv['eta']:.2f}")
    print(f"[{tag}] authors' SCAPS: 872 / 30.8 / 79.6 / 21.4    measured: 875.5 / 30.43 / 80.48 / 21.44")
    print(f"[{tag}] EQE rms difference vs measured over {lam[m].min():.0f}-{lam[m].max():.0f} nm: {rms:.2f} %-points")
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
        V = [float(r["V_mV"]) for r in meas_jv]; J = [-float(r["J_mA_cm2"]) for r in meas_jv]
        ax[0].plot(V, J, "o", ms=2.5, mfc="none", label="measured (digitised)")
        tab = np.array(iv["table"]); ax[0].plot(tab[:, 0] * 1000, -tab[:, 1], "-", label="SCAPS rebuild")
        ax[0].set_xlim(0, 950); ax[0].set_ylim(0, 33); ax[0].set_xlabel("V (mV)"); ax[0].set_ylabel("J (mA/cm²)"); ax[0].legend(frameon=False, fontsize=8)
        ax[1].plot(lam, eqe, "o", ms=2.5, mfc="none", label="measured (digitised)"); ax[1].plot(sl, sq, "-", label="SCAPS rebuild")
        ax[1].set_xlabel("wavelength (nm)"); ax[1].set_ylabel("EQE (%)"); ax[1].legend(frameon=False, fontsize=8)
        fig.suptitle(f"21.4% ZnO/CdSeTe/CdTe cell: rebuild '{tag}'", fontsize=10); fig.tight_layout()
        fig.savefig(REPO / f"figures/kujovic_rebuild_{tag}.png", dpi=180)
    except Exception as e:  # plotting is optional
        print("plot skipped:", e)


if __name__ == "__main__":
    tag = sys.argv[1] if len(sys.argv) > 1 else "authors"
    p = dict(AUTH)
    for kv in sys.argv[2:]:
        k, v = kv.split("="); p[k] = float(v)
    name = build(p, name=f"K_kujovic_{tag}")
    b = Batch(f"K_kujovic_{tag}")
    b.case(f"{name}.def", name, step=0.01, stopV=1.2, qe=(300, 900, 10), sets=[f"set external.Rs {RECON['Rs']}"])
    r = b.run(timeout=1800)
    if "error" in r.stdout.lower():
        print(r.stdout[-400:])
    f = RESULTS / f"{name}.iv"
    if f.exists():
        compare(tag, read_iv(f), read_qe(RESULTS / f"{name}.qe"))
