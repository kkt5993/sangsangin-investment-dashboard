# ML·DL 지수예측 (KOSPI·NASDAQ·S&P)

<!-- implementation:start -->
## 현재 팀 구현

**부분 구현** · 가격 기준 2026-09-08. S&P500 · 1M / S&P500 · 3M / KOSPI · 1M / KOSPI · 3M / NASDAQ · 1M / NASDAQ · 3M / 종합.

- 계산 코드: [ml_models.py](../../pipeline/ml_models.py)
- 화면: [research-dashboard.js](../../docs/research-dashboard.js) · [계산 결과](../../docs/data/ml.json)
- 계산/자료 계약: Ridge·BayesianRidge·ExtraTrees의 동일가중 기준모형입니다. 월말 가격·거시 13개 내외 변수, 최소 60개월 학습, 매월 재학습, 1M·3M 타깃 만기 이후만 학습합니다. 과거 OOS 잔차 24개 이상으로 경험적 68%·90% 구간과 상승확률을 계산합니다. 1M 방향전략은 편도 5bp입니다.
- 남은 범위: 원본의 Boruta·SHAP·LSTM·모델 선택 규칙을 복제한 모델이 아닙니다. 최종 모델의 표준화 Ridge 계수를 별도로 표시합니다. / 거시 데이터는 최신 수정 빈티지에 2개월 시차를 적용했습니다. 발표일·개정치를 복원한 point-in-time 실시간 성과는 아닙니다.

연결된 하위 그룹: S&P500 · 1M, S&P500 · 3M, KOSPI · 1M, KOSPI · 3M, NASDAQ · 1M, NASDAQ · 3M, 공통.

[공식 분류·단위·날짜](../DATA_DEFINITIONS.md) · [차트 대응표](../CHART_PARITY.md) · [재계산 및 검사](../../README.md)

아래는 원본을 학습하며 작성한 설계 가이드다. 초기의 “필요/미확인” 표현은 위 현재 구현 상태를 우선해 읽는다.
<!-- implementation:end -->










KOSPI·NASDAQ·S&P500의 1M/3M 수익률 예측 및 6타깃 컴포짓을 주기적으로 발행한다.

## 구현 순서

1. docs의 변수 사전 46행과 모델 표 11행을 입력·전처리 명세의 출발점으로 삼는다.
2. 설명상 정상화→훈련창 표준화→Boruta+강제 피처→회귀 모델/앙상블→확장창 OOS 평가→방향 확률·크기 예측 순서다.
3. regression/composite_series/regime_now와 차트 16종을 연결하고 1M/3M을 분리해 표시한다.
4. 선택 모델·피처·훈련 종료일·예측 대상일·평가 구간을 실제 실행 결과에서 자동 생성한다.

## 검증 과제

- 겹치는 3M 라벨과 학습/평가 purge·embargo
- OOS로 최고 모델을 고른 뒤 같은 OOS 성과를 보고하는 선택편향
- 리드-래그 최적화와 성과 측정 구간 분리
- 거래비용·base rate·예측확률 calibration
- 전표본 SHAP는 설명용으로 OOS 성능과 구분

## 확인이 더 필요한 부분

안내의 OOS 기간·피처 수·모델 수에 상충하는 설명이 있다. 원문에 과적합이 불가능하다는 취지의 표현이 있어도 재현 검증 사실로 채택하지 않는다.

[전체 화면 목록](../MODULES.md)
