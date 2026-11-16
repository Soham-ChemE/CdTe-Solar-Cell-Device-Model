"""Step 2: run the ZnO-front (x = 0, Eg 3.28 eV) hypothesis grid that SCAPS could not converge.

Same 48 cases and order as optionA/zno_hypotheses.py (index i <-> SCAPS file A_mzo_x0p00_h{i:03d}.def):
  dEc in {-0.10, -0.22, -0.32} eV x S_front in {1e3, 1e5, 1e6, 1e7} cm/s x ND_ZnO in {1e15, 1e17} cm-3
  x NA in {4.14e14, 2e16} cm-3; everything else at the x = 0.15 best fit; Rs = 1.32 ohm cm2.
Every case is first checked parameter-by-parameter against the SCAPS .def that SCAPS failed on.
Optics: T_front 0.9, R_back 0.2 (the SCAPS generation; see README).

Usage: python grid.py              -> grid_results.csv, grid_jv_curves.csv, grid_summary.png  (SCAPS model: IL)
       python grid.py --interface  -> grid_results_interface.csv, ..._interface.png  (sensitivity: front
                                      recombination through buffer-CB / absorber-VB interface states, same S)
       add --plot to redraw a figure from its CSV
"""
import csv
import itertools
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sesame_cell as sc  # noqa: E402

RS = sc.RS_BEST
DEC = [-0.10, -0.22, -0.32]
SF = [1e3, 1e5, 1e6, 1e7]
NDS = [1e15, 1e17]
NAS = [4.14e14, 2e16]
GRID = list(itertools.product(DEC, SF, NDS, NAS))
PANDEY_ZNO = dict(Voc=707.0, Jsc=20.1, FF=54.2, eta=8.0)          # Cu-doped ZnO cells, 25-cell averages
KUJOVIC = dict(Voc=875.5, Jsc=30.43, FF=80.48, eta=21.44)         # resistive ZnO on As-doped CdSeTe/CdTe


def scaps_row(i):
    rows = list(csv.DictReader(open(sc.REPO / "optionA/zno_hypotheses.csv")))
    r = rows[i]
    return r if r["ok"] == "True" else None


def build_case(x, dEc, Eg, p, front="IL", def_name=None):
    """front = 'IL' (SCAPS model) or 'interface' (sensitivity: the IL becomes plain CdSeTe and S_front is carried
    by two-node interface states that couple the buffer conduction band to the absorber valence band)."""
    layers, contacts = sc.case_layers(x, dEc, Eg, p)
    if def_name:
        mism = sc.compare_with_def(layers, contacts, sc.REPO / f"scaps/defs/{def_name}.def")
        if mism:
            raise SystemExit(f"{def_name}: inputs differ from SCAPS .def: {mism}")
    if front == "interface":
        layers[2]["tau"] = layers[3]["tau"]
    cell = sc.build_cell(layers, contacts, 0.9, 0.2)
    if front == "interface":
        sc.add_interface_defect(cell, p["S_front"])
    return cell


def main(front="IL"):
    suffix = "" if front == "IL" else "_interface"
    rows, curves = [], []
    t_all = time.time()
    cases = [(i, 0.0, dEc, 3.28, S, nd, na) for i, (dEc, S, nd, na) in enumerate(GRID)]
    if front == "interface":       # reference points: the calibrated spike cell and the x = 0 cell at the best fit
        cases = [("ref_x0.15", 0.15, 0.19, 3.71, sc.BEST["S_front"], sc.BEST["ND_MZO"], sc.BEST["NA"]),
                 ("ref_x0.00", 0.0, -0.10, 3.28, sc.BEST["S_front"], sc.BEST["ND_MZO"], sc.BEST["NA"])] + cases
    for i, x, dEc, Eg, S, nd, na in cases:
        p = {**sc.BEST, "S_front": S, "ND_MZO": nd, "NA": na}
        cell = build_case(x, dEc, Eg, p, front, f"A_mzo_x0p00_h{i:03d}" if isinstance(i, int) else None)
        jv = sc.run_jv(cell, dV=0.01, tol=1e-8, time_limit=1200)
        m = sc.jv_metrics(jv.V, jv.J, RS) if jv.ok else {k: float("nan") for k in ("Voc", "Jsc", "FF", "eta", "Vmpp", "Jmpp")}
        row = dict(i=i, front_model=front, scaps_def=f"A_mzo_x0p00_h{i:03d}" if isinstance(i, int) else "",
                   x=x, dEc=dEc, S_front=S, ND_ZnO=nd, NA=na, status="ok" if jv.ok else f"FAILED: {jv.note}",
                   Voc_mV=m["Voc"], Jsc=m["Jsc"], FF=m["FF"], eta=m["eta"], Vmpp=m["Vmpp"], Jmpp=m["Jmpp"])
        sr = scaps_row(i) if isinstance(i, int) else None
        row.update(scaps_converged=sr is not None, Voc_scaps=float(sr["Voc_mV"]) if sr else "", Jsc_scaps=float(sr["Jsc"]) if sr else "",
                   FF_scaps=float(sr["FF"]) if sr else "", eta_scaps=float(sr["eta"]) if sr else "")
        if jv.ok:
            d0 = jv.detail[0]
            # loss breakdown at short circuit (V_int = 0) and at the internal voltage closest to Voc
            vx = jv.V - jv.J * 1e-3 * RS
            k = int(np.argmin(np.abs(vx - m["Voc"] / 1000)))
            dv = jv.detail[k]
            tot = sum(dv["rec"].values()) + dv["loss_front_minority"] + dv["loss_back_minority"]
            # front recombination = the IL (SCAPS model) or the interface states (sensitivity variant)
            fr = lambda d: d["rec"]["IL"] + d["rec"].get("interface", 0.0)
            row.update(Jgen=d0["gen"], JscLoss_front=fr(d0), JscLoss_bulk=d0["rec"]["CdSeTe"] + d0["rec"]["CdTe"],
                       JscLoss_front_contact=d0["loss_front_minority"], JscLoss_back_contact=d0["loss_back_minority"],
                       Voc_frac_front=fr(dv) / tot, Voc_frac_bulk=(dv["rec"]["CdSeTe"] + dv["rec"]["CdTe"]) / tot,
                       Voc_frac_back_contact=dv["loss_back_minority"] / tot)
            for v, vxx, j in zip(jv.V, vx, jv.J):
                curves.append(dict(i=i, dEc=dEc, S_front=S, ND_ZnO=nd, NA=na, V_int=round(v, 6), V_ext=round(vxx, 6), J_mAcm2=round(j, 6)))
            # consistency: terminal current (sum of G - R) vs Sesame's link current, worst point on the curve
            row["max_dJ_link_check"] = max(abs(d["J"] - d["J_link_absorber_median"]) for d in jv.detail)
        row.update(nodes=len(cell.x), seconds=round(jv.seconds, 1), **jv.stats)
        rows.append(row)
        print(f"[{i}] x {x} dEc {dEc:+.2f} S {S:.0e} ND {nd:.0e} NA {na:.2e} ({front}): {row['status']:6s} "
              f"Voc {m['Voc']:6.1f}  Jsc {m['Jsc']:6.2f}  FF {m['FF']:5.1f}  eta {m['eta']:5.2f}  ({row['seconds']} s)", flush=True)
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(HERE / f"grid_results{suffix}.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader()
        w.writerows([{k: (f"{r[k]:.6g}" if isinstance(r.get(k), float) else r.get(k, "")) for k in keys} for r in rows])
    with open(HERE / f"grid_jv_curves{suffix}.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(curves[0])); w.writeheader(); w.writerows(curves)
    print(f"{len(rows)} cases, {sum(r['status'] == 'ok' for r in rows)} converged, wall {time.time() - t_all:.0f} s")
    plot([r for r in rows if isinstance(r["i"], int)], front)


def plot(rows, front="IL"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ink, ink2, grid = "#0b0b0b", "#52514e", "#e4e3df"
    col = {-0.10: "#2a78d6", -0.22: "#eb6834", -0.32: "#1baf7a"}
    ls = {1e15: (0, (4, 2.5)), 1e17: "-"}
    mk = {1e15: "s", 1e17: "o"}
    metrics = [("Voc_mV", "Voc (mV)", "Voc"), ("Jsc", "Jsc (mA/cm$^2$)", "Jsc"), ("FF", "FF (%)", "FF"), ("eta", "Efficiency (%)", "eta")]
    fig, axs = plt.subplots(2, 4, figsize=(15, 7.6), sharex=True)
    for r_i, na in enumerate(NAS):
        for c_i, (key, lab, mkey) in enumerate(metrics):
            ax = axs[r_i, c_i]
            for dEc in DEC:
                for nd in NDS:
                    sel = [r for r in rows if r["dEc"] == dEc and r["ND_ZnO"] == nd and r["NA"] == na]
                    xs = [r["S_front"] for r in sel if r["status"] == "ok"]
                    ys = [r[key] for r in sel if r["status"] == "ok"]
                    ax.plot(xs, ys, color=col[dEc], ls=ls[nd], lw=2 if nd == 1e17 else 1.4, marker=mk[nd], ms=5,
                            mfc=col[dEc] if nd == 1e17 else "white", mec=col[dEc], mew=1.3,
                            label=f"dEc {dEc:+.2f} eV, ND_ZnO {nd:.0e}")
            ref, rlab = (PANDEY_ZNO, "Pandey 2021 Cu-doped ZnO (avg of 25)") if na < 1e15 else (KUJOVIC, "Kujovic As-doped ZnO record (thicker, graded)")
            ax.axhline(ref[mkey], color=ink2, lw=1, ls=":")
            ax.text(1.1e3, ref[mkey], f" {rlab}", fontsize=6.8, color=ink2, va="bottom")
            ax.set_xscale("log")
            ax.grid(color=grid, lw=0.6); ax.set_axisbelow(True)
            for s in ("top", "right"):
                ax.spines[s].set_visible(False)
            ax.tick_params(colors=ink2, labelsize=8)
            ax.set_title(f"{lab}, NA = {na:.3g} cm$^{{-3}}$", fontsize=9, color=ink, loc="left")
            if r_i == 1:
                ax.set_xlabel("Front recombination velocity S_front (cm/s)", fontsize=8.5, color=ink)
    h, l = axs[0, 0].get_legend_handles_labels()
    rep = ("front recombination in the 10 nm IL (SCAPS model)" if front == "IL"
           else "sensitivity: front recombination via buffer-CB / absorber-VB interface states")
    fig.suptitle(f"Sesame ZnO-front grid (x = 0, Eg 3.28 eV, best-fit absorber, Rs 1.32 ohm cm$^2$): {rep}",
                 y=0.99, fontsize=10.5, color=ink)
    fig.legend(h, l, loc="upper center", bbox_to_anchor=(0.5, 0.96), ncol=6, frameon=False, fontsize=8.5)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(HERE / ("grid_summary.png" if front == "IL" else "grid_summary_interface.png"), dpi=150)


if __name__ == "__main__":
    front = "interface" if "--interface" in sys.argv else "IL"
    if "--plot" in sys.argv:
        rr = []
        for r in csv.DictReader(open(HERE / ("grid_results.csv" if front == "IL" else "grid_results_interface.csv"))):
            if r["i"].startswith("ref"):
                continue
            for k in ("dEc", "S_front", "ND_ZnO", "NA", "Voc_mV", "Jsc", "FF", "eta"):
                r[k] = float(r[k]) if r[k] not in ("", "nan") else float("nan")
            rr.append(r)
        plot(rr, front)
    else:
        main(front)
