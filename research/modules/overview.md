# 시장 종합

<!-- implementation:start -->
## 현재 팀 구현

**계산·화면 연결** · 가격 기준 2026-09-10. 6/5축 원단위와 z·36시점 궤적/회전·4층 레이더·시총50표본/주도주10·현황.

- 계산: [overview_state.py](../../pipeline/overview_state.py) · [화면](../../docs/overview-views.js) · [결과](../../docs/data/overview_state.json)
- [축·단위·발표 시차·표본 계산 계약](../OVERVIEW_CONTRACT.md)
- 남은 범위: 원본 z 창/극단치 설정·세계 전체 시총50·역사 발표 빈티지 동등성 미확보

[공식 분류·단위·날짜](../DATA_DEFINITIONS.md) · [차트 대응표](../CHART_PARITY.md) · [재계산 및 검사](../../README.md)

아래는 원본을 학습하며 작성한 설계 가이드다. 초기의 “필요/미확인” 표현은 위 현재 구현 상태를 우선해 읽는다.
<!-- implementation:end -->

전체 모듈을 국면→주도→맥락→기회 순서로 요약하는 첫 화면. 별도의 예측 엔진이 아니라 모듈 스냅샷을 조합하는 진입점이다.

## 구현 순서

1. data/index.json의 modules를 읽고 각 module.json을 연결한다. 현재 코드는 Promise.all로 전 모듈을 최초 로딩한다.
2. narrative·주간 연대기, 기업분석 요약, keycharts, Tesseract, crowding을 읽고 4개 PILLARS별 카드를 만든다.
3. 카드 클릭을 mod-{module} 해시와 연결하고 as_of와 전체 generated_at을 구분해 표시한다.
4. Canvas 장식은 cosmos/holo/aragorn에, 정보 렌더링은 app.js에 분리한다.

## 검증 과제

- index의 모든 모듈이 메뉴와 상세 화면에 연결되는지 검사
- 보조 데이터가 없을 때 전체 Summary가 사라지지 않는지 확인
- 서로 다른 모듈 기준일과 하위 모델 기준일을 별도로 표시

## 확인이 더 필요한 부분

Summary 문장은 저장된 시점의 관찰값이다. 현재 시장에 대한 독립 검증은 이 작업 범위에 포함하지 않았다.

[전체 화면 목록](../MODULES.md)
