"""
data/raw/household_power_consumption.txt(분 단위)를 시간 단위로 집계한다.

- 완전결측 9일(1,440분 전부 결측 -- 2010-08-18~21 등 며칠씩 몰려 있음)은 보간 신뢰도가
  낮아 통째로 제외한다. 리샘플 후 이 날짜들의 시간대는 값이 하나도 없어 전부 NaN 행으로
  나타나므로 그대로 드롭한다.
- 부분결측 73일(1~12월 고르게 분포, 계절 쏠림 없음)은 시간별로 남아있는 분 데이터만으로
  평균을 낸다(pandas mean()의 기본 skipna=True). 그래도 특정 시간이 통째로 빈 경우만
  남는 NaN은 앞뒤 값 기준 time-based interpolation으로 메운다(공백이 크면 보간하지
  않고 그대로 남겨 로그로 남긴다).
- 원본은 133MB라 커밋하지 않으므로(.gitignore), 이 스크립트는 01_load_data.py와
  독립적으로 원본을 직접 다시 읽어 처리한다.
"""

import sys
from pathlib import Path

import pandas as pd

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = ROOT / "data" / "raw" / "household_power_consumption.txt"
PREPROCESSED_DIR = ROOT / "data" / "preprocessed"
QUALITY_DIR = ROOT / "outputs" / "quality"

FULL_DAY_MISSING_THRESHOLD = 1440  # 하루(1,440분) 전부 결측이면 완전결측으로 간주
INTERPOLATION_LIMIT_HOURS = 3  # 부분결측으로 남은 NaN 시간을 메울 때, 이보다 긴 공백은 보간하지 않음


def main() -> None:
    df = pd.read_csv(RAW_PATH, sep=";", na_values="?", low_memory=False)
    df["datetime"] = pd.to_datetime(df["Date"] + " " + df["Time"], dayfirst=True)
    numeric_cols = [c for c in df.columns if c not in ("Date", "Time", "datetime")]

    # 1) 완전결측 날짜 찾기 (01_load_data.py와 동일한 기준: 결측 행이 하루 전체 분량 이상)
    is_missing = df[numeric_cols].isna().any(axis=1)
    missing_by_date = df.loc[is_missing, "datetime"].dt.date.value_counts()
    full_day_missing_dates = set(missing_by_date[missing_by_date >= FULL_DAY_MISSING_THRESHOLD].index)
    print(f"완전결측으로 제외할 날짜 {len(full_day_missing_dates)}개: {sorted(full_day_missing_dates)}")

    before_rows = len(df)
    df = df[~df["datetime"].dt.date.isin(full_day_missing_dates)]
    print(f"제외 전 {before_rows}행 -> 제외 후 {len(df)}행 ({before_rows - len(df)}행 제거)")

    # 2) 시간 단위로 리샘플 (남은 분 데이터만으로 평균)
    df = df.set_index("datetime")
    hourly = df[numeric_cols].resample("h").mean()

    # 3) 완전결측 날짜의 시간대는 리샘플 과정에서 전부 NaN 행으로 채워지므로 그대로 드롭
    hourly_dates = pd.Series(hourly.index.date, index=hourly.index)
    hourly = hourly[~hourly_dates.isin(full_day_missing_dates)]

    # 4) 남은 NaN(부분결측 중 특정 시간이 통째로 빈 경우)은 근처 값으로 보간
    still_missing_before = int(hourly.isna().any(axis=1).sum())
    hourly = hourly.interpolate(method="time", limit=INTERPOLATION_LIMIT_HOURS, limit_direction="both")
    still_missing_after = int(hourly.isna().any(axis=1).sum())
    print(f"\n리샘플 직후 부분결측으로 남은 시간: {still_missing_before}개")
    print(f"보간(최대 {INTERPOLATION_LIMIT_HOURS}시간 공백까지) 후에도 남은 결측: {still_missing_after}개")
    if still_missing_after > 0:
        # 완전결측으로 제외한 날짜 바로 옆(예: 2007-04-28, 2010-09-28)이 보간 한도(3시간)보다
        # 긴 연속 공백을 갖고 있어 남는 값들이다 -- 채우지 않고 그대로 드롭한다.
        remaining_gap = hourly[hourly.isna().any(axis=1)]
        print("보간 한도를 넘는 공백이라 드롭함:")
        print(remaining_gap.index.to_series().dt.date.value_counts().sort_index())
        hourly = hourly.dropna()

    print(f"\n최종 시간 단위 행 수: {len(hourly)}")
    print(f"기간: {hourly.index.min()} ~ {hourly.index.max()}")

    PREPROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PREPROCESSED_DIR / "household_power_hourly.csv.gz"
    hourly.to_csv(out_path, compression="gzip")
    print(f"\n저장: {out_path}")

    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    log_path = QUALITY_DIR / "hourly_aggregation_log.csv"
    log_df = pd.DataFrame(
        {
            "구분": [
                "완전결측 제외 날짜 수",
                "완전결측 제외 시간 수",
                "부분결측으로 리샘플 후 NaN이었던 시간 수",
                f"보간 한도({INTERPOLATION_LIMIT_HOURS}시간) 초과로 드롭한 시간 수",
                "최종 행 수",
            ],
            "값": [
                len(full_day_missing_dates),
                len(full_day_missing_dates) * 24,
                still_missing_before,
                still_missing_after,
                len(hourly),
            ],
        }
    )
    log_df.to_csv(log_path, index=False, encoding="utf-8-sig")
    print(f"저장: {log_path}")


if __name__ == "__main__":
    main()
