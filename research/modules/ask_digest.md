# ask_digest

ASK ARAGORN이 참고할 사이트 데이터 요약. 현재 index.json에 포함되어 ETC 탭에도 노출된다.

## 구현 순서

1. brief/watchlist/cross_asset/macro_risk/research_recent/modules/ontology를 공통 식별자로 묶는다.
2. ask.js의 POST /api/ask 요청은 질문을 보내고 응답을 표시한다. 실제 retrieval·모델·시스템 프롬프트는 서버 쪽이다.
3. 팀 버전은 스냅샷 기준일과 근거 ID를 답변에 포함하고 수치 계산은 검증된 함수에서 수행한다.

## 검증 과제

- 요약의 원모듈 기준일·수치 일치
- 모델의 근거 없는 수치 생성 방지
- 내부용 JSON 모듈을 실제 메뉴에 노출할지 명시 결정

## 확인이 더 필요한 부분

Cloudflare /api/ask 구현은 다운로드 가능한 프런트 소스에 포함되지 않는다. 질문 제출은 하지 않았다.

[전체 화면 목록](../MODULES.md)
