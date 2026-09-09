# PRINCIPIUM

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
