"""Detailed-balance (Shockley-Queisser) limits from the SCAPS AM1.5G spectrum file.
Used as a hard physics check: no simulated Voc, Jsc or efficiency may exceed these for the absorber's band gap."""
import sys
from pathlib import Path
import numpy as np

q, h, c, k = 1.602176634e-19, 6.62607015e-34, 2.99792458e8, 1.380649e-23
SPE = Path(__file__).resolve().parents[1] / "tools/wineprefix/drive_c/Program Files (x86)/Scaps3311/spectrum/AM1_5G 1 sun.spe"


def load_spectrum():
    lam, P = [], []
    for line in SPE.read_text(encoding="latin-1").replace("\r", "").split("\n"):
        p = line.split()
        if len(p) >= 2:
            try:
                lam.append(float(p[0])); P.append(float(p[1]))
            except ValueError:
                pass
    lam, P = np.array(lam), np.array(P)          # nm, W/m2 per wavelength bin (bins sum to 1000 W/m2)
    return lam, P


def sq(Eg, T=300.0):
    lam, P = load_spectrum()
    Ein = P.sum()                                # W/m2
    E = h * c / (lam * 1e-9)                     # J
    phi = P / E                                  # photons /m2/s in each bin
    Jsc = q * phi[E >= Eg * q].sum()             # A/m2
    Ee = np.linspace(Eg, 4.5, 20000) * q
    J0 = q * 2 * np.pi / (h ** 3 * c ** 2) * np.trapezoid(Ee ** 2 / np.expm1(Ee / (k * T)), Ee)   # A/m2
    V = np.linspace(0, Eg, 40000)
    J = Jsc - J0 * np.expm1(q * V / (k * T))
    Pm = (V * J).max()
    Voc = k * T / q * np.log(Jsc / J0 + 1)
    return {"Eg": Eg, "Pin_W_m2": Ein, "Jsc_mA_cm2": Jsc / 10, "Voc_V": Voc, "FF_pct": 100 * Pm / (Voc * Jsc), "eta_pct": 100 * Pm / Ein}


if __name__ == "__main__":
    for Eg in [float(x) for x in (sys.argv[1:] or ["1.42", "1.5", "1.6", "1.7"])]:
        r = sq(Eg)
        print(f"Eg {Eg:.2f} eV: Jsc {r['Jsc_mA_cm2']:.2f} mA/cm2, Voc {r['Voc_V']:.3f} V, FF {r['FF_pct']:.1f}%, eta {r['eta_pct']:.1f}%  (spectrum {r['Pin_W_m2']:.0f} W/m2)")
