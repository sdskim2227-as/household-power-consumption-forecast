"""
요일별(평일/주말)·계절별(봄/여름/가을/겨울) 전력 사용량 패턴을 확인한다.
docs/problem-definition.md "세부 질문 2"에 대응.
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
BAR_COLOR = "#2a78d6"
SEASON_COLORS = {"봄": "#2aa876", "여름": "#d64545", "가을": "#c98a1f", "겨울": "#2a78d6"}

WEEKDAY_ORDER = ["월", "화", "수", "목", "금", "토", "일"]
WEEKDAY_MAP = dict(enumerate(WEEKDAY_ORDER))  # dayofweek 0=월 ... 6=일
SEASON_ORDER = ["봄", "여름", "가을", "겨울"]


def month_to_season(month: int) -> str:
    if month in (3, 4, 5):
        return "봄"
    if month in (6, 7, 8):
        return "여름"
    if month in (9, 10, 11):
        return "가을"
    return "겨울"


def read_dataset(path: Path = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["datetime"])
    df["요일"] = df["datetime"].dt.dayofweek.map(WEEKDAY_MAP)
    df["계절"] = df["datetime"].dt.month.map(month_to_season)
    return df


def weekday_summary(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby("요일")["Global_active_power"].mean().round(3).reindex(WEEKDAY_ORDER)
    return grouped.reset_index()


def season_summary(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby("계절")["Global_active_power"].mean().round(3).reindex(SEASON_ORDER)
    return grouped.reset_index()


def render(weekday_df: pd.DataFrame, season_df: pd.DataFrame, out_path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5), dpi=150, facecolor=SURFACE)

    ax = axes[0]
    ax.set_facecolor(SURFACE)
    colors = ["#d64545" if d in ("토", "일") else BAR_COLOR for d in weekday_df["요일"]]
    ax.bar(weekday_df["요일"], weekday_df["Global_active_power"], color=colors)
    ax.set_title("요일별 평균 유효전력", fontsize=12, color=INK, loc="left")
    ax.set_ylabel("평균 유효전력 (kW)", color=INK_DIM)
    ax.grid(axis="y", color=GRID)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(AXIS)
    ax.tick_params(colors=INK_FAINT)

    ax = axes[1]
    ax.set_facecolor(SURFACE)
    colors = [SEASON_COLORS[s] for s in season_df["계절"]]
    ax.bar(season_df["계절"], season_df["Global_active_power"], color=colors)
    ax.set_title("계절별 평균 유효전력", fontsize=12, color=INK, loc="left")
    ax.grid(axis="y", color=GRID)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(AXIS)
    ax.tick_params(colors=INK_FAINT)

    fig.tight_layout()
    fig.savefig(out_path, facecolor=SURFACE)
    plt.close(fig)


if __name__ == "__main__":
    df = read_dataset()
    weekday_df = weekday_summary(df)
    season_df = season_summary(df)

    print("=== 요일별 평균 유효전력 ===")
    print(weekday_df.to_string(index=False))
    print("\n=== 계절별 평균 유효전력 ===")
    print(season_df.to_string(index=False))

    weekday_ratio = weekday_df.loc[weekday_df["요일"].isin(["토", "일"]), "Global_active_power"].mean() / \
        weekday_df.loc[~weekday_df["요일"].isin(["토", "일"]), "Global_active_power"].mean()
    print(f"\n주말/평일 배율: {weekday_ratio:.3f}배")

    season_ratio = season_df["Global_active_power"].max() / season_df["Global_active_power"].min()
    print(f"계절 최대/최소 배율: {season_ratio:.3f}배")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    weekday_df.to_csv(OUTPUT_DIR / "weekday_summary.csv", index=False, encoding="utf-8-sig")
    season_df.to_csv(OUTPUT_DIR / "season_summary.csv", index=False, encoding="utf-8-sig")

    out_path = OUTPUT_DIR / "weekday_season.png"
    render(weekday_df, season_df, out_path)
    print(f"\n저장: {out_path.relative_to(ROOT)}")
    print(f"저장: {(OUTPUT_DIR / 'weekday_summary.csv').relative_to(ROOT)}")
    print(f"저장: {(OUTPUT_DIR / 'season_summary.csv').relative_to(ROOT)}")
