# 🏠 가정용 전력 사용량 예측

**상태: 정규 파이프라인(01~13) 완료.** 선형회귀가 R²=0.5039로 최종 1위, 두 기준선을
확실히 이겼다. 상세 결과는 [`REPORT.md`](./REPORT.md) 참고.

포트폴리오 4번째 프로젝트. [`seoul-rainfall-prediction`](../seoul-rainfall-prediction)·
[`seoul-subway-demand-forecast`](../seoul-subway-demand-forecast)(예측 중심)·
[`korea-power-consumption-analysis`](../korea-power-consumption-analysis)(전국 단위 EDA
중심, 12개월치)에 이어, 이번엔 **가정 1채의 4년치 분 단위 시계열**로 다시 "예측"이
핵심인 프로젝트를 진행했다.

## 풀려는 문제

**핵심 질문**: 이 가정의 전력 사용량은 언제 늘어나고, 무엇이 그 사용량을 만드는가?
그리고 다음 날의 사용량을 예측할 수 있는가?

1. 하루 중 언제 전력 사용량이 가장 많은가?
2. 요일별(평일/주말)·계절별(여름/겨울) 패턴은 어떻게 다른가?
3. 가전 카테고리(주방/세탁실/온수기+에어컨) 중 무엇이 전체 사용량을 가장 많이 설명하는가?
4. 서브미터링 3종의 합이 전체 사용량을 얼마나 설명하는가?
5. **다음 날 총 사용량을 예측할 수 있는가?** (이 프로젝트의 핵심 — 처음엔 "다음 시간"
   으로 시작했으나, 관성 문제·데이터의 강점(4년치 계절성)을 더 잘 살리려고 "다음 날"로
   변경. 경위는 [`REPORT.md`](./REPORT.md) 1장·부록 참고)

자세한 문제 정의는 [`docs/problem-definition.md`](./docs/problem-definition.md), 진행 계획·
회고는 [`docs/CLAUDE_CODE_WORKFLOW.md`](./docs/CLAUDE_CODE_WORKFLOW.md) 참고.

## 결과 요약

무작위 8:2 분할 기준(train 1,128 / test 283):

| 모델 | RMSE | MAE | R² |
|---|---|---|---|
| **선형회귀** | 6.647 | 5.059 | **0.5039** |
| 랜덤포레스트 | 6.840 | 5.080 | 0.4747 |
| XGBoost | 7.003 | 5.222 | 0.4493 |
| persistence 기준선 | 8.766 | 6.424 | 0.1372 |
| 평균값 기준선 | 9.495 | 7.601 | -0.0123 |

가장 단순한 선형회귀가 1위 — 표본(1,128행)이 트리 기반 모델의 복잡도를 감당하기엔
작아서 랜덤포레스트·XGBoost는 과적합했다(XGBoost는 train R²=1.0000). 가전 카테고리별
비중은 기타가전(추정) 51.2% > 온수기+에어컨 35.5% > 세탁실 7.1% > 주방 6.2% 순.

## 데이터

UCI Machine Learning Repository의 "Individual household electric power consumption
Data Set" — 프랑스 가정 1채, 2006-12-16~2010-11-26(약 4년), 분 단위 2,075,259행.
**원본이 133MB로 GitHub 100MB 제한을 넘어 이 저장소엔 커밋하지 않는다**
(`data/raw/`가 `.gitignore` 처리돼 있음) — 재현 방법은 아래 "데이터 출처" 참고.

## 재현 방법

```
scripts/01_load_data.py              # 원본 구조·결측 패턴 확인 (저장 없음)
scripts/02_aggregate_hourly.py       # 분 -> 시간 집계, 결측 처리
scripts/03_data_quality_check.py     # 결측·중복·범위 점검
scripts/04_hourly_pattern_eda.py     # 시간대별 패턴 (평일/주말)
scripts/05_weekday_season_eda.py     # 요일·계절별 패턴
scripts/06_submetering_share_eda.py  # 가전 카테고리별 비중
scripts/07_aggregate_daily.py        # 시간 -> 일 집계
scripts/08_build_next_day_target.py  # 다음 날 타깃 생성, 누수 검증
scripts/09_train_test_split.py       # 기준선 2종 + 분할
scripts/10_linear_regression.py
scripts/11_random_forest_regression.py
scripts/12_xgboost_regression.py
scripts/13_model_comparison_chart.py
```

각 스크립트는 서로 의존하지 않고 원본(01~02) 또는 앞 단계 산출물을 다시 읽어
완결적으로 동작한다.

## 아직 못 한 것

- **시간 누수 검증(무작위 분할 vs 날짜순 분할 비교)을 하지 않았다.** `seoul-subway-demand-forecast`
  와 같은 이유로 생략 — 이미 선형회귀가 기준선을 크게 이겨 결론이 분명했다. 08단계의
  "다음 행=+1일" 검증으로 최소한의 인접성만 확인했다.
- **하이퍼파라미터 튜닝을 하지 않았다.** 표본이 작아(train 1,128행) 트리 기반 모델이
  과적합했지만, 이미 선형회귀가 최선이라는 결론이 명확해 튜닝의 기대 이익이 낮다고
  판단했다.
- **이상치 탐지·잔차 분석은 진행하지 않았다.**

## 폴더 구조

```
household-power-consumption-forecast/
├── README.md                  # 이 파일
├── REPORT.md                  # 상세 분석 리포트
├── CLAUDE.md                  # 이 프로젝트의 작업 규칙 (gitignore, 로컬 전용)
├── LICENSE
├── requirements.txt
├── data/
│   ├── raw/                   # 원본 데이터 (133MB, gitignore — 로컬에만 존재)
│   └── preprocessed/          # 시간/일 단위 집계, train/test (커밋 대상)
├── scripts/                   # 01~13 순서대로
├── outputs/
│   ├── quality/                # 결측치·중복·데이터사전
│   ├── eda/                    # 시간대·요일·계절·가전별 비교
│   └── model/                  # 성능지표·중요도·비교차트
├── docs/
│   ├── problem-definition.md   # 문제 정의·세부 질문
│   └── CLAUDE_CODE_WORKFLOW.md # 계획+회고 문서
└── worklogs/                   # 날짜별 작업 기록 (로컬 전용)
```

## 데이터 출처

[UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption),
"Individual household electric power consumption Data Set" (제공: Georges Hebrail,
Alice Berard — EDF R&D, France). 재현하려면 위 링크에서 원본을 내려받아
`data/raw/household_power_consumption.txt` 경로에 배치해야 한다. 라이선스는
[LICENSE](./LICENSE) 참고.
