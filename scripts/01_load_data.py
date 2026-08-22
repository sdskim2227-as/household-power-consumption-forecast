"""
data/raw/household_power_consumption.txt(세미콜론 구분, 분 단위, 133MB)를 읽어
컬럼 구조·기간·결측 패턴을 확인한다.

- 원본은 133MB라 GitHub에 커밋하지 않는다(.gitignore) — 이 스크립트는 결과를 저장하지
  않고 "이 데이터가 어떤 모양인가"만 확인한다. 실제 집계·저장은 다음 단계
  (02_aggregate_hourly.py)에서 raw를 직접 다시 읽어 처리한다(중간 산출물이 raw만큼
  커지는 걸 피하기 위해).
- 결측은 원본에 `?`로 표시돼 있다 — `na_values="?"`로 읽어 결측으로 인식시킨다.
- Date+Time을 합쳐 datetime을 만든다(유럽식 dd/mm/yyyy이므로 `dayfirst=True`).
- 결측이 무작위인지, 특정 날짜가 통째로 빠진 것인지 확인한다(하루=1,440분).
"""

import sys
from pathlib import Path

import pandas as pd

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = ROOT / "data" / "raw" / "household_power_consumption.txt"


def main() -> None:
    df = pd.read_csv(RAW_PATH, sep=";", na_values="?", low_memory=False)

    print(f"행 수: {len(df)}")
    print(f"컬럼 수: {len(df.columns)}")
    print(f"컬럼: {df.columns.tolist()}")

    df["datetime"] = pd.to_datetime(df["Date"] + " " + df["Time"], dayfirst=True)

    print(f"\n기간: {df['datetime'].min()} ~ {df['datetime'].max()}")
    print(f"기간 일수: {(df['datetime'].max() - df['datetime'].min()).days}일")

    numeric_cols = [c for c in df.columns if c not in ("Date", "Time", "datetime")]
    print("\n=== 컬럼별 결측치 ===")
    for c in numeric_cols:
        n_null = df[c].isna().sum()
        print(f"  {c}: {n_null}건 ({n_null / len(df) * 100:.2f}%)")

    print("\n=== 컬럼별 관측 범위 (결측 제외) ===")
    for c in numeric_cols:
        series = df[c].dropna()
        print(f"  {c}: {series.min()} ~ {series.max()}")

    # 결측 패턴: 날짜별 결측 행 수 집계 -> 하루(1440분) 통째로 빠진 날짜 확인
    is_missing = df[numeric_cols].isna().any(axis=1)
    missing_by_date = df.loc[is_missing, "datetime"].dt.date.value_counts()
    full_day_missing = missing_by_date[missing_by_date >= 1440]

    print(f"\n결측이 있는 날짜 수: {len(missing_by_date)}")
    print(f"하루 전체(1,440분)가 결측인 날짜 수: {len(full_day_missing)}")
    print(f"부분 결측(1,440분 미만)인 날짜 수: {len(missing_by_date) - len(full_day_missing)}")
    if len(missing_by_date) - len(full_day_missing) > 0:
        partial = missing_by_date[missing_by_date < 1440]
        print("\n=== 부분 결측 날짜 (상위 10) ===")
        print(partial.head(10).to_string())


if __name__ == "__main__":
    main()
