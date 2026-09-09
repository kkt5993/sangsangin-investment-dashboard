# 실적 모멘텀 (대형주)

<!-- implementation:start -->
## 현재 팀 구현 · 2026-09-09

**부분 구현** · 가격 기준 2026-09-08. 연간 NI실적·글로벌 EPS 추정·국내 2025/26/27 NI 막대.

- 계산 코드: [financial_modules.py](../../pipeline/financial_modules.py)
- 화면: [research-dashboard.js](../../docs/research-dashboard.js) · [계산 결과](../../docs/data/earnings.json)
- 계산/자료 계약: 연간 순이익 성장률은 실제 재무제표, FY1/FY2 EPS는 Yahoo 애널리스트 추정치입니다. EPS를 현재 주식수로 곱해 순이익 컨센서스로 가장하지 않습니다. 국내 3개년 순이익은 별도 날짜의 로컬 QuantiWise 스냅샷(억원)을 사용합니다. 음수·0 분모 성장률은 —로 표시합니다.
- 남은 범위: 해외 영업이익·순이익 FY1/FY2 컨센서스는 EPS와 다른 항목이므로 동일 지표로 대체하지 않았습니다.

연결된 하위 그룹: US, KR, 공통.

[공식 분류·단위·날짜](../DATA_DEFINITIONS.md) · [차트 대응표](../CHART_PARITY.md) · [재계산 및 검사](../../README.md)

아래는 원본을 학습하며 작성한 설계 가이드다. 초기의 “필요/미확인” 표현은 위 현재 구현 상태를 우선해 읽는다.
<!-- implementation:end -->


미국·한국 대형주의 이익 성장과 가격 모멘텀, 전세계 순이익 순위 및 컨센서스 점검을 보여준다.

## 구현 순서

1. 당해/차년 추정치·직전 실적·가격 기준일을 분리 수집한다.
2. bars/heatmaps/table 외에 global_earn, estimate_verify, us_consensus를 전용 컴포넌트로 렌더링한다.
3. globalEarnHTML은 실적·당해·차년을 겹친 막대로 그리고 corrupt 표시가 있는 보정값을 별도 표시한다.

## 검증 과제

- 회계연도 FY1/FY2와 달력연도 CY 혼동 방지
- USD B·KRW 등 규모 단위 검증
- 보정 컨센서스와 제공처 원값·보정 근거 이력 저장

## 확인이 더 필요한 부분

추정치 보정의 정확한 Python 규칙 및 역사적 컨센서스 저장 방식은 확인할 수 없다.

[전체 화면 목록](../MODULES.md)
