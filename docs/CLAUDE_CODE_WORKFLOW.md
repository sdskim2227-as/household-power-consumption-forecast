# Claude Code로 이 프로젝트를 어떻게 진행하려는가 (계획)

이 문서는 분석이 끝난 뒤 쓰는 회고가 아니라, **지금 시점(스캐폴딩+원본 데이터 배치만
끝난 상태)에서 세운 계획**이다. 분석이 진행되는 대로 이 문서도 계속 갱신한다. 시간순
상세 기록은 [`worklogs/`](../worklogs/)에 있다.

## 무엇을 예측하려는가

[`problem-definition.md`](./problem-definition.md)에서 정한 문제:

1. **가정 사용 패턴 EDA** — 시간대·요일·계절·가전 카테고리별 사용량 구조 (탐색, 예측
   모델의 준비 단계)
2. **다음 시점 전력 사용량 예측 (회귀)** — 이 프로젝트의 핵심. `seoul-rainfall-prediction`·
   `seoul-subway-demand-forecast`처럼 예측이 메인이고, `korea-power-consumption-analysis`
   처럼 EDA가 메인이 아니다.

데이터는 `data/raw/household_power_consumption.txt`(세미콜론 구분, 133MB, 분 단위,
2006-12-16~2010-11-26, 2,075,259행). **133MB로 GitHub 100MB 제한을 넘으므로
`data/raw/`를 이 프로젝트의 `.gitignore`에 추가한다** — 앞의 세 프로젝트와 달리 원본을
커밋하지 않고, `data/preprocessed/`의 집계된(시간 단위 등) 결과만 커밋한다.

**가장 중요한 제약**: 다른 프로젝트와 동일하게, 입력은 항상 예측 시점까지의 값만 쓴다.
타깃은 `shift(-1)`(집계 단위 기준 다음 시점)로 다음 행에서 끌어오고, 입력 피처는 앞당기지
않는다.

## 이전 세 프로젝트와의 차이

| | seoul-rainfall-prediction | seoul-subway-demand-forecast | korea-power-consumption-analysis | household-power-consumption-forecast |
|---|---|---|---|---|
| 범위 | 서울 1개 지점 | 서울 5개 역 | 전국 17개 시도 | 가정 1채 |
| 기간 | 30년(일 단위) | 1년(시간 단위) | 1년(월 단위) | **4년(분 단위 → 집계)** |
| 핵심 | 예측 | 예측 | EDA | **예측** |
| 원본 커밋 | O(15MB) | O(24MB) | O(<1MB) | **X(133MB, gitignore)** |

4개를 합치면 "다양한 시간 해상도·범위·문제 유형(EDA/예측)에서 같은 분석 절차를 반복할
수 있다"는 포트폴리오의 폭이 완성된다.

## 계획 단계에서 이미 정한 것 / 앞으로 진행하며 정할 것

| 지점 | 계획 단계에서 정한 것 | 진행하며 확인해야 할 것 |
|---|---|---|
| 폴더/스크립트 규칙 | 앞 세 프로젝트와 동일하게 `scripts/NN_동작이름.py`, `outputs/{quality,eda,model}` 3분류, `worklogs/YYYY-MM-DD.md` | — |
| 데이터 취급 | `data/raw/`를 이 프로젝트만 gitignore(133MB 제한 초과) | 원본 다운로드 경로를 README에 안내(재현자가 직접 받아야 함) |
| 시간 해상도 | 분 단위 원본 → 시간 단위로 집계해서 분석·예측(잠정) | EDA에서 분 단위 노이즈가 실제로 얼마나 큰지 확인한 뒤 최종 확정, 일 단위도 검토 |
| 결측 처리 | 82일치 통째 결측 — 날짜 목록 뽑아서 제거 또는 보간 결정 | 결측일이 특정 계절에 몰려 있으면 단순 제거가 계절성 학습에 영향 줄 수 있어 주의 |
| 모델 비교 구조 | `baseline(평균+persistence) → 랜덤포레스트 → XGBoost` 3종, 튜닝은 이전 프로젝트들처럼 필요성 낮으면 생략 | — |

## 예상 스크립트 순서 (확정 아님, 진행하며 번호·내용 조정 — 매 단계 승인 받고 진행)

- `01_load_data.py` — 원본 로딩(세미콜론 구분, 결측 `?` 처리), 컬럼 구조·기간·결측 확인
- `02_aggregate_hourly.py` — 분 단위 → 시간 단위 집계(EDA 결과로 최종 해상도 확정)
- `03_data_quality_check.py` — 결측치·중복값·기초 통계 → `outputs/quality/`
- `04~06_eda_*.py` — 시간대별 패턴, 요일·계절 패턴, 가전 카테고리별 비중 → `outputs/eda/`
- `07_build_next_period_target.py` — 다음 시점 타깃 생성, 누수 검증
- `08_train_test_split.py` — 기준선(평균값+persistence) 계산 + 분할
- `09~11_*_regression.py` — 선형회귀/랜덤포레스트/XGBoost 회귀 비교
- `12_model_comparison_chart.py`

## 재현 가능성을 지키려고 정한 것

- 원본 데이터(`data/raw/`, `data/preprocessed/`)는 어떤 스크립트도 고치지 않고 읽기만 한다.
- 표 형식 결과는 CSV로 저장해 값 비교·diff가 쉽게 한다.
- 원본이 gitignore 대상이므로, README에 "다시 돌려보려면" 절에 UCI 다운로드 링크와
  배치 경로를 명확히 안내한다 — 그래야 다른 사람이 이 저장소를 클론해도 재현할 수 있다.
