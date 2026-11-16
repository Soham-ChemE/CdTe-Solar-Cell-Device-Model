"""Band diagrams and front-interface state for representative grid cases (mechanism behind the grid trends).

For each case: equilibrium bands near the front, and at V_int = 0 and at the internal voltage nearest the
maximum-power point: carrier densities in the 10 nm interface layer (IL), where the front recombination sits,
and the electron barrier/inversion at the buffer/IL interface.

Usage: python diagnose.py  -> diagnose_bands.png, diagnose.csv
"""
import csv
import os
import sys
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sesame_cell as sc  # noqa: E402

VT = sc.VT
CASES = [  # label, x, dEc, Eg, overrides (grid index in brackets)
    ("MgZnO x=0.15 best fit (spike +0.19)", 0.15, 0.19, 3.71, {}),
    ("[4] ZnO dEc -0.10, S 1e5, ND 1e15, NA 4.1e14", 0.0, -0.10, 3.28, {"S_front": 1e5, "ND_MZO": 1e15}),
    ("[20] ZnO dEc -0.22, S 1e5, ND 1e15, NA 4.1e14", 0.0, -0.22, 3.28, {"S_front": 1e5, "ND_MZO": 1e15}),
    ("[36] ZnO dEc -0.32, S 1e5, ND 1e15, NA 4.1e14", 0.0, -0.32, 3.28, {"S_front": 1e5, "ND_MZO": 1e15}),
    ("[44] ZnO dEc -0.32, S 1e7, ND 1e15, NA 4.1e14", 0.0, -0.32, 3.28, {"S_front": 1e7, "ND_MZO": 1e15}),
    ("[5] ZnO dEc -0.10, S 1e5, ND 1e15, NA 2e16", 0.0, -0.10, 3.28, {"S_front": 1e5, "ND_MZO": 1e15, "NA": 2e16}),
    ("[7] ZnO dEc -0.10, S 1e5, ND 1e17, NA 2e16", 0.0, -0.10, 3.28, {"S_front": 1e5, "ND_MZO": 1e17, "NA": 2e16}),
    ("[6] ZnO dEc -0.10, S 1e5, ND 1e17, NA 4.1e14", 0.0, -0.10, 3.28, {"S_front": 1e5, "ND_MZO": 1e17}),
]


def bands(cell, sol):
    s = cell.system
    Ec = -(s.bl + sol["v"]) * VT
    Ev = Ec - s.Eg * VT
    n = s.Nc * np.exp(s.bl + sol["efn"] + sol["v"]) * s.scaling.density
    p = s.Nv * np.exp(-s.Eg - s.bl - sol["efp"] - sol["v"]) * s.scaling.density
    return Ec, Ev, sol["efn"] * VT, sol["efp"] * VT, n, p


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rows = []
    fig, axs = plt.subplots(2, 4, figsize=(19, 8.5), sharey=False)
    for ax, (lab, x, dEc, Eg, ov) in zip(axs.flat, CASES):
        p = {**sc.BEST, **ov}
        layers, contacts = sc.case_layers(x, dEc, Eg, p)
        cell = sc.build_cell(layers, contacts, 0.9, 0.2)
        keep = tuple(np.round(np.arange(0, 1.2001, 0.01), 2))
        jv = sc.run_jv(cell, dV=0.01, keep=keep)
        m = sc.jv_metrics(jv.V, jv.J, sc.RS_BEST)
        vmpp_int = m["Vmpp"] + m["Jmpp"] * 1e-3 * sc.RS_BEST
        kv = min(jv.sols, key=lambda v: abs(v - vmpp_int))
        il = cell.layer_of == 2
        i_if = int(np.where(cell.layer_of == 1)[0][-1])        # last buffer node = buffer/IL interface
        out = dict(case=lab, Voc=m["Voc"], Jsc=m["Jsc"], FF=m["FF"], eta=m["eta"])
        veq = {"efn": np.zeros_like(cell.v_eq), "efp": np.zeros_like(cell.v_eq), "v": cell.v_eq}
        Ec0, Ev0, _, _, n0, p0 = bands(cell, veq)
        out["eq_Ec_minus_EF_at_IL_eV"] = float(Ec0[i_if + 1])      # E_F = 0: >0 means CB above E_F at the IL
        out["eq_EF_minus_Ev_at_IL_eV"] = float(-Ev0[i_if + 1])
        out["eq_n_IL_cm3"], out["eq_p_IL_cm3"] = float(n0[i_if + 1]), float(p0[i_if + 1])
        for tag, vk in (("V0", 0.0), ("Vmpp", kv)):
            Ec, Ev, Fn, Fp, n, pp = bands(cell, jv.sols[vk])
            out[f"{tag}_Vint"] = vk
            out[f"{tag}_n_IL_mean"], out[f"{tag}_p_IL_mean"] = float(n[il].mean()), float(pp[il].mean())
            out[f"{tag}_QFL_split_IL_eV"] = float((Fn[il] - Fp[il]).mean())
            d = next(dd for dd in jv.detail if abs(dd["V"] - vk) < 1e-9)
            out[f"{tag}_J_IL_rec"] = d["rec"]["IL"]
            out[f"{tag}_J_bulk_rec"] = d["rec"]["CdSeTe"] + d["rec"]["CdTe"]
            out[f"{tag}_J_back_contact"] = d["loss_back_minority"]
            if tag == "Vmpp":
                xs = cell.x * 1e4
                sel = (xs > 0.45) & (xs < 2.2)
                ax.plot(xs[sel], Ec[sel], color="#0b0b0b", lw=1.6, label="Ec, Ev")
                ax.plot(xs[sel], Ev[sel], color="#0b0b0b", lw=1.6)
                ax.plot(xs[sel], Fn[sel], color="#2a78d6", lw=1.4, ls=(0, (4, 2)), label="E_Fn")
                ax.plot(xs[sel], Fp[sel], color="#eb6834", lw=1.4, ls=(0, (4, 2)), label="E_Fp")
                for b in cell.bounds[1:4]:
                    ax.axvline(b * 1e4, color="#c3c2b7", lw=0.6)
                ax.set_title(f"{lab}\nat V_int = {vk:.2f} V (near MPP): eta {m['eta']:.1f}%, FF {m['FF']:.1f}%", fontsize=8.5, loc="left")
                ax.set_xlabel("depth from front contact (um)", fontsize=8.5)
                ax.set_ylabel("energy (eV, E_F,eq = 0)", fontsize=8.5)
                ax.set_ylim(-2.2, 1.0)
                ax.tick_params(labelsize=8)
                for sp in ("top", "right"):
                    ax.spines[sp].set_visible(False)
        rows.append(out)
        print({k: (round(v, 4) if isinstance(v, float) and abs(v) < 1e4 else (f"{v:.3g}" if isinstance(v, float) else v)) for k, v in out.items()}, flush=True)
    axs.flat[0].legend(fontsize=8, frameon=False, loc="lower right")
    fig.tight_layout()
    fig.savefig(HERE / "diagnose_bands.png", dpi=140)
    with open(HERE / "diagnose.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader()
        w.writerows([{k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in r.items()} for r in rows])


if __name__ == "__main__":
    main()
