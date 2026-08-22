"""
랜덤포레스트로 "다음 날 총 사용량(next_day_energy_kWh)"을 예측한다.
10_linear_regression.py와 같은 입력 변수·같은 분할을 써서 나란히 비교할 수 있게 한다.
원본(train.csv/test.csv)은 읽기만 하고 고치지 않는다.
"""

import sys
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
TRAIN_PATH = ROOT / "data" / "preprocessed" / "train.csv"
TEST_PATH = ROOT / "data" / "preprocessed" / "test.csv"
OUTPUT_DIR = ROOT / "outputs" / "model"

TARGET = "next_day_energy_kWh"
CATEGORICAL_COLS = ["month_tomorrow", "weekday_tomorrow"]
NUMERIC_COLS = [
    "Global_active_energy_kWh",
    "Global_reactive_energy_kWh",
    "Voltage",
    "Global_intensity",
    "Sub_metering_1_Wh",
    "Sub_metering_2_Wh",
    "Sub_metering_3_Wh",
]
SEED = 42
N_TREES = 300


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    tomorrow = pd.to_datetime(df["date"]) + pd.Timedelta(days=1)
    df["month_tomorrow"] = tomorrow.dt.month
    df["weekday_tomorrow"] = tomorrow.dt.dayofweek
    return df


def main() -> None:
    train_df = build_features(pd.read_csv(TRAIN_PATH, parse_dates=["date"]))
    test_df = build_features(pd.read_csv(TEST_PATH, parse_dates=["date"]))

    combined = pd.concat([train_df, test_df], keys=["train", "test"])
    combined_encoded = pd.get_dummies(
        combined[CATEGORICAL_COLS + NUMERIC_COLS], columns=CATEGORICAL_COLS
    )

    X_train = combined_encoded.loc["train"].reset_index(drop=True)
    X_test = combined_encoded.loc["test"].reset_index(drop=True)
    y_train = train_df[TARGET].reset_index(drop=True)
    y_test = test_df[TARGET].reset_index(drop=True)

    model = RandomForestRegressor(n_estimators=N_TREES, random_state=SEED, n_jobs=-1)
    model.fit(X_train, y_train)

    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)

    train_r2 = r2_score(y_train, train_pred)
    rmse = mean_squared_error(y_test, test_pred) ** 0.5
    mae = mean_absolute_error(y_test, test_pred)
    r2 = r2_score(y_test, test_pred)

    importances = (
        pd.DataFrame({"feature": X_train.columns, "importance": model.feature_importances_})
        .sort_values("importance", ascending=False)
    )

    print(f"입력 {X_train.shape[1]}개, n_estimators={N_TREES}, train={len(X_train)} test={len(X_test)}")
    print(f"\ntrain R2: {train_r2:.4f}  vs  test R2: {r2:.4f}  (격차가 크면 과적합 의심)")
    print("\n=== 랜덤포레스트 결과(test) ===")
    print(f"RMSE: {rmse:.3f}")
    print(f"MAE: {mae:.3f}")
    print(f"R2: {r2:.4f}")
    print("\n=== 변수중요도 (상위 10) ===")
    print(importances.head(10).to_string(index=False))

    for path, label in [
        (OUTPUT_DIR / "baseline_regression.csv", "기준선"),
        (OUTPUT_DIR / "linear_regression_metrics.csv", "선형회귀"),
    ]:
        if path.exists():
            print(f"\n=== {label} 대비 ===")
            print(pd.read_csv(path).to_string(index=False))

    result = pd.DataFrame(
        [{"모델": "랜덤포레스트", "RMSE": round(rmse, 3), "MAE": round(mae, 3), "R2": round(r2, 4)}]
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_DIR / "rf_regression_metrics.csv", index=False, encoding="utf-8-sig")
    importances.to_csv(OUTPUT_DIR / "rf_regression_importances.csv", index=False, encoding="utf-8-sig")
    print(f"\n저장: {(OUTPUT_DIR / 'rf_regression_metrics.csv').relative_to(ROOT)}")
    print(f"저장: {(OUTPUT_DIR / 'rf_regression_importances.csv').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
