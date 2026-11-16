"""Tabulate bulk references and derived volume deformation potentials (central differences, a_exp*(1 +- 1%)).
Writes bulk_summary.csv and deformation_potentials.csv."""
import json, glob, math, csv
from common import MAT, HERE
from bulk_refs import tag_of

def load(m, a, **kw):
    return json.loads((HERE / "bulk" / tag_of(m, round(a, 5), **kw) / "result.json").read_text())

rows = []
for f in sorted(glob.glob(str(HERE / "bulk" / "*" / "result.json"))):
    r = json.loads(open(f).read())
    if not r.get("ok"):
        rows.append(dict(tag=f.split("/")[-2], ok=False)); continue
    cs = [k for k in r if k in ("Cd4s", "Zn3s")][0]
    rows.append(dict(tag=f.split("/")[-2], mat=r["mat"], a=r["a"], c=r.get("c"), ecut=r["ecut"], gap=round(r["gap"], 4),
                     VBM_minus_Vbar=round(r["VBM_minus_Vbar"], 4),
                     VBM_minus_cation_s=round(r["E_VBM_gamma"] - r[cs], 4),
                     **{k: round(v, 4) for k, v in r.items() if k.endswith("_minus_Vbar") and k != "VBM_minus_Vbar"},
                     pw_s=round(r["pw_s"], 1)))
keys = []
for r in rows:
    for k in r:
        if k not in keys: keys.append(k)
with open(HERE / "bulk_summary.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, keys); w.writeheader(); [w.writerow(r) for r in rows]

dp = []
for m, (cat, an, a0) in MAT.items():
    lo, hi = load(m, a0 * 0.99), load(m, a0 * 1.01)
    dlnV = 3 * math.log(1.01 / 0.99)
    cs = "Cd4s" if cat == "Cd" else "Zn3s"
    d = dict(mat=m,
             a_gap=(hi["gap"] - lo["gap"]) / dlnV,
             a_VBM_rel_Vbar=(hi["VBM_minus_Vbar"] - lo["VBM_minus_Vbar"]) / dlnV,
             a_VBM_rel_cation_s=((hi["E_VBM_gamma"] - hi[cs]) - (lo["E_VBM_gamma"] - lo[cs])) / dlnV)
    for lev in ("Cd4p", "Zn3p", "Te4d", "Se3d"):
        if lev in hi:
            d[f"a_VBM_rel_{lev}"] = ((hi["E_VBM_gamma"] - hi[lev]) - (lo["E_VBM_gamma"] - lo[lev])) / dlnV
    dp.append({k: (round(v, 3) if isinstance(v, float) else v) for k, v in d.items()})
keys = []
for r in dp:
    for k in r:
        if k not in keys: keys.append(k)
with open(HERE / "deformation_potentials.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, keys); w.writeheader(); [w.writerow(r) for r in dp]
for r in dp: print(r)
