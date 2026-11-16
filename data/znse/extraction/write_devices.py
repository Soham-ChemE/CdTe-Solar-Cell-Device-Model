import csv, sys
out = sys.argv[1]
cols = ["source_id","year","buffer","buffer_thickness_nm","buffer_position","absorber","absorber_thickness_um",
        "activation","back_contact","Voc_mV","Jsc_mA_cm2","FF_pct","eta_pct","Vbi_V","NA_cm3","notes","value_type",
        "Rs_ohm_cm2","Rsh_ohm_cm2","source_location","evidence_level"]
R = []
def add(**k): R.append({c: k.get(c, "") for c in cols})

# ---------------- Fedorenko et al. 2015 (JAP 118,165705) / 2016 (MRS Adv 1,937) ----------------
F = dict(source_id="fedorenko2015", year=2015,
         absorber="CdTe (CSS, Tsource 605 C, Tsub 520 C)", absorber_thickness_um="3.5-4.0",
         activation="NP etch, then MgCl2 solution (applied in excess) + anneal 430 C in air 25-30 min",
         back_contact="NP etch 30 s, then Au; no Cu",
         evidence_level="full_text (arXiv v2 = JAP accepted manuscript; MRS Adv preprint)")
common_F = ("Stack: TEC7 glass (SnO2:F)/buffer (magnetron sputtered)/CdS 200 nm (magnetron sputtered at 200 C)/CdTe/Au. "
            "Series identical except buffer. Values are series averages +/- spread (n and illumination not stated). "
            "Contact area 0.24 cm2. Vbi from 1/C2-V at 300 K, 10 kHz. NA column = range of digitized apparent doping rho "
            "(Fig. 1b) over 0.1-0.8 of W_D (x normalised, measured from CdTe/CdS interface); full profile in digitized/.")
add(**F, buffer="ZnSe", buffer_thickness_nm=100,
    buffer_position="HRT buffer on SnO2:F, under CdS (ZnSe not in contact with CdTe)",
    Voc_mV=468, Jsc_mA_cm2=6.22, FF_pct=33.38, eta_pct=0.98, Vbi_V=0.32, NA_cm3="1.2e14-2.5e14",
    notes=common_F + " +/-: eta 0.25, FF 1.92, Jsc 1.33, Voc 22 mV. Rectification vanishes at 230-200 K. Dominant trap 0.50 eV (see defects csv).",
    value_type="averaged",
    source_location="JAP Table I (arXiv:1506.03068v2 p.12) = MRS Adv Table 1 (arXiv:1511.08421v2 p.3); process p.3; Vbi p.4; Fig.1b p.13")
add(**F, buffer="ZnS", buffer_thickness_nm=110,
    buffer_position="HRT buffer on SnO2:F, under CdS (ZnS not in contact with CdTe)",
    Voc_mV=507, Jsc_mA_cm2=6.03, FF_pct=27.61, eta_pct=0.85, Vbi_V=0.54, NA_cm3="1.2e14-5.0e14",
    notes=common_F + " +/-: eta 0.29, FF 3.39, Jsc 1.59, Voc 24 mV. Text/Table say 110 nm ZnS; JAP SI Fig.2 legend says 'ZnS 120 nm'. Rectification vanishes at 230-200 K. Dominant trap 0.75-0.76 eV.",
    value_type="averaged",
    source_location="JAP Table I (arXiv:1506.03068v2 p.12); Vbi p.4; Fig.1b p.13")
add(**F, buffer="ZnO (reference)", buffer_thickness_nm=120,
    buffer_position="HRT buffer on SnO2:F, under CdS",
    Voc_mV=675, Jsc_mA_cm2=20.30, FF_pct=59.25, eta_pct=8.22, Vbi_V=0.68, NA_cm3="8.6e14-1.5e15",
    notes=common_F + " +/-: eta 1.70, FF 2.75, Jsc 1.67, Voc 60 mV. Digitized rho rises to 1.8e16 at W=0 (junction side). Same-lab reference for the ZnSe/ZnS rows.",
    value_type="averaged",
    source_location="JAP Table I (arXiv:1506.03068v2 p.12); Vbi Fig.1a inset p.13; Fig.1b p.13")

# ---------------- Chen et al. 2018, Appl. Sci. 8, 1195 ----------------
C = dict(source_id="chen2018", year=2018, buffer="ZnSe nanocrystal (wurtzite, hot-injection, EDT-free unless stated)",
         buffer_position="inverted stack ITO/ZnO(~40 nm sol-gel)/ZnSe NC/CdTe NC; ZnSe directly on CdTe (light enters via ITO)",
         absorber="CdTe nanocrystal film (5 sintered layers)", absorber_thickness_um=0.45,
         back_contact="MoOx ~8 nm / Au ~80 nm (thermal evaporation); area 0.16 cm2",
         evidence_level="full_text (CC BY 4.0)")
cn = ("Each ~20 nm ZnSe NC layer annealed 150 C 3 min + 380 C 40 s. Single device per condition (statistics not given); "
      "illumination: Xe simulator with AM1.5G filter (intensity not stated). ")
act = lambda T: f"saturated CdCl2/methanol spin-cast, anneal {T} (Table 1 condition); fab section says 330 C 25 min"
for t,j,v,ff,e,rs,rsh,extra in [
    (25,3.58,400,30.17,0.38,67.56,148.18," Internal inconsistency: Jsc*Voc*FF = 0.43%, table PCE 0.38%."),
    (60,4.09,370,29.96,0.45,64.67,132.51,""),
    (80,6.03,440,38.04,1.02,35.84,219.07,""),
    (110,10.35,560,33.30,1.93,26.08,120.76," Best of thickness series."),
    (125,5.61,390,37.83,0.84,33.27,250.40,"")]:
    add(**C, buffer_thickness_nm=t, activation=act("350 C"), Voc_mV=v, Jsc_mA_cm2=j, FF_pct=ff, eta_pct=e,
        Rs_ohm_cm2=rs, Rsh_ohm_cm2=rsh, notes=cn+"ZnSe thickness series."+extra,
        value_type="best" if t==110 else "measured", source_location="Table 1 rows 1-5 (PDF p.8); text p.6")
for T,j,v,ff,e,rs,rsh,extra in [
    ("300 C",7.07,410,33.89,0.99,32.9,115.80,""),
    ("330 C",10.35,510,33.3,1.70,12.55,106.72," Jsc and FF identical to the 110 nm/350 C row (possible transcription duplicate); Jsc*Voc*FF = 1.76%."),
    ("370 C",11.94,630,40.79,3.07,23.50,246.15," Best anneal; identical to the 'WO EDT' row of Table 1."),
    ("400 C",11.23,530,30.49,1.81,32.32,79.59,"")]:
    add(**C, buffer_thickness_nm=110, activation=act(T), Voc_mV=v, Jsc_mA_cm2=j, FF_pct=ff, eta_pct=e,
        Rs_ohm_cm2=rs, Rsh_ohm_cm2=rsh, notes=cn+"CdTe anneal-temperature series."+extra,
        value_type="best" if T=="370 C" else "measured", source_location="Table 1 rows 6-9 (PDF p.8); text p.6")
add(**{**C, "buffer": "ZnSe nanocrystal + 1,2-ethanedithiol (EDT) ligand exchange"}, buffer_thickness_nm=110, activation=act("370 C"),
    Voc_mV=640, Jsc_mA_cm2=13.55, FF_pct=47.33, eta_pct=3.58, Rs_ohm_cm2=19.48, Rsh_ohm_cm2=251.00,
    notes=cn+"Champion device. Internal inconsistency: Jsc*Voc*FF = 4.10% but table/abstract PCE = 3.58% (3.58% matches the Fig. 4a J-V curve by eye). EQE peak ~50% near 575 nm (Fig. 4c, figure-read).",
    value_type="best", source_location="Table 1 'W EDT' (PDF p.8); abstract; text p.8; Fig.4 p.9")
add(source_id="chen2018", year=2018, buffer="CdS nanocrystal (reference, authors' earlier work)", buffer_thickness_nm="",
    buffer_position="inverted stack ITO/ZnO/CdS/CdTe NC", absorber="CdTe nanocrystal film", absorber_thickness_um="",
    activation="", back_contact="MoOx/Au",
    Voc_mV=560, Jsc_mA_cm2=17.26, FF_pct=52.84, eta_pct=5.14,
    notes="Quoted in Chen 2018 text as the group's previous CdS device; not re-measured in this paper. In-text citation [12] points to an efficiency-table paper, so the original source is uncertain.",
    value_type="best", source_location="text p.8", evidence_level="full_text (quoted from prior work)")

# ---------------- USF (Morel, Ferekides) NREL subcontract reports ----------------
U_act = "CdCl2 heat treatment (USF: methanol/CdCl2 dip or evaporated CdCl2; method for this device not stated)"
U_bc = "USF baseline: Br-methanol or NP etch, doped graphite paste (HgTe:Cu) + Ag paste (not stated specifically for this device)"
add(source_id="usf1997", year=1997, buffer="ZnSe (CSS)", buffer_thickness_nm=80,
    buffer_position="CSS ZnSe on CVD SnO2 (borosilicate glass), directly under CSS CdTe; SR suggests ZnSe consumed by alloying",
    absorber="CdTe (CSS)", absorber_thickness_um="", activation=U_act, back_contact=U_bc,
    Voc_mV=726, Jsc_mA_cm2=21.3, FF_pct=58, eta_pct=9,
    notes="Best CdTe/ZnSe device of Phase I ('Thin ZnSe (800 A)', Fig.19). Most CdTe/ZnSe devices in this phase had Voc 400-550 mV and very poor characteristics; thick ZnSe formed an interfacial compound (SR cut-off ~625 nm) that absorbs but does not collect. Thinning ZnSe was the only way to avoid it.",
    value_type="best", source_location="NREL/SR-520-22707 p.20 (PDF p.23), Fig.19", evidence_level="full_text (public DOE/NREL report)")
U98 = dict(source_id="usf1998", year=1998, buffer="ZnSe (CSS, 1-300 Torr He, Tsource 700-780 C, Tsub 560-680 C)",
           absorber="CdTe (CSS)", absorber_thickness_um="", activation=U_act, back_contact=U_bc,
           evidence_level="full_text (public DOE/NREL report)")
add(**U98, buffer_thickness_nm=80, buffer_position="CSS ZnSe on SnO2, directly under CdTe; type I SR shows no ZnSe edge (ZnSe fully consumed)",
    Voc_mV=724, Jsc_mA_cm2=24.8, FF_pct=63, eta_pct=11.3, Rs_ohm_cm2=1.9, Rsh_ohm_cm2=1185,
    notes="SR type I. Starting ZnSe ~800 A. Blue QE ~0.8-0.9 at 400 nm (above the CdS/CdTe reference) and a red-shifted long-wavelength edge, which the authors attribute to Se (and Zn) diffusion into CdTe lowering its gap. Rs units not printed in Table 8 (Rsh given in ohm-cm2).",
    value_type="best", source_location="NREL/SR-520-25941 Table 8 and Fig.11, p.17 (PDF p.20); 11.3% also p.5")
add(**U98, buffer_position="CSS ZnSe on SnO2, directly under CdTe; electrically inactive interfacial compound at front",
    Voc_mV=560, Jsc_mA_cm2=17.0, FF_pct=59, eta_pct=5.6, Rs_ohm_cm2=2.5, Rsh_ohm_cm2=780,
    notes="SR type II: no distinct ZnSe edge; an interdiffusion compound of unknown composition formed at the front (visible after CdTe removal; its transmission matched the SR loss).",
    value_type="measured", source_location="NREL/SR-520-25941 Table 8, p.17-18 (PDF p.20-21)")
add(**U98, buffer_position="CSS ZnSe on SnO2, directly under CdTe; ZnSe appears fully consumed",
    Voc_mV=550, Jsc_mA_cm2=9.8, FF_pct=33, eta_pct=1.8, Rs_ohm_cm2=1, Rsh_ohm_cm2=54,
    notes="SR type III: ZnSe consumed like type I but poor collection.", value_type="measured",
    source_location="NREL/SR-520-25941 Table 8, p.17-18 (PDF p.20-21)")
add(source_id="usf1998", year=1998, buffer="CdS (reference)", buffer_thickness_nm="", buffer_position="CdS on SnO2 under CdTe",
    absorber="CdTe (CSS)", activation=U_act, back_contact=U_bc,
    Voc_mV=840, Jsc_mA_cm2=23.0, FF_pct=68, eta_pct=13.1, Rs_ohm_cm2=1.5, Rsh_ohm_cm2=900,
    notes="Same-table CdTe/CdS reference for the ZnSe rows.", value_type="measured",
    source_location="NREL/SR-520-25941 Table 8, p.17 (PDF p.20)", evidence_level="full_text (public DOE/NREL report)")
for v,lab in [(470,"A or C"),(720,"A or C")]:
    add(**U98, buffer_position="CSS ZnSe on SnO2, directly under CdTe",
        Voc_mV=v, notes="One of two CdTe/ZnSe cells on the same substrate (Fig.9 SR curves A, C); text gives only the Voc spread 470-720 mV. ZnSe thickness uniform within 2-5%, films stoichiometric by EDS, so the spread was attributed to uncontrolled interdiffusion.",
        value_type="measured", source_location="NREL/SR-520-25941 p.15 (PDF p.18), Fig.9")

# ---------------- Potlog / Spalatu 2011 (abstract level) ----------------
add(source_id="potlog2011_spalatu2011", year=2011, buffer="ZnSe (CSS; wurtzite/zinc-blende polytype films)", buffer_thickness_nm="",
    buffer_position="glass/SnO2/ZnSe/CdTe superstrate, ZnSe directly under CdTe; best devices used a Zn interlayer at ZnSe/CdTe",
    absorber="CdTe (CSS)", absorber_thickness_um="",
    activation="CdCl2 solution + elevated-temperature air anneal of completed device before back contact",
    back_contact="", eta_pct="4.7 (about)",
    notes="Only efficiency available (abstracts). ZnSe thickness varied (values not in abstracts). Zn incorporation at ZnSe/CdTe interface 'doubles' Jsc. Same group/paper: CdS/CdTe ~9.9%, ZnTe/CdTe ~1.3%. Full texts paywalled (IEEE, MRS). Chen 2018 cites this work as the vacuum-processed ZnSe/CdTe benchmark.",
    value_type="best", source_location="Potlog et al. PVSC 2011 abstract (IEEE Xplore 6186211); Spalatu et al. CAS 2011 abstract (IEEE Xplore 6095844); Potlog et al. MRS Proc. 1324 abstract",
    evidence_level="abstract_only")
add(source_id="potlog2011_spalatu2011", year=2011, buffer="CdS (reference)", buffer_position="glass/TCO/CdS/CdTe superstrate",
    absorber="CdTe (CSS)", activation="CdCl2 solution + air anneal", eta_pct="9.9 (about)",
    notes="Same-paper CdS/CdTe reference.", value_type="best",
    source_location="Potlog et al. PVSC 2011 abstract (IEEE Xplore 6186211)", evidence_level="abstract_only")

# ---------------- Armstrong 2005 thesis (abstract level) ----------------
add(source_id="armstrong2005", year=2005, buffer="ZnSe or ZnSxSe1-x (abstract does not say which gave the best cell)",
    buffer_position="superstrate; CSTE buffer then CdTe deposited in same chamber without breaking vacuum",
    absorber="CdTe (CSTE)", Voc_mV=460, Jsc_mA_cm2=17, eta_pct="approaching 3",
    notes="Best cell from abstract. Full thesis PDF behind a Cloudflare human check (not read). FF not given.",
    value_type="best", source_location="Northumbria Research Portal thesis abstract", evidence_level="abstract_only")

# ---------------- Samantilleke 1998 thesis ----------------
add(source_id="samantilleke1998", year=1998, buffer="ZnSe (electrodeposited, n-type) + CdSe", buffer_thickness_nm=250,
    buffer_position="glass/ITO/ZnSe/CdSe(250 nm)/CdTe/Au; ZnSe separated from CdTe by CdSe; ZnSe/CdSe interdiffusion layer (Zn1-xCdxSe, ~2.16 eV edge)",
    absorber="CdTe (electrodeposited)", absorber_thickness_um=1.5,
    activation="air anneal 350 C 40 min (no CdCl2 mentioned), then etch (NaOH/Na2S2O7)", back_contact="Au",
    Voc_mV=250, Jsc_mA_cm2=15, FF_pct=60, eta_pct=0.9,
    notes="Approximate values ('~'). Inconsistent within thesis: abstract Jsc ~10 mA/cm2, FF ~0.7; p.241 Jsc 16 mA/cm2. Illumination intensity not stated in pages read; Voc*Jsc*FF does not give 0.9% at 100 mW/cm2. Early device: Voc ~200 mV, FF 0.36, eta 0.2% (Jsc quoted as 10 uA/cm2 on p.235 but 0.4 mA/cm2 on p.240).",
    value_type="best", source_location="Thesis section 6.3, pp.227, 235, 238 (Fig.6.4.2), 240-241 (PDF pp.238-252)",
    evidence_level="full_text (scanned thesis, read from page images)")

# ---------------- Xiao et al. 2014 ZnS/CdS (comparison, abstract level) ----------------
add(source_id="xiao2014", year=2014, buffer="ZnS/CdS combined window", buffer_thickness_nm="",
    buffer_position="ZnS + CdS window on commercial SnO2/SnO2:F soda-lime glass (layer order not stated in abstract)",
    absorber="CdTe", eta_pct=12.3,
    notes="ZnS comparison point: ZnS together with CdS can give >12% (vs Fedorenko ZnS/CdS 0.85%). Various ZnS/CdS thickness combinations; values not in abstract.",
    value_type="best", source_location="Xiao et al. PVSC 2014 abstract (IEEE Xplore 6925418)", evidence_level="abstract_only")
add(source_id="xiao2014", year=2014, buffer="CdS (reference)", buffer_position="CdS window on SnO2/SnO2:F soda-lime glass",
    absorber="CdTe", eta_pct=13,
    notes="Same-paper CdS reference.", value_type="best",
    source_location="Xiao et al. PVSC 2014 abstract (IEEE Xplore 6925418)", evidence_level="abstract_only")

with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(R)
print(len(R), "rows")
