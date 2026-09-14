"""
Phase 4C - Final untouched test evaluation (Potato only).

Purpose
-------
Model selection is CLOSED. The frozen model is:
    Extended features (lag_1, lag_2, lag_3, rolling_mean_3, rolling_std_3,
    day_of_week) + plain Linear Regression + StandardScaler fit on
    pre-test data only.

This script evaluates that exact, unchanged specification -- and only
that specification, plus the two mandatory baselines (persistence,
moving-average-3) -- against the 35-row test partition (rows [140:175]
of the common 175-row window) that has been untouched since Phase 3A.9.

This is a ONE-TIME evaluation. The script is written once, run once, and
its printed output is transcribed into the report as-is -- no branch of
this file changes behavior based on what the test numbers turn out to be,
and no second run with different settings is performed after seeing them.

Final-model training data (Task 1, made explicit rather than assumed):
the frozen Linear Regression is refit on ALL data strictly before the
test period -- rows [0:140], i.e. the original training range [0:105]
COMBINED with the validation range [105:140] -- because both are
"available before the final test period" per this phase's own
instruction, and validation's only role during model SELECTION (Phases
4A/4B) is now complete. This is not a hyperparameter change: the model
family, feature set, and preprocessing are identical to the frozen
specification; only the amount of pre-test data used to fit that same
specification has grown, which is standard practice once selection is
closed and a final model is being prepared for a single test evaluation.

No feature is recreated differently from Phase 3A.8. day_of_week is not
removed or re-encoded. No additional model or configuration is tried.
"""

import csv
import statistics
from datetime import datetime
from pathlib import Path

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RAW_POTATO_CSV = PROCESSED_DIR / "potato_hyderabad_daily.csv"
EXTENDED_CSV = PROCESSED_DIR / "potato_ml_extended.csv"

TARGET_COL = "target_modal_price_next_observation"
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

TRAIN_SIZE = 105
VAL_SIZE = 35
TEST_START = TRAIN_SIZE + VAL_SIZE   # 140
COMMON_WINDOW_SIZE = 175             # test range is [140:175]

# Quoted from Phase 4A/4B for the generalization comparison in Section 9 --
# not recomputed by copying, only compared against.
VALIDATION_LR_MEAN_MAE = 147.54
VALIDATION_LR_MEAN_RMSE = 193.32
VALIDATION_BEST_BASELINE_MAE = 189.84  # moving-average-3


def load_extended():
    with open(EXTENDED_CSV, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        for k in list(r.keys()):
            if k not in ("date", "day_of_week"):
                r[k] = float(r[k])
    return rows


def load_raw_potato():
    with open(RAW_POTATO_CSV, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["_date"] = datetime.strptime(r["date"], "%Y-%m-%d").date()
        r["_modal"] = float(r["modal_price_rs_quintal"])
    return rows


def build_matrix(rows):
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


# ---------------------------------------------------------------------------
# TASK 3 -- test-set leakage audit
# ---------------------------------------------------------------------------

def leakage_audit(extended_rows, raw_rows, train_rows, test_rows):
    print("=== TASK 3: Test-Set Leakage Audit ===")

    # 1 & 3: no overlap between train range and test range.
    n_train, n_test = len(train_rows), len(test_rows)
    no_overlap = n_train == TEST_START and n_test == COMMON_WINDOW_SIZE - TEST_START
    print(f"  [1,3] Training range is exactly [0:{TEST_START}] ({n_train} rows); "
          f"test range is exactly [{TEST_START}:{COMMON_WINDOW_SIZE}] ({n_test} rows); "
          f"no row index appears in both: {'CONFIRMED' if no_overlap else 'FAILED'}")
    assert no_overlap

    # 2 & 4: independently re-derive every TEST row's features and target
    # directly from the raw source, confirming each uses only information
    # at or before its own t (never a later target), exactly as Phase 4B
    # did for the full file -- repeated here specifically for the test
    # rows, standalone, so this script's own leakage claim does not merely
    # inherit trust from an earlier phase's run.
    raw_dates = [r["_date"] for r in raw_rows]
    date_to_idx = {d: i for i, d in enumerate(raw_dates)}
    mismatches = []
    for r in test_rows:
        t_idx = date_to_idx[datetime.strptime(r["date"], "%Y-%m-%d").date()]
        window = raw_rows[t_idx - 2: t_idx + 1]
        checks = [
            abs(raw_rows[t_idx]["_modal"] - r["lag_1_modal_price"]) < 1e-9,
            abs(raw_rows[t_idx - 1]["_modal"] - r["lag_2_modal_price"]) < 1e-9,
            abs(raw_rows[t_idx - 2]["_modal"] - r["lag_3_modal_price"]) < 1e-9,
            abs(statistics.mean(w["_modal"] for w in window) - r["rolling_mean_3_modal_price"]) < 1e-9,
            abs(statistics.pstdev(w["_modal"] for w in window) - r["rolling_std_3_modal_price"]) < 1e-9,
            raw_rows[t_idx]["_date"].strftime("%A") == r["day_of_week"],
            abs(raw_rows[t_idx + 1]["_modal"] - r[TARGET_COL]) < 1e-9,
        ]
        if not all(checks):
            mismatches.append(r["date"])
    print(f"  [2,4] Independent recomputation of all 35 test rows' features+target from raw data: "
          f"{len(mismatches)} mismatches. Every test feature uses only data at or before its own t; "
          f"every test target is confirmed to be raw_rows[t_idx+1], never used as a feature input.")
    assert not mismatches

    print(f"  Test targets used during fitting: NO (see Task 1 -- fitting uses rows [0:{TEST_START}] only, "
          f"the model object is fit BEFORE test rows are ever read for prediction).")
    print(f"  Test targets used for feature engineering: NO -- features were built in Phase 3A.8, "
          f"long before this test evaluation, using only each row's own past window.")
    print(f"  [5] Test period previously used for model selection: NO -- Phases 4A and 4B both "
          f"asserted, in their own code, that no slice exceeded row index {TEST_START}; this phase "
          f"is the first to read rows [{TEST_START}:{COMMON_WINDOW_SIZE}] at all.")


# ---------------------------------------------------------------------------
# Baselines
# ---------------------------------------------------------------------------

def persistence_predictions(test_rows):
    return np.array([r["lag_1_modal_price"] for r in test_rows])


def moving_average_3_predictions(test_rows):
    return np.array([r["rolling_mean_3_modal_price"] for r in test_rows])


def mae_rmse(y_true, y_pred):
    err = np.asarray(y_true) - np.asarray(y_pred)
    return float(np.mean(np.abs(err))), float(np.sqrt(np.mean(err ** 2)))


if __name__ == "__main__":
    print("=== Phase 4C: Final Untouched Test Evaluation (Potato only) ===")
    print("This is a ONE-TIME evaluation. No branch below reacts to the result.\n")

    extended_rows = load_extended()
    raw_rows = load_raw_potato()
    assert len(extended_rows) == COMMON_WINDOW_SIZE

    train_rows = extended_rows[0:TEST_START]        # rows [0:140] -- train+validation combined
    test_rows = extended_rows[TEST_START:COMMON_WINDOW_SIZE]  # rows [140:175] -- test, read for the first time

    print("=== TASK 1: Final Model Training Data ===")
    print(f"  Frozen model refit on rows [0:{TEST_START}] = {len(train_rows)} observations "
          f"({train_rows[0]['date']} to {train_rows[-1]['date']}).")
    print(f"  This is the original training range [0:105] COMBINED WITH the validation range "
          f"[105:140], per this phase's instruction that the final fit may use all data "
          f"'available before the final test period.' No hyperparameter or feature changed -- "
          f"only the amount of pre-test data used to fit the SAME frozen specification.")
    print(f"  Test rows [{TEST_START}:{COMMON_WINDOW_SIZE}] = {len(test_rows)} observations "
          f"({test_rows[0]['date']} to {test_rows[-1]['date']}) are NOT included above.\n")

    print("=== TASK 2: Feature Preparation ===")
    print("  Test-row features are read AS-IS from potato_ml_extended.csv (Phase 3A.8's own "
          "construction) -- lag_1/2/3, rolling_mean_3, rolling_std_3, day_of_week. Nothing was "
          "recreated, recomputed differently, or re-encoded for this evaluation.\n")

    leakage_audit(extended_rows, raw_rows, train_rows, test_rows)

    # --- Fit the frozen model exactly once, on rows [0:140] only ---
    X_train, y_train, feature_names = build_matrix(train_rows)
    X_test, y_test, _ = build_matrix(test_rows)
    scaler = StandardScaler().fit(X_train)          # fit ONLY on pre-test data
    model = LinearRegression().fit(scaler.transform(X_train), y_train)
    lr_pred = model.predict(scaler.transform(X_test))

    persistence_pred = persistence_predictions(test_rows)
    ma3_pred = moving_average_3_predictions(test_rows)

    print("\n=== TASK 7: Fair Comparison Check ===")
    n_persist, n_ma3, n_lr = len(persistence_pred), len(ma3_pred), len(lr_pred)
    identical_n = n_persist == n_ma3 == n_lr == len(test_rows)
    print(f"  Predictions produced: persistence={n_persist}, moving_avg_3={n_ma3}, "
          f"linear_regression={n_lr}, test_rows_available={len(test_rows)}")
    if not identical_n:
        raise SystemExit("STOPPING: unequal evaluation sample sizes across methods -- "
                          "cannot proceed with a fair comparison.")
    print(f"  All three methods evaluated on the IDENTICAL {len(test_rows)} test rows, "
          f"same target values, same date range ({test_rows[0]['date']} to {test_rows[-1]['date']}): CONFIRMED")

    print("\n=== TASK 4: Persistence Test Evaluation ===")
    p_mae, p_rmse = mae_rmse(y_test, persistence_pred)
    print(f"  MAE = {p_mae:.2f}, RMSE = {p_rmse:.2f}")

    print("\n=== TASK 5: Moving-Average-3 Test Evaluation ===")
    m_mae, m_rmse = mae_rmse(y_test, ma3_pred)
    print(f"  MAE = {m_mae:.2f}, RMSE = {m_rmse:.2f}")

    print("\n=== TASK 6: Frozen Linear Regression Test Evaluation ===")
    lr_mae, lr_rmse = mae_rmse(y_test, lr_pred)
    abs_errors = np.abs(np.asarray(y_test) - lr_pred)
    print(f"  MAE = {lr_mae:.2f}, RMSE = {lr_rmse:.2f}")
    print(f"  Number of predictions: {len(lr_pred)}")
    print(f"  Date range: {test_rows[0]['date']} to {test_rows[-1]['date']}")
    print(f"  Minimum absolute error: {abs_errors.min():.2f}")
    print(f"  Maximum absolute error: {abs_errors.max():.2f}")
    print(f"  Median absolute error: {np.median(abs_errors):.2f}")

    print("\n=== TASK 8: Final Results Table ===")
    print(f"  {'Method':22s} {'MAE':>8s} {'RMSE':>8s}")
    print(f"  {'Persistence':22s} {p_mae:8.2f} {p_rmse:8.2f}")
    print(f"  {'Moving-Average-3':22s} {m_mae:8.2f} {m_rmse:8.2f}")
    print(f"  {'Linear Regression':22s} {lr_mae:8.2f} {lr_rmse:8.2f}")
    best_baseline = "Persistence" if p_mae < m_mae else "Moving-Average-3"
    best_baseline_mae = min(p_mae, m_mae)
    best_overall = min([("Persistence", p_mae), ("Moving-Average-3", m_mae), ("Linear Regression", lr_mae)],
                        key=lambda x: x[1])
    print(f"  Best baseline: {best_baseline} (MAE {best_baseline_mae:.2f})")
    print(f"  Best overall method: {best_overall[0]} (MAE {best_overall[1]:.2f})")

    print("\n=== TASK 9: Generalization Analysis ===")
    print(f"  Validation-stage Linear Regression: MAE {VALIDATION_LR_MEAN_MAE}, RMSE {VALIDATION_LR_MEAN_RMSE}")
    print(f"  Validation-stage best baseline (moving-avg-3): MAE {VALIDATION_BEST_BASELINE_MAE}")
    print(f"  Test-stage Linear Regression: MAE {lr_mae:.2f}, RMSE {lr_rmse:.2f}")
    print(f"  Test-stage moving-average-3: MAE {m_mae:.2f}, RMSE {m_rmse:.2f}")
    val_gap = VALIDATION_BEST_BASELINE_MAE - VALIDATION_LR_MEAN_MAE
    test_gap = m_mae - lr_mae
    print(f"  Validation gap (baseline MAE - LR MAE): {val_gap:+.2f} (positive = LR ahead)")
    print(f"  Test gap (baseline MAE - LR MAE): {test_gap:+.2f} (positive = LR ahead)")

    print("\n=== TASK 10: Error Analysis ===")
    diffs = np.asarray(y_test) - lr_pred  # positive = actual > predicted -> model underpredicted
    n_under = int(np.sum(diffs > 0))
    n_over = int(np.sum(diffs < 0))
    print(f"  Signed errors (actual - predicted): mean={diffs.mean():.2f}, "
          f"underpredictions(actual>pred)={n_under}, overpredictions(actual<pred)={n_over}, ties={len(diffs)-n_under-n_over}")
    order = np.argsort(-abs_errors)[:5]
    print("  Top 5 largest absolute errors:")
    for idx in order:
        r = test_rows[idx]
        print(f"    {r['date']} -> target={y_test[idx]:.2f} predicted={lr_pred[idx]:.2f} "
              f"abs_error={abs_errors[idx]:.2f} (lag_1={r['lag_1_modal_price']:.2f}, "
              f"day_of_week={r['day_of_week']})")
    print(f"  Predicted-value range: [{lr_pred.min():.2f}, {lr_pred.max():.2f}] "
          f"(spread={lr_pred.max()-lr_pred.min():.2f})")
    print(f"  Actual target range: [{np.min(y_test):.2f}, {np.max(y_test):.2f}] "
          f"(spread={np.max(y_test)-np.min(y_test):.2f})")

    print("\n=== Done. Test rows were read exactly once, for this evaluation only. "
          "No branch of this script changed behavior based on the resulting numbers. ===")
