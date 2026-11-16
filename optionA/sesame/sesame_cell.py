"""NIST Sesame 2.0 drift-diffusion model of the option-A CdSeTe/CdTe cell with a ZnO or MgZnO front buffer.

It reproduces the SCAPS model written by optionA/mzo_model.py (P dict and build()), layer by layer:

    front (light, x = 0)  FTO 0.5 um | buffer 100 nm | IL 10 nm | CdSeTe 0.49 um | CdTe 3.0 um  (x = L) back

Sesame's x axis runs from the front contact (x = 0, light enters here) to the back contact (x = L).
SCAPS draws the same stack back -> front (left -> right); only the axis direction differs.

Physics choices (each mirrors the SCAPS .def unless README.md says otherwise):
  * Material constants (eps, Nc, Nv, mobilities) are those SCAPS uses (CdTe baseline file, Gloeckler 2003).
  * Bulk SRH through one neutral midgap level (E_t = Ev + Eg/2, as in SCAPS); tau = 1/(Nt sigma vth).
  * Front recombination: a 10 nm CdSeTe interface layer (IL) whose midgap-defect density gives
    S_front = Nt sigma vth d_IL, exactly as SCAPS does (tau_IL = d_IL / S_front). No Sesame planar defect.
    Optional sensitivity variant (not SCAPS): add_interface_defect() puts S_front on two-node interface states that
    couple the buffer conduction band to the absorber valence band (see README, grid.py --interface).
  * Buffer and FTO carry no recombination centres (SCAPS removes their defects): tau = 1 s.
  * Back contact: Schottky with work function phi_back, Sn = Sp = 1e7 cm/s.
    Front contact: Ohmic (flat band, Dirichlet charge neutrality) on FTO, Sn = Sp = 1e7 cm/s.
  * Optics: Beer-Lambert with the SCAPS absorption files, log interpolation of alpha (SCAPS rule), SCAPS
    AM1.5G spectrum, front transmission T_front and back reflection R_back with a second (reflected) pass,
    no internal front reflection (SCAPS Rint = 0). Generation is the exact photon absorption in each node's
    control volume, so the discrete generation integrates to the optical total.
  * Series resistance: post-processing V_ext = V_int - J*Rs (generator convention), as SCAPS reports it.
"""
from __future__ import annotations

import logging
import math
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

import sesame
from sesame.observables import get_bulk_rr, get_jn, get_jp
from sesame.solvers import Solver

logging.getLogger().setLevel(logging.WARNING)       # sesame sets the root logger to DEBUG on import

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SCAPS_DIR = REPO / "tools/wineprefix/drive_c/Program Files (x86)/Scaps3311"
ABS_DIR = REPO / "scaps/absorption"
sys.path.insert(0, str(REPO / "physics"))
from sq_limit import load_spectrum  # noqa: E402

Q = 1.602176634e-19
KB = 1.380649e-23
H = 6.62607015e-34
C = 2.99792458e8
T = 300.0
VT = KB * T / Q                                   # 0.025852 V

# ------------------------------------------------------------------ SCAPS model inputs (cm units)
# Per-layer constants exactly as they appear in the generated .def files (SCAPS CdTe baseline; buffer = the
# baseline's CdS layer with eps set to 9.0 by mzo_model.build, FTO = the baseline's SnOx layer).
CDTE_BASE = dict(eps=9.4, Nc=8e17, Nv=1.8e19, mu_e=320.0, mu_h=40.0)
BUF_BASE = dict(eps=9.0, Nc=2.2e18, Nv=1.8e19, mu_e=100.0, mu_h=25.0)
FTO_BASE = dict(eps=9.0, Nc=2.2e18, Nv=1.8e19, mu_e=100.0, mu_h=25.0, Eg=3.6, chi=4.0)

# mzo_model.P (priors) and the x = 0.15 best fit (LHS sample 220, rounded as in zno_hypotheses.BEST)
P = {"chi_CdTe": 3.90, "Eg_CdTe": 1.50, "Eg_CdSeTe": 1.40, "dchi_CdSeTe": 0.10, "NA": 1e15, "tau": 30e-9,
     "sigma": 1e-13, "vth": 1e7, "S_front": 1e4, "d_IL": 10e-7, "ND_MZO": 1e17, "ND_FTO": 1e20,
     "phi_back": 5.10, "Eg_cap": 3.50, "S_contact": 1e7}
BEST = {"tau": 7.24e-9, "NA": 4.14e14, "phi_back": 5.27, "S_front": 7.51e3, "ND_MZO": 6.47e17}
RS_BEST = 1.32                                    # ohm cm2

ABS_FILES = {
    "CdTe": SCAPS_DIR / "absorption/CdTe-base.abs",
    "CdSeTe": ABS_DIR / "CdSeTe_from_CdTe_shift0p10.abs",
    "FTO": SCAPS_DIR / "absorption/SnOx-base.abs",
}
NO_RECOMB_TAU = 1.0                               # s; SCAPS buffer/FTO have no recombination centres


def buffer_abs_file(Eg_opt: float) -> Path:
    """Absorption file mzo_model.build writes for an optical buffer gap Eg_opt (ZnO.abs shifted)."""
    return ABS_DIR / (f"MgZnO_Eg{Eg_opt:.2f}.abs".replace(".", "p", 1))


def case_layers(x: float, dEc: float, Eg_buf: float, p: dict | None = None) -> tuple[list[dict], dict]:
    """Layer list (front -> back) and contact dict for Mg fraction x, mirroring mzo_model.build().

    dEc = buffer CBM offset relative to CdSeTe (positive = spike); buffer chi = chi_CdSeTe - dEc.
    Eg_buf is the measured (optical) buffer gap; the electrical gap is capped at P['Eg_cap'] like SCAPS.
    """
    p = {**P, **(p or {})}
    chi_se = p["chi_CdTe"] + p["dchi_CdSeTe"]
    tau_il = p["d_IL"] / p["S_front"]             # = 1/(Nt_IL sigma vth) with Nt_IL = S/(sigma vth d)
    layers = [
        dict(name="FTO", d=0.5e-4, **FTO_BASE, NA=0.0, ND=p["ND_FTO"], tau=NO_RECOMB_TAU, abs=ABS_FILES["FTO"]),
        dict(name="buffer", d=0.1e-4, **BUF_BASE, Eg=min(Eg_buf, p["Eg_cap"]), chi=chi_se - dEc, NA=0.0,
             ND=p["ND_MZO"], tau=NO_RECOMB_TAU, abs=buffer_abs_file(Eg_buf)),
        dict(name="IL", d=p["d_IL"], **CDTE_BASE, Eg=p["Eg_CdSeTe"], chi=chi_se, NA=p["NA"], ND=0.0,
             tau=tau_il, abs=ABS_FILES["CdSeTe"]),
        dict(name="CdSeTe", d=0.49e-4, **CDTE_BASE, Eg=p["Eg_CdSeTe"], chi=chi_se, NA=p["NA"], ND=0.0,
             tau=p["tau"], abs=ABS_FILES["CdSeTe"]),
        dict(name="CdTe", d=3.0e-4, **CDTE_BASE, Eg=p["Eg_CdTe"], chi=p["chi_CdTe"], NA=p["NA"], ND=0.0,
             tau=p["tau"], abs=ABS_FILES["CdTe"]),
    ]
    contacts = dict(phi_back=p["phi_back"], S_back=p["S_contact"], S_front=p["S_contact"])
    return layers, contacts


# ------------------------------------------------------------------ SCAPS .def reader (for cross-checks)
def read_scaps_def(path: Path | str) -> tuple[list[dict], dict]:
    """Parse a SCAPS .def into the same (layers front -> back, contacts) structure, converted to cm units."""
    t = Path(path).read_text(encoding="latin-1").replace("\r", "")
    head, *layer_txt = t.split("\nlayer\n")
    layer_txt[-1], _, tail = layer_txt[-1].partition("front contact")

    def first(txt, key):
        m = re.search(rf"^{re.escape(key)}\s*:\s*([-\d.eE+]+)", txt, re.M)
        return float(m.group(1)) if m else None

    layers = []
    for lt in layer_txt:
        name = re.search(r"^name : (.*)$", lt, re.M).group(1).strip()
        nt = first(lt, "Nt(uniform)")
        sig = first(lt, "sigma_n")
        vth = first(lt, "v_th_n")
        et = first(lt, "Et")
        L = dict(name=name, d=first(lt, "d") * 100, eps=first(lt, "eps"), chi=first(lt, "chi"),
                 Eg=first(lt, "Eg"), Nc=first(lt, "Nc") * 1e-6, Nv=first(lt, "Nv") * 1e-6,
                 mu_e=first(lt, "mu_n") * 1e4, mu_h=first(lt, "mu_p") * 1e4,
                 NA=first(lt, "Na(uniform)") * 1e-6, ND=first(lt, "Nd(uniform)") * 1e-6,
                 vth=vth * 100, Krad=first(lt, "K_rad"),
                 abs=re.search(r"absorptionfile pure A material \(y=0\) : (.*)$", lt, re.M).group(1).strip())
        if nt is not None:
            L["Nt"] = nt * 1e-6
            L["sigma"] = sig * 1e4
            L["Et_above_Ev"] = et
            L["tau"] = 1.0 / (L["Nt"] * L["sigma"] * L["vth"])
        else:
            L["tau"] = None
        layers.append(L)
    back = head.split("back contact", 1)[1]
    front = tail
    contacts = dict(phi_back=first(back, "Fi_m"), flatband_back=first(back, "flatband"),
                    S_back=first(back, "Sn") * 100, Sp_back=first(back, "Sp") * 100,
                    filter_back=re.search(r"optical filter : (\w+)", back).group(1),
                    filterfile_back=re.search(r"filterfile : (.*)$", back, re.M).group(1).strip(),
                    flatband_front=first(front, "flatband"), S_front=first(front, "Sn") * 100,
                    Sp_front=first(front, "Sp") * 100,
                    filter_front=re.search(r"optical filter : (\w+)", front).group(1),
                    filterfile_front=re.search(r"filterfile : (.*)$", front, re.M).group(1).strip())
    return layers[::-1], contacts                       # SCAPS lists back -> front


def compare_with_def(layers: list[dict], contacts: dict, def_path: Path | str, rtol: float = 2e-3) -> list[str]:
    """Return a list of mismatches between a Sesame layer list and a SCAPS .def (empty list = identical)."""
    dl, dc = read_scaps_def(def_path)
    bad = []
    if [L["name"] for L in dl] != ["FTO", "MgZnO", "IL", "CdSeTe", "CdTe"]:
        bad.append(f"layer order {[L['name'] for L in dl]}")
    for a, b in zip(layers, dl):
        for k in ("d", "eps", "chi", "Eg", "Nc", "Nv", "mu_e", "mu_h", "NA", "ND"):
            va, vb = a[k], b[k]
            if not (abs(va - vb) <= rtol * max(abs(va), abs(vb)) or (va == 0 and vb == 0)):
                bad.append(f"{a['name']}.{k}: sesame {va:g} vs def {vb:g}")
        if b["tau"] is None:
            if a["tau"] < 1e-3:
                bad.append(f"{a['name']}: def has no defect but sesame tau {a['tau']:g}")
        elif abs(a["tau"] - b["tau"]) > rtol * b["tau"]:
            bad.append(f"{a['name']}.tau: sesame {a['tau']:g} vs def {b['tau']:g}")
        if b["tau"] is not None and abs(b["Et_above_Ev"] - b["Eg"] / 2) > 1e-3:
            bad.append(f"{a['name']}: defect not at midgap ({b['Et_above_Ev']} eV above Ev)")
        if Path(a["abs"]).name != b["abs"]:
            bad.append(f"{a['name']}.abs: sesame {Path(a['abs']).name} vs def {b['abs']}")
    if abs(contacts["phi_back"] - dc["phi_back"]) > 1e-4:
        bad.append(f"phi_back: sesame {contacts['phi_back']} vs def {dc['phi_back']}")
    for k in ("S_back", "Sp_back", "S_front", "Sp_front"):
        if abs(dc[k] - 1e7) > 1:
            bad.append(f"{k} = {dc[k]:g} cm/s in def")
    if dc["flatband_back"] != 0 or dc["flatband_front"] != 1:
        bad.append("contact flatband flags differ")
    return bad


# ------------------------------------------------------------------ optics
def read_abs(path: Path | str) -> tuple[np.ndarray, np.ndarray]:
    lam, a = [], []
    for line in Path(path).read_text(encoding="latin-1").replace("\r", "").split("\n"):
        q = line.split()
        if len(q) >= 2 and not line.lstrip().startswith(("/", ">")):
            try:
                lam.append(float(q[0])); a.append(float(q[1]))
            except ValueError:
                pass
    lam, a = np.array(lam), np.array(a)
    o = np.argsort(lam)
    return lam[o], a[o]


def alpha_scaps(path: Path | str, lam_nm: np.ndarray) -> np.ndarray:
    """alpha(lambda) in 1/cm with SCAPS rules (manual 3.5.5.3, 3.5.6.1): logarithmic interpolation; logarithmic
    extrapolation that may not rise away from the table; a zero end point gives zero beyond it."""
    L, A = read_abs(path)
    out = np.empty_like(lam_nm, dtype=float)
    inside = (lam_nm >= L[0]) & (lam_nm <= L[-1])
    la = np.log(np.maximum(A, 1e-300))
    out[inside] = np.exp(np.interp(lam_nm[inside], L, la))
    for side in ("lo", "hi"):
        m = lam_nm < L[0] if side == "lo" else lam_nm > L[-1]
        if not m.any():
            continue
        i0, i1 = (0, 1) if side == "lo" else (-1, -2)
        if A[i0] == 0:
            out[m] = 0.0
            continue
        slope = (la[i0] - la[i1]) / (L[i0] - L[i1])
        ext = la[i0] + slope * (lam_nm[m] - L[i0])
        out[m] = np.exp(np.minimum(ext, la[i0]))          # may not rise away from the table
    return out / 100.0                                      # 1/m -> 1/cm


def spectrum_flux():
    """SCAPS AM1.5G: wavelengths (nm) and photon flux per bin (photons / cm2 / s)."""
    lam, Pw = load_spectrum()
    return lam, Pw / (H * C / (lam * 1e-9)) * 1e-4


def optical_generation(layers: list[dict], bounds: np.ndarray, cv_edges: np.ndarray, T_front=0.9, R_back=0.2):
    """Generation per control volume [cv_edges[i], cv_edges[i+1]] (cm^-3 s^-1) and per-layer photon currents.

    Forward pass attenuated from x = 0; reflected pass (R_back) from x = L back to the front; no further passes.
    Absorbed photons in a control volume = (forward flux in - out) + (backward flux in - out): exact integral.
    """
    lam, phi0 = spectrum_flux()
    alph = np.array([alpha_scaps(L["abs"], lam) for L in layers])          # (nlayer, nlam) 1/cm
    tau_b = np.concatenate([[np.zeros_like(lam)], np.cumsum(alph * np.array([L["d"] for L in layers])[:, None], 0)])

    def optical_depth(xs):
        k = np.clip(np.searchsorted(bounds, xs, side="right") - 1, 0, len(layers) - 1)
        return tau_b[k] + alph[k] * (xs - bounds[k])[:, None]

    tL = tau_b[-1]
    fwd = lambda tx: T_front * phi0 * np.exp(-tx)
    bwd = lambda tx: T_front * phi0 * np.exp(-tL) * R_back * np.exp(-(tL - tx))
    te = optical_depth(cv_edges)
    absorbed = (fwd(te[:-1]) - fwd(te[1:])) + (bwd(te[1:]) - bwd(te[:-1]))      # (ncv, nlam) photons/cm2/s
    g = absorbed.sum(1) / np.diff(cv_edges)
    tb = optical_depth(bounds)
    per_layer = (fwd(tb[:-1]) - fwd(tb[1:]) + bwd(tb[1:]) - bwd(tb[:-1])).sum(1) * Q * 1e3   # mA/cm2
    return g, {L["name"]: float(j) for L, j in zip(layers, per_layer)}


# ------------------------------------------------------------------ mesh
@dataclass
class MeshSpec:
    h_contact_front: float = 0.5e-7      # cm (0.5 nm)
    h_fto_buf: float = 0.02e-7           # FTO Debye length ~0.36 nm at 1e20 cm-3
    h_buf_il: float = 0.02e-7            # main heterojunction
    h_il_cst: float = 0.1e-7
    h_cst_cdte: float = 0.1e-7
    h_contact_back: float = 0.5e-7
    growth: float = 0.15                 # spacing grows by (1 + growth) per node away from an interface
    hmax: tuple = (10e-7, 2e-7, 0.5e-7, 10e-7, 20e-7)   # FTO, buffer, IL, CdSeTe, CdTe
    refine: float = 1.0                  # divide every spacing by this (mesh-convergence checks)


def make_mesh(layers: list[dict], ms: MeshSpec = MeshSpec()) -> tuple[np.ndarray, np.ndarray]:
    """Nodes from x = 0 (front contact) to x = L. Spacing grows linearly with distance from each layer edge
    (geometric progression) up to the layer's hmax. Every layer boundary is a node."""
    bounds = np.concatenate([[0.0], np.cumsum([L["d"] for L in layers])])
    h_edge = [ms.h_contact_front, ms.h_fto_buf, ms.h_buf_il, ms.h_il_cst, ms.h_cst_cdte, ms.h_contact_back]
    h_edge = [h / ms.refine for h in h_edge]
    xs = [np.array([0.0])]
    for k in range(len(layers)):
        a, b = bounds[k], bounds[k + 1]
        ha, hb, hm = h_edge[k], h_edge[k + 1], ms.hmax[k] / ms.refine
        d = b - a
        u = np.unique(np.concatenate([d * np.geomspace(1e-9, 1, 4000), d - d * np.geomspace(1e-9, 1, 4000), [0, d]]))
        s = np.minimum.reduce([np.full_like(u, hm), ha + ms.growth * u, hb + ms.growth * (d - u)])
        Nint = np.concatenate([[0], np.cumsum(np.diff(u) * 0.5 * (1 / s[1:] + 1 / s[:-1]))])
        n = max(int(math.ceil(Nint[-1])), 2)
        pts = a + np.interp(np.linspace(0, Nint[-1], n + 1), Nint, u)
        pts[-1] = b
        xs.append(pts[1:])
    x = np.concatenate(xs)
    return x, bounds


# ------------------------------------------------------------------ system
@dataclass
class Cell:
    layers: list
    contacts: dict
    x: np.ndarray
    bounds: np.ndarray
    layer_of: np.ndarray
    system: object
    g_full: np.ndarray
    J_opt: dict                          # photon current absorbed per layer (mA/cm2)
    optics: dict = field(default_factory=dict)
    v_eq: np.ndarray | None = None
    if_defect: dict | None = None        # optional two-node interface recombination (add_interface_defect)


def build_cell(layers, contacts, T_front=0.9, R_back=0.2, mesh: MeshSpec = MeshSpec()) -> Cell:
    x, bounds = make_mesh(layers, mesh)
    layer_of = np.clip(np.searchsorted(bounds[1:-1], x, side="left"), 0, len(layers) - 1)
    s = sesame.Builder(x, T=T)
    for k, L in enumerate(layers):
        loc = (lambda kk: (lambda pos: np.clip(np.searchsorted(bounds[1:-1], pos, side="left"), 0, len(layers) - 1) == kk))(k)
        mat = {"Nc": L["Nc"], "Nv": L["Nv"], "Eg": L["Eg"], "epsilon": L["eps"], "affinity": L["chi"],
               "mu_e": L["mu_e"], "mu_h": L["mu_h"], "tau_e": L["tau"], "tau_h": L["tau"],
               # SCAPS level at Ev + Eg/2; Sesame measures E_t from the intrinsic level Ei
               "Et": -0.5 * VT * math.log(L["Nv"] / L["Nc"]), "B": 0.0, "Cn": 0.0, "Cp": 0.0}
        s.add_material(mat, loc)
        if L["ND"] > 0:
            s.add_donor(L["ND"], loc)
        if L["NA"] > 0:
            s.add_acceptor(L["NA"], loc)
    s.contact_type("Ohmic", "Schottky", None, contacts["phi_back"])
    s.contact_S(contacts["S_front"], contacts["S_front"], contacts["S_back"], contacts["S_back"])
    cv = np.concatenate([[x[0]], 0.5 * (x[1:] + x[:-1]), [x[-1]]])
    g, J_opt = optical_generation(layers, bounds, cv, T_front, R_back)
    s.generation(g)
    return Cell(layers, contacts, x, bounds, layer_of, s, np.array(s.g, copy=True), J_opt, dict(T_front=T_front, R_back=R_back))


def neutral_guess(cell: Cell) -> np.ndarray:
    """Local charge-neutrality potential (kT units) with E_F = 0; Dirichlet contact values included."""
    s = cell.system
    v = np.where(s.rho > 0, np.log(np.abs(s.rho) / s.Nc) - s.bl, -s.Eg - np.log(np.abs(s.rho) / s.Nv) - s.bl)
    if cell.contacts.get("back_type", "Schottky") == "Schottky":
        v[-1] = -cell.contacts["phi_back"] / s.scaling.energy
    if cell.contacts.get("front_type", "Ohmic") == "Schottky":      # used by kujovic/kj_sesame.py only
        v[0] = -cell.contacts["phi_front"] / s.scaling.energy
    return v


# ------------------------------------------------------------------ currents and losses
def currents(cell: Cell, sol: dict) -> dict:
    """Terminal current and loss breakdown (mA/cm2, generator convention: + = delivered photocurrent).

    J_term = jn(back link) + jp(front link) + sum (g - r) dxbar  -- built from local quantities only, so it
    does not suffer the cancellation of quasi-Fermi-level differences in degenerate FTO. The plain link
    current (Sesame's full_current, at every link) is returned as a convergence check.
    """
    s, x = cell.system, cell.x
    efn, efp, v = sol["efn"], sol["efp"], sol["v"]
    n = s.Nc * np.exp(s.bl + efn + v)
    p = s.Nv * np.exp(-s.Eg - s.bl - efp - v)
    r = get_bulk_rr(s, n, p)
    N = len(x)
    dxbar = np.zeros(N)
    dxbar[1:-1] = 0.5 * (s.dx[1:] + s.dx[:-1])
    veq = cell.v_eq
    n_eq = s.Nc * np.exp(s.bl + veq)
    p_eq = s.Nv * np.exp(-s.Eg - s.bl - veq)
    jn_back = -s.Scn[1] * (n[-1] - n_eq[-1])          # minority electrons into the back contact
    jp_front = -s.Scp[0] * (p[0] - p_eq[0])           # minority holes into the front contact
    sc = s.scaling.current * 1e3                       # -> mA/cm2
    gen = float((s.g * dxbar).sum()) * sc
    rec_layer = {L["name"]: float((r * dxbar)[cell.layer_of == k].sum()) * sc for k, L in enumerate(cell.layers)}
    U_if = 0.0
    if cell.if_defect is not None:
        U_if = float(_if_rate(cell, efn, efp, v)[0])
        rec_layer["interface"] = U_if * sc
    J = (jn_back + jp_front + ((s.g - r) * dxbar).sum() - U_if) * sc
    i = np.arange(N - 1)
    jl = (get_jn(s, efn, v, i, i + 1, s.dx) + get_jp(s, efp, v, i, i + 1, s.dx)) * sc
    mid = N // 2
    return dict(J=float(J), J_link_mid=float(jl[mid]), J_link_absorber_median=float(np.median(jl[cell.layer_of[:-1] >= 2])),
                gen=gen, rec=rec_layer, loss_back_minority=float(-jn_back * sc), loss_front_minority=float(-jp_front * sc))


# ------------------------------------------------------------------ optional: cross-interface front recombination
# Not used for the SCAPS validation or the main grid (those use the IL, exactly as SCAPS). This is a sensitivity
# variant: interface states at the buffer/absorber boundary capture electrons from the BUFFER conduction band and
# holes from the ABSORBER valence band (the textbook cliff mechanism, activation energy Eg - |dEc|). Sesame's own
# planar defects only see carriers on one node, so the two-node rate is added by subclassing the solver
# (Sesame's source is not modified).
def add_interface_defect(cell: Cell, S: float, k_front: int = 1):
    """Two-node SRH at the interface between layer k_front (buffer) and the next layer: equal capture, level at
    the middle of the interface gap Ec(buffer) - Ev(absorber), recombination velocity S = sigma vth N_s (cm/s)."""
    s = cell.system
    Z = int(np.where(cell.layer_of == k_front)[0][-1])
    I = Z + 1
    cell.if_defect = dict(Z=Z, I=I, S_cm_s=S, S=S / s.scaling.velocity,
                          dxbar_Z=0.5 * (s.dx[Z - 1] + s.dx[Z]), dxbar_I=0.5 * (s.dx[I - 1] + s.dx[I]))
    return cell


def _finalize_interface(cell: Cell):
    s, d, v = cell.system, cell.if_defect, cell.v_eq
    Z, I = d["Z"], d["I"]
    Ec_Z = -(s.bl[Z] + v[Z])
    Ev_I = -(s.bl[I] + v[I]) - s.Eg[I]
    half = 0.5 * (Ec_Z - Ev_I)                       # trap at mid interface gap (kT units, E_F = 0 reference)
    d["n1"], d["p1"] = s.Nc[Z] * np.exp(-half), s.Nv[I] * np.exp(-half)
    d["Eg_interface_eV"] = float(2 * half * s.scaling.energy)


def _if_rate(cell: Cell, efn, efp, v):
    """Interface rate (dimensionless, per area) and its derivatives w.r.t. (efn_Z, v_Z, efp_I, v_I)."""
    d, s = cell.if_defect, cell.system
    Z, I = d["Z"], d["I"]
    n = s.Nc[Z] * np.exp(s.bl[Z] + efn[Z] + v[Z])
    p = s.Nv[I] * np.exp(-s.Eg[I] - s.bl[I] - efp[I] - v[I])
    E = np.exp(efp[I] - efn[Z])
    N = n * p * (1 - E)
    D = n + p + d["n1"] + d["p1"]
    dN = np.array([n * p, N, -n * p, -N])
    dD = np.array([n, n, -p, -p])
    return d["S"] * N / D, d["S"] * (dN * D - N * dD) / D ** 2


class _IFSolver(Solver):
    """Sesame solver with the two-node interface recombination added to the residual and the Jacobian."""

    def __init__(self, cell: Cell):
        super().__init__(use_mumps=False)
        self.cell = cell

    def _get_system(self, x, system, periodic_bcs):
        f, J = super()._get_system(x, system, periodic_bcs)
        if self.equilibrium is None:
            return f, J
        d = self.cell.if_defect
        Z, I = d["Z"], d["I"]
        U, dU = _if_rate(self.cell, x[0::3], x[1::3], x[2::3])
        f[3 * Z] -= U / d["dxbar_Z"]                 # electrons removed from the buffer node
        f[3 * I + 1] += U / d["dxbar_I"]             # holes removed from the absorber node
        cols = [3 * Z, 3 * Z + 2, 3 * I + 1, 3 * I + 2] * 2
        rows = [3 * Z] * 4 + [3 * I + 1] * 4
        vals = np.concatenate([-dU / d["dxbar_Z"], dU / d["dxbar_I"]])
        from scipy.sparse import csr_matrix
        return f, J + csr_matrix((vals, (rows, cols)), shape=J.shape)


# ------------------------------------------------------------------ J-V sweep
@dataclass
class JV:
    V: np.ndarray                      # internal (junction) voltage, V
    J: np.ndarray                      # mA/cm2, generator convention (Jsc > 0)
    ok: bool
    note: str
    seconds: float
    detail: list = field(default_factory=list)     # per-point loss breakdown
    sols: dict = field(default_factory=dict)       # stored solutions at selected voltages
    stats: dict = field(default_factory=dict)      # convergence aids used (ramp insertions, step halvings)


def _solve(solver, cell, guess, tol, maxiter):
    try:
        return solver.solve(cell.system, compute="all", guess=guess, tol=tol, maxiter=maxiter, verbose=False)
    except Exception as e:          # singular Jacobian etc.
        logging.debug("solve exception %s", e)
        return None


def _copy(sol):
    return {k: np.array(v, copy=True) for k, v in sol.items()}


def run_jv(cell: Cell, V_max=1.2, dV=0.01, tol=1e-8, maxiter=60, stop_after_voc=3, keep=(0.0,), min_dV=1e-4, ramp=None, vlist=None,
           time_limit=1800, log=None) -> JV:
    """Equilibrium -> generation ramp at V = 0 -> forward sweep in steps dV (halved on failure)."""
    t0 = time.time()
    say = log or (lambda *a: None)
    solver = _IFSolver(cell) if cell.if_defect is not None else Solver(use_mumps=False)
    s = cell.system
    eq = None
    try:
        eq = solver.solve(s, compute="Poisson", guess={"v": neutral_guess(cell)}, tol=tol, maxiter=400, verbose=False)
    except Exception as e:
        say(f"equilibrium exception: {e}")
    if eq is None:
        return JV(np.array([]), np.array([]), False, "equilibrium Poisson solve failed", time.time() - t0)
    cell.v_eq = np.array(solver.equilibrium, copy=True)
    if cell.if_defect is not None:
        _finalize_interface(cell)
    vR = cell.v_eq[-1]
    # generation ramp at V = 0 (a failed step inserts an intermediate intensity)
    sol, f_done, fails = _copy(eq), 0.0, 0
    queue = list(ramp) if ramp is not None else [1e-8, 1e-6, 1e-4, 1e-3, 1e-2, 0.03, 0.1, 0.3, 0.6, 1.0]
    while queue:
        f = queue[0]
        s.g = cell.g_full * f
        new = _solve(solver, cell, _copy(sol), tol, maxiter)
        if new is None:
            fails += 1
            if fails > 40 or time.time() - t0 > time_limit:
                s.g = cell.g_full.copy()
                return JV(np.array([]), np.array([]), False, f"generation ramp failed at {f:.3g} sun", time.time() - t0)
            queue.insert(0, math.sqrt(f_done * f) if f_done > 0 else f / 100)
            continue
        sol, f_done = new, f
        queue.pop(0)
    s.g = cell.g_full.copy()
    # forward sweep on the dV grid; a failed step inserts a midpoint voltage
    Vs, Js, det, keep_sols = [], [], [], {}
    V, prev, n_after, note, n_retry, n_half = 0.0, None, 0, "ok", 0, 0
    queue = [round(v, 10) for v in (vlist if vlist is not None else np.arange(dV, V_max + dV / 2, dV))]
    while True:
        c = currents(cell, sol)
        Vs.append(V); Js.append(c["J"]); det.append({"V": V, **c})
        if any(abs(V - kv) < 1e-9 for kv in keep):
            keep_sols[round(V, 6)] = _copy(sol)
        if c["J"] < 0:
            n_after += 1
        if n_after >= stop_after_voc or not queue:
            break
        if time.time() - t0 > time_limit:
            note = f"time limit at V = {V:.3f}"
            break
        while queue:
            V_next = queue[0]
            g = _copy(sol)
            if prev is not None:                   # linear predictor from the last two points
                w = (V_next - V) / (V - prev[0])
                for key in ("efn", "efp", "v"):
                    g[key] = sol[key] + w * (sol[key] - prev[1][key])
            g["v"][-1] = vR + V_next / s.scaling.energy
            new = _solve(solver, cell, g, tol, maxiter)
            if new is None and prev is not None:   # retry from the last solution without the predictor
                g = _copy(sol); g["v"][-1] = vR + V_next / s.scaling.energy
                new = _solve(solver, cell, g, tol, maxiter)
                n_retry += new is not None
            if new is not None:
                queue.pop(0)
                prev, sol, V = (V, sol), new, V_next
                break
            if V_next - V < min_dV:
                note = f"Newton failed beyond V = {V:.4f} V"
                queue = []
                break
            n_half += 1
            queue.insert(0, round(0.5 * (V + V_next), 10))
        if note != "ok":
            break
    J = np.array(Js)
    ok = note == "ok" and (J < 0).any()
    if note == "ok" and not (J < 0).any():
        note = f"no Voc below V_max = {V_max} V"
    stats = dict(ramp_insertions=fails, predictor_fallbacks=n_retry, step_halvings=n_half)
    return JV(np.array(Vs), J, ok, note, time.time() - t0, det, keep_sols, stats)


# ------------------------------------------------------------------ SCAPS-style figures of merit
def jv_metrics(V_int, J, Rs=0.0, P_in=100.0) -> dict:
    """Voc, Jsc, FF, eta from an internal-voltage J-V (mA/cm2, generator convention), with series resistance
    applied as SCAPS does: V_ext = V_int - J*Rs (J in A/cm2)."""
    V_int, J = np.asarray(V_int, float), np.asarray(J, float)
    Vx = V_int - J * 1e-3 * Rs
    out = dict(Voc=float("nan"), Jsc=float("nan"), FF=float("nan"), eta=float("nan"), Vmpp=float("nan"), Jmpp=float("nan"))
    if len(J) < 3 or not (J < 0).any() or Vx[0] > 0:
        return out
    from scipy.interpolate import PchipInterpolator
    o = np.argsort(Vx)
    Vx, J = Vx[o], J[o]
    f = PchipInterpolator(Vx, J)
    out["Jsc"] = float(f(0.0))
    i = int(np.argmax(J < 0))
    from scipy.optimize import brentq
    out["Voc"] = float(brentq(f, Vx[i - 1], Vx[i]))
    vv = np.linspace(0, out["Voc"], 20001)
    P = vv * f(vv)
    k = int(np.argmax(P))
    out.update(Vmpp=float(vv[k]), Jmpp=float(f(vv[k])), FF=float(100 * P[k] / (out["Voc"] * out["Jsc"])), eta=float(100 * P[k] / P_in))
    out["Voc"] *= 1000          # mV
    return out
