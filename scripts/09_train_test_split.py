"""
train/test 분할과 기준선(baseline) 2종을 계산한다. 모델은 이 두 기준선을 확실히 넘어야 한다.

- 분할: 다른 프로젝트들과 동일하게 무작위 8:2 분할(random_state=42)을 우선 사용한다.
  시간 순서가 있는 데이터라 나중에 날짜순 분할과 비교하는 시간 누수 검증을 거친다.
- 기준선 1(평균값): train의 `next_day_energy_kWh` 평균으로만 test 전체를 예측했을 때의 오차.
- 기준선 2(persistence): "오늘 쓴 만큼 내일도 쓴다"고 가정 — 오늘 `Global_active_energy_kWh`를
  그대로 `next_day_energy_kWh` 예측값으로 쓴다. 하루 단위로 집계하면서 시간대별 요동은
  평균으로 뭉개졌지만, 계절 흐름(겨울>여름)은 며칠 사이엔 크게 안 바뀌므로 이 기준선이
  꽤 강할 것으로 예상된다.
"""

from pathlib import Path

import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "preprocessed" / "household_power_daily_with_target.csv"
OUTPUT_DIR = ROOT / "outputs" / "model"

TRAIN_PATH = ROOT / "data" / "preprocessed" / "train.csv"
TEST_PATH = ROOT / "data" / "preprocessed" / "test.csv"

TARGET_COL = "next_day_energy_kWh"
TODAY_COL = "Global_active_energy_kWh"


def evaluate(y_true, y_pred, name: str) -> dict:
    return {
        "기준선": name,
        "RMSE": round(mean_squared_error(y_true, y_pred) ** 0.5, 3),
        "MAE": round(mean_absolute_error(y_true, y_pred), 3),
        "R2": round(r2_score(y_true, y_pred), 4),
    }


def main() -> None:
    df = pd.read_csv(DATA_PATH, parse_dates=["date"])

    train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)
    print(f"전체 행 수: {len(df)}")
    print(f"train: {len(train_df)} / test: {len(test_df)}")

    y_test = test_df[TARGET_COL]

    # 기준선 1: 평균값
    mean_pred = pd.Series(train_df[TARGET_COL].mean(), index=test_df.index)
    mean_result = evaluate(y_test, mean_pred, "평균값 기준선")

    # 기준선 2: persistence (오늘 사용량 = 내일 예측값)
    persistence_pred = test_df[TODAY_COL]
    persistence_result = evaluate(y_test, persistence_pred, "persistence 기준선(오늘=내일)")

    results = pd.DataFrame([mean_result, persistence_result])
    print("\n=== 회귀 기준선 ===")
    print(results.to_string(index=False))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results.to_csv(OUTPUT_DIR / "baseline_regression.csv", index=False, encoding="utf-8-sig")

    train_df.to_csv(TRAIN_PATH, index=False, encoding="utf-8-sig")
    test_df.to_csv(TEST_PATH, index=False, encoding="utf-8-sig")
    print(f"\n저장: {(OUTPUT_DIR / 'baseline_regression.csv').relative_to(ROOT)}")
    print(f"저장: {TRAIN_PATH.relative_to(ROOT)}")
    print(f"저장: {TEST_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
