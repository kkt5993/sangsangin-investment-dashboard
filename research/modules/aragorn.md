# ARAGORN MAP

<!-- implementation:start -->
## 현재 팀 구현

**부분 구현** · 가격 기준 2026-09-08. 종합.

- 계산 코드: [platform_modules.py](../../pipeline/platform_modules.py)
- 화면: [research-dashboard.js](../../docs/research-dashboard.js) · [계산 결과](../../docs/data/aragorn.json)
- 계산/자료 계약: 회전·선택 가능한 3D 관계 지도와 연간 수익률 퀼트를 구현했습니다. 관계는 KRX·미국 GICS 시장/업종 소속이라는 확인 가능한 사실만 연결합니다. 퀼트는 전년 말 대비 배당 조정종가이며 마지막 연도는 YTD입니다.
- 남은 범위: 원본의 매크로 인과 그래프 생성기가 없어 소속 관계를 인과관계로 표시하지 않습니다.

연결된 하위 그룹: 공통.

[공식 분류·단위·날짜](../DATA_DEFINITIONS.md) · [차트 대응표](../CHART_PARITY.md) · [재계산 및 검사](../../README.md)

아래는 원본을 학습하며 작성한 설계 가이드다. 초기의 “필요/미확인” 표현은 위 현재 구현 상태를 우선해 읽는다.
<!-- implementation:end -->









주간 시장의 개념 지식그래프를 3D로 보고 하단에서 자산군 연간 수익률 퀼트를 비교한다.

## 구현 순서

1. aragorn.json nodes/links와 미리 계산된 좌표를 Canvas에 투영해 회전·줌·선택을 구현한다.
2. 소스 주석은 builder/aragorn.py에서 networkx의 3D force-directed와 중심성을 계산한다고 설명한다. 팀 builder에서 노드·관계·레이아웃을 생성한다.
3. quilt.json years/assets/cols로 연도별 총수익 순위를 정렬하고 자산별 고정색을 부여한다.

## 검증 과제

- 링크가 실제 노드를 참조하는지 검사
- 연도별 총수익과 YTD를 구별
- 그래프 중요도와 투자 성과를 구분

## 확인이 더 필요한 부분

관계 생성 및 해석 문장 생성의 전체 builder 코드는 확보되지 않았다.

[전체 화면 목록](../MODULES.md)
