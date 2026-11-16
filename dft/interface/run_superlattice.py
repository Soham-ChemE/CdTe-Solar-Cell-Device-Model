"""Run pw.x scf -> pp.x (plot_num=11, V_bare+V_H) -> average.x for one superlattice directory.

Usage: python run_superlattice.py sl/ZnTe_CdTe_n3 [--nk 2] [--keepwfc]
Writes timings.json in the directory. Never uses more than 4 MPI ranks.
"""
import argparse, json, shutil, sys
from pathlib import Path
from common import run_qe, HERE, NP_MAX

ap = argparse.ArgumentParser()
ap.add_argument("dir"); ap.add_argument("--nk", type=int, default=2); ap.add_argument("--keepwfc", action="store_true")
ap.add_argument("--skip-scf", action="store_true")
a = ap.parse_args()
d = (HERE / a.dir).resolve()
tim = json.loads((d / "timings.json").read_text()) if (d / "timings.json").exists() else {}
if not a.skip_scf:
    t, txt = run_qe("pw.x", "scf.in", d, NP_MAX, ["-nk", str(a.nk)])
    tim["pw_scf_s"] = t; tim["scf_ok"] = "JOB DONE" in txt and "convergence has been achieved" in txt
    (d / "timings.json").write_text(json.dumps(tim, indent=1))
    print(f"{d.name}: scf {t:.0f} s ok={tim['scf_ok']}", flush=True)
    if not tim["scf_ok"]:
        sys.exit(1)
t, txt = run_qe("pp.x", "pp.in", d, NP_MAX)
tim["pp_s"] = t
t, txt = run_qe("average.x", "average.in", d, 1)
tim["average_s"] = t
(d / "timings.json").write_text(json.dumps(tim, indent=1))
if not a.keepwfc:
    for f in list((d / "tmp").glob("*.save/wfc*")) + list((d / "tmp").glob("*.wfc*")):
        f.unlink()
print(f"{d.name}: pp+average done", flush=True)
