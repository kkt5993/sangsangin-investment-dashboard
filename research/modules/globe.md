# GLOBAL UNIVERSE

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
