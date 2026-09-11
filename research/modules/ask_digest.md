# 시장 요약

<!-- implementation:start -->
## 현재 팀 구현

**부분 구현** · 가격 기준 2026-09-10. 시장 브리프 / 기간별 추세 / 테마 관찰 / 종목 관찰 / 크로스에셋 / 위험 요약 / 핵심 차트 / 모듈 요약 / 최근 뉴스 / 질문·근거 기록.

- 계산 코드: [platform_modules.py](../../pipeline/platform_modules.py) · [subview_modules.py](../../pipeline/subview_modules.py) · [public_assets.py](../../pipeline/public_assets.py) · [pdf-text.js](../../docs/pdf-text.js) · [pdf-ocr.js](../../docs/pdf-ocr.js) · [notebook-pdf.js](../../docs/notebook-pdf.js) · [research-store.js](../../docs/research-store.js)
- 화면: [research-dashboard.js](../../docs/research-dashboard.js) · [계산 결과](../../docs/data/ask_digest.json)
- 계산/자료 계약: ASK의 brief/기간별 추세/10테마/16종목/21자산/위험 양음/4핵심 차트/모듈별 요약 구조에 독립 계산값을 연결합니다. 테마 구성·사업 근거와 KRX/GICS 공식 산업분류는 구분합니다. 수익률은 조정가격, 핵심 차트의 비율은 비조정 종가 기준입니다. 선물은 근월물 가격 변화이며 롤 투자 성과가 아닙니다. 각 자산 현지 호가/통화 기준이며 원화환산하지 않습니다. 수치 기반 규칙 요약은 정기 수집 후 자동 재생성됩니다.
- 남은 범위: 테마는 공식 사업 설명으로 구성한1~2기업 표본이며 전체 테마 수익률·사업 매출 순도·원본 heat 모델이 아닙니다. 현재 목록으로 과거 수익을 관찰하며 역사 편입 시점 성과가 아닙니다. / 구루 보유·전체 기업 뉴스 관심량·원본 LLM 해석은 미연결입니다. 표시한 RSS 제목 표본의 명시적 종목명 일치만 집계합니다. / 정적 사이트에는 자동 AI 질의 서버가 없습니다. 개인 질문·근거·첨부는 브라우저 로컬 기록에 저장합니다.

연결된 하위 그룹: 시장 브리프, 기간별 추세, 테마 관찰, 종목 관찰, 크로스에셋, 위험 요약, 핵심 차트, 모듈 요약, 최근 뉴스, 질문·근거 기록.

[공식 분류·단위·날짜](../DATA_DEFINITIONS.md) · [차트 대응표](../CHART_PARITY.md) · [재계산 및 검사](../../README.md)

아래는 원본을 학습하며 작성한 설계 가이드다. 초기의 “필요/미확인” 표현은 위 현재 구현 상태를 우선해 읽는다.
<!-- implementation:end -->

시장 요약이 참고할 사이트 데이터 요약. 현재 index.json에 포함되어 ETC 탭에도 노출된다.

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
