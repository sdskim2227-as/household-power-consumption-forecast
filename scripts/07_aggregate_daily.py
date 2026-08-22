"""
02단계가 만든 시간 단위 데이터(household_power_hourly.csv.gz, 결측 0건)를 일 단위로
다시 뭉친다. 예측 단위를 "다음 시간"에서 "다음 날"로 바꾸기로 한 결정
(2026-08-22, 사용자와 논의 -- REPORT.md 부록 참고)에 따른 단계다.

집계 방식(컬럼 성격에 따라 다르게 처리):
- Global_active_power / Global_reactive_power: 시간별 평균전력(kW)이 그대로 "그 1시간의
  에너지(kWh)"와 같은 숫자이므로, 하루 24개 값을 그냥 합하면 하루 총 에너지(kWh)가 된다.
- Voltage / Global_intensity: 누적량이 아니라 순간값의 평균이므로, 하루 24개 값의 평균을
  그대로 하루 대표값으로 쓴다.
- Sub_metering_1/2/3: 시간별 값이 "그 시간 동안 분당 평균 Wh"이므로, 하루 총 Wh를 구하려면
  24개 값을 합한 뒤 60(분)을 곱해야 한다.

**하루 총량을 계산하는 거라, 시간이 하나라도 비면 그 날의 합계가 실제보다 작게 나온다.**
그래서 이 단계는 부분적으로 빈 날(24시간 중 일부만 있는 날)을 보간하지 않고 통째로
제외한다 -- 02단계의 "부분결측은 보간"과 다른 기준이다(합계는 보간에 더 민감하기 때문).
"""

import sys
from pathlib import Path

import pandas as pd

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
HOURLY_PATH = ROOT / "data" / "preprocessed" / "household_power_hourly.csv.gz"
OUT_PATH = ROOT / "data" / "preprocessed" / "household_power_daily.csv"
QUALITY_DIR = ROOT / "outputs" / "quality"

SUM_AS_IS_COLS = ["Global_active_power", "Global_reactive_power"]  # 합 = kWh
MEAN_COLS = ["Voltage", "Global_intensity"]
SUM_TIMES_60_COLS = ["Sub_metering_1", "Sub_metering_2", "Sub_metering_3"]  # 합*60 = Wh


def main() -> None:
    hourly = pd.read_csv(HOURLY_PATH, parse_dates=["datetime"])
    hourly["date"] = hourly["datetime"].dt.date

    hours_per_day = hourly.groupby("date")["datetime"].count()
    complete_days = hours_per_day[hours_per_day == 24].index
    incomplete_days = hours_per_day[hours_per_day != 24]
    print(f"전체 날짜 수: {len(hours_per_day)}개")
    print(f"24시간 전부 있는 날: {len(complete_days)}개")
    print(f"24시간이 안 되는 날(제외 대상): {len(incomplete_days)}개")
    if len(incomplete_days) > 0:
        print(incomplete_days.to_string())

    df = hourly[hourly["date"].isin(complete_days)]

    daily = df.groupby("date").agg(
        **{c: (c, "sum") for c in SUM_AS_IS_COLS},
        **{c: (c, "mean") for c in MEAN_COLS},
        **{c: (c, "sum") for c in SUM_TIMES_60_COLS},
    )
    for c in SUM_TIMES_60_COLS:
        daily[c] = daily[c] * 60

    daily = daily.rename(
        columns={
            "Global_active_power": "Global_active_energy_kWh",
            "Global_reactive_power": "Global_reactive_energy_kWh",
            "Sub_metering_1": "Sub_metering_1_Wh",
            "Sub_metering_2": "Sub_metering_2_Wh",
            "Sub_metering_3": "Sub_metering_3_Wh",
        }
    )
    daily.index = pd.to_datetime(daily.index)
    daily.index.name = "date"
    daily = daily.sort_index()

    print(f"\n최종 일 단위 행 수: {len(daily)}")
    print(f"기간: {daily.index.min().date()} ~ {daily.index.max().date()}")
    print("\n=== 컬럼별 범위 ===")
    print(daily.describe().T[["min", "mean", "max"]])

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    daily.to_csv(OUT_PATH)
    print(f"\n저장: {OUT_PATH.relative_to(ROOT)}")

    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    log_path = QUALITY_DIR / "daily_aggregation_log.csv"
    log_df = pd.DataFrame(
        {
            "구분": ["전체 날짜 수", "24시간 전부 있는 날", "제외된 날(24시간 미만)", "최종 행 수"],
            "값": [len(hours_per_day), len(complete_days), len(incomplete_days), len(daily)],
        }
    )
    log_df.to_csv(log_path, index=False, encoding="utf-8-sig")
    print(f"저장: {log_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
