# 🏠 가정용 전력 사용량 예측

**상태: 스캐폴딩 완료, 데이터 배치 완료, 분석 시작 전.** 이 파일은 진행되는 대로 갱신한다.

포트폴리오 4번째 프로젝트. [`seoul-rainfall-prediction`](../seoul-rainfall-prediction)·
[`seoul-subway-demand-forecast`](../seoul-subway-demand-forecast)(예측 중심)·
[`korea-power-consumption-analysis`](../korea-power-consumption-analysis)(전국 단위 EDA
중심, 12개월치)에 이어, 이번엔 **가정 1채의 4년치 분 단위 시계열**로 다시 "예측"이
핵심인 프로젝트를 진행한다.

## 풀려는 문제

**핵심 질문**: 이 가정의 전력 사용량은 언제 늘어나고, 무엇이 그 사용량을 만드는가?
그리고 다음 시점의 사용량을 예측할 수 있는가?

1. 하루 중 언제 전력 사용량이 가장 많은가?
2. 요일별(평일/주말)·계절별(여름/겨울) 패턴은 어떻게 다른가?
3. 가전 카테고리(주방/세탁실/온수기+에어컨) 중 무엇이 전체 사용량을 가장 많이 설명하는가?
4. 서브미터링 3종의 합이 전체 사용량을 얼마나 설명하는가?
5. **다음 시점 전력 사용량을 예측할 수 있는가?** (이 프로젝트의 핵심)

자세한 문제 정의는 [`docs/problem-definition.md`](./docs/problem-definition.md), 진행 계획은
[`docs/CLAUDE_CODE_WORKFLOW.md`](./docs/CLAUDE_CODE_WORKFLOW.md) 참고.

## 데이터

UCI Machine Learning Repository의 "Individual household electric power consumption
Data Set" — 프랑스 가정 1채, 2006-12-16~2010-11-26(약 4년), 분 단위 2,075,259행.
**원본이 133MB로 GitHub 100MB 제한을 넘어 이 저장소엔 커밋하지 않는다**
(`data/raw/`가 `.gitignore` 처리돼 있음) — 재현 방법은 아래 "다시 돌려보려면" 참고.

## 다음 할 일

- [ ] `01_load_data.py`부터 시작 — 세미콜론 구분 로딩, 결측(`?`) 확인

## 폴더 구조

```
household-power-consumption-forecast/
├── README.md                  # 이 파일
├── REPORT.md                  # 상세 분석 리포트 (분석 진행 후 작성)
├── CLAUDE.md                  # 이 프로젝트의 작업 규칙 (gitignore, 로컬 전용)
├── LICENSE
├── requirements.txt
├── data/
│   ├── raw/                   # 원본 데이터 (133MB, gitignore — 로컬에만 존재)
│   └── preprocessed/          # 시간 단위 집계 등 (커밋 대상)
├── scripts/                   # 01부터 순서대로 (아직 비어 있음)
├── outputs/
│   ├── quality/                # 결측치·중복·데이터사전
│   ├── eda/                    # 시간대·요일·계절·가전별 비교
│   └── model/                  # 성능지표·중요도·비교차트
├── docs/
│   ├── problem-definition.md   # 문제 정의·세부 질문
│   └── CLAUDE_CODE_WORKFLOW.md # 계획 문서
└── worklogs/                   # 날짜별 작업 기록 (로컬 전용)
```

## 데이터 출처

[UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption),
"Individual household electric power consumption Data Set" (제공: Georges Hebrail,
Alice Berard — EDF R&D, France). 재현하려면 위 링크에서 원본을 내려받아
`data/raw/household_power_consumption.txt` 경로에 배치해야 한다. 라이선스는
[LICENSE](./LICENSE) 참고.
