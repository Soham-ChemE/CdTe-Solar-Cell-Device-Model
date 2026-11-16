# II-VI heterojunction band offsets with Quantum ESPRESSO: validated workflow and the ZnSe/CdTe offset

Directory: `dft/interface/` (QE 7.6, PseudoDojo NC PBE standard v0.4, 80 Ry). Everything here was computed
in this directory on 2026-11-15/16 with at most 4 MPI ranks while SCAPS jobs shared the machine.

## Summary

- **Validation.** The lineup workflow (PBE superlattice lineup + PBE+SOC bulk references) with the natural-offset
  correction "L" (semicore reference + absolute [001] deformation potentials from homojunctions) gives
  dEv(ZnTe/CdTe) = +0.11 eV (XPS -0.1; error +0.2) and dEv(CdS/CdTe) = +0.73 eV (XPS 0.65-0.94; inside).
  Li et al. 2009 natural offsets (+0.32, +1.17) overshoot both by 0.2-0.5 eV; the classic core-level-fixed method
  misses CdS/CdTe by 0.5-0.8 eV; the "deformation potential relative to Vbar" route is unusable in a pseudopotential
  code. Method accuracy on dEv: about +-0.15-0.2 eV for 6-11 % misfit.
- **ZnSe/CdTe (13 % misfit): dEc = Ec(ZnSe) - Ec(CdTe) = +0.55 +- 0.3 eV** (dEv = Ev(CdTe) - Ev(ZnSe) =
  +0.65 eV); PBE+SOC +0.58, with HSE06 bulk correction +0.52 (+0.40 if the correction is evaluated at a_exp).
  Not near 0 (Li 2009) and not as large as +1.0 (Nelson 1995 read with CdTe's valence band higher); closer to the
  latter in the sense that it is a substantial electron-blocking spike.
- **Pseudomorphic limits:** ZnSe strained to CdTe in-plane: dEc = -0.06 eV; CdTe strained to ZnSe: +0.53 to +0.67 eV.
- **ZnSe/CdSe:** dEv = +0.21 eV, dEc = +0.75 eV (zb-CdSe gap 1.74 eV); linear interpolation formula for
  ZnSe/CdSe(x)Te(1-x) in section 7.
- **Nelson 1995:** full text not obtainable (closed access; abstract only): dEv = 0.20 eV, sign/definition
  unverified; either sign implies dEc >= 1.0 eV. No other independent ZnSe/CdTe measurement exists in the sources
  searched (the Acharya et al. 2015 I-V/C-V paper takes its offsets from the electron-affinity rule).
- **Main accuracy limits:** the volume (absolute deformation potential) correction for large misfit, the two-pair
  validation set, and the functional; superlattice size (n = 3 -> 4: 0.03 eV) and k-mesh (0.01 eV) are minor.

## 1. Sign convention (read this first)

For a pair written `X/CdY` (X = ZnTe, CdS, ZnSe; CdY = CdTe or CdSe):

    dEv = Ev(CdY) - Ev(X)                         (Li et al. 2009 / Wei-Zunger: dEv(AX/BY) = Ev(BY) - Ev(AX))
    dEc = Ec(X) - Ec(CdY) = [Eg(X) - Eg(CdY)]_exp - dEv

dEv > 0 means the CdTe valence band lies above the partner's. dEc > 0 means the partner's conduction band lies
above CdTe's (a spike, seen from the absorber). The task text wrote "dEc = dEv + dEg", which holds only with the
opposite sign of dEv; the measured and Li-2009 numbers quoted in the task (ZnTe/CdTe dEv 0 to -0.15 with
dEc 0.8-0.95; ZnSe/CdTe Li dEc +0.04) are consistent with the convention above, so that is what is used.
Experimental gaps: CdTe 1.50, ZnSe 2.70, ZnTe 2.26, CdS 2.42, zinc-blende CdSe 1.74 eV.

**Reference values in this convention, with the sign source:**

| pair | value | source and sign evidence |
|---|---|---|
| ZnTe/CdTe | **-0.1 eV** (XPS) | Li et al. 2009, p. 212109-1, left column: "the XPS measurement obtained a value of -0.1 eV" (Spath et al., Thin Solid Films 480-481, 204 (2005)). ZnTe VBM above CdTe. |
| ZnTe/CdTe | **-0.09 eV** (Wei-Zunger 1998 core-level calc.) | same sentence: "the calculated valence band offset dEv(ZnTe/CdTe) is -0.09 eV". |
| ZnTe/CdTe | **+0.32 eV** (Li 2009 revised) | Fig. 2c VBM energies: CdTe 3.95, ZnTe 3.63 (higher number = higher VBM; Eq. 1 gives dEv(AX/BY) = Ev(BY) - Ev(AX)). |
| CdS/CdTe | +0.65 to +0.94 eV (XPS, range given in the task); Li 2009 **+1.17** | Fig. 2c: CdTe 3.95, CdS 2.78. Niles and Hochst photoemission (MBE cubic CdS on CdTe(110), abstract only): CdS VBM 0.65 eV below CdTe. |
| ZnSe/CdTe | Li 2009 **+1.16** (dEc +0.04); Nelson 1995 **magnitude 0.20**, sign not verifiable | Fig. 2c: CdTe 3.95, ZnSe 2.79. Nelson: section 8. |

Sign check on the Li 2009 PDF: the PDF's embedded text layer drops the minus signs, the Delta and the
parentheses in that sentence (it extracts as "EvZnTe/CdTe is 0.09 eV ... a value of 0.1 eV"). The printed page
shows "-0.09 eV" and "-0.1 eV"; a high-resolution crop of the printed sentence is saved as
`refs/li2009_p1_ZnTe_CdTe_sign_evidence.png`. Li's statement that "VBM energies increase with increasing cation
atomic number" describes their revised Fig. 2 (CdTe 0.32 eV above ZnTe), which has the opposite sign to the
XPS value they quote; it is not a statement about the measurement. The task's range "0 to -0.15 eV" for
ZnTe/CdTe therefore has the correct sign in this convention, and so does the derived dEc = 0.76 - dEv = 0.76-0.91 eV.

## 2. Protocol actually used

1. **Superlattice** (`make_superlattice.py`). Unrelaxed (A)n(B)n (001) zinc-blende superlattice, simple tetragonal
   cell, in-plane vectors a/sqrt2 along [110] and [1-10], c along [001]; 4 atoms (2 cation + 2 anion planes) per
   conventional-cell height per material; n = number of conventional cells per material (n = 3: 24 atoms,
   6 monolayers per side, the same thickness as Li et al.'s n = 6; n = 4: 32 atoms). Both materials cubic at
   a_avg = (a_A + a_B)/2, ideal positions, experimental lattice constants (CdTe 6.481, ZnTe 6.101, CdS 5.818,
   ZnSe 5.668, CdSe 6.077 A). PBE, 80 Ry, k 6x6x1 (Gamma-centred), conv_thr 1e-9 Ry (first run) or 1e-8 Ry.
   Common-anion and common-cation cells have two equivalent interfaces. ZnSe/CdTe has no common ion, so a
   stoichiometric cell necessarily contains one Se-Cd-bonded and one Te-Zn-bonded interface (see section 6).
2. **Lineup** (`run_superlattice.py`, `lineup.py`). pp.x plot_num = 11 (V_bare + V_Hartree, no xc), written both as
   the pp.x file for average.x and as a cube. Planar average along z, then macroscopic average with a box window
   equal to the monolayer period a_avg/2. Primary numbers use an exact Fourier-space box filter on the cube data;
   average.x (`average.in`: 1 file, weight 1, 3000 points, idir 3, window a_avg/2 in bohr) is run as a cross-check.
   dV = Vbar(CdY) - Vbar(X) is taken at the centres of the two layers; plateau ripple and slope are recorded.
3. **Bulk references** (`bulk_refs.py`, `run_bulk_set.py`). Same pseudopotentials and cutoff, 2-atom fcc cell,
   8x8x8 k. For every material at its own a_exp, at the a_avg of each pair it enters, and at a_exp(1 +- 1 %):
   Gamma-point VBM, cell-average Vbar (pp.x plot_num 11), and the semicore levels at Gamma (Cd 4s, Cd 4p, Zn 3s,
   Zn 3p, Te 4d, Se 3d) used as "core levels". Volume deformation potentials: `deformation_potentials.csv`.
   The step from the strained superlattice to each material's own volume is the whole difficulty; four
   treatments are computed and reported side by side (section 4):
   - **A** (no volume correction): dEv = dV + (E_VBM - Vbar)_CdY(a_avg) - (E_VBM - Vbar)_X(a_avg). This is exact
     for the coherent superlattice at a_avg and equals the natural offset only if the absolute VBM deformation
     potentials are zero.
   - **C** (core-level method, Wei-Zunger 1998 / the logic of an XPS Kraut measurement): the cation-s semicore
     level is assumed to have zero absolute deformation potential:
     Ev(M) = Vbar_M(SL) + (E_c - Vbar)_M(a_avg) + (E_VBM - E_c)_M(a_exp). All 9 (or 6) choices of semicore level
     are evaluated; their spread is reported.
   - **L** (Li et al. 2009 style): C plus the absolute deformation potential of the cation-s level, computed here
     from a strained/unstrained (001) homojunction of each compound (5 % uniaxial [001] strain, `homojunction.py`).
     Li et al. angular-average [001], [110] and [111] homojunctions; only [001] was affordable here.
   - **V** (the "volume deformation potential of the VBM relative to Vbar" route suggested in the task): Vbar
     treated as a fixed reference, i.e. (E_VBM - Vbar) evaluated at a_exp. Reported only to document that it fails
     (section 4): Vbar contains the G = 0 part of the local pseudopotentials, which scales as 1/Omega, so
     d(E_VBM - Vbar)/dlnV is about -10 to -12 eV and carries no physical meaning.
4. **Spin-orbit** (`run_bulk_set.py soc`). PBE+SOC with the fully relativistic PseudoDojo set at a_exp; Gamma8-Gamma7
   splitting; VBM shift Delta_SO/3 per material.
5. **dEc** from experimental gaps as in section 1.
6. **HSE06 bulk correction** (optional, reported separately): shift of (E_VBM - Vbar) between HSE06 (nq 2x2x2,
   k 6x6x6, ecutfock 120 Ry, same settings as `../bulk`) and PBE, computed at each pair's a_avg (the lineup
   geometry) and applied as d_HSE(CdY) - d_HSE(X); also evaluated at a_exp with nq 2 and nq 3 to show its
   sensitivity. The superlattice lineup stays PBE.
7. **Pseudomorphic limits** (`pseudomorphic.py`, `pseudomorphic_offsets.py`): explicit strained superlattices,
   in-plane lattice of the substrate, strained layer tetragonal with c from linear elasticity, and bulk references
   computed at exactly the same strain (SR and FR), so no deformation-potential assumption enters.

## 3. Convergence and consistency checks

| check | result | verdict |
|---|---|---|
| k-mesh, ZnTe/CdTe n=3: 4x4x1 (9 k) vs 6x6x1 (16 k) | dV -2.1595 vs -2.1480 eV (11.5 meV) | 6x6x1 used; residual k error estimated <~0.005 eV, **not explicitly converged beyond 6x6x1** |
| superlattice thickness, ZnTe/CdTe n=3 vs n=4 (6x6x1) | dV -2.1480 -> -2.1528 eV (-4.7 meV); L +0.112 -> +0.107 eV; ripple 0.6 meV at n=4 | converged to 0.005 eV |
| superlattice thickness, ZnSe/CdTe n=3 vs n=4 (6x6x1) | dV -4.3830 -> -4.4123 eV (-29 meV); both interface-resolved steps move by the same -29/-30 meV; plateau slopes -1.7/-2.3 -> -1.2/-1.8 meV/A | **converged to ~0.03 eV, not to 0.01 eV**; n = 4 used for the ZnSe/CdTe result; a further change of the same sign of up to ~0.03 eV for n > 4 cannot be excluded |
| plateau flatness (+-a/2 around layer centres) | ripple 1.4 meV ZnTe/CdTe, 5.5 meV CdS/CdTe, 14 meV ZnSe/CdTe (field from two inequivalent interfaces, sec. 6) | ok |
| bulk-likeness of layer centres (projwfc.x, ZnTe/CdTe n=3) | central-atom Zn 3s, Zn 3p, Cd 4s, Cd 4p, Te 4d minus local Vbar equal the bulk values at a_avg within 0-2 meV; interface atoms deviate 14-38 meV | n=3 centres are bulk-like |
| independent route for A and C (SL semicore eigenvalues from projwfc, no Vbar) | A +0.156, C -0.304 eV vs +0.157, -0.304 via Vbar | bookkeeping and signs verified |
| own Fourier filter vs average.x | identical planar averages; dV differs by <0.01 meV (ZnTe/CdTe, CdS/CdTe) and 5 meV (ZnSe/CdTe, average.x box sampling of a large-amplitude planar average) | own filter used |
| cutoff 60/80/100 Ry (bulk E_VBM - Vbar, CdTe, ZnSe, ZnTe, CdS) | 80 -> 100 Ry changes <= 0.4 meV; 60 Ry within 7 meV | 80 Ry converged |
| SCF threshold | 1e-9 Ry (ZnTe/CdTe n=3) and 1e-8 Ry (others) | not tested separately; expected << 1 meV |
| SOC: Delta_SO/3 vs direct FR - SR shift of E_VBM - Vbar | 0.287/0.283 (CdTe), 0.296/0.291 (ZnTe), 0.127/0.130 (ZnSe), 0.014/0.020 (CdS), 0.121/0.125 (CdSe) | Delta_SO/3 rule holds to 6 meV |
| bulk gaps (PBE, Gamma) | CdTe 0.773, ZnSe 1.289, ZnTe 1.254, CdS 1.164, CdSe 0.615 eV, identical to ../bulk | ok |

Computed Delta_SO (PBE, FR PseudoDojo): CdTe 0.860, ZnTe 0.889, ZnSe 0.382, CdSe 0.363, CdS 0.043 eV
(literature cross-check given in the task: 0.9, 0.9, 0.4, -, 0.07). PBE underestimates them by 5-10 %; using the
literature values instead would change dEv(ZnSe/CdTe) by +0.01 eV and dEv(CdS/CdTe) by +0.02 eV.

Volume deformation potentials (eV per unit dlnV, central differences at a_exp +-1 %; `deformation_potentials.csv`):

| | a_gap | VBM rel. Vbar | VBM rel. cation s | absolute D001 of cation s (homojunction, 5 %) | implied absolute a_v = rel. cation s + D001 |
|---|---|---|---|---|---|
| CdTe | -3.03 | -10.8 | -2.36 | +2.15 | -0.21 |
| ZnTe | -4.74 | -10.4 | -2.66 | +2.54 | -0.12 |
| ZnSe | -4.01 | -10.3 | -2.28 | +2.16 | -0.12 |
| CdS | -2.14 | -11.7 | -1.96 | +1.43 | -0.54 |
| CdSe | -2.05 | -11.0 | -2.00 | +1.73 | -0.27 |

The "relative to Vbar" column (-10 to -12 eV) is the G = 0 pseudopotential term, not physics; that is why route V
fails. Relative to any semicore level the VBM deformation potential is -2.0 to -2.7 eV and almost independent of
which level is used (Cd 4s/4p, Zn 3s/3p, Te 4d, Se 3d agree within 0.3 eV). The homojunctions say the semicore
levels themselves move by +1.4 to +2.5 eV per unit dlnV, so the absolute VBM deformation potentials are small
(-0.1 to -0.5 eV), consistent in size (not in sign) with Li, Gong and Wei, PRB 73, 245206 (2006), whose
abstract (full text not read) describes the VBM values as small and positive. The [001]-only homojunction is an approximation to their
angular average; the absolute values above carry that caveat.

## 4. Validation on measured offsets (PBE + SOC, n = 3, 6x6x1)

| pair (mismatch) | A: at a_avg | L: natural, [001] abs. DP | C: core fixed | Li 2009 natural | measured dEv | dEc from L |
|---|---|---|---|---|---|---|
| ZnTe/CdTe (6.0 %) | +0.147 | +0.112 | -0.313 | +0.32 | -0.1 (XPS); range 0 to -0.15 | 0.65 (meas. 0.76-0.91) |
| CdS/CdTe (10.8 %) | +0.854 | +0.732 | +0.156 | +1.17 | +0.65 to +0.94 (XPS) | 0.19 (meas. -0.02 to 0.27) |
| error vs. midpoint (ZnTe, CdS) | +0.22, +0.06 | +0.19, -0.06 | -0.24, -0.64 | +0.40, +0.38 | | |

HSE06 bulk correction (reported separately, as asked). Shift of E_VBM - Vbar, HSE06 minus PBE (eV):

| | CdTe | ZnTe | ZnSe | CdS | CdSe |
|---|---|---|---|---|---|
| a_exp, nq 2 | -0.752 | -0.820 | -0.958 | -0.750 | -0.853 |
| a_exp, nq 3 | -0.640 | -0.687 | -0.816 | -0.633 | -0.734 |
| a_avg of ZnTe/CdTe (6.291), nq 2 | -0.778 | -0.789 | | | |
| a_avg of CdS/CdTe (6.1495), nq 2 | -0.796 | | | -0.709 | |
| a_avg of ZnSe/CdTe (6.0745), nq 2 | -0.805 | | -0.865 | | |
| a_avg of ZnSe/CdSe (5.8725), nq 2 | | | -0.911 | | -0.891 |

The correction applied is the difference at the superlattice's a_avg (the geometry where the lineup is computed):
ZnTe/CdTe +0.011, CdS/CdTe -0.087, ZnSe/CdTe +0.060, ZnSe/CdSe +0.020 eV. Two caveats: (1) going from
nq 2 to nq 3 shifts every material by +0.11 to +0.14 eV, so pair differences move by <= 0.03 eV (q error);
(2) the shift depends on volume (CdTe -0.75 at 6.481 vs -0.81 at 6.0745; ZnSe -0.96 at 5.668 vs -0.87 at
6.0745), so evaluating it at each a_exp instead gives larger corrections (ZnSe/CdTe +0.18 eV at nq 3). Applying it
through the semicore chain of method L is not consistent (HSE moves the semicore levels by 5-7 eV while the
homojunction D001 values are PBE) and is not used.

With the a_avg HSE correction, L becomes +0.123 (ZnTe/CdTe) and +0.645 eV (CdS/CdTe): ZnTe/CdTe is unchanged
within 0.01 eV and CdS/CdTe moves to the lower edge of the measured range. The hybrid correction therefore does
not improve the validation; it is reported, not adopted.

Outcome:
- L and A reproduce CdS/CdTe inside the measured range and are 0.1-0.25 eV too positive for ZnTe/CdTe (they put
  the CdTe VBM 0.11-0.15 eV above ZnTe's; XPS has it 0.1 eV below). Mean absolute error vs. the midpoints:
  L 0.13 eV, A 0.14 eV.
- C (core level fixed, the Wei-Zunger 1998 assumption) gets the ZnTe/CdTe sign right but overshoots it, and misses
  CdS/CdTe by 0.5-0.8 eV. The core-level assumption fails because the semicore levels have large absolute
  deformation potentials (+1.4 to +2.5 eV), exactly as Li et al. 2009 argue.
- Li 2009 revised natural offsets are 0.2-0.5 eV too positive for both pairs. My L lies 0.2-0.5 eV below Li for
  all three pairs (ZnTe 0.21, CdS 0.44, ZnSe 0.51 eV) and the gap grows with mismatch, which is what positive
  angular-averaged absolute VBM deformation potentials (theirs) versus small negative [001]-only ones (mine) would
  produce. Their LDA-LAPW lineups at a_avg are not published, so this attribution is not proven.
- V is unusable (dEv -1.8 eV for ZnTe/CdTe).
- Two validation pairs with spread-out XPS values cannot pin the method below about +-0.2 eV. L is selected as the
  production method; A is the no-correction bound; an empirical one-parameter interpolation between A and C fitted
  to both pairs (`calibrate.py`) is reported as a sensitivity check, not as the answer.

## 5. ZnSe/CdTe result

All values PBE lineup + PBE+SOC bulk references, natural (unstrained) offsets unless stated; dEc uses
Eg(ZnSe) - Eg(CdTe) = 1.20 eV.

| method | n | dEv = Ev(CdTe) - Ev(ZnSe) | dEc = Ec(ZnSe) - Ec(CdTe) |
|---|---|---|---|
| A (both at a_avg = 6.0745 A) | 3 | +0.745 | +0.455 |
| L | 3 | +0.653 | +0.547 |
| C (core fixed) | 3 | -0.214 | +1.414 |
| A (both at a_avg) | 4 | +0.716 | +0.484 |
| **L (production, PBE + SOC)** | **4** | **+0.623** | **+0.577** |
| C (core fixed) | 4 | -0.244 | +1.444 |
| L + HSE06 bulk correction at a_avg (+0.060) | 4 | +0.683 | +0.517 |
| L + HSE06 correction evaluated at a_exp, nq 3 (+0.176; upper bound of the hybrid effect) | 4 | +0.799 | +0.401 |
| calibrated A + f(C - A), f = 0.28 fitted to the two validation pairs (sensitivity only; HSE variant +0.65) | 4 | +0.44 (0.10 to 0.84) | +0.76 (0.36 to 1.10) |
| pseudomorphic P1 (ZnSe strained to CdTe) / P2 (CdTe strained to ZnSe), section 7 | 3 | +0.29 / +1.24 to +1.38 | -0.06 / +0.53 to +0.67 |
| Li et al. 2009 (Fig. 2c) | - | +1.16 | +0.04 |
| Nelson 1995 (abstract; sign unverified) | - | 0.20 in magnitude | +1.00 (or +1.40) |

**Best estimate: dEc(ZnSe/CdTe) = +0.55 eV, 1-sigma uncertainty about +-0.3 eV** (natural offset; dEv = +0.65 eV).
The central value is the mean of the validated PBE+SOC result (+0.58, method L, n = 4) and its HSE06-corrected
variant (+0.52); the HSE correction evaluated at a_exp would give +0.40.
Uncertainty budget (dEc, 1 sigma, added in quadrature = 0.27 eV):
- method error from validation: L residuals +0.19 (ZnTe/CdTe) and -0.06 eV (CdS/CdTe), rms 0.14 eV; scaled by the
  larger volume correction for ZnSe/CdTe (13 % misfit; |C - A| = 0.96 eV vs 0.46 and 0.70 eV): +-0.23 eV;
- functional (PBE vs HSE06 bulk correction, including where it is evaluated): +-0.10 eV;
- [001]-only absolute deformation potential, linear in strain, extrapolated to +-20 % volume: +-0.07 eV
  (spread of D001 between semicore levels times the volume changes);
- interface type (Se-Cd vs Te-Zn bonded, section 6): +-0.04 eV;
- superlattice thickness: n = 3 -> 4 moved dEc by +0.03 eV; allow +-0.03 eV for n > 4; k-mesh +-0.01 eV.

Answer to the central question: the computed natural offset is **neither near 0 nor near +1 eV; it is a positive
spike of about +0.55 eV (68 % range +0.25 to +0.85 eV)**. A dEc near +0.04 eV (Li 2009 natural) sits about
1.7 sigma below, and the Li-type natural offsets overshoot dEv by 0.2-0.5 eV on both validation pairs, which is
exactly what would push dEc down to ~0. A dEc near +1.0 eV (Nelson's 0.20 eV read with the CdTe valence band
higher) sits about 1.5 sigma above; the empirical A-to-C calibration (+0.65 to +0.76 eV, range up to 1.10) leans
that way. A coherently strained ZnSe layer on CdTe would have dEc ~ -0.06 eV (section 7), so the near-zero value
is physically reachable only for a pseudomorphic interface. For the device model: nominal +0.55 eV, sensitivity
bounds +0.25 and +1.0 eV.

## 6. ZnSe/CdTe interface type

A stoichiometric no-common-ion (001) superlattice contains one interface with Se-Cd bonds and one with Te-Zn bonds.
Their different dipoles leave a small field in the layers (macroscopic-average slope -1.7 and -2.3 meV/A, n = 3).
Extrapolating the plateau fits to each interface gives dV = -4.347 eV (Se-Cd) and -4.419 eV (Te-Zn), i.e. the
two interface types differ by 0.07 eV in dEv; the centre-to-centre value used above (-4.383 eV) is their mean.
At n = 4 the same analysis gives -4.376 and -4.449 eV (difference again 0.07 eV).
A polycrystalline interface samples both. Te-Zn-type bonding gives the smaller dEv (dEc larger by ~0.04 eV than
the mean), Se-Cd-type bonding the larger dEv (dEc smaller by ~0.04 eV).

## 7. Pseudomorphic limits, ZnSe/CdSe and the CdSe(x)Te(1-x) interpolation

Pseudomorphic limits (strained layer tetragonal, c from linear elasticity with room-temperature C11/C12:
CdTe 53.5/36.7, ZnSe 85.9/50.6 GPa; at 12.5-14 % misfit this is an extrapolation and the critical thickness is
below one monolayer, so these are bounds, not expected states):

| case | strained-layer geometry | strained-layer gap (exp-anchored) | dEv route (i) explicit SL | dEv route (ii) bulk + D001 | dEc |
|---|---|---|---|---|---|
| P1: ZnSe strained to CdTe in-plane | a_par 6.481, c 4.710 A | ZnSe 1.73 eV | +0.289 | +0.288 | **-0.06** |
| P2: CdTe strained to ZnSe in-plane | a_par 5.668, c 7.596 A | CdTe 0.79 eV | +1.381 (fixed occupations; +1.305 with smearing) | +1.239 | **+0.53 to +0.67** (route i / ii) |

- Route (i) is the explicit pseudomorphic superlattice (n = 3, 4x4x1, Gaussian smearing 0.005 Ry; checked: P1
  superlattice gap 0.50 eV, no charge transfer) with bulk references at exactly the same strain. Route (ii) uses the
  natural L offset (n = 3) plus the bulk VBM shift of the strained layer and its cation-s absolute deformation
  potential. For P1 the two routes agree to 1 meV, which is an independent check of the D001-based volume
  correction used in method L (route (i) uses no deformation potential at all). For P2 the PBE superlattice gap is
  only 0.13 eV, and the 0.005 Ry Gaussian smearing moved 0.02 electrons per cell across it. A rerun with fixed
  occupations (`sl/P2_CdTe_on_ZnSe_n3_fixed`, superlattice gap 0.10 eV, insulating) gives dV -1.199 instead of
  -1.275 eV, and the routes then differ by 0.14 eV. In P2 the PBE superlattice is nearly metallic (strained CdTe
  valence band almost touching the ZnSe conduction band), and the strained CdTe is under 12.5 % in-plane compression,
  where the [001]-only D001 is least trustworthy; I quote both routes as the P2 range.
- Spin-orbit for the strained layer uses the quasi-cubic (Hopfield) 6x6 p-manifold model with the scalar-relativistic
  crystal-field splitting and the cubic Delta_SO. For P1 it reproduces the explicit FR calculation (levels 0, -0.577,
  -0.870 eV vs 0, -0.576, -0.871; SOC shift of the top state 0.039 vs 0.041 eV). For P2 the explicit FR calculation
  is band-inverted at Gamma in PBE (strained CdTe gap closes), so only the model value (HH top shifted by
  Delta_SO/3 = 0.287 eV) is used.
- Strained gaps: experimental cubic gap + PBE change of E_CBM(Gamma) - E_top(Gamma) (scalar-relativistic) + change
  of the SOC shift. ZnSe loses 0.97 eV under the P1 strain, CdTe 0.71 eV under the P2 strain.
- Reading: a thin ZnSe film forced onto CdTe's lattice would have almost no conduction-band spike (-0.06 eV);
  CdTe forced onto ZnSe would keep a +0.53 to +0.67 eV spike. Real polycrystalline interfaces relax within a
  monolayer at this misfit, so the natural value (section 5) is the relevant one; a partially strained interface
  region lies between -0.06 and about +0.6 eV depending on which side carries the strain. The near-zero dEc that
  Li's natural offsets imply is reproduced here only for ZnSe coherently strained to CdTe.

**ZnSe/CdSe** (zinc-blende, 6.9 % misfit, n = 3, 6x6x1; plateaus flat to 1.6 meV, both interfaces Se-bonded):

| method | dEv = Ev(CdSe) - Ev(ZnSe) | dEc = Ec(ZnSe) - Ec(CdSe), Eg(zb-CdSe) = 1.74 eV |
|---|---|---|
| A | +0.251 | +0.709 |
| **L** | **+0.210** | **+0.750** |
| C | -0.197 | +1.157 |
| Li 2009 (CdSe 3.26, ZnSe 2.79) | +0.47 | +0.49 |
| L + HSE06 bulk correction at a_avg (+0.020) | +0.231 | +0.729 |

**Interpolation to ZnSe/CdSe(x)Te(1-x)** (method L, PBE+SOC; ZnSe/CdTe at n = 4, ZnSe/CdSe at n = 3):

    dEv(x) = Ev(alloy) - Ev(ZnSe) = 0.62 (1 - x) + 0.21 x + beta * b * x (1 - x)
    Eg(x)  = 1.50 (1 - x) + 1.74 x - b * x (1 - x)
    dEc(x) = 2.70 - Eg(x) - dEv(x) = 0.58 (1 - x) + 0.75 x + (1 - beta) * b * x (1 - x)

b is the optical bowing of zinc-blende CdSe(x)Te(1-x) and beta the fraction of it carried by the valence band
(VBM rising); neither was computed here. With a literature-scale b of about 0.8 eV (not computed or verified here)
and x = 0.2, dEc = 0.61 eV if the bowing sits entirely in the valence band (beta = 1) and 0.74 eV if it sits
entirely in the conduction band (beta = 0). The same +-0.3 eV uncertainty as for ZnSe/CdTe applies; with the
HSE06 a_avg correction both end members move by -0.06 (CdTe side) and -0.02 eV (CdSe side) in dEc.
Implied CdSe/CdTe natural offset by transitivity (method L, n = 3 for both): Ev(CdTe) - Ev(CdSe) =
0.653 - 0.210 = +0.44 eV (Li 2009: 3.95 - 3.26 = +0.69). A direct CdSe/CdTe superlattice was queued as a
transitivity check but **not run** (dropped for time).

## 8. Measured ZnSe/CdTe offsets: what could and could not be verified

**Nelson 1995.** A. J. Nelson (NREL, single author), "Photoemission investigation of the ZnSe/CdTe heterojunction
band discontinuity", J. Appl. Phys. 78(4), 2537 (1995), doi:10.1063/1.360109, OSTI ID 91888.
Full text: **not obtained.** Unpaywall and Semantic Scholar list it as closed access with no repository copy; the
OSTI record has metadata and abstract only; pubs.aip.org returned a bot-verification page, which I did not try to
get past. What the abstract (OSTI) establishes:
- synchrotron soft-x-ray photoemission plus RHEED; ZnSe overlayers grown stepwise at 200 C on p-type CdTe(100)
  **single crystals**, measured in situ after each step;
- core lines followed: Cd 4d, Zn 3d and Te 4d (no Se core line is named), plus the valence band;
- result: "the valence band offset is dEv = 0.20 eV". The abstract gives a magnitude only. **The sign and the
  exact definition could not be verified.** The usual reading (ZnSe valence band 0.20 eV below CdTe's) gives
  dEc = 1.20 - 0.20 = 1.00 eV. The opposite sign would give dEc = 1.40 eV. Either way this measurement implies
  dEc >= 1.0 eV; it cannot be read as supporting dEc near 0. With 12.5-14 % misfit, a ZnSe overlayer a few nm
  thick on CdTe(100) is far beyond its critical thickness, so the measured interface is relaxed and possibly
  intermixed, and the abstract notes that interfacial chemistry was correlated with the electronic structure.

**Other measurements searched (OSTI, Semantic Scholar/Unpaywall, publisher pages, general web):**
- Acharya, Bangera, Shivakumar, Appl. Nanosci. 5, 1003 (2015), doi:10.1007/s13204-015-0406-x, open access.
  Thermally evaporated p-CdTe/n-ZnSe on quartz, I-V and C-V. Its dEc = 0.19 eV and dEv = 1.12 eV are
  **drawn from the electron-affinity rule, not measured** (the text says the band profile is drawn "using electron
  affinity rule"). Not an independent offset measurement.
- Ray et al., Adv. Theory Simul. (2023), doi:10.1002/adts.202200718: HSE slab calculation, band edges placed with
  Mulliken electronegativities, states a 1.5 % ZnSe/CdTe lattice mismatch (the real value is 13 %); quotes
  VBO 0.08 / CBO 1.04 eV. A calculation, and not one I would use.
- No XPS/UPS, internal-photoemission or I-V-T measurement of pure ZnSe/CdTe was found. Related systems only:
  type-II CdTe quantum dots in a ZnCdSe matrix (Deligiannakis et al., arXiv:1908.00088), cubic CdS on CdTe(110)
  photoemission (Niles and Hochst, abstract: CdS VBM 0.65 eV below CdTe, the low end of the CdS/CdTe range of section 4).

## 9. Wall times (Apple M4, 4 MPI ranks, shared with 4 SCAPS processes; load average 8-20)

| superlattice | atoms | k-points | SCF iterations | pw.x wall (min) |
|---|---|---|---|---|
| ZnTe_CdTe_n3 | 24 | 16 | 14 | 38.7 |
| ZnTe_CdTe_n3_k4 | 24 | 9 | 13 | 20.8 |
| ZnTe_CdTe_n4 | 32 | 16 | 14 | 52.7 |
| CdS_CdTe_n3 | 24 | 10 | 27 | 26.1 |
| ZnSe_CdTe_n3 | 24 | 16 | 15 | 37.8 |
| ZnSe_CdTe_n4 | 32 | 16 | 15 | 51.4 (plus 16 min lost on a first attempt that swapped; restarted with disk_io='high', 4.9 GB) |
| ZnSe_CdSe_n3 | 24 | 16 | 14 | 20.6 |
| P1_ZnSe_on_CdTe_n3 | 24 | 9 | 14 | 16.4 |
| P2_CdTe_on_ZnSe_n3 (smearing / fixed occupations) | 24 | 9 | 16 / 15 | 16.9 / 16.5 |
| homojunctions HJ_{CdTe,ZnTe,ZnSe,CdS,CdSe}_eps5_n2 | 16 | 16 | 12-15 | 16.1, 17.5, 13.7, 13.9, 9.9 |

Bulk: 43 PBE runs 33.5 min in total (median 19 s; tetragonal 4-atom cells up to 3.5 min); 7 PBE+SOC runs 25.6 min
(median 77 s, strained FR cell 10 min); 18 HSE06 runs 36.7 min (nq 2: 45-115 s; nq 3: 2-4.6 min). pp.x 2-4 s,
average.x 2 s, projwfc.x 23 s per superlattice. Whole campaign: 2026-11-15 23:42 to 2026-11-16 07:55 (8.2 h)
(sequential queue, `queue_done.txt` and `logs/queue_runner.log` list every job with its wall time).

## 10. Files

| file | purpose |
|---|---|
| `common.py` | paths, constants, QE runner (<= 4 ranks), output parsers |
| `make_superlattice.py` | builds `sl/<tag>/scf.in`, `pp.in`, `average.in`, `meta.json` for (A)n(B)n (001) |
| `run_superlattice.py` | pw.x scf -> pp.x (plot_num 11) -> average.x for one superlattice |
| `lineup.py` | planar + macroscopic averages, dV, plateau ripple/slope, interface-resolved steps, average.x cross-check |
| `bulk_refs.py`, `run_bulk_set.py` | bulk E_VBM, Vbar, semicore levels (SR, FR/SOC, HSE06, cubic or tetragonal) |
| `sl_core_levels.py` | projwfc.x atom-resolved semicore levels in a superlattice (bulk-likeness check) |
| `homojunction.py` | strained/unstrained (001) homojunctions -> absolute [001] deformation potentials of semicore levels |
| `pseudomorphic.py`, `pseudomorphic_offsets.py` | explicit pseudomorphic ZnSe/CdTe superlattices and their offsets |
| `offsets.py`, `make_results.py`, `calibrate.py` | assemble methods A/C/V/L, SOC, HSE; validation; `results.csv` |
| `bulk_summary.py` | `bulk_summary.csv`, `deformation_potentials.csv` |
| `plot_lineups.py` | `lineups.png` (planar and macroscopic averages of every superlattice) |
| `queue_runner.sh`, `queue_done.txt` | the sequential job queue actually used, with per-job wall times |
| `sl/<tag>/` | inputs, outputs (`scf.out`, `pp.out`, `average.out`, `avg.dat`, `macro_avg.dat`, `lineup.json`, `timings.json`) |
| `bulk/`, `soc/`, `hse/` | bulk reference inputs/outputs, `result.json` per calculation |
| `refs/li2009_apl_offsets.pdf`, `refs/li2009_p1_ZnTe_CdTe_sign_evidence.png` | Li et al. 2009 (author copy from the WMD group site); crop of the printed ZnTe/CdTe sentence with its minus signs |
| `results.csv` | every computed offset (methods A, C, L, V, +HSE06, calibrated, pseudomorphic, best estimates) |
| `calibration.json`, `pseudomorphic.json`, `results_detail.json`, `results_extra.json` | machine-readable intermediate results |
| `bulk_summary.csv`, `deformation_potentials.csv`, `lineups.png` | bulk references, deformation potentials, potential profiles |
| `walltimes.py` | wall-time table from the pw.x outputs |

## 11. Not converged, not verified, or approximate (read before using the numbers)

- **Superlattice thickness:** ZnSe/CdTe moved by 0.03 eV between n = 3 and n = 4 (not converged to 0.01 eV);
  ZnTe/CdTe moved by 0.005 eV (converged). CdS/CdTe and ZnSe/CdSe were run at n = 3 only (plateaus flat to 5.5 and
  1.6 meV).
- **k-mesh:** 6x6x1 vs 4x4x1 differ by 11.5 meV; 6x6x1 itself was not compared with a denser mesh. The pseudomorphic
  superlattices used 4x4x1.
- **Absolute deformation potentials:** only [001] homojunctions (Li, Gong and Wei average [001], [110] and [111]),
  and D001 measured at 5 % strain is applied linearly to volume changes of up to 20 %.
- **Functional:** all lineups are PBE. The HSE06 correction (sections 4-5) is bulk-only, taken at a_avg with
  nq = 2x2x2 (nq 3 at a_exp moves the pair differences by <= 0.03 eV, but every absolute shift by 0.11-0.14 eV),
  and assumes the PBE lineup is unchanged. Where it is evaluated (a_avg vs a_exp) changes the ZnSe/CdTe correction
  from +0.06 to +0.18 eV; this is part of the +-0.10 eV functional uncertainty.
- **Elastic constants** for the pseudomorphic limits are experimental literature values quoted from memory
  (CdTe C11/C12 53.5/36.7 GPa, ZnSe 85.9/50.6 GPa), not re-derived here; linear elasticity at 12-14 % misfit.
- **Validation set:** two pairs, each with a measured range of 0.15-0.3 eV, and the ZnTe/CdTe value rests on one XPS
  study (Spath et al. 2005, as quoted by Li et al.). The ranges in section 4 are those given in the task; I did not
  re-read the original XPS papers.
- **Nelson 1995:** full text not obtained; sign and definition of its 0.20 eV unverified (section 8).
- **zinc-blende CdSe gap:** 1.74 eV assumed for dEc(ZnSe/CdSe) (zinc-blende CdSe is often quoted 1.67-1.74 eV at
  room temperature); dEv does not depend on it.
