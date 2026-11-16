import csv, sys
cols=["source_id","year","buffer","quantity","value","value_low","value_high","unit","condition","method","source_location","value_type","notes"]
R=[]
def add(**k): R.append({c:k.get(c,"") for c in cols})
F=dict(source_id="fedorenko2015", year=2015)
# dominant deep trap
for b,v,lo,hi,loc in [("ZnO (reference)",0.38,"","","JAP p.5; MRS p.3-4"),("ZnSe",0.50,"","","JAP p.5; MRS p.3-4"),("ZnS","",0.75,0.76,"JAP p.5; MRS p.4")]:
    add(**F, buffer=b, quantity="dominant deep trap activation energy E_A", value=v, value_low=lo, value_high=hi, unit="eV",
        condition="zero bias; ac admittance (Walter p-i-n model), Arrhenius of emission rate", method="admittance spectroscopy",
        source_location=loc+"; JAP SI Fig.4 p.21", value_type="measured",
        notes="Only one deep level observed per device. Energy is from the Walter model E = kT ln(2 xi N_v,c / omega); the reference band is not stated explicitly. Authors compare with known CdTe/CdS defects at 0.35-0.75 eV and the E_V+0.76 eV acceptor complex, so read as above E_V. ZnO-buffer E_A unchanged under bias.")
add(**F, buffer="ZnS", quantity="dominant trap E_A under forward bias", value_low=0.40, value_high=0.43, unit="eV",
    condition="V = 0.2-0.4 V", method="admittance spectroscopy", source_location="JAP SI Fig.4 caption p.21", value_type="measured",
    notes="Bias-dependent E_A for ZnS only; paper uses zero-bias values.")
for b,v in [("ZnO (reference)","1.43e7"),("ZnSe","3e5"),("ZnS","2.52e9")]:
    add(**F, buffer=b, quantity="emission prefactor nu0 (Arrhenius ln(omega/T^2) intercept)", value=v, unit="s^-1 K^-2",
        condition="zero bias", method="admittance spectroscopy", source_location="JAP Fig.2 labels p.14; MRS Fig.3 labels p.4",
        value_type="measured (fit parameter)", notes="With N_V, gives the capture cross-section (not reported by the authors).")
for b,v,lo,hi in [("ZnO (reference)","1e14","",""),("ZnSe","",8e15,9e15),("ZnS","9.6e14","","")]:
    add(**F, buffer=b, quantity="integrated deep-trap density N_it (Gaussian fit of N_t(E))", value=v, value_low=lo, value_high=hi, unit="cm^-3",
        condition="Gaussian fit to N_t(E)", method="admittance spectroscopy", source_location="MRS Adv Fig.3(b-d) labels p.4 (not in JAP version)",
        value_type="measured (fit parameter)", notes="Values given as '~' in the figure.")
for b,v,lo,hi,cond,E in [("ZnO (reference)","1.07e15","","","200 K (falls to ~4.5e14-5e14 at 240-260 K)","0.38"),
                         ("ZnSe","",1.6e16,2.8e16,"2.8e16 at 320 K falling to 1.6e16 at 400 K","0.51-0.54"),
                         ("ZnS","6.0e15","","","320-400 K (weak T dependence)","0.77-0.79")]:
    add(**F, buffer=b, quantity="peak trap density of states N_t(E) max", value=v, value_low=lo, value_high=hi, unit="cm^-3 eV^-1",
        condition=cond+"; peak at E = "+E+" eV", method="admittance spectroscopy; digitized from vector figure",
        source_location="MRS Adv Fig.3(b-d) p.4 (same data as JAP Fig.2)", value_type="figure-read (digitized, +/-3%)",
        notes="Digitized from PDF vector marker coordinates (extraction/digit_dos.py).")
add(**F, buffer="ZnO and ZnSe", quantity="DOS Gaussian broadening delta", value_low=0.026, value_high=0.100, unit="eV",
    condition="180-400 K (increases with T)", method="Gaussian fit of N_t(E)", source_location="JAP p.6 and Fig.2(a) inset p.14",
    value_type="measured (fit parameter)",
    notes="MRS Adv text says '0.26 meV to 100 meV' (typo for 26 meV). Inset (figure-read, approx.): ZnO ~0.02-0.05 eV at 180-280 K; ZnSe ~0.07 eV at 320 K to ~0.11 eV at 400 K.")
add(**F, buffer="ZnSe and ZnS", quantity="series-resistance activation energy E_A(Rs)", value_low=0.160, value_high=0.170, unit="eV",
    condition="250-350 K", method="T-dependent J-V, Werner differential method", source_location="JAP p.4; SI Fig.2 p.19",
    value_type="measured", notes="SI Fig.2 label reads 'E_A = 160-220 meV'. Rs magnitudes not extracted (axis labelled ln(Rs) on what looks like a log axis; ambiguous).")
add(**F, buffer="ZnO (reference)", quantity="series-resistance activation energy E_A(Rs)", value=0.13, unit="eV",
    condition="T-dependent J-V", method="Werner differential method", source_location="MRS Adv Fig.1 p.2", value_type="measured", notes="")
add(**F, buffer="ZnO (reference)", quantity="back-contact (Au) barrier height", value=0.5, unit="eV",
    condition="from saturation current J_t vs 1/T", method="T-dependent J-V", source_location="JAP p.4, SI Fig.3 p.20; MRS Fig.1",
    value_type="measured", notes="Measured on ZnO-buffer cells only. Back-side apparent doping saturates at (0.7-2.0)e15 cm^-3 for all buffers, which the authors read as no large back-barrier difference between series.")
add(**F, buffer="ZnSe and ZnS", quantity="temperature where rectification is lost", value_low=200, value_high=230, unit="K",
    condition="dark J-V", method="T-dependent J-V", source_location="JAP p.9", value_type="measured",
    notes="Attributed to much lower base carrier density than ZnO-buffer cells. ZnO cells still rectify at 110 K (Fig.3).")
add(**F, buffer="ZnSe and ZnS", quantity="forward transport mechanism", unit="",
    condition="200-350 K", method="Schottky / Poole-Frenkel / Fowler-Nordheim plots", source_location="JAP p.8-9, Fig.4 p.16", value_type="measured (qualitative)",
    notes="No SCLC (unlike ZnO cells). Linear FN plot at high field = electron tunnelling; trap-assisted at low field; FN behaviour absent below 200 K. Reverse current = generation current (log I linear in V^1/2). Fig.4 is labelled ZnS; text applies it to ZnS and ZnSe.")
add(**F, buffer="ZnO (reference)", quantity="trap density from SCLC trap-filled-limit voltage", value_low=7e15, value_high=4.2e16, unit="cm^-3",
    condition="7e15 forward, 4.2e16 reverse polarity; 110-300 K", method="SCLC analysis (V_T = qN_t d^2/2 eps eps0, eps=10.16)",
    source_location="JAP p.8; MRS p.4-5", value_type="measured (model-derived by authors)", notes="ZnO cells only; SCLC slope m = 1.4-1.6.")
add(**F, buffer="ZnO (reference)", quantity="electron mobility from trap-free SCLC", value=0.1, unit="cm^2 V^-1 s^-1",
    condition="300 K; trap-free SCLC current ~1e-5 A/cm2", method="Mott-Gurney with free-carrier fraction", source_location="MRS Adv p.5 (not in JAP)",
    value_type="measured (model-derived by authors)", notes="Order of magnitude ('~').")
for b,v in [("ZnSe","3.43e16"),("ZnS","8.04e16")]:
    add(**F, buffer=b, quantity="1/C^2 at 0 V", value=v, unit="cm^4 F^-2", condition="300 K, 10 kHz, dark",
        method="digitized from vector Fig.1(a)", source_location="JAP Fig.1(a) p.13", value_type="figure-read (digitized)",
        notes="Derived by this dataset (not reported by authors): W(0 V) = eps*eps0/(C/A) with eps=10.16 gives "+("1.67" if b=="ZnSe" else "2.55")+" um. Use to put the normalised depth of Fig.1(b) on an absolute scale.")
add(**F, buffer="all", quantity="contact (device) area", value=0.24, unit="cm^2", condition="", method="", source_location="JAP Fig.3 caption; SI Fig.1", value_type="measured", notes="")

# Chen 2018
C=dict(source_id="chen2018", year=2018, buffer="ZnSe nanocrystal")
add(**C, quantity="ZnSe NC film optical band gap", value=2.81, unit="eV", condition="ITO/ZnO/ZnSe films 60-120 nm, annealed 380 C 10 min",
    method="Tauc plot (alpha h nu)^2", source_location="PDF p.4, Fig.1d inset", value_type="measured", notes="")
add(**C, quantity="ZnSe NC absorption peak (solution)", value=412, unit="nm", condition="NCs in toluene (= 3.0 eV)", method="UV-vis",
    source_location="PDF p.4, Fig.1c", value_type="measured", notes="Authors say gap from peak is inaccurate (size distribution).")
add(**C, quantity="ZnSe NC size", value=30, unit="nm", condition="TEM, average ('~')", method="TEM", source_location="PDF p.4, Fig.1a", value_type="measured", notes="Large aggregation noted.")
add(**C, quantity="ZnSe NC film RMS roughness", value_low=4.8, value_high=6.5, unit="nm", condition="4.8 with EDT, 6.5 without", method="AFM",
    source_location="PDF p.7, Fig.3c,d", value_type="measured", notes="")
add(**C, quantity="EQE maximum", value_low=47, value_high=50, unit="%", condition="~47% without EDT, ~50% with EDT, near 575 nm; cut-off ~850-860 nm",
    method="EQE", source_location="Fig.4c (PDF p.9)", value_type="figure-read (approx., by eye)", notes="Authors note EQE below their CdS/CdSe-buffer devices across the whole spectrum; they suspect interface recombination from the CdTe/ZnSe lattice mismatch.")
add(**C, quantity="band alignment diagram", unit="", condition="", method="schematic", source_location="Fig.2b (PDF p.6)", value_type="not measured",
    notes="Schematic only (type-I, CB spike at ZnSe/CdTe). XPS in Fig.2d is Zn 2p / Se 3d core-level composition only, not a band-offset measurement.")

# USF
U=dict(source_id="usf1997", year=1997, buffer="ZnSe (CSS)")
add(**U, quantity="parasitic interfacial-compound absorption edge", value=625, unit="nm", condition="thick ZnSe; low- and high-temperature processing",
    method="spectral response + transmission of layer left after CdTe removal", source_location="NREL/SR-520-22707 p.20 (PDF p.23)", value_type="measured",
    notes="'Relatively sharp cut off at about 625 nm' (~2.0 eV): a compound that absorbs light but does not collect current. Persisted with all processing <=450 C and with no anneals.")
add(**U, quantity="typical Voc of CdTe/ZnSe devices", value_low=400, value_high=550, unit="mV", condition="most Phase I devices", method="J-V",
    source_location="NREL/SR-520-22707 p.20", value_type="measured (range stated in text)", notes="Population statement, no individual values.")
U8=dict(source_id="usf1998", year=1998, buffer="ZnSe (CSS)")
add(**U8, quantity="CSS ZnSe composition (EDS)", value_low=55, value_high=56, unit="at.% Zn", condition="two CSS films; Se 44-45 at.%; single-crystal reference 56/44",
    method="EDS", source_location="NREL/SR-520-25941 Table 7 p.16", value_type="measured", notes="Authors conclude films stoichiometric.")
add(**U8, quantity="effect of CdCl2 amount on Voc", unit="mV", condition="evaporated CdCl2 3-6 kA vs 10-15 kA on split samples (11 devices)",
    method="J-V", source_location="NREL/SR-520-25941 p.16, Fig.10", value_type="measured (qualitative)",
    notes="On average Voc higher with the thinner (3-6 kA) CdCl2 layer; variation within 3-6 kA not significant. Per-device delta-Voc values only in Fig.10 (not digitized).")
add(**U8, quantity="Voc spread on one substrate", value_low=470, value_high=720, unit="mV", condition="two cells, same substrate, same ZnSe deposition-rate regime",
    method="J-V", source_location="NREL/SR-520-25941 p.15", value_type="measured", notes="ZnSe thickness uniform within 2-5%.")

# Nelson 1995 band offset
add(source_id="nelson1995", year=1995, buffer="ZnSe on CdTe(100)", quantity="valence band offset Delta E_v (ZnSe/CdTe)", value=0.20, unit="eV",
    condition="ZnSe grown stepwise at 200 C on p-CdTe(100) single crystal, in situ", method="synchrotron soft X-ray photoemission + RHEED",
    source_location="J. Appl. Phys. 78, 2537 (1995) abstract (OSTI 91888)", value_type="measured",
    notes="Abstract only; full text (AIP) not read, so sign convention, error bar and any conduction-band offset given there are unverified. Single-crystal epitaxial interface, not a CdCl2-treated polycrystalline device.")
# Acharya 2015 (not measured offsets)
A=dict(source_id="acharya2015", year=2015, buffer="ZnSe (thermal evaporation, 700 nm) / CdTe (1 um), quartz, Ag contacts, as-deposited")
add(**A, quantity="conduction band offset Delta E_c", value=0.19, unit="eV", condition="", method="electron-affinity rule (drawn, not measured)",
    source_location="Appl. Nanosci. 5, 1003 (2015) p.1006, Fig.4", value_type="not measured (model)",
    notes="Listed because many SCAPS papers use the same electron-affinity values. Disagrees with the measured photoemission valence band offset (nelson1995).")
add(**A, quantity="valence band offset Delta E_v", value=1.12, unit="eV", condition="", method="electron-affinity rule (drawn, not measured)",
    source_location="Appl. Nanosci. 5, 1003 (2015) p.1006, Fig.4", value_type="not measured (model)", notes="See above.")
add(**A, quantity="built-in potential qV_bi", value=0.9, unit="eV", condition="", method="calculated from Eg, Fermi levels and Delta E_c (Eq.7)",
    source_location="p.1006", value_type="not measured (calculated)", notes="C-V intercept was 'too large', attributed to an insulating interdiffusion layer. Frequency-dependent C-V (100 kHz vs 2 MHz) indicates interface traps.")
add(**A, quantity="dark diode ideality factor n", value_low=1, value_high=2, unit="", condition="n~2 below 0.1 V; n~1 for 0.1-0.17 V; n>2 above 0.17 V",
    method="dark I-V", source_location="p.1005, Fig.2b", value_type="measured", notes="No illuminated J-V reported. Series resistance ~253 ohm (absolute; area not given). SCLC (I ~ V^2) at high bias.")
# Samantilleke
add(source_id="samantilleke1998", year=1998, buffer="ZnSe/CdSe (electrodeposited)", quantity="interdiffusion layer absorption edge (Zn1-xCdxSe)", value=2.16, unit="eV",
    condition="glass/ITO/ZnSe/CdSe after 350 C anneal; second edge 1.70 eV = CdSe", method="optical absorption",
    source_location="Thesis p.229 and p.239 (PDF p.240, 250)", value_type="measured", notes="Evidence of Zn/Cd interdiffusion at ZnSe/CdSe; no ZnSe edge visible.")

with open(sys.argv[1],"w",newline="") as f:
    w=csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(R)
print(len(R),"rows")
