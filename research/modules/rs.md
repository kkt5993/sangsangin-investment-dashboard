# 주간 상대강도 (RS)

<!-- implementation:start -->
## 현재 팀 구현

**부분 구현** · 가격 기준 2026-09-08. 공식 상품 35페어·KR/US 종목 1W선별 1M막대·3유니버스 순위.

- 계산 코드: [market_modules.py](../../pipeline/market_modules.py) · [build.py](../../pipeline/build.py) · [analytics.py](../../pipeline/analytics.py) · [universe.py](../../pipeline/universe.py)
- 화면: [dashboard.js](../../docs/dashboard.js) · [계산 결과](../../docs/data/rs.json)
- 계산/자료 계약: 공식 KRX·ETF 운용사·미국 GICS 정의를 바탕으로 독립 계산합니다. 국내 종목 순위는 KRX 구성목록, 미국은 IVV 공시 주식입니다. 원본의 불명확한 종목명은 공식 상품명으로 확정해 표시하며, 비공개 원본 엔진과 수치 동등성은 미검증입니다.
- 남은 범위: 조선 신규 상장으로 5Y 준비 구간 부족, z 비공개 세부 설정 미검증

[공식 분류·단위·날짜](../DATA_DEFINITIONS.md) · [차트 대응표](../CHART_PARITY.md) · [재계산 및 검사](../../README.md)

아래는 원본을 학습하며 작성한 설계 가이드다. 초기의 “필요/미확인” 표현은 위 현재 구현 상태를 우선해 읽는다.
<!-- implementation:end -->









> 2026-09-09 구현: 실제 가격 기반 29/35 페어와 차트·히트맵·수치 표를 연결했다. 6개 페어와 대형주/오닐 순위는 미확인 항목이다. [가격 계약](../PRICE_CONTRACT.md) · [차트 대응](../CHART_PARITY.md). 아래는 전체 구현을 위한 기존 가이드다.

국내·미국 페어의 3개월 수익률 차이를 공통 5년 분포에서 z-score로 비교한다.

## 구현 순서

1. 페어와 벤치마크 유니버스를 table 및 charts에서 추출한다.
2. 원문 chart.note 기준 3M 기간수익률 스프레드를 일간 rolling z-score(5년 동일 베이스)로 만든다. 단순 가격비 z와 혼동하지 않는다.
3. +1/-1σ 강약, +2/-2σ 과열·과매도 표시와 랭킹·히트맵·페어 차트를 만든다.

## 검증 과제

- 휴장일 교집합·분배금 조정
- z-score 표준편차 정의와 최소 관측 수
- 기간수익률 차이와 가격비 변화율을 혼동하지 않았는지

## 확인이 더 필요한 부분

5년 창의 정확한 거래일 수·ddof·결측 정책은 공개 설명만으로 확정할 수 없다.

[전체 화면 목록](../MODULES.md)
