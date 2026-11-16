# Design study: levers on the calibrated 21.4% cell (design)

**Baseline.** The ident best fit, under Sesame's interface-state front model: dEc −0.30 eV, S 5.2 cm/s, φ_b 0.50 eV,
bulk τ 100 ns.
- Dead FTO and ZnO, the stored front Fi_m of 4.10 eV, and optics T_front 0.9 / R_back 0.2.
- 300 K, 1 sun, Rs 0, and no radiative recombination (as calibrated).
- **Model baseline: Voc 872.5 mV, Jsc 27.06 mA/cm², FF 77.81%, eta 18.37%.** EQE-integrated Jsc is 27.05.
- Measured: 875.5 / 30.43 / 80.48 / 21.44. The measured EQE integrates to 27.69 mA/cm², so the J-V Jsc is 9.9% above
  the EQE.

**Each design is reported four ways:**
- the absolute model numbers;
- Δ against its branch baseline;
- the requested projection: 21.44% × eta / eta_baseline;
- an EQE-anchored projection: 19.51% × eta / eta_baseline, where 19.51% = 875.5 mV × 27.69 mA/cm² × 80.48% is the
  measured cell with its EQE-integrated Jsc.

The "lever" columns in `design_results.csv` isolate each lever against the same point with that lever at its
baseline value.

**SQ limit at the front gap (1.41 eV, SCAPS AM1.5G):** Voc 1146.4 mV, Jsc 31.51 mA/cm², eta 32.29%. 90% of the SQ Voc
is 1031.8 mV.

## Step 1: one lever at a time

Every lever is isolated from its own reference point.

| Lever | Setting | ΔVoc (mV) | ΔJsc | ΔFF | Δeta (abs) | projected gain |
|---|---|---|---|---|---|---|
| **Front offset** (from −0.30, S 5.2) | −0.20 | +76.9 | +0.01 | +3.35 | +2.49 | +2.90 |
| | −0.10 | +96.1 | +0.02 | +7.89 | +4.11 | +4.79 |
| | 0 / +0.10 | +97.3 | +0.02 | +8.31 | **+4.25** | **+4.96** |
| | +0.20 | +97.2 | +0.02 | +8.24 | +4.23 | +4.93 |
| | +0.30 (spike blocks: FF falls) | +97.2 | +0.02 | +5.20 | +3.43 | +4.00 |
| Front offset at S 52 (from −0.30, S 52: 16.10%) | 0 / +0.10 / +0.20 | +205–207 | +0.02 | +7.5–8.0 | +6.3–6.5 | +7.3–7.6 |
| Interface S at dEc 0 (from 5.2) | 52 | −2.7 | 0 | −0.64 | −0.23 | −0.27 |
| | 521 | −25.6 | 0 | −2.89 | −1.34 | −1.56 |
| | 5210 | −94.8 | 0 | −4.15 | −3.19 | −3.73 |
| Bulk τ at dEc −0.30 | 300 ns / 1 µs | +0.2 / +0.3 | +0.02 | +0.05 | +0.03 | +0.04 |
| Bulk τ at dEc 0 | 300 ns / 1 µs | +4.7 / +6.5 | +0.01 / +0.02 | +0.87 / +1.26 | +0.35 / +0.50 | +0.41 / +0.58 |
| NA scale at dEc 0, τ 300 ns | ×0.3 | −38.7 | 0 | −0.35 | −1.00 | −1.17 |
| | ×3 | +32.4 | 0 | +0.03 | +0.78 | +0.91 |
| | **×10** (grid edge; Voc 1041 mV > 90% SQ) | +66.7 | +0.02 | +0.84 | **+1.82** | **+2.13** |
| Back contact at dEc 0 (from φ_b 0.50) | 0.30 / 0.10 / ohmic | +10.6 / +13.8 / +11.6 | ≤ +0.03 | +0.57 | +0.40 / +0.49 / +0.43 | +0.47 / +0.57 / +0.50 |
| Optics at baseline | (a) MAR, T_front 0.97 | +3.7 | **+2.10** | −0.08 | +1.49 | +1.74 |
| | (b) FTO 150 nm | +0.5 | **+0.28** | −0.03 | +0.20 | +0.23 |
| | (c) both | +4.2 | **+2.41** | −0.11 | +1.70 | +1.99 |
| | (c) at dEc 0 | +1.5 | +2.41 | +0.01 | +2.06 | +2.40 |
| Absorber 2.5 µm at dEc 0, τ 300 ns | 3.5 → 2.5 µm | −8.7 | −0.36 | +0.02 | −0.50 | −0.58 |

**The levers that matter, ranked by projected gain:**

1. **Remove the front cliff: dEc 0 to +0.20 eV, +4.3% abs (projected +5.0).**
   - Interface recombination stops limiting Voc: it falls from 93% of the recombination at Voc to 1.5%.
   - This holds only while S stays below ~50 cm/s. At dEc 0, S 521 already costs 1.3% abs and S 5200 costs 3.2%.
   - The window is narrow on the spike side: +0.30 eV blocks photocurrent and FF falls 3 points.
   - At the baseline cliff, S 52 instead of 5.2 would cost 2.3% abs. So with a less clean buffer, removing the cliff
     matters even more (+6.5% abs).
2. **Absorber doping ×10 (NA 1e17 → 3e17 graded), +1.8% abs (projected +2.1).** ×3 gives +0.8% (+0.9).
   - It only pays once the cliff is gone, and ×10 is the grid edge.
   - With radiative recombination added (B = 1e-10 cm³/s) the ×10 gain shrinks to +1.4% abs.
3. **Optics, MAR plus 150 nm FTO, +1.7–2.1% abs (projected +2.0–2.4).** The Jsc gain is +2.41 mA/cm²: MAR gives
   +2.10 and thinner FTO +0.28.
4. **Back contact and bulk τ, about +0.4–0.5% abs each, and only without the cliff.**
   - φ_b ≤ 0.30 or ohmic gives +11–14 mV.
   - τ 1 µs gives +6.5 mV. At the cliff, τ changes nothing (+0.3 mV), as expected.
   - A thinner absorber (2.5 µm) loses 0.5% abs.

## Step 2: combined designs (base branch)

Step-1 choices (`design_choices.json`):
- **Realistic dEc +0.20:** the best within −0.10 to +0.20 at S 52. The plateau from 0 to +0.20 is flat within
  0.2% abs; +0.10 gives the same result within 0.02%.
- **Aggressive dEc 0:** best at S 5.2.
- **NA ×10.**

The two designs:
- **Realistic:** dEc +0.20, S 52, τ 300 ns, NA ×10, φ_b 0.30, MAR, FTO 150 nm.
- **Aggressive:** dEc 0, S 5.2, τ 1 µs, NA ×10, ohmic back, MAR, FTO 150 nm.

| Design | Voc (mV) | Jsc (J-V / EQE) | FF | eta | ΔVoc / ΔJsc / ΔFF / Δeta | projected (21.44×) | projected Jsc | EQE-anchored |
|---|---|---|---|---|---|---|---|---|
| baseline | 872.5 | 27.06 / 27.05 | 77.81 | 18.37 | — | 21.44 | 30.43 | 19.51 |
| realistic | 1051.7 | 29.54 / 29.54 | 85.86 | **26.68** | +179.2 / +2.48 / +8.06 / +8.31 | 31.14 | **33.22 > SQ** | 28.34 |
| aggressive | 1054.4 | 29.56 / 29.55 | 88.02 | **27.44** | +181.9 / +2.50 / +10.22 / +9.07 | 32.02 | **33.24 > SQ** | 29.14 |

The EQE curves are in `design_eqe.csv` and in `design_results.png` (right panel), against the measured EQE. MAR
lifts the plateau from about 88% to 95%; the thinner FTO lifts the response below 400 nm.

## Step 3: uncertainty from the calibration valley

The same design changes are applied to each branch:
- dEc, τ, NA and optics are set to the design value.
- S is ×10 the branch's S for the realistic design and ×1 for the aggressive design.
- The back contact goes to 0.30 eV, or stays ohmic where it already is.
- Branches with σ keep the parallel-domain σ on.

| Branch | baseline (Voc / FF / eta) | realistic: eta / projected / EQE-anchored | aggressive: eta / projected / EQE-anchored |
|---|---|---|---|
| base (−0.30, S 5.2) | 872.5 / 77.81 / 18.37 | 26.68 / 31.14 / 28.34 | 27.44 / 32.02 / 29.14 |
| (i) −0.34, S 1.83, σ 15 meV | 882.5 / 77.33 / 18.47 | 26.53 / 30.80 / 28.03 | 27.33 / 31.73 / 28.87 |
| (ii) −0.34, S 1.83, σ 60 meV, ohmic | 848.3 / 78.36 / 17.99 | 25.12 / 29.93 / 27.24 | 25.50 / 30.40 / 27.66 |

**Band across branches:**

| Design | model eta | projected | EQE-anchored |
|---|---|---|---|
| realistic | 25.1–26.7% | 29.9–31.1% | 27.2–28.3% |
| aggressive | 25.5–27.4% | 30.4–32.0% | 27.7–29.1% |

The fluctuation-heavy branch is the low end: σ 60 meV holds Voc at about 985 mV whatever the design does.

## Step 4: sanity limits

**Voc above 90% of the SQ Voc (1031.8 mV)** is flagged on:
- NA ×10 at dEc 0: 1041 mV;
- realistic and aggressive in the base branch and branch (i): 1047–1054 mV, 91–92% of SQ.

Branch (ii) stays at 86%.

**The requested projection is not physical for the optical designs.** It multiplies the model Jsc by 30.43/27.06 =
1.125, which gives a projected Jsc of 33.2 mA/cm², above the SQ Jsc of 31.5. Projected efficiencies of 31–32% sit at
the 32.3% SQ efficiency.
- The factor comes mostly from the J-V Jsc excess over the EQE (+9.9%) and from the model's FF deficit (77.8 against
  80.5).
- Neither is a property of the designs.
- The EQE-anchored projection (27–29%) and the absolute model numbers (25–27%) are the defensible ones.
- Even these assume Rs = 0 and no shunt (FF 86–88%), so they are upper bounds.

**Radiative sensitivity** (B in the absorber; K_rad = 0 in the calibrated model):

| Case | B 1e-11 cm³/s | B 1e-10 cm³/s |
|---|---|---|
| realistic | −1.6 mV, −0.08% abs | −12.5 mV, −0.64% abs |
| aggressive | −1.8 mV, −0.06% abs | −13.7 mV, −0.46% abs |
| NA ×10 at dEc 0 | −1.2 mV | −9.6 mV, −0.38% abs |

**Extra finding: what limits Voc once the cliff is gone.**
- **Electrons lost at the back contact take over.** They are 58% of the recombination at Voc at dEc 0, and 82–88% in
  the combined designs (S_n,back 1e7 cm/s, no electron reflector).
- **Lowering S_n to 1e3 cm/s helps only with an ohmic back:** +23 mV at dEc 0, and +64 mV in the aggressive design
  (1119 mV, 29.2%, 97.6% of the SQ Voc).
  - With B 1e-10 that gain collapses to +3 mV (1058 mV). Voc then sits at the internal radiative limit.
- **With a Schottky back (φ_b 0.3–0.5 eV) S_n changes nothing.** The downward band bending under the hole barrier
  draws electrons to the contact at any S_n.
- **A real electron reflector needs a conduction-band barrier layer.** This 7-layer structure does not contain one, so
  that was not simulated.

## SCAPS cross-check inputs (`defs_scaps/`, not run)

Three files: `Design_baseline.def`, `Design_realistic.def` (dEc +0.20) and `Design_aggressive.def` (dEc 0).

- **Interface block:** on the IL/ZnO boundary, neutral, σ_n (ZnO side) = σ_p (absorber side) = 1e-16 m², vth 1e5 m/s,
  level at mid interface gap (reference 9, Et 0). N = S/(σ·vth): 5.21e9 m⁻² for S 5.2 and 5.21e10 m⁻² for S 52.
- **IL:** keeps only its bulk SRH block.
- **Dead window:** a block in ZnO and FTO (Nt 1e18 cm⁻³, σ 1e-13 cm², τ 1e-12 s).
- **Front filter:** MAR uses `3%mirror.ftr`, included here; copy it into SCAPS's `filter/` folder first.
- **Back:** Fi_m 5.51 eV for φ_b 0.30, or flatband + recalculate for ohmic. Front: stored Fi_m 4.10 eV.

**Round trip:** reading these defs back into Sesame reproduces the design numbers exactly. Baseline 872.5 / 27.06 /
77.81 / 18.37, realistic 1051.7 / 29.54 / 85.86 / 26.68, aggressive 1054.4 / 29.56 / 88.02 / 27.44.

## Files

| File | What it is |
|---|---|
| `design.py` | Designs, cells, runs (`run`), SCAPS export (`defs`). |
| `design_report.py` | Tables, choices, EQE, SQ checks, figure (`report`). |
| `curves/` | One J-V per design and domain. |
| `defs/` | SCAPS-format inputs Sesame reads. |
| `design_results.csv` | Every design: absolute, Δ, lever Δ, projections, SQ ratios and flags. |
| `design_eqe.csv` | EQE of the baseline and the combined designs. |
| `design_choices.json` | Step-2 choices read from step 1. |
| `design_results.png` | Projected efficiency of every design (with the SQ limit), and EQE. |
| `defs_scaps/` | SCAPS cross-check defs, the MAR filter and a README. |

**Bug found and fixed during the study.** The design key first rounded τ to 6 decimals, so 100 ns and 300 ns runs
shared one curve. All curves were then regenerated.
