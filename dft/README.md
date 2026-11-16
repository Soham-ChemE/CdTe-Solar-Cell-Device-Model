# DFT (Quantum ESPRESSO 7.6)

Role in this project: supply material inputs that have never been measured, mainly band offsets and band-edge positions for interfaces such as ZnSe or MgZnO on graded CdSeTe. Every method is first validated on interfaces with measured offsets, and every DFT-derived input carries an uncertainty that the device-model sensitivity analysis propagates.

- Install: `tools/bin/micromamba create -p tools/qe-env -c conda-forge qe=7.6`. It provides pw.x, ph.x, pp.x and average.x with Open MPI.
- Pseudopotentials: PseudoDojo v0.4 norm-conserving PBE "standard". Scalar-relativistic files go in `dft/pseudo/sr` and fully relativistic ones in `dft/pseudo/fr`. Download them from https://www.pseudo-dojo.org/pseudos/nc-sr-04_pbe_standard_upf.tgz and nc-fr-04_pbe_standard_upf.tgz. They are git-ignored here.
- Run: `tools/qe-env/bin/mpirun -np 8 tools/qe-env/bin/pw.x -nk 4 -in INPUT`.

## Smoke test (2026-11-15)

Bulk zincblende CdTe at the experimental lattice constant a = 6.481 Å, PBE without spin-orbit coupling, 80 Ry cutoff, 8x8x8 k-points:

- Converged in 43 s wall time on an Apple M4.
- Γ-point gap 0.77 eV, against the experimental 1.50 eV.
- The PBE underestimate is the expected behaviour. Band edges for device inputs will come from hybrid-functional bulk calculations combined with a PBE interface potential lineup, validated on measured offsets first.
