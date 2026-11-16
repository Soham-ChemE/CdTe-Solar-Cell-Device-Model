"""Build the SCAPS side of the SCAPS-vs-Sesame benchmark.

Device = Sesame tutorial 1 (NIST): 3 um CdTe-like p-n homojunction.
  n-region 0.5 um, ND 1e17 cm-3 | p-region 2.5 um, NA 1e15 cm-3
  Nc 8e17, Nv 1.8e19 cm-3, Eg 1.5 eV, chi 3.9 eV, eps 9.4, mu_e = mu_h = 100 cm2/Vs
  SRH lifetime 10 ns for both carriers, trap at the intrinsic level
  Contacts: n-side Sn 1e7, Sp ~0 cm/s; p-side Sn ~0, Sp 1e7 cm/s
  Generation G(d) = phi*alpha*exp(-alpha*d), phi 1e17 cm-2 s-1, alpha 2.3e4 cm-1, d = depth from lit surface
SCAPS geometry: p-layer on the left (back), n-layer on the right (front), light from the right.
"""
import math, re, sys, pathlib

SCAPS = pathlib.Path(sys.argv[1])           # SCAPS install dir
kT = 8.617333262e-5 * 300.0
Nc, Nv, Eg = 8e17, 1.8e19, 1.5
Et_above_Ev = Eg / 2 + 0.5 * kT * math.log(Nv / Nc)    # trap at Ei
vth, sigma = 1e5, 1e-19                                 # m/s, m^2
Nt = 1.0 / (sigma * vth * 10e-9)                        # m^-3 -> tau = 10 ns

src = (SCAPS / "def" / "simple pn.def").read_text(encoding="latin-1").replace("\r", "")
head, *layers_and_tail = src.split("\nlayer\n")
assert len(layers_and_tail) == 2
p_block, n_rest = layers_and_tail
n_block, tail = n_rest.split("front contact", 1)

def setcols(block, key, val):
    """Set the y=0, y=1 and grading end columns (1,2,6,7) of a parameter line."""
    pat = re.compile(r"^(" + re.escape(key) + r"\s*:\s*)(.*)$", re.M)
    m = pat.search(block); assert m, key
    cols = m.group(2).split("\t")
    nums = [c for c in cols if c.strip()]
    idx = [i for i, c in enumerate(cols) if c.strip()]
    for k in (0, 1, 5, 6):
        cols[idx[k]] = f" {val:.6e}" if abs(val) >= 1e3 or abs(val) < 1e-2 else f" {val:.6f}"
    return block[:m.start(2)] + "\t".join(cols) + block[m.end(2):]

def material(block, d_um, Na, Nd):
    block = re.sub(r"^d : .*$", f"d : {d_um*1e-6:.3e} [m]", block, flags=re.M)
    for key, val in [("eps", 9.4), ("chi", 3.9), ("Eg", Eg), ("Nc", Nc * 1e6), ("Nv", Nv * 1e6),
                     ("mu_n", 100e-4), ("mu_p", 100e-4), ("Na(y)", Na * 1e6), ("Nd(y)", Nd * 1e6),
                     ("Nt(y)", Nt)]:
        block = setcols(block, key, val)
    block = re.sub(r"^Nleft : .*$", f"Nleft : {Nt:.3e} [/m^3]", block, flags=re.M)
    block = re.sub(r"^Nright : .*$", f"Nright : {Nt:.3e} [/m^3]", block, flags=re.M)
    block = re.sub(r"^sigma_n : .*$", f"sigma_n : {sigma:.3e}\t[m^2]", block, flags=re.M)
    block = re.sub(r"^sigma_p : .*$", f"sigma_p : {sigma:.3e}\t[m^2]", block, flags=re.M)
    block = re.sub(r"^Et : .*$", f"Et :   {Et_above_Ev:.4f}\t[eV]", block, flags=re.M)
    return block

p_block = material(p_block, 2.5, 1e15, 1e1)
n_block = material(n_block, 0.5, 1e1, 1e17)
out = head + "\nlayer\n" + p_block + "\nlayer\n" + n_block + "front contact" + tail
(SCAPS / "def" / "bench_sesame_t1.def").write_text(out.replace("\n", "\r\n"), encoding="latin-1")

# Generation file: x from the left (back) contact, light enters at x = L
L_um, phi, alpha = 3.0, 1e17, 2.3e4
import numpy as np
d = np.unique(np.concatenate([np.geomspace(1e-6, L_um, 600), [0.0]]))   # depth from lit surface, um
x = np.sort(L_um - d)
G = phi * alpha * np.exp(-alpha * (L_um - x) * 1e-4) * 1e6           # cm-3 s-1 -> m-3 s-1
lines = ["Beer-Lambert G for SCAPS-vs-Sesame benchmark (Sesame tutorial 1)", "", "x (um)\tGeh (#/m3.s)"]
lines += [f"{xi:.8f}\t{gi:.6E}" for xi, gi in zip(x, G)]
(SCAPS / "generation" / "bench_sesame_t1.gen").write_text("\r\n".join(lines) + "\r\n", encoding="latin-1")
print(f"Et above Ev = {Et_above_Ev:.4f} eV, Nt = {Nt:.3e} m^-3, gen points = {len(x)}")
