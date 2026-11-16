"""Design study: levers on the calibrated Kujovic 21.4% cell (Sesame, interface-state front model).

Baseline = ident best fit: dEc -0.30 eV, S 5.2 cm/s (log 0.717), phi_b 0.50, bulk tau 100 ns, dead FTO/ZnO
(tau 1e-12 s), stored front Fi_m 4.10 eV, T_front 0.9, R_back 0.2, 300 K, 1 sun, Rs 0.
A design is a dict (see BASE); the SCAPS .def is written by optionA/kujovic_model.build with the design's dEc, NA
scale (grading shape kept), FTO and absorber thickness, back contact and tau; Sesame then sets the bulk tau (IL
included), kills FTO/ZnO recombination-free generation (tau 1e-12, as ident) and puts S on the two-node interface
states (buffer CB <-> absorber VB, mid interface gap). Branches with sigma > 0 use the parallel-domain composite of
kujovic/fluct (absorber gap shifted by delta, f_cb 0.5, offsets follow, metal fixed in absolute energy).

  python design.py run      simulate every design (resumable; one CSV per design and domain, atomic writes)
  python design.py report   -> design_results.csv, design_eqe.csv, design_*.png
  python design.py defs     -> SCAPS .defs of the combined designs with the interface block (defs_scaps/)
"""
import csv
import hashlib
import json
import math
import os
import sys
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np

HERE = Path(__file__).resolve().parent
KJ = HERE.parent / "kujovic"
REPO = HERE.parents[2]
sys.path.insert(0, str(KJ)); sys.path.insert(0, str(KJ.parent)); sys.path.insert(0, str(KJ / "fluct"))
import kj_sesame as kj  # noqa: E402
import sesame_cell as sc  # noqa: E402

CURVES = HERE / "curves"
DEFS = HERE / "defs"
VBM0, NT_BULK = 5.81, 5e11
DELTAS = [-0.30, -0.24, -0.18, -0.12, -0.06, 0.0, 0.06, 0.12, 0.18, 0.30]
FINE = np.round(np.arange(-0.30, 0.3001, 0.005), 3)
VG = np.arange(0.0, 1.6, 0.001)
RAMPS = [None, [1e-3, 1e-2, 0.1, 0.3, 1.0], [1.0]]
ETA_MEAS = 21.44
S_BASE = 10 ** 0.717

BASE = dict(dEc=-0.30, S=S_BASE, tau=100e-9, nas=1.0, back="b0.50", Tf=0.90, dFTO=350, dabs=3.5, sigma=0.0, B=0.0)
BRANCHES = {"base": BASE,
            "i_sigma15": dict(BASE, dEc=-0.34, S=1.8323144223712118, sigma=0.015),
            "ii_sigma60_ohmic": dict(BASE, dEc=-0.34, S=1.8323144223712118, sigma=0.060, back="ohm")}


def key(d):
    """Short stable id of a design (all parameters)."""
    s = json.dumps({k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in sorted(d.items()) if k != "sigma"}, sort_keys=True)
    return hashlib.sha1(s.encode()).hexdigest()[:10]


def label_params(d):
    return (f"dEc {d['dEc']:+.2f}, S {d['S']:.3g}, tau {d['tau'] * 1e9:g} ns, NA x{d['nas']:g}, back {d['back']}, "
            f"T_front {d['Tf']:.2f}, FTO {d['dFTO']:g} nm, abs {d['dabs']:g} um, sigma {1000 * d['sigma']:g} meV"
            + (f", B {d['B']:.0e} cm3/s" if d.get("B", 0) > 0 else "")
            + (f", S_n,back {d['Snb']:.0e} cm/s" if d.get("Snb") else ""))


# ------------------------------------------------------------------ defs and cells
def make_def(d, delta=0.0, out_dir=DEFS, name=None):
    name = name or (f"D_{d['back']}_dEc{d['dEc']:+.2f}_na{d['nas']:g}_fto{d['dFTO']:g}_abs{d['dabs']:g}"
                    f"_t{d['tau'] * 1e9:g}_d{delta:+.3f}").replace("+", "p").replace("-", "m")
    path = out_dir / f"{name}.def"
    if path.exists():
        return path
    sys.path.insert(0, str(REPO / "optionA")); sys.path.insert(0, str(REPO / "scripts"))
    import scaps_tools
    import kujovic_model as k
    out_dir.mkdir(exist_ok=True)
    scaps_tools.DEFS = out_dir
    k.ABS = KJ / "absorption"
    p, r = dict(k.AUTH), dict(k.RECON)
    p.update(tau=d["tau"], Nt_bulk=NT_BULK, dEc=d["dEc"], NA_back=3e16 * d["nas"], NA_front=1e16 * d["nas"],
             d_FTO_nm=d["dFTO"], d_abs_um=d["dabs"])
    p["Eg_back"] += delta; p["Eg_front"] += delta
    r["VBM_abs"] = VBM0 + 0.5 * delta                       # f_cb 0.5; the buffer offset follows (dEc fixed)
    if d["back"] == "ohm":
        r["back"] = "flatband"
    else:
        r["back"] = r["VBM_abs"] - (VBM0 - float(d["back"][1:]))     # metal fixed in absolute energy
    tmp = k.build(p, r, name=name)
    return out_dir / f"{tmp}.def"


def make_cell(d, delta=0.0):
    layers, contacts = kj.parse_def(make_def(d, delta))
    assert [L["name"] for L in layers] == ["FTO", "ZnO", "IL", "abs3", "abs2", "abs1", "abs0"]
    for L in layers[2:]:
        L["tau"] = d["tau"]                                   # bulk SRH (IL included); S on the interface states
    layers[0]["tau"] = layers[1]["tau"] = 1e-12               # dead FTO and ZnO (as ident)
    cell = kj.build_cell(layers, contacts, 300.0, T_front=d["Tf"], R_back=0.2)
    if d.get("Snb"):                                          # electron reflector: back-contact electron velocity only
        cell.system.Scn[1] = d["Snb"] / cell.system.scaling.velocity
    if d.get("B", 0.0) > 0:                                   # radiative sensitivity (the calibrated model has K_rad 0)
        s = cell.system
        s.B[cell.layer_of >= 2] = d["B"] * s.scaling.density * s.scaling.time
    sc.add_interface_defect(cell, d["S"], k_front=1)
    return cell


def write_csv(path, rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader()
        w.writerows([{k: (f"{v:.7g}" if isinstance(v, float) else v) for k, v in r.items()} for r in rows])
    tmp.replace(path)


def run_domain(d, delta, vcap=None):
    out = CURVES / f"{key(d)}_d{delta:+.3f}.csv"
    if out.exists():
        return out
    CURVES.mkdir(exist_ok=True)
    jv = None
    for ramp in RAMPS:
        cell = make_cell(d, delta)
        if vcap is None:
            jv = sc.run_jv(cell, dV=0.01, tol=1e-8, time_limit=900, ramp=ramp, V_max=1.6, stop_after_voc=4)
        else:
            jv = sc.run_jv(cell, dV=0.01, tol=1e-8, time_limit=900, ramp=ramp, V_max=vcap, stop_after_voc=10 ** 6)
        if len(jv.V) > 3:
            break
    rows = [dict(V=float(v), J=float(j), status="ok" if jv.ok or vcap else jv.note) for v, j in zip(jv.V, jv.J)]
    rows = rows or [dict(V="", J="", status=jv.note)]
    write_csv(out, rows)
    m = sc.jv_metrics(jv.V, jv.J, 0.0) if len(jv.V) > 3 else {}
    print(f"  {key(d)} delta {delta:+.3f}: {jv.note}; Voc {m.get('Voc', float('nan')):.1f} Jsc {m.get('Jsc', float('nan')):.2f} "
          f"FF {m.get('FF', float('nan')):.2f} ({jv.seconds:.0f} s)", flush=True)
    return out


def read_curve(path):
    rows = list(csv.DictReader(open(path)))
    if not rows or rows[0]["V"] == "":
        return None
    return np.array([float(r["V"]) for r in rows]), np.array([float(r["J"]) for r in rows])


def simulate(d):
    """Run the design (all domains if sigma > 0)."""
    p0 = run_domain(d, 0.0)
    if d["sigma"] > 0:
        c = read_curve(p0)
        voc0 = sc.jv_metrics(*c, 0.0)["Voc"] / 1000 if c is not None else 1.2
        for dl in DELTAS:
            if dl != 0.0:
                run_domain(d, dl, vcap=round(voc0 + 0.15, 2))


def lnJd_on(V, J, Vg):
    """As kujovic/fluct: ln of Jd = Jsc - J, linear in V where resolved, linear extrapolation beyond."""
    jsc = J[0]
    jd = jsc - J
    ok = jd > 1e-6 * max(abs(jsc), 1e-3)
    if ok.sum() < 3:
        return jsc, np.full_like(Vg, -30.0)
    Vk, Lk = V[ok], np.log(jd[ok])
    out = np.interp(Vg, Vk, Lk, left=-30.0)
    hi = Vg > Vk[-1]
    if hi.any():
        s = np.polyfit(Vk[-3:], Lk[-3:], 1)[0]
        out[hi] = Lk[-1] + max(s, 0.0) * (Vg[hi] - Vk[-1])
    lo = Vg < Vk[0]
    out[lo] = np.minimum(out[lo], Lk[0])
    return jsc, out


def metrics(d):
    """Voc (mV), Jsc, FF, eta of the design; None if not (fully) simulated."""
    p0 = CURVES / f"{key(d)}_d{0.0:+.3f}.csv"
    if not p0.exists():
        return None
    c0 = read_curve(p0)
    if c0 is None:
        return None
    if d["sigma"] <= 0:
        return sc.jv_metrics(*c0, 0.0)
    ds, JSC, L = [], [], []
    for dl in DELTAS:
        p = CURVES / f"{key(d)}_d{dl:+.3f}.csv"
        if not p.exists():
            return None
        c = read_curve(p)
        if c is None:
            return None
        jsc, lj = lnJd_on(*c, VG)
        ds.append(dl); JSC.append(jsc); L.append(lj)
    ds, JSC, L = np.array(ds), np.array(JSC), np.array(L)
    sg = d["sigma"]
    dl = FINE[(FINE >= -4.5 * sg) & (FINE <= 4.5 * sg)]
    w = np.exp(-0.5 * (dl / sg) ** 2); w /= w.sum()
    i = np.clip(np.searchsorted(ds, dl, side="right") - 1, 0, len(ds) - 2)
    t = ((dl - ds[i]) / (ds[i + 1] - ds[i]))[:, None]
    Lf = (1 - t) * L[i] + t * L[i + 1]
    jsc = float((w * np.interp(dl, ds, JSC)).sum())
    jd = (w[:, None] * np.exp(Lf)).sum(0)
    return sc.jv_metrics(VG, jsc - jd, 0.0)


# ------------------------------------------------------------------ the design list
def step1():
    """(label, design, lever reference): the reference isolates the lever (same point with the lever at baseline)."""
    out = []
    for S in (S_BASE, 10 * S_BASE):
        ref = dict(BASE, S=S)
        for dEc in (-0.30, -0.20, -0.10, 0.0, 0.10, 0.20, 0.30):
            out.append((f"1a dEc {dEc:+.2f}, S {S:.3g}", dict(BASE, dEc=dEc, S=S), ref))
    for S in (S_BASE, 10 * S_BASE, 100 * S_BASE, 1000 * S_BASE):
        out.append((f"1b S {S:.3g} at dEc 0", dict(BASE, dEc=0.0, S=S), dict(BASE, dEc=0.0)))
    for dEc in (-0.30, 0.0):
        for tau in (100e-9, 300e-9, 1000e-9):
            out.append((f"1c tau {tau * 1e9:g} ns at dEc {dEc:+.2f}", dict(BASE, dEc=dEc, tau=tau), dict(BASE, dEc=dEc)))
    for nas in (0.3, 1.0, 3.0, 10.0):
        out.append((f"1d NA x{nas:g} at dEc 0, tau 300 ns", dict(BASE, dEc=0.0, tau=300e-9, nas=nas), dict(BASE, dEc=0.0, tau=300e-9)))
    for back in ("b0.50", "b0.30", "b0.10", "ohm"):
        out.append((f"1e back {back} at dEc 0", dict(BASE, dEc=0.0, back=back), dict(BASE, dEc=0.0)))
    out.append(("1f optics (a) MAR, T_front 0.97", dict(BASE, Tf=0.97), BASE))
    out.append(("1f optics (b) FTO 150 nm", dict(BASE, dFTO=150), BASE))
    out.append(("1f optics (c) MAR + FTO 150 nm", dict(BASE, Tf=0.97, dFTO=150), BASE))
    out.append(("1f optics (c) at dEc 0", dict(BASE, dEc=0.0, Tf=0.97, dFTO=150), dict(BASE, dEc=0.0)))
    out.append(("1g absorber 2.5 um at dEc 0, tau 300 ns", dict(BASE, dEc=0.0, tau=300e-9, dabs=2.5), dict(BASE, dEc=0.0, tau=300e-9)))
    return out


def choices():
    """Step-2 choices read from the step-1 results (design_choices.json, written by 'report')."""
    f = HERE / "design_choices.json"
    return json.loads(f.read_text()) if f.exists() else None


def combined(branch="base"):
    ch = choices()
    if ch is None:
        return []
    b = BRANCHES[branch]
    real = dict(b, dEc=ch["dEc_realistic"], S=10 * b["S"], tau=300e-9, nas=ch["nas"], Tf=0.97, dFTO=150,
                back="ohm" if b["back"] == "ohm" else "b0.30")
    aggr = dict(b, dEc=ch["dEc_aggressive"], S=b["S"], tau=1000e-9, nas=ch["nas"], Tf=0.97, dFTO=150, back="ohm")
    return [(f"2 realistic [{branch}]", real), (f"2 aggressive [{branch}]", aggr)]


def all_designs():
    """(label, design, reference for the lever delta)."""
    out = [("0 baseline (ident best fit)", BASE, BASE)] + step1()
    for br in BRANCHES:
        if br != "base":
            out.append((f"3 branch baseline [{br}]", BRANCHES[br], BRANCHES[br]))
    for br in BRANCHES:
        out += [(lab, d, BRANCHES[br]) for lab, d in combined(br)]
    out += radiative()
    out += reflector()
    return out


def reflector():
    """Extra lever found by the loss breakdown: once the cliff is gone, electrons lost at the back contact
    (S_n 1e7 cm/s, no electron reflector) dominate recombination at Voc. S_n,back 1e7 -> 1e3 cm/s, holes unchanged."""
    if choices() is None:
        return []
    out = [("5 electron reflector at dEc 0, phi_b 0.50 (no effect: Schottky)", dict(BASE, dEc=0.0, Snb=1e3), dict(BASE, dEc=0.0)),
           ("5 electron reflector at dEc 0, ohmic back", dict(BASE, dEc=0.0, back="ohm", Snb=1e3), dict(BASE, dEc=0.0, back="ohm")),
           ("5 electron reflector at baseline", dict(BASE, Snb=1e3), BASE)]
    for lab, d in combined("base"):
        out.append((f"5 electron reflector: {lab[2:]}", dict(d, Snb=1e3), d))
        if d["back"] == "ohm":
            out.append((f"5 electron reflector + B 1e-10: {lab[2:]}", dict(d, Snb=1e3, B=1e-10), d))
    return out


def radiative():
    """Sensitivity: radiative recombination B (cm3/s, absorber and IL) on the levers that raise n*p most."""
    if choices() is None:
        return []
    out = []
    for B in (1e-11, 1e-10):
        out.append((f"4 B {B:.0e}: baseline", dict(BASE, B=B), BASE))
        out.append((f"4 B {B:.0e}: dEc 0", dict(BASE, dEc=0.0, B=B), dict(BASE, dEc=0.0)))
        for nas in (3.0, 10.0):
            out.append((f"4 B {B:.0e}: NA x{nas:g} at dEc 0, tau 300 ns", dict(BASE, dEc=0.0, tau=300e-9, nas=nas, B=B), dict(BASE, dEc=0.0, tau=300e-9, nas=nas)))
        out.append((f"4 B {B:.0e}: tau 1000 ns at dEc 0", dict(BASE, dEc=0.0, tau=1000e-9, B=B), dict(BASE, dEc=0.0, tau=1000e-9)))
        for lab, d in combined("base"):
            out.append((f"4 B {B:.0e}: {lab[2:]}", dict(d, B=B), d))
    return out


def run():
    seen = set()
    for lab, d, _ in all_designs():
        k = (key(d), d["sigma"])
        if k in seen:
            continue
        seen.add(k)
        print(f"{lab}: {label_params(d)}", flush=True)
        simulate(d)


if __name__ == "__main__":
    if sys.argv[1] == "run":
        run()
    elif sys.argv[1] == "report":
        import design_report
        design_report.main()
    elif sys.argv[1] == "defs":
        import design_report
        design_report.scaps_defs()
