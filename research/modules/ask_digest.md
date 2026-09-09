# ask_digest

<!-- implementation:start -->
## 현재 팀 구현

**부분 구현** · 가격 기준 2026-09-08. 최근 뉴스 / 시장 / 방법론 / 질문·근거 기록.

- 계산 코드: [platform_modules.py](../../pipeline/platform_modules.py) · [subview_modules.py](../../pipeline/subview_modules.py)
- 화면: [research-dashboard.js](../../docs/research-dashboard.js) · [계산 결과](../../docs/data/ask_digest.json)
- 계산/자료 계약: 시장 수치·근거 원문과 질문/답변 메모를 구분합니다. 질문·내 해석·참조 근거·추가 확인을 기록하고 PDF·이미지를 첨부할 수 있습니다. 기록은 이 브라우저에만 보관하며 자동 AI 답변으로 표시하지 않습니다.
- 남은 범위: 원본 brief/기간별 추세·테마·종목·모듈별 위험 집계는 추가 구현 대상입니다. 외부 ASK 토론·원본 자동 AI 질의 서버와 연결하지 않았습니다. / 기록·첨부는 브라우저 로컬이며 팀 공용 저장·자동 LLM 요약은 미연결입니다.

연결된 하위 그룹: 최근 뉴스, 시장, 방법론, 질문·근거 기록.

[공식 분류·단위·날짜](../DATA_DEFINITIONS.md) · [차트 대응표](../CHART_PARITY.md) · [재계산 및 검사](../../README.md)

아래는 원본을 학습하며 작성한 설계 가이드다. 초기의 “필요/미확인” 표현은 위 현재 구현 상태를 우선해 읽는다.
<!-- implementation:end -->

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
