"""Wall-time table from QE outputs (pw.x WALL line) for every superlattice and bulk calculation."""
import re, glob, json
from common import HERE

def wall(f):
    m = re.findall(r"PWSCF\s+:\s+(.*?)CPU\s+(.*?)WALL", open(f).read())
    if not m:
        return None
    s = m[-1][1].strip()
    h = re.search(r"(\d+)h", s); mi = re.search(r"(\d+)m", s); se = re.search(r"([\d.]+)s", s)
    return (int(h.group(1)) * 3600 if h else 0) + (int(mi.group(1)) * 60 if mi else 0) + (float(se.group(1)) if se else 0)

rows = []
for f in sorted(glob.glob(str(HERE / "sl" / "*" / "scf.out"))):
    tag = f.split("/")[-2]; w = wall(f)
    nk = re.search(r"number of k points=\s*(\d+)", open(f).read())
    nat = re.search(r"number of atoms/cell\s*=\s*(\d+)", open(f).read())
    it = re.search(r"convergence has been achieved in\s+(\d+)", open(f).read())
    rows.append((tag, nat.group(1) if nat else "", nk.group(1) if nk else "", it.group(1) if it else "not converged", w))
print("| superlattice | atoms | k-points | SCF iterations | pw.x wall (min) |\n|---|---|---|---|---|")
for r in rows:
    print(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {'' if r[4] is None else f'{r[4]/60:.1f}'} |")
for base in ("bulk", "soc", "hse"):
    ws = [wall(f) for f in glob.glob(str(HERE / base / "*" / "scf.out"))]
    ws = [w for w in ws if w]
    if ws:
        print(f"\n{base}: {len(ws)} pw.x runs, total {sum(ws)/60:.1f} min, median {sorted(ws)[len(ws)//2]:.0f} s, max {max(ws):.0f} s")
