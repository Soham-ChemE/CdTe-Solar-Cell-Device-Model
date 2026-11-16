"""Pseudomorphic ZnSe/CdTe offsets.

P1: ZnSe strained in-plane to CdTe (CdTe cubic).  P2: CdTe strained in-plane to ZnSe (ZnSe cubic).
dEv = Ev(CdTe) - Ev(ZnSe);  dEc = Ec(ZnSe) - Ec(CdTe).

Route (i)  explicit strained superlattice (sl/P*_n3): dEv = dV + (E_top - Vbar)_CdTe - (E_top - Vbar)_ZnSe with each bulk
           reference computed at exactly the strain it has in the superlattice. No deformation-potential assumption,
           but PBE gaps of the strained layers are small, so the superlattice may have a PBE broken gap (checked).
Route (ii) bulk only: natural offset (method L, n = 3) + absolute shift of the strained layer's top valence state:
           [(E_top - E_c)_strained - (E_VBM - E_c)_cubic] + a_c ln(V_strained/V_cubic), a_c = D001 of the cation-s
           level from the homojunction (same approximation as method L).
SOC of a strained layer: quasi-cubic (Hopfield) model, i.e. the 6x6 p-manifold Hamiltonian with the scalar-relativistic
crystal-field splitting of that strained cell and the cubic Delta_SO of that material (checked against the explicit
FR calculation where the FR result is not band-inverted).
Strained gap = exp. cubic gap + PBE (scalar-relativistic) change of E_CBM(Gamma) - E_top(Gamma) + change of the SOC shift.
"""
import json, math
import numpy as np
from common import MAT, EG_EXP, HERE, a_avg
from bulk_refs import tag_of
from pseudomorphic import CASES


def B(m, a, c=None, soc=False):
    t = tag_of(m, round(a, 5) if c is None else a, None if c is None else round(c, 5), soc=soc)
    f = HERE / ("soc" if soc else "bulk") / t / "result.json"
    return json.loads(f.read_text()) if f.exists() else None


def so_shift(e_xy, e_z, dso):
    """Top-of-valence shift from SOC for a p manifold with SR levels e_xy (doublet) and e_z (singlet)."""
    Lx = np.array([[0, 0, 0], [0, 0, -1j], [0, 1j, 0]]); Ly = np.array([[0, 0, 1j], [0, 0, 0], [-1j, 0, 0]])
    Lz = np.array([[0, -1j, 0], [1j, 0, 0], [0, 0, 0]])
    Sx = 0.5 * np.array([[0, 1], [1, 0]]); Sy = 0.5 * np.array([[0, -1j], [1j, 0]]); Sz = 0.5 * np.array([[1, 0], [0, -1]])
    LS = sum(np.kron(L, S) for L, S in ((Lx, Sx), (Ly, Sy), (Lz, Sz)))
    H = np.kron(np.diag([e_xy, e_xy, e_z]), np.eye(2)) + (2 * dso / 3) * LS
    ev = np.linalg.eigvalsh(H)
    return ev.max() - max(e_xy, e_z), ev


def main():
    rows, out = [], {}
    nat = json.loads((HERE / "calibration.json").read_text())["pairs"]["ZnSe_CdTe_n3"]
    for name, cs in CASES.items():
        s = cs["strained"]; u = "CdTe" if s == "ZnSe" else "ZnSe"
        c_s = cs["cA"] if s == cs["A"] else cs["cB"]
        a0 = MAT[s][2]
        sr_s, sr_eq = B(s, cs["apar"], c_s), B(s, a0)
        fr_s = B(s, cs["apar"], c_s, soc=True)
        dso = {m: B(m, MAT[m][2], soc=True)["Delta_SO"] for m in ("CdTe", "ZnSe")}
        top3 = np.array(sr_s["top_val_gamma"][-3:])        # p manifold at Gamma, ascending
        # identify doublet/singlet
        if abs(top3[2] - top3[1]) < 1e-3:
            e_xy, e_z = top3[2], top3[0]
        else:
            e_xy, e_z = top3[0], top3[2]
        sh, ev = so_shift(e_xy, e_z, dso[s])
        rec = dict(strained=s, apar=cs["apar"], c=c_s, dcf_SR=float(e_z - e_xy), so_shift_model=float(sh),
                   so_levels_model=[float(x - ev.max()) for x in ev[::2]], so_shift_cubic=dso[s] / 3)
        if fr_s and fr_s.get("ok"):
            t6 = np.array(fr_s["top6"][-6:])
            rec["FR_top6_rel"] = [float(x - t6[-1]) for x in t6]
            rec["FR_gap"] = fr_s["gap"]
            rec["so_shift_FR_direct"] = float(fr_s["VBM_minus_Vbar"] - sr_s["VBM_minus_Vbar"])
        # strained gap (exp-anchored)
        gap_change = (sr_s["E_CBM_gamma"] - sr_s["E_VBM_gamma"]) - (sr_eq["E_CBM_gamma"] - sr_eq["E_VBM_gamma"])
        Eg_s = EG_EXP[s] + gap_change - (sh - dso[s] / 3)
        rec.update(gap_change_SR=gap_change, Eg_strained=Eg_s)
        Eg = {s: Eg_s, u: EG_EXP[u]}
        # route (ii): bulk only, method L natural offset + absolute shift of the strained layer
        hj = json.loads((HERE / "sl" / f"HJ_{s}_eps5_n2" / "homojunction.json").read_text())
        cat = "Cd4s" if MAT[s][0] == "Cd" else "Zn3s"
        a_c = hj["D001_" + cat]
        dlnV = math.log((cs["apar"] / a0) ** 2 * (c_s / a0))
        rel = (sr_s["E_VBM_gamma"] - sr_s[cat]) - (sr_eq["E_VBM_gamma"] - sr_eq[cat])
        dE_abs = rel + a_c * dlnV + (sh - dso[s] / 3)
        dEv_ii = nat["L"] - dE_abs if s == "ZnSe" else nat["L"] + dE_abs
        dEc_ii = (Eg["ZnSe"] - Eg["CdTe"]) - dEv_ii
        rec.update(route_ii=dict(dEv=dEv_ii, dEc=dEc_ii, natural_L=nat["L"], VBM_shift_rel_core=rel, a_c=a_c, dlnV=dlnV,
                                 VBM_shift_abs=dE_abs))
        # route (i): explicit superlattice
        d = HERE / "sl" / f"{name}_n3"
        if (HERE / "sl" / f"{name}_n3_fixed" / "lineup.json").exists():   # fixed-occupation rerun preferred (P2)
            d = HERE / "sl" / f"{name}_n3_fixed"
        if (d / "lineup.json").exists():
            lin = json.loads((d / "lineup.json").read_text())
            sr_u = B(u, MAT[u][2])
            ev_ = {s: sr_s["VBM_minus_Vbar"] + sh, u: sr_u["VBM_minus_Vbar"] + dso[u] / 3}
            EvZ = lin["VA_centre"] + ev_["ZnSe"]; EvC = lin["VB_centre"] + ev_["CdTe"]
            dEv_i = EvC - EvZ
            rec.update(route_i=dict(dEv=dEv_i, dEc=(Eg["ZnSe"] - Eg["CdTe"]) - dEv_i, dV=lin["dV_centre"],
                                    ripple=max(lin["ripple_A"], lin["ripple_B"]),
                                    dV_IF1=lin["dV_IF1_extrap"], dV_IF2=lin["dV_IF2_extrap"]))
            scf = (d / "scf.out").read_text()
            import re
            ef = re.findall(r"the Fermi energy is\s+([-\d.]+)", scf)
            rec["route_i"]["fermi_eV"] = float(ef[-1]) if ef else None
        out[name] = rec
        for route in ("route_i", "route_ii"):
            if route not in rec:
                continue
            r = rec[route]
            rows.append(dict(pair="ZnSe/CdTe", method=f"pseudomorphic {name} {route.replace('_', ' ')}", n=3,
                             dV=f"{r['dV']:.3f}" if "dV" in r else "",
                             dEv_PBE="", SO_correction="SOC in dEv (quasi-cubic model for strained layer)",
                             dEv_final=f"{r['dEv']:.3f}", dEc_final=f"{r['dEc']:.3f}",
                             notes=(f"{s} at a_par={cs['apar']:.3f}, c={c_s:.3f} A (lin. elasticity); strained {s} gap "
                                    f"{Eg_s:.2f} eV (exp-anchored); "
                                    + (f"explicit SL ({d.name}), k 4x4x1" if route == "route_i"
                                       else "natural L + bulk VBM shift with a_c(D001)"))))
    (HERE / "pseudomorphic.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps(out, indent=1, default=float))
    ex = HERE / "results_extra.json"
    prev = json.loads(ex.read_text()) if ex.exists() else []
    prev = [r for r in prev if not r["method"].startswith("pseudomorphic")] + rows
    ex.write_text(json.dumps(prev, indent=1))


if __name__ == "__main__":
    main()
