# MAXIMUS

<!-- implementation:start -->
## 현재 팀 구현

**부분 구현** · 가격 기준 2026-09-08. 지수 · S&P500 / 지수 · KOSPI / 지수 · NASDAQ / 종목 · NVIDIA / 종목 · Microsoft / 종목 · Apple / 종목 · Alphabet / 종목 · Amazon / 종목 · Meta / 종목 · Broadcom / 종목 · Tesla / 종목 · Netflix / 종목 · 삼성전자 / 종목 · SK하이닉스 / 종목 · 삼성바이오로직스 / 종목 · 현대차 / 매크로 · 미국 10Y 금리 변화 / 매크로 · CPI MoM.

- 계산 코드: [maximus_model.py](../../pipeline/maximus_model.py) · [ml_models.py](../../pipeline/ml_models.py)
- 화면: [research-dashboard.js](../../docs/research-dashboard.js) · [계산 결과](../../docs/data/maximus.json)
- 계산/자료 계약: 지수·매크로·15개 입력 후보 종목의 캐시 예측 콘솔입니다. 3개 전문가(Ridge·BayesianRidge·ExtraTrees), 만기가 끝난 최근 24개 OOS 오류의 역 MSE 75%와 동일가중 25%로 게이트를 계산합니다. 전문가별 가중치와 실제 결과를 표시합니다. 미관측 타깃은 비워 둡니다.
- 남은 범위: 원본 10-expert MoE·SIS·ADF 파이프라인과 다른 명시적 기준모형입니다. 원본 모델을 실행했다고 표시하지 않습니다. / GitHub Pages에서 Python 재학습·임의 종목 서버 요청은 실행하지 않습니다. 로컬 명령으로 캐시를 갱신합니다.

연결된 하위 그룹: 지수 · S&P500, 지수 · KOSPI, 지수 · NASDAQ, 종목 · NVIDIA, 종목 · Microsoft, 종목 · Apple, 종목 · Alphabet, 종목 · Amazon, 종목 · Meta, 종목 · Broadcom, 종목 · Tesla, 종목 · Netflix, 종목 · 삼성전자, 종목 · SK하이닉스, 종목 · 삼성바이오로직스, 종목 · 현대차, 매크로 · 미국 10Y 금리 변화, 매크로 · CPI MoM.

[공식 분류·단위·날짜](../DATA_DEFINITIONS.md) · [차트 대응표](../CHART_PARITY.md) · [재계산 및 검사](../../README.md)

아래는 원본을 학습하며 작성한 설계 가이드다. 초기의 “필요/미확인” 표현은 위 현재 구현 상태를 우선해 읽는다.
<!-- implementation:end -->



지수·매크로·입력 종목의 1개월 예측을 수행하는 MoE 콘솔. 공개 캐시 결과와 실계산 서버가 분리되어 있다.

## 구현 순서

1. data/maximus.json의 modes.idx/macro/stock을 읽어 targets, features_report, 전문가 가중치, 예측 범위와 결과 차트를 먼저 재현한다.
2. 원문 method에는 ADF 정상화→훈련창 SIS 30~50개 선택+코어 피처→10 experts→soft gate→예측·잔차 밴드 흐름이 설명되어 있다. 이 절차를 Python에서 따로 구현해야 한다.
3. 게이트 설명은 다항 로지스틱 25%와 성능 프라이어 75%, 전문가 예측 ±2.5σ 제한, 붕괴 오버라이드가 포함된다. 자세한 원문은 데이터 문서를 확인한다.
4. 온라인 실행은 POST /maximus/run, GET /maximus/status를 통해 진행률을 표시한다. 학습용 사본에서는 캐시만 사용한다.

## 검증 과제

- 금리 수준·수익률·CPI MoM/YoY의 단위와 타깃 정의 일치
- 공시 filed 날짜와 가격 스플릿 정렬
- SIS·표준화·HP 필터·게이트 학습이 각 훈련창 안에서만 수행되는지 검증
- 최종 홀드아웃을 모델 선택·게이트 선택과 분리; 등가중·단일모델·추세 벤치 비교

## 확인이 더 필요한 부분

실제 Python 모델 코드와 가중치·학습 데이터는 미공개. OOS나 룩어헤드 차단이라는 설명만으로 검증 완료라고 판단할 수 없다. 실계산 버튼은 누르지 않았다.

[전체 화면 목록](../MODULES.md)
