"""
09단계 기준선 2개 + 10~12단계 모델 3개를 하나의 표·차트로 비교한다.
각 스크립트가 이미 저장해 둔 metrics CSV를 다시 읽기만 하고, 모델을 재학습하지 않는다.

R2를 기준으로 정렬한다 -- RMSE만 보면 평균값 기준선이 persistence보다 낮게(좋아 보이게)
나올 수 있는 함정이 있다(09단계에서 확인: R2는 평균값 기준선이 ~0인데 RMSE는 오히려
persistence보다 크다).
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
MODEL_DIR = ROOT / "outputs" / "model"

INK = "#0b0b0b"
INK_DIM = "#52514e"
INK_FAINT = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SURFACE = "#fcfcfb"
COLOR_BASELINE = "#c3c2b7"
COLOR_MODEL = "#2a78d6"


def load_regression() -> pd.DataFrame:
    baseline = pd.read_csv(MODEL_DIR / "baseline_regression.csv")
    rows = [
        {
            "model": row["기준선"].replace("(오늘=내일)", ""),
            "kind": "baseline",
            "rmse": row["RMSE"],
            "mae": row["MAE"],
            "r2": row["R2"],
        }
        for _, row in baseline.iterrows()
    ]
    for filename in [
        "linear_regression_metrics.csv",
        "rf_regression_metrics.csv",
        "xgb_regression_metrics.csv",
    ]:
        m = pd.read_csv(MODEL_DIR / filename).iloc[0]
        rows.append({"model": m["모델"], "kind": "model", "rmse": m["RMSE"], "mae": m["MAE"], "r2": m["R2"]})

    df = pd.DataFrame(rows)
    return df.sort_values("r2", ascending=False).reset_index(drop=True)


def bar_color(kind: str) -> str:
    return {"baseline": COLOR_BASELINE, "model": COLOR_MODEL}[kind]


def render(df: pd.DataFrame, metric: str, title: str, xlabel: str, out_path: Path) -> None:
    ordered = df.iloc[::-1]
    y = range(len(ordered))
    colors = [bar_color(k) for k in ordered["kind"]]

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)

    ax.barh(list(y), ordered[metric], color=colors, height=0.6)
    ax.margins(x=0.18)
    span = ordered[metric].max() - ordered[metric].min()
    offset = max(span, 1e-6) * 0.02
    for i, v in zip(y, ordered[metric]):
        ax.text(
            v + (offset if v >= 0 else -offset), i, f"{v:.3f}",
            va="center", ha="left" if v >= 0 else "right", fontsize=9, color=INK_DIM,
        )

    ax.set_yticks(list(y), ordered["model"], color=INK_DIM, fontsize=10)
    ax.axvline(0, color=AXIS, lw=1)
    ax.set_title(title, fontsize=14, color=INK, loc="left", pad=14)
    ax.set_xlabel(xlabel, color=INK_DIM)

    handles = [
        plt.Rectangle((0, 0), 1, 1, color=COLOR_BASELINE, label="기준선"),
        plt.Rectangle((0, 0), 1, 1, color=COLOR_MODEL, label="모델"),
    ]
    ax.legend(handles=handles, loc="lower right", frameon=False, fontsize=9, labelcolor=INK_DIM)

    ax.grid(axis="x", color=GRID)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(AXIS)
    ax.tick_params(colors=INK_FAINT)

    fig.tight_layout()
    fig.savefig(out_path, facecolor=SURFACE)
    plt.close(fig)


if __name__ == "__main__":
    OUTPUT_DIR = MODEL_DIR
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    reg = load_regression()
    print("=== 회귀 비교 (next_day_energy_kWh, R2 기준 정렬) ===")
    print(reg.to_string(index=False))
    reg.to_csv(OUTPUT_DIR / "model_comparison_regression.csv", index=False, encoding="utf-8-sig")
    render(
        reg, "r2", "다음 날 총 사용량 예측 -- 모델 비교 (R²)", "R² (test)",
        OUTPUT_DIR / "model_comparison_regression.png",
    )

    print(f"\n저장: {(OUTPUT_DIR / 'model_comparison_regression.csv').relative_to(ROOT)}")
    print(f"저장: {(OUTPUT_DIR / 'model_comparison_regression.png').relative_to(ROOT)}")
