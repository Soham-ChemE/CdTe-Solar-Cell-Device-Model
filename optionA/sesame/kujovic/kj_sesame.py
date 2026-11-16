"""Sesame model of the rebuilt Loughborough 21.4% ZnO/CdSeTe/CdTe cell (Kujovic 2024), built straight from the
SCAPS .def files that optionA/kujovic_model.py writes.

Differences from optionA/sesame/sesame_cell.read_scaps_def (which handles the option-A MgZnO stack):
  * any number of layers (here abs0..abs3, IL, ZnO, FTO);
  * every SRH block of a layer is read. All blocks here are neutral, midgap, sigma_n = sigma_p, so they combine
    into one lifetime: 1/tau = sum Nt sigma vth (the IL carries bulk tau 10 ns plus the S_front-equivalent block);
  * back contact: 'flatband : 1' AND 'recalculate : 1' -> flat band (Sesame Ohmic: p = NA at the contact, with the
    temperature's Nv); otherwise the stored Fi_m is used (Schottky). K_u_base.def has flatband 1 / recalculate 0,
    so SCAPS used Fi_m = 5.0 eV there, and so do we;
  * temperature: Nc, Nv scale as (T/300)^1.5 (as SCAPS does); vth and mobilities stay at their inputs.
The J-V sweep, current bookkeeping, optics (SCAPS rules, T_front 0.9, R_back 0.2) and metrics come from
sesame_cell.py, unchanged.
"""
from __future__ import annotations

import math
import re
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import sesame_cell as sc  # noqa: E402
import sesame  # noqa: E402

REPO = sc.REPO
DEF_DIRS = [HERE / "defs", REPO / "scaps/defs"]
ABS_DIRS = [HERE / "absorption", REPO / "scaps/absorption", sc.SCAPS_DIR / "absorption"]


def _first(txt, key):
    m = re.search(rf"^{re.escape(key)}\s*:\s*([-\d.eE+]+)", txt, re.M)
    return float(m.group(1)) if m else None


def find_abs(name):
    for d in ABS_DIRS:
        if (d / name).exists():
            return d / name
    raise FileNotFoundError(name)


def sqrt_abs_file(A, B, Eg):
    """Tabulate SCAPS's sqrt model alpha = (A + B/hv) sqrt(hv - Eg) (A in 1/(m sqrt(eV)), B in sqrt(eV)/m) as an
    .abs file (1/m, 0.25 nm steps), with a zero end point so alpha_scaps extrapolates to zero below the gap."""
    hc = 1239.84198
    out = HERE / "absorption" / f"sqrt_A{A:.3e}_B{B:.3e}_Eg{Eg:.3f}.abs"
    if not out.exists():
        out.parent.mkdir(exist_ok=True)
        lam_edge = hc / Eg
        lam = np.arange(200.0, lam_edge, 0.25)
        hv = hc / lam
        a = (A + B / hv) * np.sqrt(np.clip(hv - Eg, 0, None))
        lines = ["/ SCAPS sqrt absorption model tabulated by kj_sesame.sqrt_abs_file", "/ lambda (nm)\talpha (1/m)"]
        lines += [f"{l_:.4f}\t{x:.6g}" for l_, x in zip(lam, a) if x > 0]
        lines += [f"{lam_edge + 0.01:.4f}\t0", "3000.0000\t0"]
        tmp = out.with_suffix(".tmp"); tmp.write_text("\n".join(lines) + "\n"); tmp.replace(out)
    return out


def parse_def(path, front_rule="scaps"):
    """(layers front -> back, contacts) in cm units, with all SRH blocks of each layer combined."""
    t = Path(path).read_text(encoding="latin-1").replace("\r", "")
    head, *lts = t.split("\nlayer\n")
    lts[-1], _, front = lts[-1].partition("front contact")
    layers = []
    for lt in lts:
        name = re.search(r"^name : (.*)$", lt, re.M).group(1).strip()
        body, _, _ = lt.partition("interface properties")
        L = dict(name=name, d=_first(body, "d") * 100, eps=_first(body, "eps"), chi=_first(body, "chi"),
                 Eg=_first(body, "Eg"), Nc=_first(body, "Nc") * 1e-6, Nv=_first(body, "Nv") * 1e-6,
                 mu_e=_first(body, "mu_n") * 1e4, mu_h=_first(body, "mu_p") * 1e4,
                 NA=_first(body, "Na(uniform)") * 1e-6, ND=_first(body, "Nd(uniform)") * 1e-6,
                 vth_n=_first(body, "v_th_n") * 100, vth_p=_first(body, "v_th_p") * 100, Krad=_first(body, "K_rad"),
                 abs=None)
        mfile = re.search(r"absorptionfile pure A material \(y=0\) : (.*)$", body, re.M)
        if "absorptionmodel pure A material (y=0) : coefficients A and B" in body:   # SCAPS sqrt(hv - Eg) model
            L["abs"] = sqrt_abs_file(_first(body, "A"), _first(body, "B"), L["Eg"])
        else:
            L["abs"] = find_abs(mfile.group(1).strip())
        assert L["Krad"] == 0 and L["vth_n"] == L["vth_p"]
        rate, blocks = 0.0, []
        for blk in body.split("srhrecombination")[1:]:
            nt, sn, sp = _first(blk, "Nt(uniform)") * 1e-6, _first(blk, "sigma_n") * 1e4, _first(blk, "sigma_p") * 1e4
            et, ref = _first(blk, "Et"), _first(blk, "Reference for defect energy")
            assert "type : neutral" in blk, f"{name}: non-neutral defect"
            assert ref == 0 and abs(et - L["Eg"] / 2) < 2e-3, f"{name}: defect not at midgap ({et} above Ev)"
            assert abs(sn - sp) <= 1e-6 * sn, f"{name}: sigma_n != sigma_p"
            rate += nt * sn * L["vth_n"]
            blocks.append(dict(Nt=nt, sigma=sn, tau=1 / (nt * sn * L["vth_n"])))
        L["tau"] = 1.0 / rate if rate > 0 else sc.NO_RECOMB_TAU
        L["defects"] = blocks
        layers.append(L)
    back = head.split("back contact", 1)[1]
    fb, rc, fim = _first(back, "flatband"), _first(back, "recalculate"), _first(back, "Fi_m")
    contacts = dict(back_type="Ohmic" if (fb == 1 and rc == 1) else "Schottky", phi_back=fim,
                    flatband_back=fb, recalculate_back=rc, S_back=_first(back, "Sn") * 100, Sp_back=_first(back, "Sp") * 100,
                    S_front=_first(front, "Sn") * 100, Sp_front=_first(front, "Sp") * 100,
                    flatband_front=_first(front, "flatband"), phi_front_stored=_first(front, "Fi_m"),
                    filter_back=re.search(r"optical filter : (\w+)", back).group(1),
                    filterfile_back=re.search(r"filterfile : (.*)$", back, re.M).group(1).strip(),
                    filter_front=re.search(r"optical filter : (\w+)", front).group(1),
                    filterfile_front=re.search(r"filterfile : (.*)$", front, re.M).group(1).strip())
    assert contacts["S_back"] == contacts["Sp_back"] and contacts["S_front"] == contacts["Sp_front"]
    # Front contact, same rule as the back: SCAPS honours 'flatband : 1' only with 'recalculate : 1'; otherwise it
    # keeps the stored Fi_m (4.10 eV here, on FTO with chi 4.5: a 0.4 eV accumulation contact that repels holes).
    ffb, frc = _first(front, "flatband"), _first(front, "recalculate")
    contacts["recalculate_front"] = frc
    if front_rule == "scaps" and not (ffb == 1 and frc == 1):
        contacts.update(front_type="Schottky", phi_front=contacts["phi_front_stored"])
    else:
        contacts.update(front_type="Ohmic", phi_front=None)
    return layers[::-1], contacts


def make_mesh(layers, refine=1.0, growth=0.18):
    """Fine spacing at heterointerfaces and contacts, coarser at the small steps between graded sublayers."""
    n = len(layers)
    bounds = np.concatenate([[0.0], np.cumsum([L["d"] for L in layers])])
    h_edge = [0.5e-7]
    for a, b in zip(layers[:-1], layers[1:]):
        step = max(abs(a["chi"] - b["chi"]), abs(a["Eg"] - b["Eg"]))
        dop = abs(math.log10(max(a["ND"], a["NA"], 1.0)) - math.log10(max(b["ND"], b["NA"], 1.0)))
        h_edge.append(0.02e-7 if (step > 0.05 or dop > 2) else (0.1e-7 if a["name"] == "IL" or b["name"] == "IL" else 0.5e-7))
    h_edge.append(0.5e-7)
    hmax = [10e-7 if L["name"] == "FTO" else 2e-7 if L["name"] == "ZnO" else 0.5e-7 if L["name"] == "IL" else 15e-7 for L in layers]
    xs = [np.array([0.0])]
    for k in range(n):
        a, b = bounds[k], bounds[k + 1]
        ha, hb, hm = h_edge[k] / refine, h_edge[k + 1] / refine, hmax[k] / refine
        d = b - a
        u = np.unique(np.concatenate([d * np.geomspace(1e-9, 1, 3000), d - d * np.geomspace(1e-9, 1, 3000), [0, d]]))
        s = np.minimum.reduce([np.full_like(u, hm), ha + growth * u, hb + growth * (d - u)])
        Nint = np.concatenate([[0], np.cumsum(np.diff(u) * 0.5 * (1 / s[1:] + 1 / s[:-1]))])
        m = max(int(math.ceil(Nint[-1])), 2)
        pts = a + np.interp(np.linspace(0, Nint[-1], m + 1), Nint, u)
        pts[-1] = b
        xs.append(pts[1:])
    return np.concatenate(xs), bounds


def build_cell(layers, contacts, T=300.0, T_front=0.9, R_back=0.2, refine=1.0):
    x, bounds = make_mesh(layers, refine)
    layer_of = np.clip(np.searchsorted(bounds[1:-1], x, side="left"), 0, len(layers) - 1)
    s = sesame.Builder(x, T=T)
    vt = s.scaling.energy
    fT = (T / 300.0) ** 1.5
    for k, L in enumerate(layers):
        loc = (lambda kk: (lambda pos: np.clip(np.searchsorted(bounds[1:-1], pos, side="left"), 0, len(layers) - 1) == kk))(k)
        mat = {"Nc": L["Nc"] * fT, "Nv": L["Nv"] * fT, "Eg": L["Eg"], "epsilon": L["eps"], "affinity": L["chi"],
               "mu_e": L["mu_e"], "mu_h": L["mu_h"], "tau_e": L["tau"], "tau_h": L["tau"],
               "Et": -0.5 * vt * math.log(L["Nv"] / L["Nc"]), "B": 0.0, "Cn": 0.0, "Cp": 0.0}   # level at Ev + Eg/2
        s.add_material(mat, loc)
        if L["ND"] > 0:
            s.add_donor(L["ND"], loc)
        if L["NA"] > 0:
            s.add_acceptor(L["NA"], loc)
    back = contacts["back_type"]
    front = contacts.get("front_type", "Ohmic")
    s.contact_type(front, back, contacts.get("phi_front") if front == "Schottky" else None,
                   contacts["phi_back"] if back == "Schottky" else None)
    s.contact_S(contacts["S_front"], contacts["S_front"], contacts["S_back"], contacts["S_back"])
    cv = np.concatenate([[x[0]], 0.5 * (x[1:] + x[:-1]), [x[-1]]])
    g, J_opt = sc.optical_generation(layers, bounds, cv, T_front, R_back)
    s.generation(g)
    cell = sc.Cell(layers, contacts, x, bounds, layer_of, s, np.array(s.g, copy=True), J_opt,
                   dict(T_front=T_front, R_back=R_back, T=T))
    return cell


def mono_generation(cell, lam_nm, flux=1e16):
    """Generation (cm^-3 s^-1) per node for monochromatic light of `flux` photons/cm2/s (same optics as AM1.5)."""
    lam = np.atleast_1d(float(lam_nm))
    alph = np.array([sc.alpha_scaps(L["abs"], lam) for L in cell.layers])
    th = np.array([L["d"] for L in cell.layers])[:, None]
    tau_b = np.concatenate([[np.zeros_like(lam)], np.cumsum(alph * th, 0)])
    x = cell.x
    cv = np.concatenate([[x[0]], 0.5 * (x[1:] + x[:-1]), [x[-1]]])
    k = np.clip(np.searchsorted(cell.bounds, cv, side="right") - 1, 0, len(cell.layers) - 1)
    te = tau_b[k] + alph[k] * (cv - cell.bounds[k])[:, None]
    tL = tau_b[-1]
    Tf, Rb = cell.optics["T_front"], cell.optics["R_back"]
    fwd = Tf * flux * np.exp(-te)
    bwd = Tf * flux * np.exp(-tL) * Rb * np.exp(-(tL - te))
    absorbed = (fwd[:-1] - fwd[1:]) + (bwd[1:] - bwd[:-1])
    return absorbed[:, 0] / np.diff(cv)


def eqe(cell, sol0, lams, flux=2e16, tol=1e-8):
    """Small-signal EQE at short circuit under the 1-sun bias: EQE = dJ / (q * flux) for a monochromatic probe."""
    s = cell.system
    J0 = sc.currents(cell, sol0)["J"]
    solver = sc.Solver(use_mumps=False)
    solver.equilibrium = cell.v_eq
    out = []
    for lam in lams:
        g_add = mono_generation(cell, lam, flux) / s.scaling.generation
        s.g = cell.g_full + g_add
        new = solver.solve(s, compute="all", guess=sc._copy(sol0), tol=tol, maxiter=60, verbose=False)
        out.append(float("nan") if new is None else (sc.currents(cell, new)["J"] - J0) / (sc.Q * flux * 1e3) * 100)
    s.g = cell.g_full.copy()
    return np.array(out)
