# ML·DL 지수예측 (KOSPI·NASDAQ·S&P)

<!-- implementation:start -->
## 현재 팀 구현

**부분 구현** · 가격 기준 2026-09-10. 전망 요약 / KOSPI · 1M / KOSPI · 3M / NASDAQ · 1M / NASDAQ · 3M / S&P500 · 1M / S&P500 · 3M / 모델 비교 / SHAP 해석 / 변수 선택.

- 계산 코드: [ml_models.py](../../pipeline/ml_models.py) · [ml_features.py](../../pipeline/ml_features.py) · [ml_ensemble.py](../../pipeline/ml_ensemble.py) · [ml_transformer.py](../../pipeline/ml_transformer.py) · [ml_views.py](../../pipeline/ml_views.py)
- 화면: [research-dashboard.js](../../docs/research-dashboard.js) · [계산 결과](../../docs/data/ml.json)
- 계산/자료 계약: 월별 거시·시장 입력을 사용한 회귀 전망입니다. 선형·트리·거리·신경망 모델 및 평균/중앙값 앙상블을 과거 평가만으로 선택합니다. 3M은3개월 누적 수익률이며 학습·오차 보정·모델 선택에서 만기를 기다립니다. 68/90% 구간은 과거 선택 모델의 OOS 잔차 분위, P상승은 예측/잔차표준편차의 정규 누적확률이며 보장된 빈도가 아닙니다. 거시는2개월 시차의 현재 수정 빈티지입니다. 방향전략은 월말 가정 체결·편도5bp, 실제 배포 시점과 체결을 복원한 성과가 아닙니다.
- 남은 범위: 원본 전체 하이퍼파라미터·선택 주기 설정과 수치 동등성은 미검증입니다. 과거 발표/수정 빈티지와 과거 모형 설계를 복원한 PIT 실시간 성과가 아닙니다. / ICE 신용스프레드는 공개자료가 최근3년으로 제한되어 장기 z-score·일부 강제 위험 입력의 준비 기간이 부족합니다. 제외된 입력을 진단에 표시합니다. / 추가 원자료가 필요한 블록: Shiller CAPE/ERP, SF Fed news sentiment, global monthly EPU, VIX9D/VIX short-term structure, historical foreign investor net flows. / TreeSHAP는 별도 LightGBM 학습표본 해석이며 당시 선택 모델의 OOS 기여도·경제적 인과 효과가 아닙니다. US 변수 선택 패널은 S&P500 대표이며 Nasdaq은 별도 선택합니다.

연결된 하위 그룹: 전망 요약, KOSPI · 1M, KOSPI · 3M, NASDAQ · 1M, NASDAQ · 3M, S&P500 · 1M, S&P500 · 3M, 모델 비교, SHAP 해석, 변수 선택.

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
