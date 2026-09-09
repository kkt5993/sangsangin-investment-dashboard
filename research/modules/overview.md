# Summary

전체 모듈을 국면→주도→맥락→기회 순서로 요약하는 첫 화면. 별도의 예측 엔진이 아니라 모듈 스냅샷을 조합하는 진입점이다.

## 구현 순서

1. data/index.json의 modules를 읽고 각 module.json을 연결한다. 현재 코드는 Promise.all로 전 모듈을 최초 로딩한다.
2. narrative·주간 연대기, DRAGONGLASS 요약, keycharts, Tesseract, crowding을 읽고 4개 PILLARS별 카드를 만든다.
3. 카드 클릭을 mod-{module} 해시와 연결하고 as_of와 전체 generated_at을 구분해 표시한다.
4. Canvas 장식은 cosmos/holo/aragorn에, 정보 렌더링은 app.js에 분리한다.

## 검증 과제

- index의 모든 모듈이 메뉴와 상세 화면에 연결되는지 검사
- 보조 데이터가 없을 때 전체 Summary가 사라지지 않는지 확인
- 서로 다른 모듈 기준일과 하위 모델 기준일을 별도로 표시

## 확인이 더 필요한 부분

Summary 문장은 저장된 시점의 관찰값이다. 현재 시장에 대한 독립 검증은 이 작업 범위에 포함하지 않았다.

[전체 화면 목록](../MODULES.md)
