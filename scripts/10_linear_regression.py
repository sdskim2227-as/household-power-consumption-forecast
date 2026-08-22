"""
선형회귀로 "다음 날 총 사용량(next_day_energy_kWh)"을 예측한다. 09_train_test_split.py가
저장한 train.csv/test.csv를 그대로 쓴다(같은 분할이어야 기준선과 공정하게 비교됨).

입력 변수(모두 예측 시점=오늘 기준으로 알 수 있는 값만 사용):
- 오늘의 7개 수치 컬럼(Global_active_energy_kWh 등): persistence 기준선과 같은 정보 +
  전압/전류/서브미터링까지 추가로 활용.
- month_tomorrow, weekday_tomorrow: 내일 날짜의 월/요일 -- 달력은 미리 알 수 있으므로
  "미래 정보 누수"가 아니다(관측값이 아니라 계산으로 나오는 값). 2026-08-22 사용자와
  논의한 대로, 타깃은 "다음 날"로 유지하되 계절성(월)을 입력 변수로 명시적으로 넣어
  4년치 데이터의 강점을 살린다.

10~12 스크립트(선형회귀/랜덤포레스트/XGBoost)가 전부 이 입력 변수 정의를 그대로
복붙해 쓴다(공통 모듈로 묶지 않는다 -- 스크립트는 각자 완결적이어야 하므로).
"""

from pathlib import Path

import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

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


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    tomorrow = pd.to_datetime(df["date"]) + pd.Timedelta(days=1)
    df["month_tomorrow"] = tomorrow.dt.month
    df["weekday_tomorrow"] = tomorrow.dt.dayofweek
    return df


def main() -> None:
    train_df = build_features(pd.read_csv(TRAIN_PATH, parse_dates=["date"]))
    test_df = build_features(pd.read_csv(TEST_PATH, parse_dates=["date"]))

    # train/test를 합쳐서 한 번에 원-핫 인코딩해야 두 쪽의 더미 컬럼이 정확히 일치한다.
    combined = pd.concat([train_df, test_df], keys=["train", "test"])
    combined_encoded = pd.get_dummies(
        combined[CATEGORICAL_COLS + NUMERIC_COLS], columns=CATEGORICAL_COLS
    )

    X_train = combined_encoded.loc["train"].reset_index(drop=True)
    X_test = combined_encoded.loc["test"].reset_index(drop=True)
    y_train = train_df[TARGET].reset_index(drop=True)
    y_test = test_df[TARGET].reset_index(drop=True)

    print(f"입력 변수 개수(원-핫 인코딩 후): {X_train.shape[1]}")

    model = LinearRegression()
    model.fit(X_train, y_train)
    pred = model.predict(X_test)

    rmse = mean_squared_error(y_test, pred) ** 0.5
    mae = mean_absolute_error(y_test, pred)
    r2 = r2_score(y_test, pred)

    print("\n=== 선형회귀 결과 ===")
    print(f"RMSE: {rmse:.3f}")
    print(f"MAE: {mae:.3f}")
    print(f"R2: {r2:.4f}")

    baseline_path = OUTPUT_DIR / "baseline_regression.csv"
    if baseline_path.exists():
        baseline = pd.read_csv(baseline_path)
        print("\n=== 기준선 대비 ===")
        print(baseline.to_string(index=False))

    result = pd.DataFrame(
        [{"모델": "선형회귀", "RMSE": round(rmse, 3), "MAE": round(mae, 3), "R2": round(r2, 4)}]
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_DIR / "linear_regression_metrics.csv", index=False, encoding="utf-8-sig")
    print(f"\n저장: {(OUTPUT_DIR / 'linear_regression_metrics.csv').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
