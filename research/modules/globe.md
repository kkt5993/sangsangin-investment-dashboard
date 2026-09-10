# GLOBAL UNIVERSE

<!-- implementation:start -->
## 현재 팀 구현

**부분 구현** · 가격 기준 2026-09-08. 국가 교역 / 기업 국가 탐색 / 밸류체인 유니버스 / SAURON.

- 계산 코드: [platform_modules.py](../../pipeline/platform_modules.py) · [trade_data.py](../../pipeline/trade_data.py) · [trade_views.py](../../pipeline/trade_views.py) · [trade-views.js](../../docs/trade-views.js) · [sauron_data.py](../../pipeline/sauron_data.py) · [sauron_views.py](../../pipeline/sauron_views.py) · [sauron-views.js](../../docs/sauron-views.js)
- 화면: [research-dashboard.js](../../docs/research-dashboard.js) · [계산 결과](../../docs/data/globe.json)
- 계산/자료 계약: 국가 교역은 UN Comtrade 연간 상품 총수출(HS TOTAL)을 국가·통계지역 사이의 구면 곡선으로 표시합니다. 화살표는 수출 방향이며 선 굵기는 금액의 로그 척도입니다. 금액은 기업 매출·특정 품목이나 실제 선박 항로가 아닙니다. 모든 지역은 같은 연도이며, 비교 가능성을 위해 실행 연도보다2년 전 자료를30일마다 재확인합니다. 들어오는 선도 상대국의 수출 보고값으로, 선택국 수입 통계와 다를 수 있습니다. 기존 기업 표는 수집된 재무 표본의 소재국 탐색입니다.
- 남은 범위: UN 자료가 없는 국가·통계지역/방향은 미확보로 표시하며 거울 수입이나 추정값으로 채우지 않습니다. / SAURON의 Google 실사3D는 별도 키가 필요합니다. Wikipedia 지명은 문서 대표 좌표이며 주소 검색과 다릅니다. 지진은 PC 수집 시점의 관측이고 위성 위치는 궤도 모델 계산입니다. / 밸류체인 유니버스의53개 업종·151기업 탐색을 연결했습니다. 소재지는 공급자 프로필, 지도 점은 도시 대표 좌표입니다. 기업별 전체 공급·물류 및 경쟁우위 근거는 추가 수집 대상이며 소재국 총수출은 기업 수출이 아닙니다.

연결된 하위 그룹: 밸류체인 유니버스, 국가 교역, 기업 국가 탐색, SAURON.

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
