# ZnSe (and ZnS) buffered CdTe cells: calibration dataset

Measured data for CdTe solar cells that used a ZnSe buffer or window layer, plus ZnS rows for comparison. It is meant to calibrate a SCAPS-1D study of why ZnSe-buffered CdTe cells underperform the 17-25 % that uncalibrated simulations predict.

Compiled 2026-11-15. Every number comes from a source listed below. Nothing is interpolated or guessed. A cell is blank when the source does not report the value. Values read off figures are labelled `figure-read`. Values I calculated, rather than the authors, are labelled `derived` and give the formula.

## Files

| File | Contents |
|---|---|
| `znse_devices.csv` | 27 rows. One row per device, condition or averaged series: J-V parameters, stack, process, Vbi and N_A where reported. |
| `znse_defects_transport.csv` | 41 rows. Trap energies, densities and prefactors; DOS broadening; Rs activation energy; back barrier; rectification-loss temperature; band offsets; film properties. |
| `digitized/fedorenko2015_fig1b_apparent_doping_vs_normalised_depth.csv` | Apparent doping rho(W_D) for the ZnSe, ZnS and ZnO series: 270 points from the vector paths of JAP Fig. 1(b). |
| `digitized/fedorenko2015_fig1a_mott_schottky_300K_10kHz.csv` | 1/C^2-V for the ZnSe and ZnS cells: 128 points from JAP Fig. 1(a). |
| `extraction/` | The scripts used for text extraction, rendering, digitizing and writing the CSVs. They are kept for audit only and are not needed to use the data. |
| `pdf/` | Source PDFs (not redistributed; each source below gives its DOI or open copy). |

Extra columns in `znse_devices.csv`:
- `Rs_ohm_cm2`, `Rsh_ohm_cm2`: series and shunt resistance where the source tabulates them.
- `source_location`: the table, figure or page each number comes from.
- `evidence_level`: `full_text` or `abstract_only`.

`value_type` takes these values:
- `measured`: a single reported device.
- `averaged`: a series mean with its spread.
- `best`: a champion device as stated by the authors.

Where a source gives a value as `~X` or `about X`, the CSV keeps that wording.

## Main findings for the modelling study

1. **Not every measured ZnSe/CdTe cell is below 5 %.** In 1995-98, the University of South Florida (Ferekides and Morel) made CSS ZnSe/CdTe cells on SnO2:
   - 9.0 % in Phase I: Voc 726 mV, Jsc 21.3 mA/cm2, FF 58 %.
   - 11.3 % in Phase II: Voc 724 mV, Jsc 24.8 mA/cm2, FF 63 %, Rsh 1185 ohm cm2.

   The authors' own spectral response shows that the ~80 nm ZnSe in these cells had been **consumed by interdiffusion**:
   - There is no ZnSe absorption edge.
   - The blue response is above that of the CdS reference.
   - The long-wavelength edge is red-shifted, which the authors attribute to Se and Zn diffusing into CdTe.

   When the ZnSe survives, performance collapses:
   - Type II and III cells reached 5.6 % and 1.8 %.
   - Most Phase I cells had Voc 400-550 mV.
   - Thick ZnSe forms a dead interfacial compound that absorbs below about 625 nm but does not collect current.

   The best "ZnSe" cells were therefore effectively SnO2 / Se,Zn-alloyed CdTe devices, not cells with a ZnSe window that stayed intact.
2. **Three different device classes are mixed in the literature.** They should not be fitted with one model.
   - **(a) ZnSe directly on CdTe:**
     - USF CSS: 1.8-11.3 %.
     - Potlog and Spalatu CSS: about 4.7 %, with a Zn interlayer that doubles Jsc.
     - Chen nanocrystal: up to 3.58 %.
     - Armstrong CSTE: "approaching 3 %".
   - **(b) ZnSe as a resistive buffer under CdS:** Fedorenko, 0.98 %. Here ZnSe never touches CdTe.
   - **(c) ZnSe/CdSe/CdTe stack:** Samantilleke, about 0.9 %.
3. **Fedorenko's collapse is an absorber effect, not a ZnSe/CdTe band-offset effect.** CdS separates ZnSe from CdTe, yet against the ZnO-buffer control:
   - N_A drops about fivefold, from about 1e15 to about 1.2-2.5e14 cm^-3 (digitized).
   - Vbi falls from 0.68 V to 0.32 V.
   - A deep trap appears at 0.50 eV with N_it about 8-9e15 cm^-3 (peak N_t 1.6-2.8e16 cm^-3 eV^-1).
   - Rectification vanishes below 230-200 K.

   The authors attribute this to impeded Cl activation in CdTe grown on these buffers. A model that keeps ideal CdTe bulk and varies only the interface cannot reproduce these cells.
4. **Band offset: one measurement, and it disagrees with the usual SCAPS inputs.**
   - The only measured ZnSe/CdTe offset found is Delta E_v = 0.20 eV (Nelson 1995): synchrotron photoemission on epitaxial ZnSe/CdTe(100), abstract only.
   - The electron-affinity rule, as used by Acharya 2015 and typical SCAPS papers, gives Delta E_v about 1.12 eV and Delta E_c about +0.19 eV.

   Suppose Nelson's 0.20 eV means the CdTe valence band lies 0.20 eV above ZnSe's. Then with E_g(ZnSe) = 2.67-2.81 eV and E_g(CdTe) about 1.5 eV, the implied conduction-band spike is about +1.0 eV.

   This is my derivation, conditional on a sign convention I could not check. The difference between about 0.2 eV and about 1.0 eV of spike decides whether an abrupt ZnSe/CdTe junction blocks electrons. No measured offset exists for ZnSe/CdSeTe.
5. **Interdiffusion is the common thread.** The USF reports, Samantilleke's Zn1-xCdxSe layer at 2.16 eV, and Acharya's "insulating interdiffusion layer" all report interdiffusion. Potlog and Spalatu's Zn interlayer is a deliberate interface modification at the same ZnSe/CdTe junction. For SCAPS, a graded Zn/Se-alloyed front region, or a thin defective interlayer, may matter more than the ZnSe bulk parameters.

## Sources, licences and where each number came from

### 1. Fedorenko et al. 2015 / 2016 (Liverpool): `fedorenko2015`
- **JAP:** Y. G. Fedorenko, J. D. Major, A. Pressman, L. J. Phillips, K. Durose, "Modification of electron states in CdTe absorber due to a buffer layer in CdTe/CdS solar cells", *J. Appl. Phys.* 118, 165705 (2015). https://doi.org/10.1063/1.4934680. Copyright AIP.
  - Read via arXiv:1506.03068v2, https://arxiv.org/abs/1506.03068. Its page 1 carries the JAP citation, so it is the accepted manuscript. It includes the Supplemental Information (SI) on pp. 18-22.
  - File: `pdf/fedorenko2015_jap_arxiv1506.03068v2.pdf`.
- **MRS Advances:** same authors, "Electronic Properties of CdTe/CdS Solar Cells as Influenced by a Buffer Layer", *MRS Advances* 1(14), 937-942 (2016). https://doi.org/10.1557/adv.2016.69. Copyright MRS.
  - Read via arXiv:1511.08421v2, https://arxiv.org/abs/1511.08421.
  - File: `pdf/fedorenko2016_mrsadv_arxiv1511.08421v2.pdf`.
- Both arXiv copies carry the arXiv non-exclusive distribution licence 1.0. They are kept locally only.
- **Where the numbers are:**
  - J-V: JAP Table I (arXiv p. 12), identical to MRS Table 1 (p. 3).
  - Stack and process: JAP p. 3.
  - Vbi: p. 4.
  - Trap energies: p. 5.
  - Broadening: p. 6.
  - Rs E_A and back barrier: p. 4, SI Figs. 2-3.
  - Rectification loss: p. 9.
  - SCLC trap density: p. 8.
  - N_it labels and the mobility value of about 0.1: MRS version only (Fig. 3, p. 5).
- **Stack:** TEC7 glass (SnO2:F) / sputtered buffer / sputtered CdS 200 nm at 200 C / CSS CdTe 3.5-4.0 um (Tsource 605 C, Tsub 520 C).
  - Buffers: ZnO 120 nm, ZnS 110 nm or ZnSe 100 nm.
  - Treatment: NP etch, then MgCl2 in excess at 430 C in air for 25-30 min, then NP etch 30 s, then Au with no Cu.
  - Contact area 0.24 cm^2.

### 2. Chen et al. 2018: `chen2018`
- Y. Chen, X. Mei, X. Liu, B. Wu, J. Yang, J. Yang, W. Xu, L. Hou, D. Qin, D. Wang, "Solution-Processed CdTe Thin-Film Solar Cells Using ZnSe Nanocrystal as a Buffer Layer", *Appl. Sci.* 8(7), 1195 (2018). https://doi.org/10.3390/app8071195. Licence **CC BY 4.0**.
- MDPI refused curl (403), so I read the full text in a browser at mdpi.com. The table was pulled from the HTML.
- The PDF was then fetched from the Semantic Scholar mirror and checked against the HTML: identical Table 1.
- File: `pdf/chen2018_applsci_8_1195.pdf`.
- **Where the numbers are:**
  - Table 1 (PDF p. 8).
  - Fabrication: p. 3.
  - Optics: p. 4.
  - Champion and CdS comparison: p. 8.
  - EQE: Fig. 4c, p. 9.

### 3. University of South Florida reports (Morel, Ferekides et al.): `usf1997`, `usf1998`
- **Phase I:** D. L. Morel, C. S. Ferekides, "Advanced Processing of CdTe- and CuInxGa1-xSe2-Based Solar Cells, Phase I Annual Subcontract Report, 18 April 1995 - 17 April 1996", NREL/SR-520-22707 (March 1997).
  - File: `pdf/usf_morel_ferekides_1997_NREL-SR-520-22707.pdf`.
  - ZnSe: p. 20 (PDF p. 23), Fig. 19.
- **Final report:** D. L. Morel, C. S. Ferekides, R. Bhatt, et al., "... Final Report, 18 April 1995 - 31 May 1998", NREL/SR-520-25941 (November 1998). Also at https://digitalcommons.usf.edu/ege_facpub/41.
  - File: `pdf/usf_morel_ferekides_1998_NREL-SR-520-25941.pdf`.
  - ZnSe: pp. 5, 14-18 (PDF pp. 8, 17-21). Table 7: EDS. Table 8: J-V. Figs. 8-11.
- **Download:** nrel.gov did not resolve from this environment. Both files came from `https://docs.nlr.gov/docs/legosti/old/22707.pdf` and `https://docs.nlr.gov/docs/fy99osti/25941.pdf`.
- **Licence:** US DOE-sponsored subcontractor reports, publicly released through NTIS and OSTI. No Creative Commons licence is stated.
- **Process for the ZnSe devices:**
  - CSS ZnSe from a pre-sublimed ZnSe/Al2O3 source, 1-300 Torr He, Tsource 700-780 C, Tsub 560-680 C.
  - Deposited on CVD SnO2 on borosilicate glass, followed by CSS CdTe.
  - CdCl2 treatment: methanol dip or evaporation, with evaporated 3-6 kA vs 10-15 kA compared.
  - The USF baseline contact is doped graphite paste (HgTe:Cu) with Ag. The reports do not state the contact separately for the ZnSe cells, so I mark it as baseline.
  - CdTe thickness is not given.
- **ZnS:** sputtered ZnS/CdTe devices "exhibited very poor characteristics" (22707, p. 20). No numbers are given, so there is no CSV row.

### 4. Potlog, Spalatu et al. 2011 (Moldova State University / TalTech), abstract level: `potlog2011_spalatu2011`
- T. Potlog, N. Spalatu, V. Fedorov, N. Maticiuc, C. Antoniuc, V. Botnariuc, J. Hiie, T. Raadik, V. Valdna, "The performance of thin film solar cells employing photovoltaic ZnSe/CdTe, CdS/CdTe and ZnTe/CdTe heterojunctions", *37th IEEE PVSC*, pp. 1365-1370 (2011). https://doi.org/10.1109/PVSC.2011.6186211.
  - Reports η of about 4.7 % (ZnSe), 9.9 % (CdS) and 1.3 % (ZnTe).
  - CdCl2 solution plus air anneal of the completed device before the back contact.
  - Zn at the ZnSe/CdTe interface "doubles" Jsc.
- N. Spalatu, D. Serban, T. Potlog, "ZnSe films prepared by the close-spaced sublimation and their influence on ZnSe/CdTe solar cell performance", *CAS 2011*, pp. 451-454. https://doi.org/10.1109/SMICND.2011.6095844.
  - Reports about 4.7 %, and an EQE shape that depends on ZnSe thickness.
- T. Potlog, N. Spalatu, A. Mere, J. Hiie, V. Mikli, "A Comparative Study of the Thin-Film CdTe Solar Cells with ZnSe/TCO and the CdS/TCO Buffer Layers", *MRS Proc.* 1324 (2011). https://doi.org/10.1557/opl.2011.1345.
  - Stack glass/SnO2/ZnSe/CdTe.
  - ZnSe shows wurtzite/zinc-blende polytypism.
  - Best parameters come with a Zn buffer at ZnSe/CdTe.
- Abstracts were read on IEEE Xplore and Cambridge Core. The full texts are paywalled (IEEE and MRS copyright) and were not read, so Voc, Jsc, FF and ZnSe thickness are missing.

### 5. Armstrong 2005, PhD thesis (Northumbria), abstract level: `armstrong2005`
- S. Armstrong, "Investigation of ZnSe and ZnSxSe1-x for application in thin film solar cells", PhD thesis, Northumbria University (2005). Supervisor R. Miles. https://researchportal.northumbria.ac.uk/en/studentTheses/investigation-of-znse-and-znsxse1-x-for-application-in-thin-film--3/
- The abstract gives the best cell as Jsc 17 mA/cm^2, Voc 460 mV and η "approaching 3 %". It does not say whether that cell used ZnSe or ZnSxSe1-x.
- The PDF, on Northumbria and on CORE (core.ac.uk/download/4146933.pdf), is behind a Cloudflare human-verification page, so it was not read.

### 6. Samantilleke 1998, PhD thesis (Sheffield Hallam): `samantilleke1998`
- A. P. Samantilleke, "Electrodeposition of ZnSe, CdSe and CdTe thin film materials and optoelectronic devices", PhD thesis, Sheffield Hallam University (1998). https://shura.shu.ac.uk/20319/. "All rights reserved", copyright of the author.
- File: `pdf/samantilleke1998_shu_phd_thesis.pdf` (scanned).
- Read from page images: section 6.3, thesis pp. 227-241 (PDF pp. 238-252).

### 7. Xiao et al. 2014, ZnS comparison, abstract level: `xiao2014`
- C. Xiao, N. R. Paudel, C. R. Grice, Y. Yu, Y. Yan, "CdTe solar cells using combined ZnS/CdS window layers", *40th IEEE PVSC*, pp. 2428-2430 (2014). https://doi.org/10.1109/PVSC.2014.6925418. IEEE copyright, abstract only.
- Reports 12.3 % with ZnS/CdS against a 13 % CdS reference.

### 8. Nelson 1995, measured band offset: `nelson1995` (defects file only)
- A. J. Nelson, "Photoemission investigation of the ZnSe/CdTe heterojunction band discontinuity", *J. Appl. Phys.* 78(4), 2537-2540 (1995). https://doi.org/10.1063/1.360109. OSTI 91888. AIP copyright, abstract only.

### 9. Acharya et al. 2015, dark I-V only: `acharya2015` (defects file only)
- S. Acharya, K. V. Bangera, G. K. Shivakumar, "Electrical characterization of vacuum-deposited p-CdTe/n-ZnSe heterojunctions", *Appl. Nanosci.* 5, 1003-1007 (2015). https://doi.org/10.1007/s13204-015-0406-x. Creative Commons Attribution (open access).
- File: `pdf/acharya2015_applnanosci_5_1003.pdf`.
- There is no illuminated J-V. The paper's band offsets come from the electron-affinity rule and are flagged as **not measured**.

## Digitizing method

The Fedorenko figures in the arXiv PDFs are vector graphics. I digitized them from the PDF drawing commands with PyMuPDF `get_drawings()` (`extraction/digit_*.py`), using:
- marker centroids,
- the polyline vertices of the ZnO curve,
- the axis tick-mark coordinates.

There was no hand-clicking. Errors come from marker size and plot resolution: about ±3 % in value, and about ±0.005 in normalised depth. Labels from the text bounding boxes sit about 9 pt off the true ticks, so only tick marks were used for calibration.

JAP Fig. 2 (trap DOS) is a raster image. The same data in MRS Fig. 3 is vector, so I digitized that instead.

Three items were read by eye and are marked approximate:
- the broadening inset of JAP Fig. 2(a),
- the Chen EQE (Fig. 4c),
- the USF spectral-response curves.

For the Fedorenko depth axis: x is W_D, normalised and measured from the CdTe/CdS interface (JAP p. 4). Only data at V < 0.5 V were used. To put it on an absolute scale, `znse_defects_transport.csv` gives 1/C^2 at 0 V (digitized) and a **derived** W(0 V):
- ZnSe: 1.67 um.
- ZnS: 2.55 um.
- Formula: W = eps*eps0*A/C, with eps = 10.16 as the paper uses.

## Uncertainties and notes on the sources

- **Chen 2018, Table 1:**
  - Champion (EDT) row: Jsc × Voc × FF = 13.55 × 0.64 × 0.4733 = 4.10 %, but the table and abstract give 3.58 %. By eye, 3.58 % agrees with the Fig. 4a J-V curve, so the 3.58 % value is used.
  - 25 nm row: the product gives 0.43 %, against a printed 0.38 %.
  - 330 C row: it repeats the Jsc (10.35) and FF (33.3) of the 110 nm / 350 C row.
  - The fabrication section says the CdCl2 anneal is 330 C for 25 min, while the thickness series says 350 C. I keep the per-row Table 1 condition.
  - The CdS 5.14 % comparison is quoted from the authors' earlier work, and its in-text reference [12] appears to point to a different paper.
  - The light intensity is not stated.
- **Fedorenko:**
  - The SI Fig. 2 legend says ZnS 120 nm; the text and Table say 110 nm.
  - The Rs E_A is 160-170 meV in the text and labelled 160-220 meV in the figure.
  - The MRS text gives a broadening of "0.26 meV"; the JAP text gives 26 meV.
  - The MRS abstract says "SnSe" where it means ZnSe.
  - The number of cells averaged and the illumination conditions are not stated.
  - The "±" in Table I is not defined as a standard deviation.
- **USF:**
  - The Rs column of Table 8 has no units (Rsh is in ohm cm^2).
  - The 9 % Phase I efficiency is given only as "corresponding to a 9% efficiency"; 0.726 × 21.3 × 0.58 = 8.97 %.
  - CdTe thickness, cell area and contact are not stated for the ZnSe cells.
- **Samantilleke:**
  - Jsc is given as ~10 (abstract), ~15 (p. 235) and 16 mA/cm^2 (p. 241); FF as ~0.7 (abstract) and ~0.6 (body).
  - Voc × Jsc × FF does not give 0.9 % at 100 mW/cm^2, and the light intensity is not stated.
  - The early device's Jsc is "10 µA/cm^2" on p. 235 but "0.4 mA/cm^2" on p. 240.
- **Abstract-only rows** (Potlog/Spalatu, Armstrong, Xiao): the efficiencies are the authors' "about" or "approaching" figures. Whether the Potlog/Spalatu 4.7 % cell had the Zn interlayer is not stated.
- **Nelson ΔE_v = 0.20 eV:**
  - The sign convention and error bar are unverified.
  - It was measured on a 200 C epitaxial interface on single-crystal CdTe(100), not on a CdCl2-treated polycrystalline stack.

## Leads that could not be verified (not in the CSVs)

- **A claimed 7 % ZnSe/CdTe cell (with 11 % CdS/CdTe).** A search-engine summary attributes this to a Moldovan IBN record by Potlog, Hiie, Lughi, Spalatu and Maticiuc. The record (ibn.idsi.md) is behind a Cloudflare human check and could not be opened. The 7 % is unconfirmed, so it is not used.
- **Kaliyaperumal et al., *J. Mater. Sci.: Mater. Electron.* (2025), https://doi.org/10.1007/s10854-025-16294-6.** The abstract summary claims a thermally evaporated ZnSe buffer cell at 19 % with Voc 0.82 V for 70 nm ZnSe. The paper is paywalled and it is unclear whether this is a measured device. It would be far above every other ZnSe/CdTe report, so treat it as unverified.
- **T. L. Chu et al., "High efficiency thin film cadmium telluride solar cells", *AIP Conf. Proc.* 268 (1992), OSTI 5449321.** Cells with MOCVD ZnSe (or ZnO, CdZnS) windows "have significantly lower photovoltage than CdS/CdTe". No numbers are in the abstract.
- **F. Buch, A. L. Fahrenbruch, R. H. Bube, "Photovoltaic properties of five II-VI heterojunctions", *J. Appl. Phys.* 48, 1596 (1977), and Buch's 1976 Stanford thesis (OSTI 7225388).** These cover single-crystal n-ZnSe/p-CdTe made by close-spaced vapour transport, with interface-recombination-limited transport. They are paywalled, and no device numbers were obtained.

## What this data can and cannot constrain in a device model

**Can constrain:**
- **Measured ceilings and floors for each device class.** Intact or partly reacted ZnSe directly on CdTe gives at most about 5-6 %. CdTe alloyed with consumed ZnSe can reach 9-11 %, with Voc of about 0.72 V. ZnSe under CdS gives about 1 %. A calibrated model should reproduce these levels, not 17-25 %.
- **For the Fedorenko ZnSe/CdS/CdTe stack:**
  - N_A(x) profile: 1.2-2.5e14 cm^-3 over most of the SCR, against about 1e15 for ZnO.
  - Vbi = 0.32 V.
  - One Gaussian deep level at E_A = 0.50 eV, with peak N_t 1.6-2.8e16 cm^-3 eV^-1, width δ about 0.07-0.11 eV, and N_it about 8-9e15 cm^-3. The emission prefactor ν0 = 3e5 s^-1 K^-2 can constrain the capture cross-section once N_V is chosen.
  - Rs activation energy 0.16-0.17 eV.
  - Loss of rectification at 200-230 K. This is a strong low-temperature check on any freeze-out or barrier model.
  - The same-process ZnO control gives a direct baseline for which parameters changed.
- **For nanocrystal ZnSe/CdTe (Chen):**
  - Ten distinct ZnSe J-V sets with Rs and Rsh (11 table rows; the 370 C and 'WO EDT' rows are the same device), varying buffer thickness, anneal temperature and EDT treatment.
  - A ZnSe film gap of 2.81 eV.
  - Peak EQE of about 50 %.
  - Voc is about 0.08 V higher than in their CdS device, yet Jsc and FF are lower.
- **For the USF devices:** Voc 724-726 mV with FF 58-63 % for alloyed devices, and Voc 400-560 mV for devices where the ZnSe survived. Together these bracket how much a ZnSe-related loss costs in Voc.

**Cannot constrain:**
- **The ZnSe/CdTe conduction-band offset.** There is one measured valence-band offset, on single crystal, abstract only. It conflicts with the electron-affinity-rule values. Nothing is measured for ZnSe/CdSeTe or for CdCl2- or MgCl2-treated polycrystalline interfaces.
- **ZnSe bulk electronic parameters** (doping, mobility, defect density). No source measures them in a device-relevant ZnSe film.
- **Interface recombination velocity** at ZnSe/CdTe. It is not measured anywhere.
- **Lifetimes.** There is no TRPL and no minority-carrier lifetime for any ZnSe-buffered device.
- **The composition and thickness of the interdiffused layer** in the USF devices. Only spectral-response and transmission evidence exist, with no depth profile.
- **Uniform illumination and area metadata.** Several sources omit light intensity and area. The abstract-only sources give efficiency alone.
- **Absolute depth for the Fedorenko profiles,** except through the derived W(0 V) in the defects file.
