# 멀티 위험지표 (선제위험·감마)

<!-- implementation:start -->
## 현재 팀 구현

**부분 구현** · 가격 기준 2026-09-08. 리스크 콕핏 / 신호등 US·KR / 파생·옵션 / 쏠림·신용 / CFTC 포지션.

- 계산 코드: [macro_modules.py](../../pipeline/macro_modules.py) · [option_analytics.py](../../pipeline/option_analytics.py) · [subview_modules.py](../../pipeline/subview_modules.py) · [cot_data.py](../../pipeline/cot_data.py)
- 화면: [research-dashboard.js](../../docs/research-dashboard.js) · [계산 결과](../../docs/data/risk.json)
- 계산/자료 계약: US·KR 조기경보와 변동성·신용·쏠림을 계산합니다. CSD는 21일 분산·자기상관·왜도의 최근 63일 Kendall 추세 평균을 0–100으로 바꾼 진단점수입니다. 콕핏은 표시된 고정 비중 모형 장부의 120개월 역사 위험입니다. 옵션은 3개 만기의 OI·IV로 계산한 콜 + / 풋 − 부호 가정 GEX이며 실제 딜러 보유 포지션이 아닙니다. CFTC TFF는 선물만의 주간 보고값이며 레버리지펀드는 CTA 전체와 같지 않습니다. 계약별 단위가 달라 계약 수를 자산 간 달러 익스포저처럼 합하지 않습니다.
- 남은 범위: 전체 만기 딜러 포지션 및 레버리지 ETF 실제 순유입 원장은 연결되지 않았습니다. 옵션 IV를 고정한 가격 시나리오는 변동성 곡면 변화를 반영하지 않습니다. / 원본 CSD 임계값의 예측력, 실제 포트폴리오 스트레스와 회복력은 미검증입니다.

연결된 하위 그룹: 신호등 US·KR, 파생·옵션, 쏠림·신용, 리스크 콕핏, CFTC 포지션.

[공식 분류·단위·날짜](../DATA_DEFINITIONS.md) · [차트 대응표](../CHART_PARITY.md) · [재계산 및 검사](../../README.md)

아래는 원본을 학습하며 작성한 설계 가이드다. 초기의 “필요/미확인” 표현은 위 현재 구현 상태를 우선해 읽는다.
<!-- implementation:end -->



모델북 위험, 선제 취약성, 미국 옵션 감마, 한국 ETF 리밸런싱 프록시, 쏠림을 모니터링한다.

## 구현 순서

1. 기본 위험 콕핏과 신호등·특수·파생·KOSPI·쏠림 그룹을 table/subviews로 구현한다.
2. 공개 docs의 미국 GEX는 만기 7~50일·행사가 ±15% 옵션 OI/IV에서 Black-Scholes 감마를 계산하고 딜러 콜/풋 부호를 가정해 합산한다.
3. 한국은 실제 옵션체인 대신 레버리지 ETF AUM·배율로 Σ AUM×(L²−L)×Δ 리밸런싱 추정치를 사용한다.
4. flows 및 wagdog의 존재 여부에 따라 비펀더멘탈 수급·Wag-the-Dog 서브뷰를 조건부 표시한다.

## 검증 과제

- 달러감마 단위·계약승수·지수 1% 스케일
- OI 기준일·IV 결측·만기 롤오버
- KR ETF 프록시와 실제 딜러 감마 구분
- 0~100 합성 점수를 보정된 확률과 구분

## 확인이 더 필요한 부분

딜러 포지션은 관측값이 아니라 가정. 사후 충격을 보고 추가한 취약성 룰은 별도 미래 구간 검증이 필요하다.

[전체 화면 목록](../MODULES.md)
