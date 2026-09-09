# At a Glance

설계 철학, 모듈 설명, 자동 운영, 데이터 소스, 학술적 배경을 한곳에 정리한 안내 화면.

## 구현 순서

1. glance.js의 PILLARS·CROSS·STACK·SCREENS·APIS·SCHED_CHIPS를 설명 콘텐츠로 옮긴다.
2. SVG로 4단 투자 프로세스와 수집→Python builder→GitHub→Cloudflare Pages 운영 흐름을 그린다.
3. 운영 일정은 원문의 macmini launchd 기준이다. Windows에서는 같은 의존성을 가진 작업 스케줄러나 수동 CLI로 구현할 수 있다. 이번 작업에서 스케줄은 등록하지 않았다.
4. 실제 메뉴는 app.js와 index.json에서 생성되므로 SCREENS를 그대로 메뉴 명세로 삼지 말고 실제 메뉴와 대조한다.

## 검증 과제

- 현재 메뉴와 안내 목록의 불일치 검사
- 데이터 제공처·프록시·유료 옵션을 구분
- 이론의 존재와 이 사이트 모델의 성능 검증을 구분

## 확인이 더 필요한 부분

설계 안내가 계산 코드 전체는 아니다. Python builder, 캐시, 환경설정, 학습 산출물, 운영 서버는 공개 프런트에서 복원할 수 없다.

[전체 화면 목록](../MODULES.md)
