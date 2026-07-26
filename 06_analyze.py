#!/usr/bin/env python3
"""Aggregates all outputs/ CSVs into Tables 3-5 of the manuscript + statistics report.
Requires: pip install pandas scipy statsmodels
"""
import glob, os
import numpy as np
import pandas as pd
from scipy import stats

OUT = "tables"; os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(20260727)

def bootstrap_ci(x, stat=np.mean, n=10000, alpha=0.05):
    x = np.asarray(x)
    sims = np.array([stat(rng.choice(x, len(x), replace=True)) for _ in range(n)])
    return stat(x), np.quantile(sims, alpha/2), np.quantile(sims, 1-alpha/2)

def auroc(pos, neg):
    """AUROC of separating benchmark items (pos) from probe items (neg) by Min-K% score."""
    u, _ = stats.mannwhitneyu(pos, neg, alternative="greater")
    return u / (len(pos) * len(neg))

# ---- Table 3: contamination signals ----
rows = []
for path in glob.glob("outputs/*/*/mink.csv"):
    model, bench = path.split(os.sep)[1:3]
    df = pd.read_csv(path)
    probe_path = os.path.join("outputs", model, "probe", "mink.csv")
    if not os.path.exists(probe_path):
        print(f"[WARN] no probe baseline for {model}; AUROC skipped"); continue
    probe = pd.read_csv(probe_path)
    a = auroc(df["mink_20"], probe["mink_20"])
    ts_path = os.path.join("outputs", model, bench, "tsguess.csv")
    ts = pd.read_csv(ts_path)["exact"].mean() if os.path.exists(ts_path) else np.nan
    rows.append({"model": model, "benchmark": bench, "mink20_auroc": round(a, 3),
                 "tsguess_exact": round(ts, 3) if ts == ts else None})
pd.DataFrame(rows).to_csv(f"{OUT}/table3.csv", index=False)

# ---- Table 4: cross-lingual (BEnQA parallel) ----
# Expects outputs/<model>/benqa_en/mink.csv and outputs/<model>/benqa_bn/mink.csv with shared ids,
# plus per-sample harness correctness files merged on id.
rows = []
for model_dir in glob.glob("outputs/*"):
    en, bn = (os.path.join(model_dir, d, "mink.csv") for d in ("benqa_en", "benqa_bn"))
    if not (os.path.exists(en) and os.path.exists(bn)):
        continue
    den = pd.read_csv(en).set_index("id"); dbn = pd.read_csv(bn).set_index("id")
    joined = den.join(dbn, lsuffix="_en", rsuffix="_bn").dropna()
    diff = joined["mink_20_en"] - joined["mink_20_bn"]
    wstat, p = stats.wilcoxon(diff)
    m, lo, hi = bootstrap_ci(diff)
    rows.append({"model": os.path.basename(model_dir), "mink_diff_mean": round(m, 4),
                 "ci": f"[{lo:.4f},{hi:.4f}]", "wilcoxon_p": p})
if rows:
    df4 = pd.DataFrame(rows)
    # Holm-Bonferroni
    order = np.argsort(df4["wilcoxon_p"].values)
    adj = np.empty(len(df4))
    for rank, i in enumerate(order):
        adj[i] = min(1.0, df4["wilcoxon_p"].values[i] * (len(df4) - rank))
    df4["p_holm"] = adj
    df4.to_csv(f"{OUT}/table4.csv", index=False)

# ---- Table 5: robustness ----
# Expects harness per-sample logs for original and perturbed variants; adapt glob patterns.
print("Table 5 requires per-sample harness logs for original + perturbed runs; "
      "merge on item id and compute accuracy deltas + Spearman rank stability here.")
print(f"Wrote {OUT}/table3.csv and table4.csv (where inputs existed).")
