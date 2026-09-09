# GLOBAL UNIVERSE

<!-- implementation:start -->
## 현재 팀 구현

**부분 구현** · 가격 기준 2026-09-08. 종합.

- 계산 코드: [platform_modules.py](../../pipeline/platform_modules.py)
- 화면: [research-dashboard.js](../../docs/research-dashboard.js) · [계산 결과](../../docs/data/globe.json)
- 계산/자료 계약: 정사영 지구본을 회전하며 국가와 기업을 탐색합니다. 기업 소재국은 수집된 공급자 메타데이터, 업종은 공개 카탈로그·공식 시장분류입니다. 지도 점은 국가 집계 위치이며 본사 좌표가 아닙니다.
- 남은 범위: UN Comtrade 품목·교역량·물류 경로를 수집하지 않아 무역선이나 금액을 생성하지 않았습니다.

연결된 하위 그룹: 공통.

[공식 분류·단위·날짜](../DATA_DEFINITIONS.md) · [차트 대응표](../CHART_PARITY.md) · [재계산 및 검사](../../README.md)

아래는 원본을 학습하며 작성한 설계 가이드다. 초기의 “필요/미확인” 표현은 위 현재 구현 상태를 우선해 읽는다.
<!-- implementation:end -->







섹터별 기업과 밸류체인, 국가별 수출·물류 흐름을 지구본으로 탐색한다.

## 구현 순서

1. D3 orthographic 투영과 TopoJSON 세계지도를 결합한다. 공개 스크립트에는 d3@7, topojson-client@3, world-atlas@2 CDN 의존성이 있다.
2. universe의 cities/sectors를 기업·산업 목록과 좌표로 연결하고 routes/countries/trade를 교역선으로 표현한다.
3. 금액·기준연도·HS 분류·수출/수입 방향과 trade_src를 보존한다. 지정학적 해석과 실제 UN Comtrade 관측량을 구별한다.

## 검증 과제

- 국가코드와 좌표 매핑
- 교역 방향·금액 단위·기준연도
- 외부 지도 로딩 실패 시 표·범례·데이터 설명은 남도록 구성

## 확인이 더 필요한 부분

외부 지도 라이브러리와 지도 타일은 수집하지 않았다. UI 코드는 확보했으나 미러 빌더·교역경로 생성 코드는 미공개다.

[전체 화면 목록](../MODULES.md)
