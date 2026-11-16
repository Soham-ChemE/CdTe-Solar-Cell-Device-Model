# Data and licences

**Code.** All code in this repository (`*.py`, `*.sh`, `docs/assets/*.js`) is released under the MIT licence in
[`LICENSE`](LICENSE).

**Digitised experimental data.** The measured data under [`data/`](data/) (J-V, EQE, C-V and Voc(T) curves, device
tables, the Mg-fraction series and the ZnSe device and defect tables) are numbers read from published papers, theses and
reports: from the vector drawing paths of their figures, or from their tables and text. They are facts reported by the
original authors and are redistributed here only as extracted numbers, with the extraction scripts and accuracy
checks. **If you use them, cite the original publications.** Each folder's `README.md` gives the full reference, DOI,
open-access copy and the licence of the source. The main sources are:

| Folder | Source | Source licence |
|---|---|---|
| `data/kujovic2024/`, `data/kujovic_family/` (S1) | L. Kujović et al., *Adv. Funct. Mater.* 34, 2312528 (2024), doi:10.1002/adfm.202312528 | CC BY 4.0 |
| `data/kujovic_family/` (S2, S3) | L. Kujović et al., *Adv. Mater. Technol.* 10, 2401364 (2025), doi:10.1002/admt.202401364; *J. Phys. Energy* 8, 025017 (2026), doi:10.1088/2515-7655/ae7760 | CC BY 4.0 |
| `data/kujovic_family/` (S4) | L. Kujović, PhD thesis, Loughborough University (2025), doi:10.26174/thesis.lboro.30724235 | CC BY-NC-ND 4.0 (numbers only; no figure crops are included) |
| `data/kujovic_family/` (X1, X2) | M. Togay et al., *J. Phys. Energy* (2025), doi:10.1088/2515-7655/adfd87; X. Liu et al., IEEE PVSC 2022, doi:10.1109/PVSC48317.2022.9938648 | CC BY 4.0; © IEEE (facts and numbers only) |
| `data/pandey2021/` | R. Pandey et al., *Solar RRL* 5, 2100126 (2021), doi:10.1002/solr.202100126 | public-access manuscript, OSTI |
| `data/kephart2016/` | J. M. Kephart et al., *Sol. Energy Mater. Sol. Cells* (2016), OSTI 1534330 | public-access manuscript, OSTI |
| `data/znse/` | Fedorenko et al. 2015/2016, Chen et al. 2018, Morel and Ferekides (NREL subcontract reports, 1997 and 1998), and the other works listed in `data/znse/README.md` | as listed per source |

The source PDFs, their extracted full texts and the overlay images used to check the digitisation (which contain
crops of the original figures) are **not** included.

**Simulation results and figures.** The model outputs (`optionA/`, `forensics/`, `benchmark/`, `dft/`) and the figures
(`docs/figures/`, `figures/`) were produced in this project and are released under CC BY 4.0: reuse them with
attribution to this repository.

**Third-party software.** SCAPS-1D (M. Burgelman et al., University of Gent) is not included and may not be
redistributed; obtain it from https://scaps.elis.ugent.be/. NIST Sesame 2.0 and Quantum ESPRESSO 7.6 are installed
separately under their own licences. No pseudopotential files are included (the DFT inputs name the PseudoDojo files
they use).
