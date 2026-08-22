"""
"다음 날 총 사용량을 예측할 수 있는가"(problem-definition.md 세부 질문 5, 2026-08-22
사용자와 논의 후 "다음 시간" 대신 "다음 날"로 확정 -- REPORT.md 부록 참고)를 위한
타깃을 만든다.

- `Global_active_energy_kWh`(하루 총 사용량)를 `shift(-1)`로 끌어와 `next_day_energy_kWh`
  타깃을 만든다.
- 07단계에서 24시간이 안 되는 날을 통째로 뺐기 때문에 날짜가 매끄럽게 연속이 아니다.
  다음 행의 날짜가 현재 날짜+1일과 정확히 같을 때만 타깃을 인정하고, 아니면(공백) 버린다
  -- 07_build_next_hour_target.py(폐기됨, 다음 시간 버전)에서 썼던 것과 같은 안전장치다.
- 무작위 지점에서 i번째 행의 타깃이 실제 i+1번째 행의 원래 값과 정확히 같은지 대조해
  누수 없이 만들어졌는지 검증한다.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "preprocessed" / "household_power_daily.csv"
OUT_PATH = ROOT / "data" / "preprocessed" / "household_power_daily_with_target.csv"

TARGET_COL = "next_day_energy_kWh"


def main() -> None:
    df = pd.read_csv(DATA_PATH, parse_dates=["date"]).sort_values("date").reset_index(drop=True)

    next_date = df["date"].shift(-1)
    is_consecutive = (next_date - df["date"]) == pd.Timedelta(days=1)
    n_gaps = int((~is_consecutive).sum())
    print(f"전체 {len(df)}행 중 '다음 행 = +1일'이 아닌(공백 뒤) 행: {n_gaps}개 (제거 대상)")

    df[TARGET_COL] = np.where(is_consecutive, df["Global_active_energy_kWh"].shift(-1), np.nan)

    rng = np.random.default_rng(42)
    valid_idx = df.index[is_consecutive]
    check_idx = rng.choice(valid_idx, size=5, replace=False)
    print("\n=== 누수 검증 (무작위 5개 지점) ===")
    all_match = True
    for i in check_idx:
        target_val = df.loc[i, TARGET_COL]
        actual_next_val = df.loc[i + 1, "Global_active_energy_kWh"]
        match = np.isclose(target_val, actual_next_val)
        all_match = all_match and match
        print(
            f"  행 {i} ({df.loc[i, 'date'].date()}): 타깃={target_val:.3f}, "
            f"실제 다음 행({df.loc[i + 1, 'date'].date()})={actual_next_val:.3f} -> {'일치' if match else '불일치!!'}"
        )
    print(f"전체 일치 여부: {all_match}")
    if not all_match:
        raise SystemExit("누수 검증 실패 -- shift 로직을 다시 확인해야 함")

    before = len(df)
    df = df.dropna(subset=[TARGET_COL]).reset_index(drop=True)
    print(f"\n타깃 없는(공백 뒤 또는 마지막) 행 제거: {before}행 -> {len(df)}행")

    df.to_csv(OUT_PATH, index=False)
    print(f"\n저장: {OUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
