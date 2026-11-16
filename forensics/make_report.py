"""Merge reported (PR 2) and reproduced (SCAPS re-run) values into tables and figures for docs/FORENSICS.md."""
import csv
import math
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
FIG = HERE.parent / "figures"


def load(name):
    with open(HERE / name) as fh:
        return list(csv.DictReader(fh))


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return math.nan


rep, sim = load("reported_values.csv"), load("forensics_results.csv")
sheet = {(r["case"], round(f(r["x"]), 1)): r for r in rep if r["source"] == "spreadsheet_ETL_sweep"}
paper = {r["case"]: r for r in rep if r["source"] == "paper_table2_2um"}
metals_rep = {r["case"]: r for r in rep if r["source"] == "paper_metals"}
by = defaultdict(list)
for r in sim:
    by[r["group"]].append(r)

out = []
P = out.append

# --- A: transport-layer sweeps
P("## A. Transport-layer sweeps: paper vs spreadsheet vs re-run\n")
P("Values at 2 µm. The paper column is Table 2 of the drafts. The spreadsheet column is the material's own `DATA POINTS` file. The re-run is the original `.def` file run again in SCAPS 3.3.11.\n")
P("| Layer | Paper eta % | Spreadsheet eta % | Re-run eta % | Re-run Jsc mA/cm² | Re-run Voc V | Largest gap, re-run vs spreadsheet (eta points) | Verdict |")
P("|---|---|---|---|---|---|---|---|")
mats = []
for r in by["A_sweep"]:
    if r["case"] not in mats:
        mats.append(r["case"])
summary_rows = []
for m in mats:
    rr = {round(f(r["x"]), 1): r for r in by["A_sweep"] if r["case"] == m}
    gaps = [abs(f(rr[t]["eta_pct"]) - f(sheet[(m, t)]["eta_pct"])) for t in rr if (m, t) in sheet and not math.isnan(f(sheet[(m, t)]["eta_pct"]))]
    two = rr.get(2.0, {})
    s2 = sheet.get((m, 2.0), {})
    gaps = [g for g in gaps if not math.isnan(g)]
    gap = f"{max(gaps):.3f}" if gaps else "n/a"
    rep_ok = bool(gaps) and max(gaps) < 0.05
    paper_ok = abs(f(paper[m]['eta_pct']) - f(two.get('eta_pct'))) < 0.1
    verdict = ("file reproduces spreadsheet" if rep_ok else "file does NOT reproduce spreadsheet") + ("; paper matches" if paper_ok else "; paper value NOT supported")
    P(f"| {m} | {f(paper[m]['eta_pct']):.2f} | {f(s2.get('eta_pct')):.4g} | {f(two.get('eta_pct')):.4g} | {f(two.get('Jsc_mA_cm2')):.4g} | {f(two.get('Voc_V')):.4g} | {gap} | {verdict} |")
    summary_rows.append((m, f(paper[m]["eta_pct"]), f(s2.get("eta_pct")), f(two.get("eta_pct"))))
P("")
if by["A0_baseline"]:
    P("Earlier PR 2 files, run as saved:\n")
    P("| File | Voc V | Jsc mA/cm² | FF % | eta % | J_SRH at 0 V (mA/cm²) |")
    P("|---|---|---|---|---|---|")
    for r in by["A0_baseline"]:
        P(f"| {r['case']} | {f(r['Voc_V']):.4g} | {f(r['Jsc_mA_cm2']):.4g} | {f(r['FF_pct']):.4g} | {f(r['eta_pct']):.4g} | {f(r['J_SRH_at_0V']):.3g} |")
    P("")

# --- B: metals
P("## B. Back-contact metals (Cs2BiAgI6 device, 2 µm)\n")
P("| Metal | Work function eV | Reported eta % | Re-run eta % | Re-run Voc V |")
P("|---|---|---|---|---|")
for r in sorted(by["B_metal"], key=lambda r: f(r["x"])):
    m = r["case"]
    P(f"| {m} | {f(r['x']):.2f} | {f(metals_rep[m]['eta_pct']):.2f} | {f(r['eta_pct']):.2f} | {f(r['Voc_V']):.4f} |")
P("")

# --- C: temperature
P("## C. Temperature (Cs2BiAgI6 device, 2 µm)\n")
P("| T (K) | Re-run Voc V | Re-run Jsc mA/cm² | Re-run FF % | Re-run eta % |")
P("|---|---|---|---|---|")
for r in by["C_temperature"]:
    P(f"| {f(r['x']):.0f} | {f(r['Voc_V']):.4f} | {f(r['Jsc_mA_cm2']):.3f} | {f(r['FF_pct']):.2f} | {f(r['eta_pct']):.3f} |")
P("")

# --- D: absorption test
P("## D. Which layer absorbs the light?\n")
P("The \"ETL\" (layer 1) has its absorption switched off. Everything else is unchanged. Values at 2 µm.\n")
P("| Device | Jsc as saved mA/cm² | Jsc, layer-1 absorption off | Drop |")
P("|---|---|---|---|")
a2 = {r["case"]: r for r in by["A_sweep"] if round(f(r["x"]), 1) == 2.0}
for r in by["D_layer1_absorption_off"]:
    j0, j1 = f(a2[r["case"]]["Jsc_mA_cm2"]), f(r["Jsc_mA_cm2"])
    P(f"| {r['case']} | {j0:.2f} | {j1:.2f} | {100*(j0-j1)/j0:.0f}% |")
P("")

# --- E: undoing the errors
P("## E. Undoing the setup errors in the 27.99% device\n")
base = a2["Cs2BiAgI6"]
P("| Step | Voc V | Jsc mA/cm² | FF % | eta % | J_SRH at 0 V |")
P("|---|---|---|---|---|---|")
P(f"| As saved (PR 2) | {f(base['Voc_V']):.4f} | {f(base['Jsc_mA_cm2']):.3f} | {f(base['FF_pct']):.2f} | {f(base['eta_pct']):.2f} | {f(base['J_SRH_at_0V']):.3g} |")
labels = {"Eg": "CdTe band gap 1.6 to 1.5 eV", "doping": "CdTe made p-type (NA 2e14 cm⁻³)",
          "absorption": "Cs2BiAgI6 given its own absorption", "defects": "CdTe bulk defect added (Gloeckler baseline)"}
P("| *One fix at a time* | | | | | |")
for r in by["E_single_fix"]:
    P(f"| {labels[r['case']]} | {f(r['Voc_V']):.4f} | {f(r['Jsc_mA_cm2']):.3f} | {f(r['FF_pct']):.2f} | {f(r['eta_pct']):.2f} | {f(r['J_SRH_at_0V']):.3g} |")
P("| *Fixes stacked* | | | | | |")
for r in by["E_cumulative"]:
    P(f"| + {labels[r['case'].split('+')[-1]]} | {f(r['Voc_V']):.4f} | {f(r['Jsc_mA_cm2']):.3f} | {f(r['FF_pct']):.2f} | {f(r['eta_pct']):.2f} | {f(r['J_SRH_at_0V']):.3g} |")
for r in by["E_reference"]:
    P(f"| All fixes, Cs2BiAgI6 layer removed | {f(r['Voc_V']):.4f} | {f(r['Jsc_mA_cm2']):.3f} | {f(r['FF_pct']):.2f} | {f(r['eta_pct']):.2f} | {f(r['J_SRH_at_0V']):.3g} |")
P("")
(HERE / "tables.md").write_text("\n".join(out))

# --- figures
fig, ax = plt.subplots(figsize=(7.2, 3.6))
names = [m for m, *_ in summary_rows]
xs = range(len(names))
w = 0.38
ax.bar([x - w / 2 for x in xs], [p for _, p, _, _ in summary_rows], w, label="Reported in the paper", color="#9aa5b1")
ax.bar([x + w / 2 for x in xs], [s for *_, s in summary_rows], w, label="Re-run of the paper's own file", color="#1f6feb")
ax.set_xticks(list(xs)); ax.set_xticklabels(names, rotation=30, ha="right")
ax.set_ylabel("Efficiency at 2 µm (%)"); ax.legend(frameon=False, fontsize=8); ax.grid(axis="y", alpha=0.3)
ax.set_title("PR 2 transport-layer table: reported vs reproduced", fontsize=10)
fig.tight_layout(); fig.savefig(FIG / "forensics_reported_vs_rerun.png", dpi=200)

steps = [("As saved", f(base["eta_pct"]))] + [(labels[r["case"].split("+")[-1]], f(r["eta_pct"])) for r in by["E_cumulative"]]
fig, ax = plt.subplots(figsize=(7.2, 3.6))
ax.bar(range(len(steps)), [v for _, v in steps], color=["#d1242f"] + ["#1f6feb"] * (len(steps) - 1))
for i, (_, v) in enumerate(steps):
    ax.text(i, v + 0.4, f"{v:.1f}%", ha="center", fontsize=9)
ax.set_xticks(range(len(steps))); ax.set_xticklabels(["As saved"] + [f"+ {s}" for s, _ in steps[1:]], rotation=18, ha="right", fontsize=8)
ax.set_ylabel("Efficiency (%)"); ax.set_ylim(0, max(v for _, v in steps) + 4); ax.grid(axis="y", alpha=0.3)
ax.set_title("FTO/ZnSe/CdTe/Cs2BiAgI6/Ni: effect of fixing each setup error (stacked)", fontsize=10)
fig.tight_layout(); fig.savefig(FIG / "forensics_fix_waterfall.png", dpi=200)
print((HERE / "tables.md").read_text())
