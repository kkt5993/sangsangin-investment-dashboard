# 글로벌 성장주 모니터링

<!-- implementation:start -->
## 현재 팀 구현

**부분 구현** · 가격 기준 2026-09-08. FY1 / FY2 / 종합.

- 계산 코드: [financial_modules.py](../../pipeline/financial_modules.py) · [local_consensus.py](../../pipeline/local_consensus.py)
- 화면: [research-dashboard.js](../../docs/research-dashboard.js) · [계산 결과](../../docs/data/growth.json)
- 계산/자료 계약: 원본의 3D 축을 유지합니다: x=FY1/FY2 영업이익 성장, y=YTD, z=영업이익률. 국내는 KRX 대형주·KOSPI 200와 기존 로컬 컨센서스를 연결했습니다. FY1=2026, FY2=2027, 추정 빈티지는 2026-08-07. 시가총액 없는 종목은 같은 크기로 표시합니다.
- 남은 범위: 글로벌 100종목의 FY1/FY2 영업이익 컨센서스가 없어 해외 3D 점은 제외했습니다. 해외 EPS 성장률은 별도 표로 제공합니다.

연결된 하위 그룹: FY1, FY2, 공통.

[공식 분류·단위·날짜](../DATA_DEFINITIONS.md) · [차트 대응표](../CHART_PARITY.md) · [재계산 및 검사](../../README.md)

아래는 원본을 학습하며 작성한 설계 가이드다. 초기의 “필요/미확인” 표현은 위 현재 구현 상태를 우선해 읽는다.
<!-- implementation:end -->







여러 국가의 성장주를 FY1/FY2 영업이익 성장·YTD·영업이익률과 시가총액으로 비교한다.

## 구현 순서

1. companies의 국가·티커·컨센서스·성장·가격 정보를 동일 기준일로 저장한다.
2. 기본 성좌 SVG와 Plotly 3D HTML 2개를 구성한다. x=영업이익 성장, y=YTD, z=영업이익률, 색=국가, 크기=시총이다.
3. iframe HTML 안에 포함된 Plotly.newPlot의 데이터·layout을 참고해 Python Plotly로 같은 데이터 계약을 만든다.

## 검증 과제

- FY1/FY2 동일 정의·적자전환의 성장률 처리
- 국가별 통화의 시총 비교 기준
- 외부 Plotly 로딩 실패 시 표 제공

## 확인이 더 필요한 부분

성장주 모집단·스크리닝 초기 조건과 전체 컨센서스 수집 코드는 미공개다.

[전체 화면 목록](../MODULES.md)
