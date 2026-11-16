"""ZnSe front-buffer design map on the calibrated As-doped Kujovic cell (Sesame, 300 K, 1 sun).

Base: the ident best fit (interface states coupling the buffer conduction band to the absorber valence band,
dead FTO tau 1e-12 s, phi_b 0.50 eV with the metal at 5.31 eV, bulk tau 100 ns, stored front Fi_m 4.10 eV).
ZnO is replaced by ZnSe: Eg 2.70 eV, eps 9.1, Nc 1.6e18, Nv 1.5e19 cm-3, mu_n 100, mu_p 20 cm2/Vs, 80 nm (and
50 nm on the best-fit-S row), chi = chi(CdSeTe front) - dEc, absorption = SCAPS sqrt model with A = 1.8e5 cm^-1
eV^-1/2 (1.8e7 /(m sqrt(eV))), B = 0. ZnSe is live: no recombination centres (tau 1 s), so blue light absorbed in
it is collected if transport allows.
Each case is built from a SCAPS .def written here (defs/), so Sesame and a later SCAPS cross-check use one input.

  python znse.py grid    -> curves/<tag>.csv per case (atomic, resumable)
  python znse.py analyze -> znse_results.csv, znse_collapse.csv, znse_maps.png
  python znse.py defs    -> the three SCAPS defs requested for the cross-check (defs/ZnSe_dEc*_Sbest_ND1e17.def)
"""
import csv
import itertools
import math
import os
import sys
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np

HERE = Path(__file__).resolve().parent
KJ = HERE.parent
sys.path.insert(0, str(KJ)); sys.path.insert(0, str(KJ.parent))
import kj_sesame as kj  # noqa: E402
import sesame_cell as sc  # noqa: E402

REPO = kj.REPO
CURVES = HERE / "curves"
DEC = [-0.10, 0.0, 0.10, 0.20, 0.30, 0.40, 0.50, 0.55, 0.60, 0.70, 0.80]
S_BEST = 10 ** 0.717                 # ident ridge best fit at dEc(ZnO) -0.30 eV: 5.2 cm/s
SS = [S_BEST, 1e3, 1e5]
NDS = [1e15, 1e17]
RAMPS = [None, [1e-3, 1e-2, 0.1, 0.3, 1.0], [1.0]]
ZNSE = dict(Eg=2.70, eps=9.1, Nc=1.6e18, Nv=1.5e19, mu_n=100.0, mu_p=20.0, A_cm=1.8e5)
TAU, NT_BULK = 100e-9, 5e11          # tau 100 ns at the reconstruction's sigma (Nt 5e12 -> 5e11 cm-3)
PHI_B = 0.50
FTO_DEAD_NT, FTO_DEAD_SIGMA = 1e17, 1e-12   # tau = 1/(Nt sigma vth) = 1e-12 s with vth 1e7 cm/s


def tag(dEc, S, ND, d_nm):
    return f"dEc{dEc:+.2f}_S{S:.1e}_ND{ND:.0e}_d{d_nm:.0f}".replace("+", "p").replace("-", "m")


def build_def(dEc, ND, d_nm, name):
    """SCAPS .def of the ZnSe cell (absorber/IL/FTO from optionA/kujovic_model.build, buffer swapped to ZnSe)."""
    path = HERE / "defs" / f"{name}.def"
    if path.exists():
        return path
    sys.path.insert(0, str(REPO / "optionA")); sys.path.insert(0, str(REPO / "scripts"))
    import scaps_tools
    import kujovic_model as k
    from mzo_model import defect_block
    (HERE / "defs").mkdir(exist_ok=True)
    scaps_tools.DEFS = HERE / "defs"
    k.ABS = KJ / "absorption"
    p, r = dict(k.AUTH), dict(k.RECON)
    p.update(tau=TAU, Nt_bulk=NT_BULK, dEc=dEc, ND_ZnO=ND, d_ZnO_nm=d_nm)
    r["back"] = PHI_B                                  # metal at VBM - 0.50 = 5.31 eV, flatband 0
    k.build(p, r, name=name)
    d = scaps_tools.DefFile.load(path)
    sigma_bulk = 1.0 / (p["tau"] * r["vth"] * p["Nt_bulk"])
    d.remove_defects("IL").add_defect_block("IL", defect_block(p["Nt_bulk"], sigma_bulk, p["Eg_front"] / 2))  # bulk only
    d.rename_layer("ZnO", "ZnSe")
    for key, val in (("Eg", ZNSE["Eg"]), ("eps", ZNSE["eps"]), ("Nc", ZNSE["Nc"] * 1e6), ("Nv", ZNSE["Nv"] * 1e6),
                     ("mu_n", ZNSE["mu_n"] * 1e-4), ("mu_p", ZNSE["mu_p"] * 1e-4)):
        d.set_param("ZnSe", key, val)
    d.set_absorption_sqrt("ZnSe", A=ZNSE["A_cm"] * 100, B=0.0)
    d.remove_defects("ZnSe")
    d.add_defect_block("FTO", defect_block(FTO_DEAD_NT, FTO_DEAD_SIGMA, 3.6 / 2))
    d.save(name)
    return path


def make_cell(dEc, S, ND, d_nm, znse_gen=True):
    path = build_def(dEc, ND, d_nm, f"ZnSe_{tag(dEc, 0, ND, d_nm).replace('_S0.0ep00', '')}")
    layers, contacts = kj.parse_def(path)
    assert [L["name"] for L in layers] == ["FTO", "ZnSe", "IL", "abs3", "abs2", "abs1", "abs0"], [L["name"] for L in layers]
    assert abs(layers[0]["tau"] - 1e-12) < 1e-15 and layers[1]["tau"] == sc.NO_RECOMB_TAU and abs(layers[2]["tau"] - TAU) < 1e-12
    cell = kj.build_cell(layers, contacts, 300.0)
    if not znse_gen:      # diagnostic: photons absorbed in ZnSe make no carriers (no extra recombination added)
        cell.g_full[cell.layer_of == 1] = 0.0
        cell.system.g = cell.g_full.copy()
    sc.add_interface_defect(cell, S, k_front=1)
    return cell


def write_csv(path, rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader()
        w.writerows([{k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in r.items()} for r in rows])
    tmp.replace(path)


def run_case(dEc, S, ND, d_nm, znse_gen=True):
    out = CURVES / f"{tag(dEc, S, ND, d_nm)}{'' if znse_gen else '_ZnSeGenOff'}.csv"
    if out.exists():
        return
    for i_r, ramp in enumerate(RAMPS):
        cell = make_cell(dEc, S, ND, d_nm, znse_gen)
        jv = sc.run_jv(cell, dV=0.01, tol=1e-8, time_limit=900, ramp=ramp, V_max=1.6)
        if jv.ok:
            break
    m = sc.jv_metrics(jv.V, jv.J, 0.0) if jv.ok else {k: float("nan") for k in ("Voc", "Jsc", "FF", "eta", "Vmpp", "Jmpp")}
    d0 = jv.detail[0] if jv.detail else {}
    base = dict(dEc=dEc, S=S, ND=ND, d_nm=d_nm, znse_generation=znse_gen, status=jv.note, ramp_variant=i_r, Voc=m["Voc"], Jsc=m["Jsc"], FF=m["FF"], eta=m["eta"],
                J_V0=jv.J[0] if len(jv.J) else float("nan"), absorbed_ZnSe=cell.J_opt["ZnSe"], absorbed_FTO=cell.J_opt["FTO"],
                rec_ZnSe_V0=d0.get("rec", {}).get("ZnSe", float("nan")), rec_interface_V0=d0.get("rec", {}).get("interface", float("nan")),
                Eg_interface=cell.if_defect.get("Eg_interface_eV", float("nan")))
    rows = [dict(base, V=v, J=j) for v, j in zip(jv.V, jv.J)] or [base]
    write_csv(out, rows)
    print(f"{tag(dEc, S, ND, d_nm)}{'' if znse_gen else ' (ZnSe gen off)'}: {jv.note}  Voc {m['Voc']:.1f}  Jsc {m['Jsc']:.2f}  FF {m['FF']:.1f}  eta {m['eta']:.2f}  J(0) {base['J_V0']:.2f}", flush=True)


def cases():
    main = [(dEc, S, ND, 80) for S, ND, dEc in itertools.product(SS, NDS, DEC)]
    thin = [(dEc, S_BEST, ND, 50) for ND, dEc in itertools.product(NDS, DEC)]
    return main + thin


def grid():
    CURVES.mkdir(exist_ok=True)
    for c in cases():
        run_case(*c)


def genoff():
    """Diagnostic (not requested): best-fit S, 80 nm, both ND, with ZnSe photogeneration switched off, to separate the
    absorber's own J-V from the ZnSe layer's photocurrent in the blocked (S-shaped) regime."""
    for ND, dEc in itertools.product(NDS, DEC):
        run_case(dEc, S_BEST, ND, 80, znse_gen=False)


def defs():
    out = []
    for dEc in (0.30, 0.55, 0.70):
        name = f"ZnSe_dEc{dEc:+.2f}_Sbest_ND1e17_d80".replace("+", "p")
        build_def(dEc, 1e17, 80, name)
        out.append(name)
    note = HERE / "defs" / "README_scaps_crosscheck.txt"
    note.write_text(
        "SCAPS cross-check defs for the ZnSe design map (written by znse.py defs; SCAPS not run here).\n"
        f"Files: {', '.join(n + '.def' for n in out)}\n"
        "Stack back->front: abs0..abs3 (graded 1.50->1.41 eV, NA 3e16->1e16), IL 10 nm, ZnSe 80 nm, FTO 350 nm.\n"
        "IL: bulk SRH only (tau 100 ns: Nt 5e11 cm-3, sigma 2e-12 cm2, midgap). The interface (S) block is NOT in the def:\n"
        f"  add a SCAPS ZnSe/IL interface defect with S = {S_BEST:.2f} cm/s (single neutral level at mid interface gap,\n"
        "  equal capture) to match Sesame's two-node interface states (buffer CB <-> absorber VB).\n"
        "ZnSe: Eg 2.70, chi = chi_IL - dEc, eps 9.1, Nc 1.6e18, Nv 1.5e19 cm-3, mu 100/20, ND 1e17 cm-3, no defects,\n"
        "  absorption = SCAPS sqrt model A = 1.8e7 /(m sqrt(eV)), B = 0.\n"
        "FTO: dead, neutral midgap defect Nt 1e17 cm-3, sigma 1e-12 cm2 (tau 1e-12 s).\n"
        "Back contact: Fi_m 5.31 eV (flatband 0) = 0.50 eV hole barrier. Front: flatband 1 / recalculate 0, stored Fi_m 4.10 eV.\n"
        "Absorber absorption files: CdTe_shift_0p011/0p034/0p056/0p079/0p090.abs (as in scaps/absorption).\n"
        "Optics in Sesame: T_front 0.9, R_back 0.2 (the SCAPS 10% reflection / 80% transmission filters in the def).\n")
    print("wrote", out)


# ------------------------------------------------------------------ analysis
def load_all(genoff=False):
    rows = []
    for c in (cases() if not genoff else [(dEc, S_BEST, ND, 80) for ND, dEc in itertools.product(NDS, DEC)]):
        f = CURVES / f"{tag(*c)}{'_ZnSeGenOff' if genoff else ''}.csv"
        if f.exists():
            d = list(csv.DictReader(open(f)))
            r = {k: v for k, v in d[0].items() if k not in ("V", "J")}
            for k in ("dEc", "S", "ND", "d_nm", "Voc", "Jsc", "FF", "eta", "J_V0", "absorbed_ZnSe", "absorbed_FTO", "rec_interface_V0", "Eg_interface"):
                r[k] = float(r[k]) if r.get(k) not in (None, "", "nan") else float("nan")
            r["V"] = np.array([float(x["V"]) for x in d if x.get("V")]); r["J"] = np.array([float(x["J"]) for x in d if x.get("J")])
            rows.append(r)
    return rows


def analyze():
    rows = load_all()
    goff = load_all(genoff=True)
    write_csv(HERE / "znse_results.csv", [{k: v for k, v in r.items() if k not in ("V", "J")} for r in rows])
    write_csv(HERE / "znse_results_ZnSeGenOff.csv", [{k: v for k, v in r.items() if k not in ("V", "J")} for r in goff])
    coll = []
    groups = [(S, ND, dn, False) for S, ND, dn in sorted({(r["S"], r["ND"], r["d_nm"]) for r in rows})]
    groups += [(S, ND, dn, True) for S, ND, dn in sorted({(r["S"], r["ND"], r["d_nm"]) for r in goff})]
    for S, ND, dn, go in groups:
        src = goff if go else rows
        sel = sorted([r for r in src if r["S"] == S and r["ND"] == ND and r["d_nm"] == dn], key=lambda r: r["dEc"])
        # Jsc test uses J(V = 0), which exists even when a blocked J-V has no Voc below 1.6 V (FF then NaN = collapsed)
        ffb = max(r["FF"] for r in sel if np.isfinite(r["FF"])); jb = max(r["J_V0"] for r in sel if np.isfinite(r["J_V0"]))
        eb = max(r["eta"] for r in sel if np.isfinite(r["eta"]))
        best = max(sel, key=lambda r: r["eta"] if np.isfinite(r["eta"]) else -1)
        first = next((r for r in sel if not (r["FF"] >= 0.5 * ffb and r["J_V0"] >= 0.5 * jb)), None)
        prev = sel[sel.index(first) - 1] if first is not None and sel.index(first) > 0 else None
        coll.append(dict(S=S, ND=ND, d_nm=dn, znse_generation=not go, eta_best=eb, dEc_at_best=best["dEc"], Voc_best=best["Voc"], FF_best=ffb, Jsc_best=jb,
                         collapse_dEc=first["dEc"] if first else float("nan"),
                         last_ok_dEc=prev["dEc"] if prev else float("nan"),
                         FF_at_collapse=first["FF"] if first else float("nan"), J0_at_collapse=first["J_V0"] if first else float("nan"),
                         eta_at_collapse=first["eta"] if first else float("nan"),
                         eta_ge_9_range=",".join(f"{r['dEc']:+.2f}" for r in sel if r["eta"] >= 9),
                         eta_1p8_to_5p6_range=",".join(f"{r['dEc']:+.2f}" for r in sel if 1.8 <= r["eta"] <= 5.6),
                         Voc_400_to_550_range=",".join(f"{r['dEc']:+.2f}" for r in sel if 400 <= r["Voc"] <= 550)))
    write_csv(HERE / "znse_collapse.csv", coll)
    for c in coll:
        print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in c.items()})
    plot(rows, goff)


def plot(rows, goff=()):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    ink, ink2 = "#0b0b0b", "#52514e"
    cols = {S_BEST: "#2a78d6", 1e3: "#eb6834", 1e5: "#1baf7a"}
    lab = {S_BEST: f"S {S_BEST:.1f} cm/s (best fit)", 1e3: "S 1e3 cm/s", 1e5: "S 1e5 cm/s"}
    fig, ax = plt.subplots(2, 3, figsize=(17, 9))
    keys = [("eta", "Efficiency (%)"), ("Voc", "Voc (mV)"), ("Jsc", "Jsc (mA/cm$^2$)"), ("FF", "FF (%)")]
    for a, (k, yl) in zip(ax.flat[:4], keys):
        for S, c in cols.items():
            for ND, ls, mk in ((1e17, "-", "o"), (1e15, (0, (4, 2.5)), "s")):
                sel = sorted([r for r in rows if np.isclose(r["S"], S, rtol=1e-4) and r["ND"] == ND and r["d_nm"] == 80], key=lambda r: r["dEc"])
                a.plot([r["dEc"] for r in sel], [r[k] for r in sel], ls=ls, marker=mk, ms=4.5, color=c, lw=1.8 if ND == 1e17 else 1.3,
                       mfc=c if ND == 1e17 else "white", label=f"{lab[S]}, ND {ND:.0e}")
        sel = sorted([r for r in rows if r["d_nm"] == 50 and r["ND"] == 1e17], key=lambda r: r["dEc"])
        a.plot([r["dEc"] for r in sel], [r[k] for r in sel], ":", marker="^", ms=4, color=ink2, lw=1.3, label=f"50 nm ZnSe, best-fit S, ND 1e17")
        sel = sorted([r for r in goff if r["ND"] == 1e17], key=lambda r: r["dEc"])
        if sel:
            a.plot([r["dEc"] for r in sel], [r[k] for r in sel], "--", marker="x", ms=5, color="#e34948", lw=1.2,
                   label="ZnSe photogeneration off (diagnostic), best-fit S, ND 1e17")
        a.axvspan(-0.06, 0.67, ymin=0, ymax=0.03, color="#6250d6", alpha=0.6, lw=0)
        a.axvline(0.55, color="#6250d6", lw=0.9, ls="--")
        a.set_xlabel("dEc = E_C(ZnSe) - E_C(CdSeTe) (eV)"); a.set_ylabel(yl)
        a.grid(color="#e4e3df", lw=0.6)
    ax[0, 0].axhspan(1.8, 5.6, color="#eda100", alpha=0.18, lw=0); ax[0, 0].text(0.62, 3.7, "intact ZnSe cells 1.8-5.6%", fontsize=7.5, color=ink2)
    ax[0, 0].axhspan(9, 11.3, color="#1baf7a", alpha=0.15, lw=0); ax[0, 0].text(0.62, 10.1, "interdiffused 9-11.3%", fontsize=7.5, color=ink2)
    ax[0, 1].axhspan(400, 550, color="#eda100", alpha=0.18, lw=0)
    ax[0, 1].axvspan(0.45, 0.85, color="#8a8984", alpha=0.12, lw=0)
    ax[0, 1].text(0.46, 1350, "blocked, S-shaped J-V:\nJ = 0 crossing is not\nan absorber Voc", fontsize=7.5, color=ink2)
    ax[0, 1].text(0.70, 470, "intact ZnSe\n400-550 mV", fontsize=7.5, color=ink2)
    ax[0, 0].legend(frameon=False, fontsize=7, loc="lower left")
    # J-V examples at best-fit S, ND 1e17
    a = ax.flat[4]
    pal = plt.cm.viridis(np.linspace(0, 0.9, len(DEC)))
    for c, dEc in zip(pal, DEC):
        r = next((r for r in rows if np.isclose(r["S"], S_BEST, rtol=1e-4) and r["ND"] == 1e17 and r["d_nm"] == 80 and np.isclose(r["dEc"], dEc)), None)
        if r is not None and len(r["V"]):
            a.plot(r["V"], r["J"], color=c, lw=1.5, label=f"{dEc:+.2f}")
    a.set_xlim(0, 1.2); a.set_ylim(-5, 30); a.set_xlabel("V (V)"); a.set_ylabel("J (mA/cm$^2$)")
    a.set_title(f"J-V, best-fit S, ND 1e17, 80 nm (legend: dEc)", fontsize=9, loc="left"); a.legend(frameon=False, fontsize=7, ncol=2)
    a.grid(color="#e4e3df", lw=0.6)
    b = ax.flat[5]
    for S, c in cols.items():
        for ND, ls in ((1e17, "-"), (1e15, (0, (4, 2.5)))):
            sel = sorted([r for r in rows if np.isclose(r["S"], S, rtol=1e-4) and r["ND"] == ND and r["d_nm"] == 80], key=lambda r: r["dEc"])
            b.plot([r["dEc"] for r in sel], [r["J_V0"] for r in sel], ls=ls, color=c, lw=1.5)
    b.set_xlabel("dEc (eV)"); b.set_ylabel("J at V = 0 (mA/cm$^2$)"); b.set_title("short-circuit current (same colours as above)", fontsize=9, loc="left")
    b.grid(color="#e4e3df", lw=0.6)
    for a_ in ax.flat:
        for s_ in ("top", "right"):
            a_.spines[s_].set_visible(False)
        a_.tick_params(colors=ink2, labelsize=8)
    fig.suptitle("ZnSe front buffer on the calibrated As-doped cell (Sesame, 300 K, 1 sun; purple band: DFT bracket -0.06..+0.67 eV, dashed: +0.55 eV)", fontsize=10.5)
    fig.tight_layout(rect=(0, 0, 1, 0.96)); fig.savefig(HERE / "znse_maps.png", dpi=150)


if __name__ == "__main__":
    {"grid": grid, "genoff": genoff, "analyze": analyze, "defs": defs}[sys.argv[1]]()
