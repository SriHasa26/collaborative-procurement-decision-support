"""
Phase 4A - Low-complexity ML model evaluation (Potato only).

Purpose
-------
Phase 3A.9 built the experiment protocol (common 175-row evaluation
window, chronological 105/35/35 split, 5-fold expanding-window
validation) and ran only the two mandatory non-ML baselines through it
(persistence MAE 241.43, moving-average-3 MAE 189.84 -- moving-average-3
is the stronger baseline).

This script reuses that exact protocol -- same split boundaries, same
5 folds, same common-window rows -- and fits exactly three low-complexity
model families on top of it:
  1. Linear Regression (one configuration)
  2. Ridge Regression (three regularization strengths: alpha in
     {0.1, 1.0, 10.0})
  3. Decision Tree Regressor (three shallow depths: max_depth in
     {2, 3, 4}, random_state fixed for reproducibility)

No Random Forest, XGBoost, LightGBM, CatBoost, neural network, or LSTM
is imported or used anywhere in this file. No exhaustive grid search is
performed -- only the small, explicitly-listed configuration set above.

The 35-row final test partition (rows [140:175] of the common window) is
loaded only to confirm its boundaries; it is never used to fit, select,
or evaluate anything in this script.

Leakage discipline:
  - Every fold's training range strictly precedes its validation range
    (inherited unchanged from Phase 3A.9's fold definition).
  - Any scaler is fit ONLY on that fold's training rows, then applied
    (never re-fit) to that fold's validation rows.
  - day_of_week is one-hot encoded using a FIXED category list (not
    inferred per fold), so a category missing from a small training
    fold cannot silently change the feature matrix's shape between
    folds.
"""

import csv
import statistics
from pathlib import Path

import numpy as np
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MINIMAL_CSV = PROCESSED_DIR / "potato_ml_minimal.csv"
EXTENDED_CSV = PROCESSED_DIR / "potato_ml_extended.csv"

TARGET_COL = "target_modal_price_next_observation"
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Baselines, carried over unchanged from Phase 3A.9 -- not recomputed here,
# only quoted for comparison.
BASELINE_PERSISTENCE_MAE = 241.43
BASELINE_MOVING_AVG_MAE = 189.84


def load(path):
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        for k in list(r.keys()):
            if k not in ("date", "day_of_week"):
                r[k] = float(r[k])
    return rows


def verify_common_window(minimal, extended):
    offset = 2
    for j in range(len(extended)):
        m, e = minimal[j + offset], extended[j]
        assert m["date"] == e["date"] and m[TARGET_COL] == e[TARGET_COL], \
            f"Alignment failure at row {j}"
    return minimal[offset:]


def build_matrix(rows, feature_set):
    """feature_set in {'minimal', 'extended'}. day_of_week is one-hot
    encoded against the FIXED module-level DAYS list (drop Monday as the
    reference category) so the feature matrix's column count never
    depends on which categories happen to appear in a given fold."""
    if feature_set == "minimal":
        X = [[r["lag_1_modal_price"]] for r in rows]
        names = ["lag_1_modal_price"]
    else:
        names = ["lag_1_modal_price", "lag_2_modal_price", "lag_3_modal_price",
                  "rolling_mean_3_modal_price", "rolling_std_3_modal_price"] + \
                 [f"dow_{d}" for d in DAYS[1:]]
        X = []
        for r in rows:
            base = [r["lag_1_modal_price"], r["lag_2_modal_price"], r["lag_3_modal_price"],
                    r["rolling_mean_3_modal_price"], r["rolling_std_3_modal_price"]]
            dow = [1.0 if r["day_of_week"] == d else 0.0 for d in DAYS[1:]]
            X.append(base + dow)
    y = [r[TARGET_COL] for r in rows]
    return np.array(X), np.array(y), names


def define_folds(val_start, val_end, fold_size=7):
    folds = []
    cur = val_start
    while cur < val_end:
        end = min(cur + fold_size, val_end)
        folds.append({"train_range": (0, cur), "val_range": (cur, end)})
        cur = end
    return folds


def mae_rmse(y_true, y_pred):
    err = np.asarray(y_true) - np.asarray(y_pred)
    mae = np.mean(np.abs(err))
    rmse = np.sqrt(np.mean(err ** 2))
    return float(mae), float(rmse)


def run_model(rows, feature_set, folds, model_name, config_label, needs_scaling, build_model_fn):
    """Runs one (model, config) across all 5 folds. Fits a fresh model
    per fold on that fold's expanding training range only; if
    needs_scaling, fits a StandardScaler on that fold's training rows
    only and applies it (never re-fit) to that fold's validation rows.
    Also records training-set MAE/RMSE (predicting on the same rows the
    model was fit on) for the overfitting check in Section 11."""
    X_all, y_all, feature_names = build_matrix(rows, feature_set)
    fold_results = []
    for fold in folds:
        tr_s, tr_e = fold["train_range"]
        va_s, va_e = fold["val_range"]
        X_train, y_train = X_all[tr_s:tr_e], y_all[tr_s:tr_e]
        X_val, y_val = X_all[va_s:va_e], y_all[va_s:va_e]

        if needs_scaling:
            scaler = StandardScaler()
            scaler.fit(X_train)          # fit ONLY on training rows of this fold
            X_train_use = scaler.transform(X_train)
            X_val_use = scaler.transform(X_val)   # transform only, never re-fit
        else:
            X_train_use, X_val_use = X_train, X_val

        model = build_model_fn()
        model.fit(X_train_use, y_train)

        val_pred = model.predict(X_val_use)
        train_pred = model.predict(X_train_use)

        val_mae, val_rmse = mae_rmse(y_val, val_pred)
        train_mae, train_rmse = mae_rmse(y_train, train_pred)

        fold_results.append({
            "train_rows": tr_e - tr_s, "val_rows": va_e - va_s,
            "val_mae": val_mae, "val_rmse": val_rmse,
            "train_mae": train_mae, "train_rmse": train_rmse,
        })

    val_maes = [f["val_mae"] for f in fold_results]
    val_rmses = [f["val_rmse"] for f in fold_results]
    train_maes = [f["train_mae"] for f in fold_results]
    summary = {
        "feature_set": feature_set, "model": model_name, "config": config_label,
        "mean_val_mae": statistics.mean(val_maes), "stdev_val_mae": statistics.pstdev(val_maes),
        "mean_val_rmse": statistics.mean(val_rmses), "stdev_val_rmse": statistics.pstdev(val_rmses),
        "mean_train_mae": statistics.mean(train_maes),
        "fold_results": fold_results,
        "n_features": X_all.shape[1],
    }
    return summary


def print_summary(s):
    gap = s["mean_val_mae"] - s["mean_train_mae"]
    print(f"  [{s['feature_set']:8s}] {s['model']:16s} {s['config']:10s} "
          f"n_features={s['n_features']:2d} | "
          f"val MAE mean={s['mean_val_mae']:7.2f} stdev={s['stdev_val_mae']:6.2f} | "
          f"val RMSE mean={s['mean_val_rmse']:7.2f} | "
          f"train MAE={s['mean_train_mae']:7.2f} | "
          f"train-vs-val gap={gap:+7.2f}")
    for i, f in enumerate(s["fold_results"], start=1):
        print(f"      fold {i}: train_rows={f['train_rows']} val_rows={f['val_rows']} "
              f"val_MAE={f['val_mae']:.2f} val_RMSE={f['val_rmse']:.2f} train_MAE={f['train_mae']:.2f}")


if __name__ == "__main__":
    print("=== Phase 4A: Low-Complexity ML Model Evaluation (Potato only) ===\n")

    minimal_full = load(MINIMAL_CSV)
    extended = load(EXTENDED_CSV)
    minimal_common = verify_common_window(minimal_full, extended)
    n = len(extended)
    assert n == 175 and len(minimal_common) == 175
    print(f"Common evaluation window confirmed: {n} rows "
          f"({extended[0]['date']} to {extended[-1]['date']})")

    train_size, val_size = round(n * 0.6), round(n * 0.2)
    test_start = train_size + val_size
    print(f"Split: train=[0:{train_size}] validation=[{train_size}:{test_start}] "
          f"test=[{test_start}:{n}] (test NOT evaluated in this script)")

    folds = define_folds(train_size, test_start, fold_size=7)
    print(f"Folds: {len(folds)} (sizes: {[f['val_range'][1]-f['val_range'][0] for f in folds]})\n")

    configs = []
    configs.append(("LinearRegression", "default", True, lambda: LinearRegression()))
    for alpha in (0.1, 1.0, 10.0):
        configs.append(("Ridge", f"alpha={alpha}", True, lambda a=alpha: Ridge(alpha=a, random_state=42)))
    for depth in (2, 3, 4):
        configs.append(("DecisionTree", f"max_depth={depth}", False,
                         lambda d=depth: DecisionTreeRegressor(max_depth=d, random_state=42)))

    all_summaries = []
    for feature_set, rows in (("minimal", minimal_common), ("extended", extended)):
        print(f"--- Feature set: {feature_set} ---")
        for model_name, config_label, needs_scaling, build_fn in configs:
            s = run_model(rows, feature_set, folds, model_name, config_label, needs_scaling, build_fn)
            print_summary(s)
            all_summaries.append(s)
        print()

    print("=== Baseline comparison (Moving-average-3 mean MAE = {:.2f} is the benchmark) ===".format(
        BASELINE_MOVING_AVG_MAE))
    for s in sorted(all_summaries, key=lambda x: x["mean_val_mae"]):
        diff = s["mean_val_mae"] - BASELINE_MOVING_AVG_MAE
        verdict = "IMPROVES on" if diff < -1e-9 else ("WORSE than" if diff > 1e-9 else "TIES")
        print(f"  {s['feature_set']:8s} {s['model']:16s} {s['config']:10s} "
              f"MAE={s['mean_val_mae']:7.2f} (diff vs moving-avg: {diff:+7.2f}) -> {verdict} moving-average-3")

    best = min(all_summaries, key=lambda x: (x["mean_val_mae"], x["stdev_val_mae"], x["mean_val_rmse"]))
    print(f"\nBest ML configuration on validation MAE: {best['feature_set']} / {best['model']} "
          f"({best['config']}) -> mean MAE={best['mean_val_mae']:.2f}, mean RMSE={best['mean_val_rmse']:.2f}")
    if best["mean_val_mae"] < BASELINE_MOVING_AVG_MAE:
        print("  This configuration's mean validation MAE is lower than moving-average-3's.")
    else:
        print("  No tested ML configuration's mean validation MAE beats moving-average-3.")

    print("\n=== Done. Test partition (rows [{}:{}] of the common window) was never loaded into "
          "any fit() or predict() call above. ===".format(test_start, n))
