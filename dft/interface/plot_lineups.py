"""Plot planar and macroscopic averages of V_bare+V_H for every analysed superlattice -> lineups.png"""
import json, glob
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import HERE

dirs = [d for d in sorted(glob.glob(str(HERE / "sl" / "*"))) if (HERE / "sl" / d / "macro_avg.dat").exists()]
fig, axes = plt.subplots(len(dirs), 1, figsize=(7, 2.1 * len(dirs)), squeeze=False)
for ax, d in zip(axes[:, 0], dirs):
    z, vp, vm = np.loadtxt(f"{d}/macro_avg.dat", unpack=True)
    lin = json.loads(open(f"{d}/lineup.json").read())
    ax.plot(z, vp, color="0.75", lw=0.6, label="planar average")
    ax.plot(z, vm, color="C0", lw=1.5, label="macroscopic average")
    for zc, v in ((lin["zA"], lin["VA_centre"]), (lin["zB"], lin["VB_centre"])):
        ax.plot([zc], [v], "o", color="C3", ms=4)
    ax.set_title(f"{lin['tag']}: dV = Vbar({lin['B']}) - Vbar({lin['A']}) = {lin['dV_centre']:.3f} eV", fontsize=9)
    ax.set_ylabel("eV", fontsize=8); ax.tick_params(labelsize=7)
    lo, hi = min(vm) - 0.6, max(vm) + 0.6
    ax.set_ylim(lo, hi)
axes[-1, 0].set_xlabel("z (Angstrom)", fontsize=8)
axes[0, 0].legend(fontsize=7, loc="upper right")
fig.tight_layout(); fig.savefig(HERE / "lineups.png", dpi=130)
print("wrote lineups.png with", len(dirs), "panels")
