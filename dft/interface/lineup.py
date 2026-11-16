"""Potential lineup from a superlattice: planar + macroscopic average of V_bare + V_H.

Primary numbers come from my own Fourier-space filter applied to the pp.x cube (exact for periodic data,
window = ML period, or two successive windows for tetragonally distorted layers). The average.x output
(avg.dat) is read as an independent cross-check.
"""
import json
from pathlib import Path
import numpy as np
from common import read_cube, BOHR, RY, HERE


def macro_avg(z, vp, windows):
    """Periodic box-filter (macroscopic) average of planar average vp(z); windows in same units as z."""
    L = (z[1] - z[0]) * len(z)
    q = 2 * np.pi * np.fft.fftfreq(len(z), d=z[1] - z[0])
    f = np.fft.fft(vp)
    for w in windows:
        f *= np.sinc(q * w / (2 * np.pi))          # np.sinc(x) = sin(pi x)/(pi x) -> sin(qw/2)/(qw/2)
    return np.real(np.fft.ifft(f)), L


def analyse(d):
    d = Path(d)
    meta = json.loads((d / "meta.json").read_text())
    data, cell = read_cube(d / "vbh.cube")
    vp = data.mean(axis=(0, 1)) * RY                  # planar average, eV
    L = cell[2, 2] * BOHR                             # Angstrom
    z = np.arange(len(vp)) * L / len(vp)
    cA, cB, n = meta["cA"], meta["cB"], meta["n"]
    wins = [cA / 2] if abs(cA - cB) < 1e-9 else [cA / 2, cB / 2]
    vm, _ = macro_avg(z, vp, wins)
    # layer A spans planes 0..4n-1 (first cation at z=0); interfaces sit half a plane spacing outside
    zA = 0.5 * ((-(cA + cB) / 16) + (n * cA - cA / 4 + (cA + cB) / 16))
    zB0 = n * cA - cA / 4 + (cA + cB) / 8                     # first B cation plane
    zB = 0.5 * ((zB0 - (cA + cB) / 16) + (zB0 + n * cB - cB / 4 + (cA + cB) / 16))
    def at(z0):
        return float(np.interp(z0 % L, z, vm, period=L))
    def plateau(zc, c):
        sel = np.abs(((z - zc + L / 2) % L) - L / 2) <= c / 2        # +-c/2 around the centre
        zz = ((z[sel] - zc + L / 2) % L) - L / 2
        p = np.polyfit(zz, vm[sel], 1)
        return float(np.mean(vm[sel])), float(np.ptp(vm[sel])), float(p[0])
    VA, VB = at(zA), at(zB)
    mA, rA, sA = plateau(zA, cA); mB, rB, sB = plateau(zB, cB)
    res = dict(tag=d.name, A=meta["A"], B=meta["B"], n=n, k=meta["k"], ecut=meta["ecut"], L=L, zA=zA, zB=zB,
               VA_centre=VA, VB_centre=VB, dV_centre=VB - VA,
               VA_plateau=mA, VB_plateau=mB, dV_plateau=mB - mA,
               ripple_A=rA, ripple_B=rB, slope_A_eV_per_A=sA, slope_B_eV_per_A=sB)
    # interface-resolved steps (only meaningful if plateaus are sloped): extrapolate linear fits to each interface
    zi1 = n * cA - cA / 4 + (cA + cB) / 16; zi2 = L - (cA + cB) / 16
    res["dV_IF1_extrap"] = (VB + sB * (zi1 - zB)) - (VA + sA * (zi1 - zA))
    res["dV_IF2_extrap"] = (VB + sB * (zi2 - zB)) - (VA + sA * (zi2 - L - zA))
    # cross-check with average.x
    avg = d / "avg.dat"
    if avg.exists():
        a = np.loadtxt(avg)
        za = a[:, 0] * BOHR            # average.x writes z in bohr (checked: last z ~ L in bohr)
        vma = a[:, 2] * RY
        LA = (za[1] - za[0]) * len(za)
        res["avgx_L_A"] = LA
        res["avgx_dV_centre"] = float(np.interp(zB % LA, za, vma, period=LA) - np.interp(zA % LA, za, vma, period=LA))
    np.savetxt(d / "macro_avg.dat", np.c_[z, vp, vm], header="z(A) planar_avg(eV) macro_avg(eV)  [V_bare+V_H]")
    (d / "lineup.json").write_text(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    import sys
    for d in sys.argv[1:]:
        print(json.dumps(analyse(HERE / d), indent=1))
