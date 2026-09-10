# 💸 글로벌 ETF 큐레이션

<!-- implementation:start -->
## 현재 팀 구현

**계산·화면 연결** · 가격 기준 2026-09-08. 월급형 (Monthly Paycheck) / 초고배당 커버드콜·YieldMax (⚠️ 양날의 검) / 배당성장 귀족 (Dividend Growth) / 채권·현금 인컴 사다리 (Fixed Income Ladder) / 자산군 벨웨더 (One per Asset Class) / 파괴적 혁신 테마 (Disruption) / 국가 원픽 (Country Single-Play) / 팩터·스마트베타 (Smart Beta) / 레버리지·인버스 (Turbo, ⚠️위험).

- 계산 코드: [etf_details.py](../../pipeline/etf_details.py)
- 화면: [research-dashboard.js](../../docs/research-dashboard.js) · [계산 결과](../../docs/data/etfmon.json)
- 계산/자료 계약: 9분류의 1M·3M·YTD·1Y 수익률은 분배금 조정종가(USD) 기준입니다. 분배율은 최근 12개월 관측 현금분배 합계/시장 종가이며 운용사의 NAV 기준 분배율·SEC 수익률과 다릅니다. 월 금액은 세전 단순 월평균으로, 미래 지급액이나 실제 원화 투자성과가 아닙니다. 관측 날짜는 배당락일이며 지급일이 아닙니다.
- 남은 범위: 주기는 최근 배당락일 간격에서 계산한 관측 분류입니다. 세금·환전비용·향후 지급일·원금 반환 비중은 별도 원천이 필요합니다.

연결된 하위 그룹: 월급형 (Monthly Paycheck), 초고배당 커버드콜·YieldMax (⚠️ 양날의 검), 배당성장 귀족 (Dividend Growth), 채권·현금 인컴 사다리 (Fixed Income Ladder), 자산군 벨웨더 (One per Asset Class), 파괴적 혁신 테마 (Disruption), 국가 원픽 (Country Single-Play), 팩터·스마트베타 (Smart Beta), 레버리지·인버스 (Turbo, ⚠️위험).

[공식 분류·단위·날짜](../DATA_DEFINITIONS.md) · [차트 대응표](../CHART_PARITY.md) · [재계산 및 검사](../../README.md)

아래는 원본을 학습하며 작성한 설계 가이드다. 초기의 “필요/미확인” 표현은 위 현재 구현 상태를 우선해 읽는다.
<!-- implementation:end -->

현금흐름 방식과 테마·자산군으로 ETF를 분류하고 총수익과 배당을 함께 비교한다.

## 구현 순서

1. etf_cats, invest_krw, fx를 읽어 카테고리별 테이블을 만든다.
2. 원문 기준 배당률=최근12개월 지급액/현재가, 월 인컴=투자금×연 배당률/12, 총수익은 수정주가 재투자 근사다.
3. 배당주기·커버드콜·레버리지/인버스 특성을 각 종목 라벨에 보존한다.

## 검증 과제

- 연 환산 월 인컴과 실제 지급액 구분
- % 단위 100배 변환·환율 적용 검증
- 배당 중복·분할·특별배당 처리

## 확인이 더 필요한 부분

세금·수수료·환헤지는 공개 비교 수치에 모두 반영된 것으로 가정하지 않는다.

[전체 화면 목록](../MODULES.md)
