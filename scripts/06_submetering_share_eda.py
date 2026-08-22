"""
가전 카테고리(서브미터링 3종)가 전체 사용량 중 얼마를 설명하는지 확인한다.
docs/problem-definition.md "세부 질문 3·4", "확인해볼 것 3"에 대응.

- UCI 데이터셋 공식 설명이 제시하는 식을 그대로 쓴다:
    기타가전(Wh/분) = Global_active_power(kW) * 1000 / 60 - (Sub_metering_1+2+3)
  즉 "전체 유효전력을 분당 Wh로 환산한 값"에서 "서브미터링 3종 합"을 빼면, 서브미터링이
  잡아내지 못하는 나머지 가전(조명·냉장고 상시전력·전자기기 대기전력 등 추정)의 몫이다.
- 이 데이터는 이미 02단계에서 분 단위를 시간 단위 평균으로 집계한 것이지만, 평균은
  선형 연산이라 "시간별 평균에 이 식을 적용한 값" == "분 단위로 식을 적용한 뒤 시간
  평균 낸 값"이 정확히 같다 -- 근사가 아니라 정확한 값이다.
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
SURFACE = "#fcfcfb"
CATEGORY_LABELS = {
    "Sub_metering_1": "주방",
    "Sub_metering_2": "세탁실",
    "Sub_metering_3": "온수기+에어컨",
    "기타가전": "기타가전(추정)",
}
CATEGORY_COLORS = ["#2a78d6", "#2aa876", "#c98a1f", "#898781"]


def read_dataset(path: Path = DATA_PATH) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=["datetime"])


def compute_shares(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["기타가전"] = df["Global_active_power"] * 1000 / 60 - (
        df["Sub_metering_1"] + df["Sub_metering_2"] + df["Sub_metering_3"]
    )
    cols = ["Sub_metering_1", "Sub_metering_2", "Sub_metering_3", "기타가전"]

    n_negative = int((df["기타가전"] < 0).sum())
    print(f"'기타가전'이 음수로 나온 시간(계측 오차로 추정): {n_negative}건 / {len(df)}건")

    totals = df[cols].sum()
    shares = (totals / totals.sum() * 100).round(2)
    result = pd.DataFrame(
        {
            "category": cols,
            "label": [CATEGORY_LABELS[c] for c in cols],
            "total_Wh_per_min_sum": totals.values,
            "share_pct": shares.values,
        }
    ).sort_values("share_pct", ascending=False)
    return result


def render(shares: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 6), dpi=150, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)

    color_map = dict(zip(["Sub_metering_1", "Sub_metering_2", "Sub_metering_3", "기타가전"], CATEGORY_COLORS))
    colors = [color_map[c] for c in shares["category"]]

    wedges, _, autotexts = ax.pie(
        shares["share_pct"],
        labels=shares["label"],
        colors=colors,
        autopct="%.1f%%",
        startangle=90,
        textprops={"color": INK, "fontsize": 10},
        wedgeprops={"edgecolor": SURFACE, "linewidth": 1.5},
    )
    for autotext in autotexts:
        autotext.set_color("white")
        autotext.set_fontsize(9)

    ax.set_title("가전 카테고리별 전력 사용 비중", fontsize=13, color=INK, loc="left")

    fig.tight_layout()
    fig.savefig(out_path, facecolor=SURFACE)
    plt.close(fig)


if __name__ == "__main__":
    df = read_dataset()
    shares = compute_shares(df)

    print("\n=== 가전 카테고리별 비중 ===")
    print(shares.to_string(index=False))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    shares.to_csv(OUTPUT_DIR / "submetering_share_summary.csv", index=False, encoding="utf-8-sig")

    out_path = OUTPUT_DIR / "submetering_share.png"
    render(shares, out_path)
    print(f"\n저장: {out_path.relative_to(ROOT)}")
    print(f"저장: {(OUTPUT_DIR / 'submetering_share_summary.csv').relative_to(ROOT)}")
