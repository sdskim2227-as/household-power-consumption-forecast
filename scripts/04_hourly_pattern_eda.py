"""
하루 중 언제 전력 사용량이 가장 많은지 확인한다. docs/problem-definition.md
"세부 질문 1"에 대응.

- 시간(0~23시)별 평균 유효전력(Global_active_power, kW)을 선 그래프로 그린다.
- 평일/주말을 나눠서 같이 그려, 출퇴근형 패턴(평일 아침/저녁 피크)이 있는지 확인한다.
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "preprocessed" / "household_power_hourly.csv.gz"
OUTPUT_DIR = ROOT / "outputs" / "eda"

INK = "#0b0b0b"
INK_DIM = "#52514e"
INK_FAINT = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SURFACE = "#fcfcfb"
WEEKDAY_COLOR = "#2a78d6"
WEEKEND_COLOR = "#d64545"


def read_dataset(path: Path = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["datetime"])
    df["hour"] = df["datetime"].dt.hour
    df["is_weekend"] = df["datetime"].dt.dayofweek >= 5  # 5=토, 6=일
    return df


def hourly_summary(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby(["is_weekend", "hour"])["Global_active_power"]
        .mean()
        .round(3)
        .reset_index()
    )
    grouped["구분"] = grouped["is_weekend"].map({False: "평일", True: "주말"})
    return grouped[["구분", "hour", "Global_active_power"]]


def render(summary: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=150, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)

    for label, color in [("평일", WEEKDAY_COLOR), ("주말", WEEKEND_COLOR)]:
        sub = summary[summary["구분"] == label].sort_values("hour")
        ax.plot(
            sub["hour"], sub["Global_active_power"], color=color, lw=2,
            marker="o", markersize=4, label=label,
        )

    ax.set_title("시간대별 평균 유효전력 -- 평일 vs 주말", fontsize=13, color=INK, loc="left")
    ax.set_xlabel("시(hour)", color=INK_DIM)
    ax.set_ylabel("평균 유효전력 (kW)", color=INK_DIM)
    ax.set_xticks(range(0, 24, 2))
    ax.grid(axis="y", color=GRID)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(AXIS)
    ax.tick_params(colors=INK_FAINT)
    ax.legend(frameon=False, fontsize=10, loc="upper left")

    fig.tight_layout()
    fig.savefig(out_path, facecolor=SURFACE)
    plt.close(fig)


if __name__ == "__main__":
    df = read_dataset()
    summary = hourly_summary(df)

    print("=== 평일 상위 3시간대 ===")
    print(summary[summary["구분"] == "평일"].nlargest(3, "Global_active_power").to_string(index=False))
    print("\n=== 주말 상위 3시간대 ===")
    print(summary[summary["구분"] == "주말"].nlargest(3, "Global_active_power").to_string(index=False))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUTPUT_DIR / "hourly_pattern_summary.csv", index=False, encoding="utf-8-sig")

    out_path = OUTPUT_DIR / "hourly_pattern.png"
    render(summary, out_path)
    print(f"\n저장: {out_path.relative_to(ROOT)}")
    print(f"저장: {(OUTPUT_DIR / 'hourly_pattern_summary.csv').relative_to(ROOT)}")
