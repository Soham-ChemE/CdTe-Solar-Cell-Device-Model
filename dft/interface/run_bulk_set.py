"""Run the bulk reference set sequentially (4 MPI ranks max). Usage: python run_bulk_set.py [eq|avg|dp|ecut|soc|all]"""
import sys, json, time
from common import MAT, a_avg
from bulk_refs import run

PAIRS = [("ZnTe", "CdTe"), ("CdS", "CdTe"), ("ZnSe", "CdTe"), ("ZnSe", "CdSe")]
which = sys.argv[1:] or ["all"]
jobs = []
if {"eq", "all"} & set(which):
    jobs += [dict(mat=m, a=MAT[m][2]) for m in MAT]
if {"avg", "all"} & set(which):
    for A, B in PAIRS:
        jobs += [dict(mat=A, a=round(a_avg(A, B), 5)), dict(mat=B, a=round(a_avg(A, B), 5))]
if {"dp", "all"} & set(which):
    for m in MAT:
        jobs += [dict(mat=m, a=round(MAT[m][2] * f, 5)) for f in (0.99, 1.01)]
if {"ecut", "all"} & set(which):
    for m in ("CdTe", "ZnSe", "ZnTe", "CdS"):
        jobs += [dict(mat=m, a=MAT[m][2], ecut=e) for e in (60, 100)]
if {"soc", "all"} & set(which):
    jobs += [dict(mat=m, a=MAT[m][2], soc=True) for m in MAT]
seen = set()
for j in jobs:
    key = json.dumps(j, sort_keys=True)
    if key in seen:
        continue
    seen.add(key)
    t = time.time()
    r = run(**j)
    print(f"{j} ok={r['ok']} VBM-Vbar={r.get('VBM_minus_Vbar', float('nan')):.4f} "
          f"gap={r.get('gap', float('nan')):.3f} DSO={r.get('Delta_SO', float('nan')):.3f} {time.time()-t:.0f}s", flush=True)
