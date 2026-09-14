"""
Phase 3A.9 - ML experiment protocol and baseline design (Potato only).

Purpose
-------
Phase 3A.8 produced two leakage-free feature tables:
  - potato_ml_minimal.csv   (177 rows: lag_1 -> target)
  - potato_ml_extended.csv  (175 rows: lag_1/2/3, rolling_mean_3,
                              rolling_std_3, day_of_week -> target)

This script does NOT train any complex model (no Random Forest, no
XGBoost, no neural network -- none of that is imported or implemented
here). It builds the experiment INFRASTRUCTURE a future modeling phase
will plug into, and runs only the two mandatory non-ML baselines
(persistence, moving-average-3) through that infrastructure, honestly
reporting whatever the numbers turn out to be.

What this script verifies/builds, in order:
  1. Chronological ordering of both feature files (refuses to proceed if
     violated, rather than silently re-sorting).
  2. The exact row-offset relationship between the two files (extended
     row j == minimal row j+2), confirmed empirically, not assumed --
     this is what makes a "common evaluation period" (Task 11) possible.
  3. Chronological train / expanding-window-validation / test partitions,
     with exact boundaries computed from the actual row counts (not a
     blindly-applied 60/20/20).
  4. The persistence and moving-average-3 baselines, applied identically
     to every fold.
  5. MAE/RMSE per fold, plus the mean and standard deviation across folds.

The final test partition is loaded and its boundaries are computed, but
NO baseline or model is evaluated against it in this phase -- per the
Phase 3A.9 final-test policy, it stays untouched until a later phase
compares baselines and a real model together.
"""

import csv
import statistics
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MINIMAL_CSV = PROCESSED_DIR / "potato_ml_minimal.csv"
EXTENDED_CSV = PROCESSED_DIR / "potato_ml_extended.csv"

TARGET_COL = "target_modal_price_next_observation"


def load(path):
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        for k in list(r.keys()):
            if k not in ("date", "day_of_week"):
                r[k] = float(r[k])
    return rows


def verify_chronological(rows, label):
    dates = [r["date"] for r in rows]
    if dates != sorted(dates):
        raise ValueError(f"{label} is not chronologically ordered -- refusing to proceed.")
    if len(set(dates)) != len(dates):
        raise ValueError(f"{label} contains duplicate dates -- refusing to proceed.")
    print(f"  [{label}] chronological order verified. {len(rows)} rows, "
          f"{dates[0]} to {dates[-1]}.")


def verify_common_window(minimal, extended):
    """Confirms, by direct comparison (not assumption), that extended row j
    is identical (date + target) to minimal row j+2 for every j. This is
    what licenses treating extended's full range as a fair common window
    for comparing the two feature sets."""
    offset = 2
    mismatches = []
    for j in range(len(extended)):
        m, e = minimal[j + offset], extended[j]
        if m["date"] != e["date"] or m[TARGET_COL] != e[TARGET_COL]:
            mismatches.append((j, m["date"], e["date"]))
    print(f"  Alignment check (extended[j] vs minimal[j+{offset}]): "
          f"{len(mismatches)} mismatches out of {len(extended)} rows.")
    if mismatches:
        raise ValueError(f"Common-window alignment failed: {mismatches[:5]}")
    return offset


def build_common_window(minimal, extended, offset):
    """Returns the 175-row common evaluation window in BOTH representations
    -- minimal's slice and extended's full range -- guaranteed row-for-row
    aligned by the check above."""
    minimal_common = minimal[offset:]
    assert len(minimal_common) == len(extended)
    return minimal_common, extended


def define_split(n):
    """Computes exact split boundaries from the actual row count n, rather
    than blindly applying 60/20/20. For n=175 this divides perfectly into
    105/35/35 (60%/20%/20%) -- verified below, not assumed -- which is why
    this phase keeps that ratio rather than picking a different one purely
    to avoid the appearance of reusing Phase 3A.7's proposal."""
    train_size = round(n * 0.6)
    val_size = round(n * 0.2)
    test_size = n - train_size - val_size
    return {
        "train": (0, train_size),
        "validation": (train_size, train_size + val_size),
        "test": (train_size + val_size, n),
        "train_size": train_size, "val_size": val_size, "test_size": test_size,
    }


def define_folds(val_start, val_end, fold_size):
    """Expanding-window folds within the validation pool. Fold i's
    'training data' is everything strictly before its validation block
    (indices 0..fold_val_start-1); its validation block is a contiguous
    chunk of fold_size rows. Training data for fold i+1 EXPANDS to include
    fold i's validation block (now realized/known), never data from beyond
    fold i's own validation block."""
    folds = []
    cur = val_start
    while cur < val_end:
        fold_val_start = cur
        fold_val_end = min(cur + fold_size, val_end)
        folds.append({
            "train_range": (0, fold_val_start),          # strictly before validation block
            "val_range": (fold_val_start, fold_val_end),
        })
        cur = fold_val_end
    return folds


def persistence_predict(row):
    """\\hat{y}_{t+1} = y_t. Implemented as reading the row's own lag_1
    feature, which by Phase 3A.8's construction already equals the modal
    price at the most recent AVAILABLE observation -- never a future
    value, since lag_1 is built strictly from index <= t."""
    return row["lag_1_modal_price"]


def moving_average_3_predict(rows, idx):
    """\\hat{y}_{t+1} = mean(y_t, y_{t-1}, y_{t-2}) -- the trailing 3-
    observation average ending at t, never including t+1. If the extended
    file's own rolling_mean_3_modal_price column is present, this is
    cross-checked against it as an integrity check; otherwise (minimal
    file) it is computed directly from consecutive lag_1 values, which is
    possible only from the 3rd row onward within whatever slice is passed
    in (idx >= 2 relative to the start of that slice)."""
    if idx < 2:
        return None  # not enough history within this slice -- reported, not guessed
    if "rolling_mean_3_modal_price" in rows[idx]:
        return rows[idx]["rolling_mean_3_modal_price"]
    # Fallback for the minimal file, which has no rolling column: rebuild
    # the same 3-point average from lag_1 values of the current and two
    # preceding rows' *targets* is NOT used (that would reach into y_{t+1}
    # territory for earlier rows) -- instead use the three most recent
    # lag_1 values, which are themselves y_t, y_{t-1}, y_{t-2} by
    # construction of consecutive rows' lag_1 features.
    return statistics.mean([rows[idx]["lag_1_modal_price"],
                             rows[idx - 1]["lag_1_modal_price"],
                             rows[idx - 2]["lag_1_modal_price"]])


def evaluate_fold(rows, val_range, predict_fn):
    start, end = val_range
    errors = []
    skipped = 0
    for idx in range(start, end):
        pred = predict_fn(rows, idx) if predict_fn is moving_average_3_predict else persistence_predict(rows[idx])
        if pred is None:
            skipped += 1
            continue
        actual = rows[idx][TARGET_COL]
        errors.append(actual - pred)
    if not errors:
        return None
    mae = statistics.mean(abs(e) for e in errors)
    rmse = (statistics.mean(e ** 2 for e in errors)) ** 0.5
    return {"n": len(errors), "skipped": skipped, "mae": mae, "rmse": rmse}


def run_baselines_on_folds(rows, folds, label):
    print(f"\n  --- Baselines on {label} (validation folds only; test untouched) ---")
    persistence_results, ma_results = [], []
    for i, fold in enumerate(folds, start=1):
        p = evaluate_fold(rows, fold["val_range"], persistence_predict)
        m = evaluate_fold(rows, fold["val_range"], moving_average_3_predict)
        persistence_results.append(p)
        ma_results.append(m)
        print(f"    Fold {i}: val_rows={fold['val_range'][1]-fold['val_range'][0]} "
              f"train_rows={fold['train_range'][1]-fold['train_range'][0]} | "
              f"persistence MAE={p['mae']:.2f} RMSE={p['rmse']:.2f} | "
              f"moving_avg_3 MAE={m['mae']:.2f} RMSE={m['rmse']:.2f}"
              + (f" (skipped {m['skipped']})" if m['skipped'] else ""))

    def summarize(results, name):
        maes = [r["mae"] for r in results]
        rmses = [r["rmse"] for r in results]
        print(f"    {name}: mean MAE={statistics.mean(maes):.2f} (stdev {statistics.pstdev(maes):.2f}) | "
              f"mean RMSE={statistics.mean(rmses):.2f} (stdev {statistics.pstdev(rmses):.2f})")
        return {"mean_mae": statistics.mean(maes), "stdev_mae": statistics.pstdev(maes),
                "mean_rmse": statistics.mean(rmses), "stdev_rmse": statistics.pstdev(rmses)}

    p_summary = summarize(persistence_results, "Persistence")
    m_summary = summarize(ma_results, "Moving-average-3")
    return persistence_results, ma_results, p_summary, m_summary


if __name__ == "__main__":
    print("=== Phase 3A.9: Experiment Protocol and Baseline Design (infrastructure + baselines only) ===\n")

    minimal = load(MINIMAL_CSV)
    extended = load(EXTENDED_CSV)
    verify_chronological(minimal, "potato_ml_minimal.csv")
    verify_chronological(extended, "potato_ml_extended.csv")

    print("\n--- Common evaluation window verification (Task 11) ---")
    offset = verify_common_window(minimal, extended)
    minimal_common, extended_common = build_common_window(minimal, extended, offset)
    n = len(extended_common)
    print(f"  Common window size: {n} rows ({extended_common[0]['date']} to {extended_common[-1]['date']} "
          f"as feature date; targets {n} dates ahead in observation order)")

    print("\n--- Chronological split (computed from n={}, not blindly 60/20/20) ---".format(n))
    split = define_split(n)
    print(f"  train: rows [{split['train'][0]}:{split['train'][1]}] -> {split['train_size']} rows "
          f"({extended_common[split['train'][0]]['date']} to {extended_common[split['train'][1]-1]['date']})")
    print(f"  validation: rows [{split['validation'][0]}:{split['validation'][1]}] -> {split['val_size']} rows "
          f"({extended_common[split['validation'][0]]['date']} to {extended_common[split['validation'][1]-1]['date']})")
    print(f"  test (UNTOUCHED this phase): rows [{split['test'][0]}:{split['test'][1]}] -> {split['test_size']} rows "
          f"({extended_common[split['test'][0]]['date']} to {extended_common[split['test'][1]-1]['date']})")

    fold_size = 7
    folds = define_folds(split["validation"][0], split["validation"][1], fold_size)
    print(f"\n--- Expanding-window folds (fold size = {fold_size} rows -> {len(folds)} folds) ---")
    for i, f in enumerate(folds, start=1):
        print(f"  Fold {i}: train=[0:{f['train_range'][1]}] ({f['train_range'][1]} rows), "
              f"validate=[{f['val_range'][0]}:{f['val_range'][1]}] ({f['val_range'][1]-f['val_range'][0]} rows)")

    # Run baselines on the EXTENDED representation of the common window
    # (has rolling_mean_3 precomputed) ...
    ext_p_results, ext_ma_results, ext_p_summary, ext_ma_summary = run_baselines_on_folds(
        extended_common, folds, "EXTENDED file (common window)"
    )

    # ... and independently on the MINIMAL representation of the SAME
    # common window (rolling_mean_3 rebuilt from lag_1 values), to confirm
    # both representations give identical baseline results on identical
    # target observations -- a direct fairness check for Task 11/5.
    min_p_results, min_ma_results, min_p_summary, min_ma_summary = run_baselines_on_folds(
        minimal_common, folds, "MINIMAL file (same common window, recomputed)"
    )

    print("\n--- Cross-check: do both file representations agree on identical target rows? ---")
    mae_diff_p = abs(ext_p_summary["mean_mae"] - min_p_summary["mean_mae"])
    mae_diff_ma = abs(ext_ma_summary["mean_mae"] - min_ma_summary["mean_mae"])
    print(f"  Persistence mean-MAE difference (extended vs minimal representation): {mae_diff_p:.6f}")
    print(f"  Moving-average-3 mean-MAE difference (extended vs minimal representation): {mae_diff_ma:.6f}")
    print("  (Expected: 0.000000 for both -- both files describe the same underlying observations.)")

    print("\n=== Done. No raw file touched. No feature file overwritten. No complex ML model trained. "
          "Test partition was never evaluated. ===")
