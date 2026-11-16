"""Collect what PR 2 reported: the paper tables (drafts) and the raw spreadsheet sweeps.

Spreadsheet values are read directly from ~/Documents/PR 2/DATA POINTS (SIMULATED MATS)/<material> DATA POINTS.xlsx.
Paper values are transcribed from Table 2 of the Capstone/OPAS drafts and from SIMULATION RESULT.xlsx.
"""
import csv
import re
from pathlib import Path

import openpyxl

PR2 = Path.home() / "Documents/PR 2/DATA POINTS (SIMULATED MATS)"
HERE = Path(__file__).resolve().parent

# Table 2 of the drafts (ETL at 2 um, Ni contact): Voc V, Jsc mA/cm2, FF %, eta %
PAPER_TABLE2 = {
    "WS2": (1.1466, 25.4335, 89.4, 26.07), "PCBM": (1.1174, 25.4335, 89.11, 25.33),
    "Cs2BiAgI6": (1.2075, 25.962, 89.28, 27.99), "WO3": (1.3636, 9.2881, 58.17, 7.37),
    "C60": (1.2278, 24.637, 87.9, 26.59), "PC16BM": (1.0659, 25.2236, 87.09, 23.41),
    "CuO": (0.9402, 25.5485, 85.58, 20.56), "Cu2O": (1.7789, 25.519, 49.84, 22.63),
    "Sb2Se3": (0.937, 25.5491, 85.64, 20.5), "TiO2": (1.0505, 19.3294, 68.9, 13.99),
}
# SIMULATION RESULT.xlsx, sheet DIFFERENT METALS (Cs2BiAgI6 ETL)
PAPER_METALS = {
    "Cu": (4.6, 0.5945, 25.7326, 81.24, 12.43), "Fe": (4.8, 0.7945, 25.7396, 84.86, 17.35),
    "Au": (5.1, 1.0876, 25.751, 88.09, 24.67), "C": (5.0, 0.9943, 25.7465, 87.22, 22.33),
    "W": (5.2, 1.128, 25.7677, 88.48, 25.72), "Ni": (5.55, 1.2075, 25.962, 89.28, 27.99),
    "Al": (4.3, 0.2945, 25.7231, 69.46, 5.26), "Pt": (5.7, 1.2296, 25.9668, 89.06, 28.44),
    "Se": (5.9, 1.2303, 25.9669, 89.05, 28.45),
}


def sheet_params(ws):
    vals = {}
    for row in ws.iter_rows(values_only=True):
        cells = [c for c in row if c is not None]
        if not cells or not isinstance(cells[0], str):
            continue
        s = " ".join(str(c) for c in cells)
        m = re.search(r"thickness\[.m\]:\s*([\d.]+)", s)
        if m:
            vals["t"] = float(m.group(1))
        for key in ("Voc", "Jsc", "FF", "eta"):
            m = re.match(rf"\s*{key}\s*=\s*([-\d.eE+]+)", s)
            if m:
                vals[key] = float(m.group(1))
    return vals


rows = []
for mat in PAPER_TABLE2:
    wb = openpyxl.load_workbook(PR2 / f"{mat} DATA POINTS.xlsx", data_only=True)
    for ws in wb.worksheets:
        if not ws.title.startswith("ETL VARY"):
            continue
        v = sheet_params(ws)
        note = "" if "eta" in v else "no data in sheet (simulation stopped)"
        rows.append(["spreadsheet_ETL_sweep", mat, v.get("t", ""), v.get("Voc", ""), v.get("Jsc", ""),
                     v.get("FF", ""), v.get("eta", ""), ws.title, note])
for mat, (voc, jsc, ff, eta) in PAPER_TABLE2.items():
    rows.append(["paper_table2_2um", mat, 2.0, voc, jsc, ff, eta, "Capstone/OPAS Table 2", ""])
for m, (phi, voc, jsc, ff, eta) in PAPER_METALS.items():
    rows.append(["paper_metals", m, phi, voc, jsc, ff, eta, "SIMULATION RESULT.xlsx", ""])

with open(HERE / "reported_values.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["source", "case", "x", "Voc_V", "Jsc_mA_cm2", "FF_pct", "eta_pct", "where", "note"])
    w.writerows(rows)
print("rows", len(rows))
