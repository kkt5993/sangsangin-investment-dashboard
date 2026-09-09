# 플랫폼 구조

팀의 기본 구조는 데이터 수집 → Python 분석 모듈 → 버전이 있는 JSON·차트 → 정적 리서치 화면입니다.

```mermaid
flowchart LR
  A[제공처별 수집기] --> B[시점·단위 정규화]
  B --> C[분석 모듈]
  C --> D[JSON 스냅샷·차트]
  D --> E[GitHub Pages]
  C --> F[계산·모델 검증]
```

현재는 RS·모멘텀 실제 데이터 화면과 전체 탭의 구현 가이드가 공개되어 있습니다. 원형은 단일 HTML에 일반 JavaScript가 탭을 만들고 공개 JSON을 읽는 구조입니다. 팀 버전은 독립 Python 계산과 가벼운 SVG 렌더러를 사용합니다.

```text
pipeline/universe.py   종목·페어·미확인 항목
pipeline/collect.py    수동·직렬 수집, 날짜별 로컬 압축 CSV
pipeline/store.py      수집 버전·SHA256·가격 필드 선택
pipeline/analytics.py  수익률·RS·누적 초과수익, 오프라인
pipeline/build.py      공개 가능한 작은 JSON 생성
docs/data/*.json       계산 결과·시계열·기준일·범위
docs/charts.js         독립 SVG 선·막대·히트맵
docs/dashboard.js      RS·모멘텀 카드·필터·표·차트
docs/app.js            홈·가이드·경로 선택
```

원자료는 저장소 밖의 형제 `sangsangin-investment-data/`에만 저장합니다. Pages는 JSON을 탭 방문 때 한 번 읽고 필터는 메모리에서 처리합니다. 원본 사이트나 Yahoo에 브라우저 요청을 보내지 않습니다. 외부 서버·인증·자동 갱신 일정은 도입하지 않았습니다.

장기 계약은 observation_date, available_at, source, unit, revision_id를 보존하는 것입니다. 현재 가격 모듈은 관측일·수집시각·소스·날짜별 버전·파일 해시를 저장하지만 원천 데이터의 과거 실제 공개시각은 복원하지 못합니다. 이를 available_at으로 오인하지 않습니다. 전체 발행 시각과 하위 모듈 기준일을 구분하며 과거 수집본을 새 수집일의 파일로 덮어쓰지 않습니다.

실시간 모델 실행·질문 API·사용자 인증은 별도 서버가 필요한 기능입니다. GitHub Pages에는 공개 가능한 정적 결과만 배포합니다.

[전체 화면 목록](MODULES.md) · [개발 순서](ROADMAP.md)
