# SCAPS-1D working folders (local only)

SCAPS-1D 3.3.11 is distributed by the University of Gent (https://scaps.elis.ugent.be/) under its own licence and may
not be redistributed. This repository therefore ships no SCAPS binary, no SCAPS-bundled input file and no file derived
from one. The build scripts recreate everything here from a local SCAPS install:

| Folder | Written by | Content |
|---|---|---|
| `defs/` | `optionA/kujovic_model.py`, `optionA/mzo_model.py`, the `*_xcheck.py` scripts | `.def` problem definitions, built from SCAPS's own `CdTe-base.def` with every edit applied by `scripts/scaps_tools.py` |
| `absorption/` | `optionA/mzo_model.py` (`shifted_abs`) | band-gap-shifted copies of SCAPS's `CdTe-base.abs` for the graded absorber |
| `generation/` | `benchmark/make_scaps_benchmark.py` | the generation profile of the SCAPS-vs-Sesame benchmark (also written into the SCAPS install) |
| `scripts/` | `scripts/scaps_tools.py` (`Batch.write`) | SCAPS batch scripts, one per run |
| `results/` | `scripts/run_scaps.sh` | raw SCAPS outputs (`.iv`, `.qe`) |

The Sesame side (`optionA/sesame/`) reads the same `.def` files, so its `defs*/` folders are regenerated the same way.
Every number used in the results is also stored in the committed CSV files next to the script that produced it, so
the figures and tables can be checked without SCAPS (`python scripts/make_figures.py`).
