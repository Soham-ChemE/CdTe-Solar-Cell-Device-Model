"""Band diagrams of the rebuilt Loughborough model, compared with the authors' own SCAPS band diagram
(thesis Fig. 3.11, digitised in data/kujovic_family/curves/S4_fig3.11_*).

For each requested variant: equilibrium (dark, 0 V) band diagram, plus band diagram and generation/recombination
profile under light at a chosen bias (default 0.68 V, near the rebuild's Voc).
Usage: python optionA/kujovic_eb.py TAG [key=value ...]   keys: any AUTH or RECON key, bias=V
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import kujovic_model as k
from scaps_tools import Batch, RESULTS


def parse(argv):
    p, r, bias = dict(k.AUTH), dict(k.RECON), 0.68
    for kv in argv:
        key, v = kv.split("=")
        if key == "bias":
            bias = float(v)
        elif key in p:
            p[key] = float(v)
        elif key in r:
            r[key] = v if key in ("Eg_mode", "back") and not v.replace(".", "").isdigit() else (v == "True" if v in ("True", "False") else float(v))
        else:
            raise KeyError(key)
    if isinstance(r.get("n_sub"), float):
        r["n_sub"] = int(r["n_sub"])
    return p, r, bias


def eb_case(b: Batch, deffile: str, out: str, bias: float):
    b.lines += [f"load definitionfile {deffile}", "clear actions", "action workingpoint.temperature 300",
                "action workingpoint.voltage 0", "action dark", "clear simulations", "calculate",
                f"save results.eb {out}_eq.eb",
                "clear actions", "action workingpoint.temperature 300", f"action workingpoint.voltage {bias:g}",
                "action light", "clear simulations", "calculate",
                f"save results.eb {out}_V{bias:g}.eb", f"save results.genrec {out}_V{bias:g}.gr"]


if __name__ == "__main__":
    tag = sys.argv[1]
    p, r, bias = parse(sys.argv[2:])
    name = k.build(p, r, name=f"K_eb_{tag}")
    b = Batch(f"K_eb_{tag}")
    eb_case(b, f"{name}.def", name, bias)
    res = b.run(timeout=1800, prefix=sys.argv[0] and __import__("os").environ.get("SCAPS_PREFIX", "wineprefix"))
    print(res.stdout[-300:])
    for f in sorted(RESULTS.glob(f"{name}_*")):
        print(f.name, f.stat().st_size)
