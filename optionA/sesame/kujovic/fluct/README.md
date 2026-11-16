# Can absorber band-gap fluctuations mimic the cliff + back-barrier signature? (fluct)

Kujovic 21.4% cell, Sesame model from `../ident`. The absorber gap fluctuates laterally with a Gaussian spread σ. This
is a parallel-domain model (Grabitz, Rau & Werner 2005):

- **Domains.** Each domain has its gap shifted by δ, with f_cb 0.5. The buffer/IL offsets follow the shifted absorber
  edges and the absorption edge shifts with δ. The back metal stays fixed in absolute energy, so the back barrier is
  φ_b + δ/2 in each domain.
- **Simulation.** Ten domains with δ from −0.30 to +0.30 eV were simulated at 7 temperatures plus 300 K. The 0.5-sun
  curves were simulated directly, because superposition fails with a back barrier.
- **Composite.** J(V) = Σ w(δ) J_δ(V), with ln Jd interpolated on a 5 meV δ grid and Gaussian weights to ±4.5σ.
  7-point Gauss–Hermite is used as a check.
- **χ².** The same as in ident: 13 Voc(T) points with σ 4 mV and the light factor X free, plus Voc 875.5 ± 8 mV and
  FF 80.48 ± 1.5 at 1 sun. The optional σ prior is 52 ± 8 meV.
- **Scope.** Bulk τ is 100 ns. φ_b is 0.50 eV except in stage C.

Measured: high-T slope −1.70 mV/K with intercept 1.357 eV (T > 310 K); low-T slope −0.74 mV/K (T < 260 K).

## 1. Fluctuations alone on the spike (stage A: dEc +0.10, S 1e3/1e4, ohmic or φ_b 0.50, σ 0–80)

| back | S (cm/s) | σ = 0 | 30 | 45 | 60 | 80 meV |
|---|---|---|---|---|---|---|
| ohmic | 1e3 | 6095 | 4353 | 2939 | 2032 | **1381** |
| ohmic | 1e4 | 2572 | 2191 | 1883 | 1638 | 1385 |
| φ_b 0.50 | 1e3 | 3739 | 3795 | 4076 | 4154 | 3962 |
| φ_b 0.50 | 1e4 | 1919 | 3054 | 3580 | 4120 | 4966 |

**The best spike case gives χ² 1381.** The best cliff gives 15.7 with S free, or 19.0 with S ≥ 1 cm/s, a
**Δχ² ≈ 1360** in favour of the cliff.

- **Ohmic back.** σ lowers Voc and bends Voc(T), but the low-T slope stays at −1.9 to −3.6 mV/K and the 216 K Voc
  stays 70–170 mV too high.
- **With the barrier.** σ makes the fit worse.

Fluctuations alone cannot reproduce the signature.

## 2. Joint refit over (dEc, S, σ), φ_b 0.50

The S scan is the ident ridge ± 0.5 decade, interpolated quadratically in log S. σ runs 0–80 meV in 5 meV steps. The
dEc grid was extended to −0.54 eV, at which point extensions stopped on request.

| S bound | σ prior | best dEc | best S (cm/s) | best σ (meV) | χ² | dEc 95% (Δχ² 3.84) | dEc 95% (Δχ² 6.2) |
|---|---|---|---|---|---|---|---|
| none | no | −0.46 | 0.080 | 60 | 15.7 | −0.49 to −0.335 | −0.50 to −0.31 |
| none | yes | −0.46 | 0.080 | 60 | 16.7 | −0.48 to −0.42 | −0.50 to −0.40 |
| S ≥ 1 | no | −0.34 | 1.83 | 15 | 19.0 | −0.349 to −0.301 | −0.354 to −0.295 |
| S ≥ 1 | yes | −0.34 | 2.18 | 30 | 32.6 (prior 7.6) | −0.375 to −0.333 | −0.385 to −0.328 |
| S ≥ 10 | no | −0.26 | 18.6 | 0 | 41.3 | −0.272 to −0.258 (grid-limited) | −0.279 to −0.256 |
| S ≥ 10 | yes | −0.30 | 10.4 | 20 | 71.7 (prior 16) | −0.312 to −0.280 | −0.319 to −0.267 |

**Notes on the table.**

- **Unsimulated points.** Where the scanned S window lies wholly below the bound, the χ² at the window's upper edge is
  only a lower bound (`fluct_profile_Sbound.csv`, `lower_bound`). Such points are treated as excluded only when that
  bound already passes the Δχ² level.
- **S ≥ 10, no prior.** −0.46 eV was not simulated at S ≥ 10. Its window-edge value at S 0.13 cm/s is Δχ² 1.2.
  Raising S by two decades on a −0.46 eV cliff would collapse Voc, but this is not simulated.
- **φ_b.** It was fixed at 0.50 here; see section 4.

**With S unbounded, the minimum slides along the S–dEc valley.** σ pushes dEc deeper and S down. The profile along
the valley, minimised over S and σ ≤ 80:

| dEc (eV) | −0.54 | −0.50 | −0.46 | −0.42 | −0.38 | −0.34 | −0.30 | −0.26 | −0.22 | −0.14 | +0.06 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Δχ² | 22.8 | 5.2 | 0 | 4.2 | 7.3 | 3.4 | 7.3 | 25.6 | 93.6 | 204 | 472 |
| best σ (meV) | 70 | 65 | 60 | 50 | 40 | 15 | 0 | 0 | 0 | 0 | 0 |
| best log10 S | −2.03 | −1.60 | −1.10 | −0.72 | −0.22 | 0.26 | 0.72 | 1.27 | 1.79 | 3.11 | 5.30 |

- **The valley floor is flat** within Δχ² ≈ 7 from −0.30 to −0.50 eV. That is the size of the numerical scatter: at
  σ = 0, this χ² differs from ident by up to 7 near the minimum. The bumps at −0.38 and −0.34 are therefore not
  meaningful.
- **The valley closes on the deep side,** at Δχ² 23 by −0.54 eV, but only at S ≈ 0.01–0.1 cm/s. That is two to three
  decades below any measured CdTe front-interface S (≥ ~26 cm/s by CL; < 100 cm/s for MgZnO/CdSeTe).
- **Mechanism.** Along the valley, σ takes over the job of interface recombination. The σ²/2kT term lowers Voc and
  the extrapolated intercept. In the deep part, S is so low that interface recombination no longer sets Voc. At σ = 0,
  −0.46 eV gives an intercept of 1.575 eV and Voc 954 mV.
- **With S unbounded, the runaway is the result.** Once σ is free, Voc(T) alone cannot separate "moderate cliff, S of
  a few cm/s, little σ" from "deep cliff, negligible S, σ ≈ 60 meV". Only the S bound, or an independent σ, breaks it.

**Is the spike still excluded with σ free? Yes.**

| S bound | no σ prior | with σ prior |
|---|---|---|
| none | Δχ² 472 | Δχ² 514 |
| S ≥ 1 | Δχ² 469 | Δχ² 498 |
| S ≥ 10 | Δχ² 447 | Δχ² 459 |

The MOCVD XPS value, −0.22 eV, stays excluded: Δχ² 90 with S ≥ 1 and no prior.

## 3. Does a cliff remain necessary?

Yes. The spike is excluded in every case, and a cliff of at least about −0.26 eV is required under every bound.

- **With the physical bound S ≥ 1 cm/s, the answer is the ident answer.** The best fit is −0.34 eV with σ 15 meV,
  95% range −0.35 to −0.30 eV. σ improves χ² by only about 4 over σ = 0.
- **The XPS CSS value, −0.32 eV,** is inside the range with S ≥ 1 and no prior. With the σ prior it falls outside,
  at Δχ² ≈ 10, interpolated linearly between −0.34 and −0.30.

## 4. Back contact against σ (stage C, at dEc −0.34, S 1.83 cm/s fixed)

| back | best σ (meV) | χ² | with σ prior | Voc300 (mV) | low-T slope (mV/K) |
|---|---|---|---|---|---|
| ohmic | 60 | **26.0** | **27.0** (σ 60) | 848 | −1.01 |
| φ_b 0.45 | 0 | 69.2 | 105.0 | 886 | −0.69 |
| φ_b 0.50 | 15 | **19.3** | 33.8 (σ 25) | 883 | +0.33 |
| φ_b 0.55 | 65 | 101.5 | 104.2 | 852 | +0.63 (FF 74%) |

At fixed S, the ohmic back with σ = 0 gives χ² 108. At σ = 60 it gives 26.0.

**Can fluctuations replace the back barrier for the low-T flattening? Yes, at the cliff; no, at the spike.**

- **At −0.34 eV, an ohmic back with σ ≈ 60 meV comes within Δχ² 6.7 of the φ_b 0.50 fit,** without re-optimising S.
  - Its Voc(T) part is better than the barrier fit's: 12.4 against 14.0.
  - Its low-T slope is closer to the measured −0.74 mV/K: −1.01 against +0.33. The barrier fits roll over instead.
  - Its deficit comes from the 1-sun Voc: 848 against 875.5 mV, χ²_Voc 11.6.
- **With the σ prior, the ohmic back is the better solution:** 27.0 against 33.8.
- **φ_b is not monotonic with σ.** 0.45 eV prefers no fluctuations. 0.55 eV needs σ 65 and costs about 6 points of FF.
  If a barrier is present it is pinned near 0.50 eV, but the barrier itself is not required once σ ≈ 50–60 meV.
- **Untested.** The ohmic branch was evaluated at one (dEc, S) point only. Its own optimum (S, dEc) is not mapped, so
  26.0 is an upper bound on its best χ².

## Caveats

- **The parallel-domain model is the maximum-effect limit.** It has no lateral coupling between domains. A physical
  σ of 52 meV, as in Kuciauskas, maps to a smaller effective σ here, so the prior over-weights fluctuations.
- **Numerical noise.** The dV grids are 0.02–0.03 V. The σ = 0 checks against ident agree within a few units of χ²
  near the minimum and within about 40% for poor fits (`fluct_checks.csv`). GH-7 against the fine integration differs
  by 10–20% in χ²; truncating at 3.5σ instead of 4.5σ makes no difference.
- **Unconverged high-gap domains.** The δ +0.18 and +0.30 domains often did not converge to the full voltage sweep.
  Their ln Jd is extrapolated linearly; their weight is at most 1% at σ ≤ 60.
- **Model choices.** The metal is fixed in absolute energy, so the barrier varies per domain. dEg/dT is −0.4 meV/K.
  Bulk τ is fixed at 100 ns.

## Files

- **Code:** `fluct.py` (run, half, analyze) and `fluct_analysis.py`.
- **Curves:** `curves/` holds per-domain J-V, 1 sun and 0.5 sun.
- **Tables:**
  - `fluct_A_scores.csv`
  - `fluct_B_scan_{noprior,prior}.csv`, `fluct_sigma_vs_dEc.csv`
  - `fluct_profile.csv`, `fluct_profile_Sbound.csv`
  - `fluct_C_phib.csv`, `fluct_checks.csv`, `fluct_summary.csv`
  - `best_B.csv`: the unbounded σ-free best
- **Figures:** `fluct_results.png` and `fluct_sigma_vs_phib.png`.
