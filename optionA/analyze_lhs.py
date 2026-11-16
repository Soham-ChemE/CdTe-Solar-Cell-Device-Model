"""Weight LHS samples by agreement with the measured x = 0.15 cells, report what the data constrain,
and predict the x = 0.00 cliff cells blind. Likelihood: independent Gaussians on Voc, Jsc, FF.
sigma = cell-to-cell spread read from the Pandey Fig. 2 box plots (approximate), plus model-form allowance."""
import csv, math, sys
from pathlib import Path
import numpy as np

H = Path(__file__).resolve().parent
rows = [r for r in csv.DictReader(open(H / "lhs_results.csv"))]
OBS15 = {"Voc": (846.0, 12.0), "Jsc": (27.8, 0.5), "FF": (74.5, 2.0)}     # mean, sigma
OBS00 = {"Voc": 707.0, "Jsc": 20.1, "FF": 54.2, "eta": 8.0}
PAR = ["tau", "NA", "phi_back", "S_front", "ND_MZO", "Rs"]
LOG = {"tau", "NA", "S_front", "ND_MZO"}

ok = [r for r in rows if r["ok_x0p15"] == "True"]
X = np.array([[math.log10(float(r[p])) if p in LOG else float(r[p]) for p in PAR] for r in ok])
chi2 = np.array([sum(((float(r[f"{k}_x0p15"]) - m) / s) ** 2 for k, (m, s) in OBS15.items()) for r in ok])
w = np.exp(-0.5 * (chi2 - chi2.min())); w /= w.sum()
ess = 1.0 / np.sum(w ** 2)
print(f"samples ok at x=0.15: {len(ok)}/{len(rows)};  best chi2 {chi2.min():.2f};  effective sample size {ess:.1f}")
best = ok[int(np.argmin(chi2))]
print("best sample:", {p: f"{float(best[p]):.3g}" for p in PAR},
      "->", {k: round(float(best[f'{k}_x0p15']), 2) for k in ['Voc', 'Jsc', 'FF', 'eta']})


def wq(v, w, qs):
    i = np.argsort(v); c = np.cumsum(w[i]); return [v[i][np.searchsorted(c, q)] for q in qs]


print("\nparameter   prior range            weighted 10%-50%-90%            narrowing (posterior 80% width / prior width)")
for j, p in enumerate(PAR):
    lo, hi = X[:, j].min(), X[:, j].max()
    q10, q50, q90 = wq(X[:, j], w, [0.1, 0.5, 0.9])
    f = (lambda v: f"1e{v:.2f}") if p in LOG else (lambda v: f"{v:.3f}")
    print(f"{p:9s}  {f(lo):>9s} .. {f(hi):<9s}   {f(q10):>9s} {f(q50):>9s} {f(q90):>9s}      {(q90 - q10) / (hi - lo):.2f}")

# blind prediction of the cliff cell with the same weights
ok0 = np.array([r["ok_x0p00"] == "True" for r in ok])
print(f"\nx=0.00 converged for {ok0.sum()}/{len(ok)} of those samples (weight covered: {w[ok0].sum():.2f})")
for k in ["Voc", "Jsc", "FF", "eta"]:
    v = np.array([float(r[f"{k}_x0p00"]) if r["ok_x0p00"] == "True" else np.nan for r in ok])
    m = ~np.isnan(v); ww = w[m] / w[m].sum()
    q10, q50, q90 = wq(v[m], ww, [0.1, 0.5, 0.9])
    print(f"  predicted x=0.00 {k:3s}: median {q50:7.2f}  (80% band {q10:7.2f} .. {q90:7.2f})   measured avg {OBS00[k]}")
