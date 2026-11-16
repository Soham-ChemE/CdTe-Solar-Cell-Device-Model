"""Write params_from_authors.csv: every material, interface and model parameter the
authors state, with its location. Values are typed exactly as printed.

Usage: python -I make_params.py <kujovic_family folder>
"""
import csv
import os
import sys

OUT = sys.argv[1]
COLS = ["quantity", "layer_or_interface", "value", "value_low", "value_high", "unit", "kind", "source_id", "where",
        "notes"]
P = []


def p(q, layer, value="", lo="", hi="", unit="", kind="", src="", where="", notes=""):
    P.append(dict(quantity=q, layer_or_interface=layer, value=value, value_low=lo, value_high=hi, unit=unit,
                  kind=kind, source_id=src, where=where, notes=notes))


T31 = "S4 thesis Table 3.1 (PDF p.75, printed p.50)"
M1 = "S1 Experimental Section, SCAPS Simulations (PDF p.7)"
# ---------------------------------------------------------------- authors' SCAPS model of the 21.4% cell
p("thickness W", "FTO (SnO2:F)", 350, unit="nm", kind="SCAPS input", src="S4", where=T31)
p("thickness W", "ZnO", 50, unit="nm", kind="SCAPS input", src="S4", where=T31)
p("thickness W", "CdSeTe/CdTe absorber", 3500, unit="nm", kind="SCAPS input", src="S4", where=T31,
  notes="Experimental absorber 3-4 um (S1 PDF p.7).")
p("band gap Eg", "FTO", 3.6, unit="eV", kind="SCAPS input", src="S4", where=T31)
p("band gap Eg", "ZnO", 3.4, unit="eV", kind="SCAPS input", src="S4", where=T31,
  notes="Model value; the measured Tauc gap of the ZnO is 3.2-3.26 eV (see measured rows).")
p("band gap Eg", "CdSeTe/CdTe absorber", "", 1.41, 1.50, "eV", "SCAPS input", "S1;S4", f"{T31}; {M1}",
  "Linear grading: 1.41 eV in CdSeTe (front) to 1.50 eV in CdTe (back).")
p("electron mobility mu_n", "FTO", 100, unit="cm2/Vs", kind="SCAPS input", src="S4", where=T31)
p("electron mobility mu_n", "ZnO", 50, unit="cm2/Vs", kind="SCAPS input", src="S4", where=T31)
p("electron mobility mu_n", "CdSeTe/CdTe absorber", 320, unit="cm2/Vs", kind="SCAPS input", src="S4", where=T31)
p("hole mobility mu_p", "FTO", 25, unit="cm2/Vs", kind="SCAPS input", src="S4", where=T31)
p("hole mobility mu_p", "ZnO", 20, unit="cm2/Vs", kind="SCAPS input", src="S4", where=T31)
p("hole mobility mu_p", "CdSeTe/CdTe absorber", 80, unit="cm2/Vs", kind="SCAPS input", src="S4", where=T31)
p("acceptor density N_A", "FTO", 0, unit="cm-3", kind="SCAPS input", src="S4", where=T31)
p("acceptor density N_A", "ZnO", 0, unit="cm-3", kind="SCAPS input", src="S4", where=T31)
p("acceptor density N_A", "CdSeTe/CdTe absorber", "", 1e16, 3e16, "cm-3", "SCAPS input", "S1;S4", f"{T31}; {M1}",
  "Linear grading: 1e16 in CdSeTe (front) to 3e16 in CdTe (back).")
p("donor density N_D", "FTO", 1e20, unit="cm-3", kind="SCAPS input", src="S1;S4", where=f"{T31}; {M1}",
  notes="Varied 1e16-1e20 in thesis Fig. 3.12 (PDF p.78) / S1 Fig. 6c.")
p("donor density N_D", "ZnO", 1e11, unit="cm-3", kind="SCAPS input", src="S1;S4", where=f"{T31}; {M1}; S1 p.5",
  notes="Chosen because PDL Hall gave no signal (n < 1e12 cm-3).")
p("donor density N_D", "CdSeTe/CdTe absorber", 0, unit="cm-3", kind="SCAPS input", src="S4", where=T31)
p("bulk defect density N_t", "FTO", 1e14, unit="cm-3", kind="SCAPS input", src="S4", where=T31,
  notes="Defect type, energy and capture cross-sections not stated.")
p("bulk defect density N_t", "ZnO", 1e13, unit="cm-3", kind="SCAPS input", src="S4", where=T31,
  notes="Defect type, energy and capture cross-sections not stated.")
p("bulk defect density N_t", "CdSeTe/CdTe absorber", 5e12, unit="cm-3", kind="SCAPS input", src="S4", where=T31,
  notes="Uniform. Defect type, energy and capture cross-sections not stated.")
p("carrier lifetime tau", "CdSeTe/CdTe absorber", 10, unit="ns", kind="SCAPS input", src="S1;S4",
  where=f"{M1}; S4 PDF p.66")
p("interface defect density", "ZnO/CdSeTe interface", 1e9, unit="cm-2", kind="SCAPS input", src="S1;S4",
  where=f"{T31}; {M1}", notes="Acceptor-type interface defects. Energy level and cross-sections not stated.")
p("interface recombination velocity S", "ZnO/CdSeTe interface", 1e4, unit="cm/s", kind="SCAPS input", src="S1;S4",
  where=f"{T31}; {M1}", notes="Stated as equivalent to 1e9 cm-2 interface defects.")
p("conduction band offset (CBO)", "ZnO/CdSeTe interface", 0.1, unit="eV", kind="SCAPS input", src="S1;S4",
  where=f"{M1}; S1 p.5; S4 PDF p.77",
  notes="Assumed spike; the authors state it was not measured and should be measured by UPS. Electron affinities "
        "are not given.")
p("simulated eta", "21.4% cell model", 21.4, unit="%", kind="SCAPS output", src="S4", where="S4 Fig. 3.10 (PDF p.76)",
  notes="Digitised simulated curve gives 21.36% (curves/S4_fig3.10_*_simulation.csv).")
p("simulated Voc", "21.4% cell model", 872, unit="mV", kind="SCAPS output", src="S4", where="S4 Fig. 3.10 (PDF p.76)")
p("simulated Jsc", "21.4% cell model", 30.8, unit="mA/cm2", kind="SCAPS output", src="S4",
  where="S4 Fig. 3.10 (PDF p.76)")
p("simulated FF", "21.4% cell model", 79.6, unit="%", kind="SCAPS output", src="S4", where="S4 Fig. 3.10 (PDF p.76)")
p("optimal CBO range quoted", "buffer/absorber", "", 0.3, 0.4, "eV", "literature quoted", "S1;S4",
  "S1 p.5; S4 PDF p.77", "Quoted from Song et al. (J. Appl. Phys. 2016); not the authors' measurement.")

# ---------------------------------------------------------------- band alignment
X2 = "X2 Liu, Jones, Kujovic et al., IEEE PVSC 2022, p.387 (Table I, Sec. III)"
p("valence band offset (XPS, Kraut)", "ZnO/CdSeTe (CSU CSS CdSeTe, CdCl2 400 C)", -2.47, unit="eV", kind="measured",
  src="X2", where=X2, notes="Mean over Cd 3d, Se 3d, Te 3d and Zn 2p/O 1s core levels.")
p("conduction band offset (XPS, Kraut)", "ZnO/CdSeTe (CSU CSS CdSeTe, CdCl2 400 C)", -0.32, unit="eV",
  kind="measured", src="X2", where=X2, notes="Cliff. Uses Eg(ZnO)=3.54 eV and Eg(CdSeTe)=1.39 eV from Tauc plots.")
p("valence band offset (XPS, Kraut)", "ZnO/CdSeTe (Swansea MOCVD CdSeTe, CdCl2)", -2.34, unit="eV", kind="measured",
  src="X2", where=X2)
p("conduction band offset (XPS, Kraut)", "ZnO/CdSeTe (Swansea MOCVD CdSeTe, CdCl2)", -0.22, unit="eV",
  kind="measured", src="X2", where=X2, notes="Cliff.")
p("VBM - E_F (XPS)", "ZnO, 150 nm sputtered, 1% O2", 1.71, unit="eV", kind="measured", src="X2", where=X2)
p("VBM - E_F (XPS)", "CdSeTe, 300 nm CSS", 0.55, unit="eV", kind="measured", src="X2", where=X2)
p("band gap (Tauc)", "ZnO film used for XPS", 3.54, unit="eV", kind="measured", src="X2", where=X2,
  notes="Higher than the 3.2-3.26 eV the device papers report for their ZnO.")
p("band gap (Tauc)", "CdSeTe film used for XPS", 1.39, unit="eV", kind="measured", src="X2", where=X2)
F54 = "S4 thesis Fig. 5.4 (PDF p.106)"
p("conduction band minimum vs vacuum", "ZnO", -4.62, unit="eV", kind="diagram value", src="S4", where=F54,
  notes="'Obtained from this work and literature [132, 136]'. Implies ZnO/CdSeTe CBO = -0.22 eV (cliff), the X2 "
        "Swansea value.")
p("conduction band minimum vs vacuum", "CeOx", -4.25, unit="eV", kind="diagram value", src="S4", where=F54)
p("conduction band minimum vs vacuum", "CdSeTe", -4.40, unit="eV", kind="diagram value", src="S4", where=F54)
p("valence band maximum vs vacuum", "CdSeTe", -5.81, unit="eV", kind="diagram value", src="S4", where=F54)

# ---------------------------------------------------------------- buffer layer properties
p("carrier density (PDL Hall)", "ZnO 50 nm, as deposited, 22 C", "", "", 1e12, "cm-3", "measured (upper bound)", "S1",
  "S1 p.5 (Sec. 2.3); S4 PDF p.74",
  "No Hall signal; the authors conclude n < 1e12 cm-3.")
p("carrier density (PDL Hall)", "ZnO 75 nm, as deposited (S2 conditions)", "", "", 1e12, "cm-3",
  "measured (upper bound)", "S2", "S2 PDF p.7 (Experimental)", "No signal.")
p("carrier density (PDL Hall)", "ZnO and CeZnO 300 nm (co-sputtered batch)", "", "", "", "cm-3",
  "not measurable", "S4", "S4 PDF p.104", "Too resistive; Ce improved conductivity but still no reliable value.")
p("carrier density (PDL Hall)", "ZnO, 3/6/9% CeZnO, MZO, ZnSnO2 500 nm on Eagle glass", "", "", 1e12, "cm-3",
  "measured (upper bound)", "S4", "S4 PDF p.154", "All too resistive; assumed <= 1e12 cm-3.")
X1 = "X1 Togay, Kujovic et al., J. Phys.: Energy 2025, accepted manuscript, Sec. 2 (PDF p.4-6)"
p("carrier density (PDL Hall)", "ZnO 750 nm, deposited 500 C, as deposited", 1e13, unit="cm-3", kind="measured (order of magnitude)",
  src="X1", where=X1, notes="'Low 1e13 range'; mobility below 1 cm2/Vs. Films < 550 nm gave no signal.")
p("carrier density (PDL Hall)", "ZnO 750 nm, 500 C, vacuum anneal 500 C 10 min", 1e16, unit="cm-3",
  kind="measured (order of magnitude)", src="X1", where=X1)
p("carrier density (PDL Hall)", "ZnO 750 nm, 500 C, CdCl2 treated (450/420 C, 15 min)", 1e15, unit="cm-3",
  kind="measured (order of magnitude)", src="X1", where=X1)
p("carrier density (PDL Hall)", "ZnO 750 nm, 500 C, anneal + CdCl2", 1e17, unit="cm-3",
  kind="measured (order of magnitude)", src="X1", where=X1, notes="Mobility 1-5 cm2/Vs.")
p("carrier density (PDL Hall)", "ZnO 750 nm, 100 C, anneal + CdCl2", 1e16, unit="cm-3",
  kind="measured (order of magnitude)", src="X1", where=X1,
  notes="100 C as-deposited and annealed films, and all 22 C films (any treatment), gave no signal.")
p("Hall mobility", "ZnO 750 nm, 500 C, as deposited", "", "", 1, "cm2/Vs", "measured (upper bound)", "X1", X1)
p("Hall mobility", "ZnO 750 nm, 500 C, anneal + CdCl2", "", 1, 5, "cm2/Vs", "measured", "X1", X1)
p("oxygen out-diffusion from ZnO into CdSeTe", "ZnO 50 nm (22 C) in a device", "observed", kind="measured (EDX)",
  src="X1", where="X1 Fig. 4 (PDF p.6)",
  notes="Conflicts with S1, which reports no evidence of O depletion. X1 proposes O vacancies as donors in the ZnO.")
p("carrier density (PDL Hall)", "SnO2 500 nm sputtered at 500 C, Eagle glass", 1e17, unit="cm-3",
  kind="measured (order of magnitude)", src="S4", where="S4 PDF p.157", notes="Mobility 2-4 (UV set), 0.20-3.21 cm2/Vs (DH set).")
p("carrier density (PDL Hall)", "SnO2 500 nm sputtered at RT, as deposited", 1e14, unit="cm-3",
  kind="measured (order of magnitude)", src="S4", where="S4 PDF p.155", notes="Mobility 5.92 cm2/Vs.")
p("carrier density (statement)", "SnO2 buffers in high-efficiency devices", "", 1e18, 1e19, "cm-3", "statement",
  "S1;S4", "S1 p.5; S4 PDF p.142", "From Hall on SnO2 on glass; no film details.")
p("band gap (Tauc)", "ZnO (S1 device process, 22 C)", 3.2, unit="eV", kind="measured", src="S1", where="S1 p.3")
p("band gap (Tauc)", "ZnO 75 nm, 22-500 C", "", 3.23, 3.25, "eV", "measured", "S2", "S2 p.3; SI Fig. S1")
p("band gap (Tauc)", "ZnO 500 nm, 22 C", 3.26, unit="eV", kind="measured", src="S3", where="S3 Table 1 (PDF p.4)",
  notes="Thesis Table 5.1 (PDF p.109) lists 3.25 eV for the same film; thesis Table 7.2 lists 3.26 eV.")
p("band gap (Tauc)", "Ce0.03Zn0.97O 500 nm", 3.30, unit="eV", kind="measured", src="S3", where="S3 Table 1 (PDF p.4)")
p("band gap (Tauc)", "Ce0.06Zn0.94O 500 nm", 3.33, unit="eV", kind="measured", src="S3", where="S3 Table 1 (PDF p.4)")
p("band gap (Tauc)", "Ce0.09Zn0.91O 500 nm", 3.35, unit="eV", kind="measured", src="S3", where="S3 Table 1 (PDF p.4)")
p("band gap (Tauc)", "ZnO / CeO2 (co-sputter batch)", "", 3.22, 3.58, "eV", "measured", "S4", "S4 PDF p.103",
  "ZnO 3.22, CeO2 3.58; co-sputtered CeZnO 3.22-3.32 eV.")
p("band gap (Tauc)", "SnO2 sputtered RT / 500 C, ZnSnO2, NSG TEC 12D SnO2, MZO", "", 3.59, 4.17, "eV", "measured",
  "S4", "S4 Table 7.2 (PDF p.150)", "SnO2 RT 3.59; SnO2 500 C 3.91; ZnSnO2 4.00; TEC 12D 4.17; MZO 3.64.")
p("weighted average transmittance 350-900 nm", "ZnO 500 nm", 80.18, unit="%", kind="measured", src="S4",
  where="S4 Table 7.2 (PDF p.150)", notes="3/6/9% CeZnO: 78.85/79.77/80.14%.")
p("crystallite size (XRD, Scherrer)", "ZnO 500 nm", 34.13, unit="nm", kind="measured", src="S3",
  where="S3 SI Table 1", notes="Ce 3/6/9%: 5.50/6.73/6.66 nm.")
p("grain width in device (STEM)", "ZnO buffer", 45, unit="nm", kind="measured", src="S3", where="S3 PDF p.9",
  notes="Columnar grains; CeZnO grains are 3-10 nm nanocrystallites.")
p("sheet resistance (4-point probe)", "NSG TEC 12D (FTO + ~67 nm SnO2)", 12.19, unit="ohm/sq", kind="measured",
  src="S4", where="S4 Table 7.3 (PDF p.154)",
  notes="Not the device substrate; the device FTO is unspecified commercial NSG-Pilkington SnO2:F on 2.65 mm SLG.")

# ---------------------------------------------------------------- absorber and junction
p("absorber band gap (EQE derivative)", "CdSeTe front", 1.41, unit="eV", kind="measured", src="S1;S2",
  where="S1 p.3; S2 p.4; S4 PDF p.139", notes="Digitised -dEQE/dlambda peak of S1 Fig. 3b: 879.6 nm = 1.410 eV.")
p("hole density (C-V, 0 V, 40 kHz)", "absorber, 21.4% cell", 2.1e16, unit="cm-3", kind="measured", src="S1",
  where="S1 p.3, Fig. 3c", notes="Zero-bias depletion width digitised as 0.181 um.")
p("hole density (C-V, 0 V)", "absorber, 20.74% cell (ZnO 100 C)", 1.8e16, unit="cm-3", kind="measured", src="S2",
  where="S2 p.4, Fig. 4b")
p("hole density (C-V, 0 V)", "absorber, S3 cells", "", 1.01e16, 1.35e16, "cm-3", "measured", "S3",
  "S3 Table 3 (PDF p.8)", "Per-condition values are in devices.csv.")
p("hole density (C-V, 0 V)", "absorber, 21.7% bilayer cell", 1.15e16, unit="cm-3", kind="measured", src="S4",
  where="S4 PDF p.140")
p("hole density (DLCP, 0 V)", "absorber, SnO2 buffer cell", 1.04e16, unit="cm-3", kind="measured", src="S4",
  where="S4 PDF p.137")
p("hole density (DLCP, 0 V)", "absorber, SnO2/10 nm ZnO cell", 9.48e15, unit="cm-3", kind="measured", src="S4",
  where="S4 PDF p.137")
for t, v in ((22, 1.92e14), (100, 8.57e13), (200, 1.98e15), (500, 2.07e15)):
    note = "C-V minus DLCP carrier density at 0 V (Keysight E4990, dark); unit as printed (cm-3)."
    if t in (200, 500):
        note += " Text gives 1.98e15-2.07e15 for 200-500 C; digitised Fig. 5 assigns 1.978e15 to 200 C and 2.065e15 to 500 C."
    p("interface defect density (C-V minus DLCP)", f"ZnO 75 nm deposited at {t} C", v, unit="cm-3", kind="measured",
      src="S2", where="S2 p.4-5 text, Fig. 5", notes=note)
for b, v in (("ZnO", 1.287e14), ("Ce0.03Zn0.97O", 1.010e14), ("Ce0.06Zn0.94O", 9.787e14), ("Ce0.09Zn0.91O", 9.266e14)):
    p("interface defect density (C-V minus DLCP)", f"{b} 50 nm", v, unit="cm-3", kind="measured (digitised)", src="S3",
      where="S3 Fig. 7 (PDF p.8) via thesis Fig. 5.14 (PDF p.115) vector markers",
      notes="Not printed as numbers; read from the plotted marker centres (log axis, < 0.5% uncertainty).")
p("interface defect density (C-V minus DLCP)", "SnO2 buffer", 9.03e14, unit="cm-3", kind="measured", src="S4",
  where="S4 PDF p.137")
p("interface defect density (C-V minus DLCP)", "SnO2/10 nm ZnO bilayer", 4.14e14, unit="cm-3", kind="measured",
  src="S4", where="S4 PDF p.137")
p("Voc(T->0 K) activation energy Ea", "21.4% cell, ZnO 50 nm 22 C", 1.36, unit="eV", kind="measured", src="S1",
  where="S1 p.3, Fig. 3d", notes="Linear fit 315-355 K. Digitised line intercept 1.359 V; slope -1.70 mV/K.")
p("Voc(T->0 K) activation energy Ea", "co-sputter batch ZnO", 1.36, unit="eV", kind="measured", src="S4",
  where="S4 PDF p.107-108, Fig. 5.7")
p("Voc(T->0 K) activation energy Ea", "co-sputter batch Ce0.050Zn0.950O", 1.478, unit="eV",
  kind="measured (digitised)", src="S4", where="S4 Fig. 5.7 (PDF p.108)", notes="Intercept of the plotted fit line.")
p("Voc(T->0 K) activation energy Ea", "co-sputter batch Ce0.078Zn0.922O", 1.509, unit="eV",
  kind="measured (digitised)", src="S4", where="S4 Fig. 5.7 (PDF p.108)", notes="Intercept of the plotted fit line.")
p("Voc(T->0 K) activation energy Ea", "co-sputter batch Ce0.087Zn0.913O", 1.61, unit="eV", kind="measured", src="S4",
  where="S4 PDF p.108", notes="Digitised line intercept 1.610 V.")
p("TRPL lifetime tau2 (triple-exponential fit)", "SnO2 buffer device", 7.7, unit="ns", kind="measured", src="S4",
  where="S4 PDF p.138", notes="640 nm excitation through the glass. No TRPL is reported for ZnO-only devices.")
p("TRPL lifetime tau2 (triple-exponential fit)", "SnO2/10 nm ZnO bilayer device", 8.4, unit="ns", kind="measured",
  src="S4", where="S4 PDF p.138")
for b, L, sred, s in (("SnO2/CdSeTe", 15.24, 1.34, 265), ("SnO2/10 nm ZnO/CdSeTe", 10.42, 0.21, 26)):
    p("effective diffusion length L (STEM-CL)", b, L, unit="nm", kind="measured", src="S4",
      where="S4 Table 6.3 (PDF p.136)")
    p("reduced surface recombination velocity S_red (STEM-CL)", b, sred, unit="", kind="measured", src="S4",
      where="S4 Table 6.3 (PDF p.136)")
    p("surface recombination velocity s (STEM-CL)", b, s, unit="cm/s", kind="measured (relative metric)", src="S4",
      where="S4 Table 6.3 (PDF p.136)",
      notes="Uses tau_eff = tau2(TRPL); the authors say s is an underestimate and only a relative metric.")

# ---------------------------------------------------------------- process facts used in modelling
p("absorber thickness", "As-doped CdSeTe/CdTe (First Solar VTD)", "", 3, 4, "um", "process", "S1;S2;S3",
  "S1 PDF p.7; S2 PDF p.7; S3 PDF p.11")
p("CdCl2 activation temperature", "absorber", "", 400, 500, "C", "process", "S1;S2;S3", "S1 PDF p.7")
p("cell area", "device", 0.445, unit="cm2", kind="process", src="S1;S2;S3", where="S1 PDF p.7")
p("ZnO deposition rate", "ZnO, RF 1.85 W/cm2, 1 mTorr, 1% O2/Ar, 22 C", 2.0, unit="nm/min", kind="process", src="S1",
  where="S1 PDF p.7")
p("ZnO target purity", "ZnO", "", 99.9, 99.99, "%", "process", "S1;S2;S4", "S1 PDF p.7; S2 PDF p.7; S4 PDF p.51",
  "99.9% for the 21.4% work (thesis Ch.3), 99.99% for Ch.4, 6, 7.")
p("MAR coating reflection reduction", "6-layer SiO2/ZrO2 268 nm on glass", 3.38, unit="% absolute", kind="measured",
  src="S1", where="S1 p.2", notes="Stack SiO2 91/ZrO2 28/SiO2 11/ZrO2 94/SiO2 22/ZrO2 22 nm (S1 PDF p.7).")
p("glass thickness", "NSG-Pilkington FTO-coated soda-lime glass", 2.65, unit="mm", kind="process", src="S1;S2;S3",
  where="S1 PDF p.6")
p("C-V frequency", "device", 40, unit="kHz", kind="process", src="S1;S2;S3", where="S1 PDF p.7")
p("JVT temperature range", "device", "", -70, 85, "C", "process", "S1;S4", "S1 PDF p.7; S4 PDF p.59",
  "Linear fit of Voc(T) over 315-355 K.")

with open(os.path.join(OUT, "params_from_authors.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    w.writerows(P)
print("params", len(P))
