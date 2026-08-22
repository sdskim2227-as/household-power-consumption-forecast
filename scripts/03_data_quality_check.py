"""
data/preprocessed/household_power_hourly.csv.gz(02_aggregate_hourly.py가 만든 시간
단위 집계 결과)의 결측치·중복행·이상 범위값을 점검하고, 컬럼별 설명·타입·관측범위를
정리한 데이터 사전을 만든다.

산출물(outputs/quality/):
- missing_values.csv   : 컬럼별 결측 개수·비율 (02단계에서 이미 0건이어야 정상)
- duplicate_rows.csv   : 전체 행 중복, datetime 중복 여부
- range_check.csv      : 도메인 규칙(전압대·음수 불가 등) 위반 건수
- data_dictionary.csv  : 컬럼별 설명·타입·관측된 최소/최대값
"""

import sys
from pathlib import Path

import pandas as pd

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "preprocessed" / "household_power_hourly.csv.gz"
OUTPUT_DIR = ROOT / "outputs" / "quality"

COLUMN_DESCRIPTIONS = {
    "datetime": "시간 단위 타임스탬프 (02_aggregate_hourly.py가 분 단위를 리샘플)",
    "Global_active_power": "가정 전체 유효전력, 해당 시간 내 분 단위 값의 평균 (kW)",
    "Global_reactive_power": "가정 전체 무효전력, 해당 시간 내 분 단위 값의 평균 (kW)",
    "Voltage": "전압, 해당 시간 내 분 단위 값의 평균 (V)",
    "Global_intensity": "전류, 해당 시간 내 분 단위 값의 평균 (A)",
    "Sub_metering_1": "서브미터링1(주방), 분당 유효에너지(Wh)의 시간 내 평균 -- 합계가 아님",
    "Sub_metering_2": "서브미터링2(세탁실), 분당 유효에너지(Wh)의 시간 내 평균 -- 합계가 아님",
    "Sub_metering_3": "서브미터링3(온수기+에어컨), 분당 유효에너지(Wh)의 시간 내 평균 -- 합계가 아님",
}

# 02단계에서 이미 0건이어야 하는 결측을 제외하면, 모든 전력·전류·전압 관련 값은 물리적으로
# 음수가 될 수 없다. Voltage는 가정용 전원 특성상 대략 200~260V 범위를 벗어나면 의심해야 한다.
RANGE_RULES = {
    "Global_active_power": (0, None),
    "Global_reactive_power": (0, None),
    "Voltage": (200, 260),
    "Global_intensity": (0, None),
    "Sub_metering_1": (0, None),
    "Sub_metering_2": (0, None),
    "Sub_metering_3": (0, None),
}

KEY_COLUMNS = ["datetime"]


def check_missing(df: pd.DataFrame) -> pd.DataFrame:
    null_count = df.isna().sum()
    return pd.DataFrame(
        {
            "column": df.columns,
            "non_null_count": df.notna().sum().values,
            "null_count": null_count.values,
            "null_pct": (null_count / len(df) * 100).round(2).values,
        }
    ).sort_values("null_count", ascending=False)


def check_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    full_row_dup = int(df.duplicated().sum())
    key_dup = int(df.duplicated(subset=KEY_COLUMNS).sum())
    return pd.DataFrame(
        [
            {"check": "전체 행 완전 중복", "count": full_row_dup},
            {"check": f"키({'+'.join(KEY_COLUMNS)}) 중복", "count": key_dup},
        ]
    )


def check_ranges(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col, (low, high) in RANGE_RULES.items():
        series = df[col].dropna()
        violations = pd.Series(dtype=bool)
        if low is not None:
            violations = series < low
        if high is not None:
            over = series > high
            violations = over if violations.empty else (violations | over)
        rows.append(
            {
                "column": col,
                "allowed_range": f"[{low if low is not None else '-inf'}, {high if high is not None else 'inf'}]",
                "violation_count": int(violations.sum()),
                "observed_min": series.min(),
                "observed_max": series.max(),
            }
        )
    return pd.DataFrame(rows)


def build_data_dictionary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in df.columns:
        series = df[col]
        is_numeric = pd.api.types.is_numeric_dtype(series)
        rows.append(
            {
                "column": col,
                "dtype": str(series.dtype),
                "description": COLUMN_DESCRIPTIONS.get(col, ""),
                "n_unique": series.nunique(),
                "observed_min": series.min() if is_numeric else "",
                "observed_max": series.max() if is_numeric else "",
                "null_pct": round(series.isna().mean() * 100, 2),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    missing = check_missing(df)
    missing.to_csv(OUTPUT_DIR / "missing_values.csv", index=False, encoding="utf-8-sig")
    print("=== 결측치 ===")
    print(missing.to_string(index=False))

    duplicates = check_duplicates(df)
    duplicates.to_csv(OUTPUT_DIR / "duplicate_rows.csv", index=False, encoding="utf-8-sig")
    print("\n=== 중복행 ===")
    print(duplicates.to_string(index=False))

    ranges = check_ranges(df)
    ranges.to_csv(OUTPUT_DIR / "range_check.csv", index=False, encoding="utf-8-sig")
    print("\n=== 이상 범위값 ===")
    print(ranges.to_string(index=False))

    data_dict = build_data_dictionary(df)
    data_dict.to_csv(OUTPUT_DIR / "data_dictionary.csv", index=False, encoding="utf-8-sig")
    print(f"\n산출물 저장 위치: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
