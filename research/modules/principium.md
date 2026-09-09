# PRINCIPIUM

<!-- implementation:start -->
## 현재 팀 구현

**부분 구현** · 가격 기준 2026-09-08. 리서치 아카이브.

- 계산 코드: [platform_modules.py](../../pipeline/platform_modules.py)
- 화면: [research-dashboard.js](../../docs/research-dashboard.js) · [계산 결과](../../docs/data/principium.json)
- 계산/자료 계약: 논문·리포트·프라이머를 제목/메타·핵심·아이디어·근거·시사점의5단으로 열람하고 등록·수정합니다. 제목 노드의 공유 키워드 관계와 빈도 구체를 문서에서 계산합니다. 초기 공개 콘텐츠는 팀 구현 노트이며 새 글·첨부는 이 브라우저의 로컬 자료입니다.
- 남은 범위: 원본 기관 보고서·개인 아카이브는 복제하지 않습니다. 현재 첨부는 PDF/래스터 이미지 보관·다운로드이며 자동 추출·LLM 요약은 미연결입니다. / 이 브라우저의 IndexedDB에 저장합니다. 팀 공용 DB·서버 인증/공개 배포·서버 조회 통계는 추가 구현 대상입니다.

연결된 하위 그룹: 리서치 아카이브.

[공식 분류·단위·날짜](../DATA_DEFINITIONS.md) · [차트 대응표](../CHART_PARITY.md) · [재계산 및 검사](../../README.md)

아래는 원본을 학습하며 작성한 설계 가이드다. 초기의 “필요/미확인” 표현은 위 현재 구현 상태를 우선해 읽는다.
<!-- implementation:end -->

논문(article)·기관보고서(report)·프라이머(primer)의 공개 요약 아카이브. 관리자 쓰기 기능은 인증이 필요하다.

## 구현 순서

1. slug를 키로 title/date/source/author/org와 core/ideas/evidence/action_plan/keywords를 표시한다.
2. kind 필터·검색·항목 펼치기·키워드 구름·공동 키워드 연결을 구현한다.
3. 팀 자료를 같은 스키마로 요약하는 파이프라인은 파일 파싱→메타데이터→근거를 보존한 구조화 요약→검수→JSON 발행 순서로 새로 만든다.
4. 서버 /auth·/upload·/update·/delete와 조회수 /views·/view는 프런트에서 계약만 확인했다. 팀 구현 시 서버 권한 검사를 필수로 둔다.

## 검증 과제

- slug 중복·kind 정규화
- 요약의 수치와 원문 근거 일치
- 관리자 인증을 브라우저 플래그에만 의존하지 않는지 검증

## 확인이 더 필요한 부분

요약 생성 프롬프트·서버 코드는 없다. 원문 PDF·숨김 PDF·방문자 기록은 수집하지 않았다.

[전체 화면 목록](../MODULES.md)
