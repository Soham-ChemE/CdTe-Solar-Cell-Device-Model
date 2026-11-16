"""Step 1: validate the Sesame model against SCAPS where SCAPS converges.

Cases (SCAPS .def/.iv in scaps/defs, scaps/results):
  (a)  x = 0.15, dEc +0.19, Eg_buf 3.71 optical / 3.5 electrical, best fit (LHS sample 220)  A_mzo_x0p15_lhs0220
  (b)  x = 0.00, dEc -0.10, Eg 3.28, best fit with S_front 1e5/1e6 and ND_ZnO 1e15/1e17     A_mzo_x0p00_h004/6/8/10
  extra (same x = 0 family): S_front 1e3 with ND 1e15/1e17 (h000, h002) and the x = 0 best fit (x0p00_lhs0220).
Each case is built from sesame_cell.case_layers() and first checked parameter-by-parameter against the SCAPS .def.
Three optics variants: 'single' (one pass, no reflection), 'scaps' (T_front 0.9, R_back 0.2 = what SCAPS computes),
'mirror80' (T_front 0.9, R_back 0.8 = the literal reading of the 80% mirror file).

Usage: python validate.py            -> validation.csv, validation_jv_curves.csv, validation_jv.png
       python validate.py --plot     -> redraw validation_jv.png from the CSVs
       python validate.py --numerics -> validation_numerics.csv (mesh refinement / Newton tolerance checks)
"""
import csv
import os
import re
import sys
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sesame_cell as sc  # noqa: E402

RES = sc.REPO / "scaps/results"
DEFS = sc.REPO / "scaps/defs"

# LHS sample 220 (optionA/lhs_results.csv): the x = 0.15 best fit, at full precision
S220 = dict(tau=7.242813964412892e-09, NA=413944387563621.5, phi_back=5.270976101460403, S_front=7511.075432164792,
            ND_MZO=6.471683252205372e+17)
RS220 = 1.3159875200631173
B = sc.BEST
CASES = [
    dict(case="a_x0.15_best", group="a", scaps="A_mzo_x0p15_lhs0220", x=0.15, dEc=0.19, Eg=3.71, p=S220, Rs=RS220),
    dict(case="b_S1e5_ND1e15", group="b", scaps="A_mzo_x0p00_h004", x=0.0, dEc=-0.10, Eg=3.28, p={**B, "S_front": 1e5, "ND_MZO": 1e15}, Rs=1.32),
    dict(case="b_S1e5_ND1e17", group="b", scaps="A_mzo_x0p00_h006", x=0.0, dEc=-0.10, Eg=3.28, p={**B, "S_front": 1e5, "ND_MZO": 1e17}, Rs=1.32),
    dict(case="b_S1e6_ND1e15", group="b", scaps="A_mzo_x0p00_h008", x=0.0, dEc=-0.10, Eg=3.28, p={**B, "S_front": 1e6, "ND_MZO": 1e15}, Rs=1.32),
    dict(case="b_S1e6_ND1e17", group="b", scaps="A_mzo_x0p00_h010", x=0.0, dEc=-0.10, Eg=3.28, p={**B, "S_front": 1e6, "ND_MZO": 1e17}, Rs=1.32),
    dict(case="x_S1e3_ND1e15", group="extra", scaps="A_mzo_x0p00_h000", x=0.0, dEc=-0.10, Eg=3.28, p={**B, "S_front": 1e3, "ND_MZO": 1e15}, Rs=1.32),
    dict(case="x_S1e3_ND1e17", group="extra", scaps="A_mzo_x0p00_h002", x=0.0, dEc=-0.10, Eg=3.28, p={**B, "S_front": 1e3, "ND_MZO": 1e17}, Rs=1.32),
    dict(case="x_x0.00_best", group="extra", scaps="A_mzo_x0p00_lhs0220", x=0.0, dEc=-0.10, Eg=3.28, p=S220, Rs=RS220),
]
OPTICS = {"single": (1.0, 0.0), "scaps": (0.9, 0.2), "mirror80": (0.9, 0.8)}


def read_scaps_iv(path):
    t = Path(path).read_text(encoding="latin-1").replace("\r", "")
    out = {k: float(re.search(rf"{k}\s*=\s*([-\d.eE+]+)", t).group(1)) for k in ("Voc", "Jsc", "FF", "eta")}
    out["Voc"] *= 1000
    out["def"] = re.search(r"problem definition file :\s*(.*)$", t, re.M).group(1).split("\\")[-1].strip()
    lines = t.split("\n")
    i = next(k for k, l in enumerate(lines) if l.strip().startswith("v(V)"))
    cols = [c.strip() for c in lines[i].split("\t")]
    rows = []
    for l in lines[i + 1:]:
        q = l.split()
        if len(q) < 2:
            if rows:
                break
            continue
        rows.append([float(v) for v in q])
    tab = np.array(rows)
    out["table"] = {c: tab[:, j] for j, c in enumerate(cols)}
    return out


def run_case(c, optics="scaps", mesh=sc.MeshSpec(), tol=1e-8, dV=0.01):
    layers, contacts = sc.case_layers(c["x"], c["dEc"], c["Eg"], c["p"])
    mism = sc.compare_with_def(layers, contacts, DEFS / f"{c['scaps']}.def")
    if mism:
        raise SystemExit(f"{c['case']}: Sesame inputs differ from SCAPS .def: {mism}")
    cell = sc.build_cell(layers, contacts, *OPTICS[optics], mesh=mesh)
    jv = sc.run_jv(cell, dV=dV, tol=tol)
    m = sc.jv_metrics(jv.V, jv.J, c["Rs"]) if jv.ok else {k: float("nan") for k in ("Voc", "Jsc", "FF", "eta")}
    return cell, jv, m


def main():
    rows, curves = [], []
    for c in CASES:
        siv = read_scaps_iv(RES / f"{c['scaps']}.iv")
        assert siv["def"] == f"{c['scaps']}.def", siv["def"]
        tb = siv["table"]
        jg_s = -tb["jtot(mA/cm2)"]                                      # generator convention
        vint_s = tb["v(V)"] + jg_s * 1e-3 * c["Rs"]
        m_s2 = sc.jv_metrics(vint_s, jg_s, c["Rs"])                     # SCAPS curve, our extraction
        for opt in OPTICS:
            t0 = time.time()
            cell, jv, m = run_case(c, opt)
            d0 = jv.detail[0] if jv.detail else {}
            dev = devV = float("nan")
            if jv.ok:
                vx = jv.V - jv.J * 1e-3 * c["Rs"]
                # curve agreement: |dJ| at fixed V below the SCAPS MPP, |dV| at fixed J between the MPP and Voc
                sel = (tb["v(V)"] >= 0) & (tb["v(V)"] <= m_s2["Vmpp"])
                dev = float(np.max(np.abs(np.interp(tb["v(V)"][sel], vx, jv.J) - jg_s[sel])))
                sel = (jg_s <= m_s2["Jmpp"]) & (jg_s >= 0)
                devV = float(1000 * np.max(np.abs(np.interp(-jg_s[sel], -jv.J, vx) - tb["v(V)"][sel])))
                for v, vxx, j in zip(jv.V, vx, jv.J):
                    curves.append(dict(case=c["case"], optics=opt, V_int=round(v, 6), V_ext=round(vxx, 6), J_mAcm2=round(j, 6)))
            row = dict(case=c["case"], group=c["group"], scaps_file=c["scaps"], optics=opt,
                       T_front=OPTICS[opt][0], R_back=OPTICS[opt][1], status="ok" if jv.ok else f"FAILED: {jv.note}",
                       Voc_sesame=m["Voc"], Jsc_sesame=m["Jsc"], FF_sesame=m["FF"], eta_sesame=m["eta"],
                       Voc_scaps=siv["Voc"], Jsc_scaps=siv["Jsc"], FF_scaps=siv["FF"], eta_scaps=siv["eta"],
                       dVoc_mV=m["Voc"] - siv["Voc"], dJsc_pct=100 * (m["Jsc"] / siv["Jsc"] - 1),
                       dFF_abs=m["FF"] - siv["FF"], deta_abs=m["eta"] - siv["eta"],
                       Voc_scaps_reext=m_s2["Voc"], Jsc_scaps_reext=m_s2["Jsc"], FF_scaps_reext=m_s2["FF"], eta_scaps_reext=m_s2["eta"],
                       maxdJ_below_Vmpp_mAcm2=dev, maxdV_Vmpp_to_Voc_mV=devV,
                       Jgen_sesame=d0.get("gen", float("nan")), Jgen_scaps=tb["j_total_gen(mA/cm2)"][0],
                       Jrec_bulk_sesame_V0=sum(d0["rec"].values()) if d0 else float("nan"), Jrec_bulk_scaps_V0=tb["jbulk(mA/cm2)"][0],
                       Jrec_IL_sesame_V0=d0["rec"]["IL"] if d0 else float("nan"),
                       Jloss_front_sesame_V0=d0.get("loss_front_minority", float("nan")), Jloss_front_scaps_V0=tb["jminor_right(mA/cm2)"][0],
                       Jloss_back_sesame_V0=d0.get("loss_back_minority", float("nan")), Jloss_back_scaps_V0=tb["jminor_left(mA/cm2)"][0],
                       J_absorbed_per_layer=";".join(f"{k}:{v:.4f}" for k, v in cell.J_opt.items()),
                       nodes=len(cell.x), seconds=round(time.time() - t0, 1), **jv.stats)
            rows.append(row)
            print(f"{c['case']:16s} {opt:8s} {row['status']:6s} Voc {m['Voc']:7.1f}/{siv['Voc']:7.1f}  Jsc {m['Jsc']:6.3f}/{siv['Jsc']:6.3f}  "
                  f"FF {m['FF']:5.2f}/{siv['FF']:5.2f}  eta {m['eta']:5.2f}/{siv['eta']:5.2f}  gen {row['Jgen_sesame']:.3f}/{row['Jgen_scaps']:.3f}"
                  f"  max|dJ| {dev:.3f} mA/cm2, max|dV| {devV:.2f} mV  {row['seconds']} s", flush=True)
    fmt = lambda v: f"{v:.6g}" if isinstance(v, float) else v
    with open(HERE / "validation.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader()
        w.writerows([{k: fmt(v) for k, v in r.items()} for r in rows])
    with open(HERE / "validation_jv_curves.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(curves[0])); w.writeheader(); w.writerows(curves)
    plot()


def plot():
    """Figure from the written CSVs (validation.csv, validation_jv_curves.csv) and the SCAPS .iv files."""
    rows = list(csv.DictReader(open(HERE / "validation.csv")))
    for r in rows:
        for k in ("dVoc_mV", "dJsc_pct", "dFF_abs", "deta_abs"):
            r[k] = float(r[k])
    pd = {}
    for r in csv.DictReader(open(HERE / "validation_jv_curves.csv")):
        pd.setdefault((r["case"], r["optics"]), ([], []))
        pd[(r["case"], r["optics"])][0].append(float(r["V_ext"])); pd[(r["case"], r["optics"])][1].append(float(r["J_mAcm2"]))
    for c in CASES:
        tb = read_scaps_iv(RES / f"{c['scaps']}.iv")["table"]
        pd[(c["case"], "scaps_ref")] = (tb["v(V)"], -tb["jtot(mA/cm2)"])
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ink, ink2, grid = "#0b0b0b", "#52514e", "#e4e3df"
    c_ses, c_scaps, c_single = "#2a78d6", "#eb6834", "#8a8984"
    fig, axs = plt.subplots(2, 4, figsize=(15, 7.4), sharey=True)
    for ax, c in zip(axs.flat, CASES):
        r = next(r for r in rows if r["case"] == c["case"] and r["optics"] == "scaps")
        if (c["case"], "single") in pd:
            v, j = pd[(c["case"], "single")]
            ax.plot(v, j, color=c_single, lw=1.2, ls=(0, (4, 3)), label="Sesame, single pass, no reflection")
        if (c["case"], "scaps") in pd:
            v, j = pd[(c["case"], "scaps")]
            ax.plot(v, j, color=c_ses, lw=2, label="Sesame, SCAPS optics (T 0.9, R 0.2)")
        v, j = pd[(c["case"], "scaps_ref")]
        ax.plot(v, j, ls="none", marker="o", ms=4.5, mfc="white", mec=c_scaps, mew=1.4, label="SCAPS 3.3.11")
        ax.set_xlim(0, 0.9); ax.set_ylim(0, 32)
        ax.grid(color=grid, lw=0.6); ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(ink2)
        ax.tick_params(colors=ink2, labelsize=8)
        lab = {"a": "(a) MgZnO x = 0.15, spike +0.19 eV", "b": "(b) ZnO, cliff -0.10 eV", "extra": "extra: ZnO, cliff -0.10 eV"}[c["group"]]
        sub = f"S_front {c['p']['S_front']:.3g} cm/s, ND_buf {c['p']['ND_MZO']:.3g} cm$^{{-3}}$" 
        ax.set_title(f"{lab}\n{sub}", fontsize=8.5, color=ink, loc="left")
        ax.text(0.02, 0.04, f"dVoc {r['dVoc_mV']:+.1f} mV   dJsc {r['dJsc_pct']:+.2f}%\ndFF {r['dFF_abs']:+.2f}   deta {r['deta_abs']:+.2f} (abs. %)",
                transform=ax.transAxes, fontsize=7.5, color=ink2, family="monospace")
    for ax in axs[1]:
        ax.set_xlabel("Voltage incl. Rs (V)", fontsize=9, color=ink)
    for ax in axs[:, 0]:
        ax.set_ylabel("Current density (mA/cm$^2$)", fontsize=9, color=ink)
    h, l = axs[0, 0].get_legend_handles_labels()
    fig.suptitle("Sesame vs SCAPS: J-V of the validation cases (AM1.5G, Rs applied to the internal-voltage curve)", y=0.99, fontsize=11, color=ink)
    fig.legend(h, l, loc="upper center", bbox_to_anchor=(0.5, 0.955), ncol=3, frameon=False, fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    fig.savefig(HERE / "validation_jv.png", dpi=150)


def numerics():
    """Mesh refinement, Newton tolerance and voltage-step checks: the spike cell, the worst validated cliff cell,
    and three grid cells SCAPS could not solve (deep cliff, high S; two of them have kinked J-V curves)."""
    rows = []
    variants = [("baseline", sc.MeshSpec(), 1e-8, 0.01), ("mesh x2", sc.MeshSpec(refine=2.0), 1e-8, 0.01),
                ("mesh x4", sc.MeshSpec(refine=4.0), 1e-8, 0.01), ("mesh x0.5", sc.MeshSpec(refine=0.5), 1e-8, 0.01),
                ("tol 1e-10", sc.MeshSpec(), 1e-10, 0.01), ("dV 0.005", sc.MeshSpec(), 1e-8, 0.005)]
    grid_cases = [dict(case=f"grid[{i}] dEc {d:+.2f} S {s:.0e} ND {nd:.0e} NA {na:.3g}", scaps=f"A_mzo_x0p00_h{i:03d}", x=0.0,
                       dEc=d, Eg=3.28, p={**B, "S_front": s, "ND_MZO": nd, "NA": na}, Rs=1.32)
                  for i, (d, s, nd, na) in [(42, (-0.32, 1e6, 1e17, 4.14e14)), (44, (-0.32, 1e7, 1e15, 4.14e14)),
                                            (47, (-0.32, 1e7, 1e17, 2e16))]]
    for c in (CASES[0], CASES[3], *grid_cases):
        for name, ms, tol, dV in variants:
            cell, jv, m = run_case(c, "scaps", mesh=ms, tol=tol, dV=dV)
            rows.append(dict(case=c["case"], variant=name, nodes=len(cell.x), status="ok" if jv.ok else jv.note,
                             Voc=m["Voc"], Jsc=m["Jsc"], FF=m["FF"], eta=m["eta"], seconds=round(jv.seconds, 1)))
            print(rows[-1], flush=True)
    with open(HERE / "validation_numerics.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader()
        w.writerows([{k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in r.items()} for r in rows])


if __name__ == "__main__":
    if "--numerics" in sys.argv:
        numerics()
    elif "--plot" in sys.argv:
        plot()
    else:
        main()
