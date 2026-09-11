# 시장 변동성

<!-- implementation:start -->
## 현재 팀 구현

**부분 구현** · 가격 기준 2026-09-10. S&P500 / KOSPI / NASDAQ / NVIDIA / Microsoft / Apple / Alphabet / Amazon / Meta / Broadcom / Tesla / Netflix / Palantir / 삼성전자 / SK하이닉스 / LG에너지솔루션 / 삼성바이오로직스 / 현대차.

- 계산 코드: [market_modules.py](../../pipeline/market_modules.py) · [dynamics_model.py](../../pipeline/dynamics_model.py) · [dynamics-views.js](../../docs/dynamics-views.js) · [dynamics-export.js](../../docs/dynamics-export.js)
- 화면: [research-dashboard.js](../../docs/research-dashboard.js) · [계산 결과](../../docs/data/dynamics.json)
- 계산/자료 계약: 가격만으로 β·α·∇τ·확장창z·취약성·목표노출을 계산합니다. 전일 신호, 결측 시점, 드리프트 후 거래량과 명시적 비용 가정을 분리합니다. 지수의 노출/성과는 실제 매매상품이 아닌 가상 비교입니다.
- 남은 범위: 원본 확장창 최소표본·0분산 세부 처리/가격정정 빈티지 동등성은 미검증입니다. 팀 설정과 실제 가용 이력을 표시합니다. / 비용은 사용자가 선택하는 가정이며 실제 스프레드·차입조건·시장충격·현금이자·세금과 과거 실시간 데이터 빈티지를 재현하지 않습니다. / 결측 이후 연속 유효 구간만 성과를 비교합니다. 일부 종목은 전체22년 이력이 없으며 과거 월말 신호가 당시 발표된 투자판단이라는 보증은 없습니다.

연결된 하위 그룹: S&P500, KOSPI, NASDAQ, NVIDIA, Microsoft, Apple, Alphabet, Amazon, Meta, Broadcom, Tesla, Netflix, Palantir, 삼성전자, SK하이닉스, LG에너지솔루션, 삼성바이오로직스, 현대차.

[공식 분류·단위·날짜](../DATA_DEFINITIONS.md) · [차트 대응표](../CHART_PARITY.md) · [재계산 및 검사](../../README.md)

아래는 원본을 학습하며 작성한 설계 가이드다. 초기의 “필요/미확인” 표현은 위 현재 구현 상태를 우선해 읽는다.
<!-- implementation:end -->

가격의 추세 에너지·불안정성으로 방향이 아닌 보유 노출과 붕괴 취약성을 분석한다.

## 구현 순서

1. 설명상 22년 일간 종가와 21일 창에서 β·α·∇τ를 계산한다. docs의 핵심변수 표를 그대로 구현 계약으로 사용한다.
2. 확장창 z→로지스틱 합성 0~100→연 15% 변동성 목표×취약성 게이트→전일 신호로 익일 노출을 계산한다.
3. dynamics.indices/order의 지수별 시계열·위상공간·서피스 데이터를 app.js 전용 Canvas/SVG 렌더러로 표시한다.

## 검증 과제

- 확장창 최소표본·분산 0 처리
- 노출 시프트 1일과 거래비용
- 0~100 취약성 점수와 발생확률을 구분
- V자 반등 기회비용·Buy&Hold 성과 비교

## 확인이 더 필요한 부분

위험 합성의 전체 계수·게이트 함수·원자료 정합성은 독립 구현 때 검증해야 한다.

[전체 화면 목록](../MODULES.md)
