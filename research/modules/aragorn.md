# ARAGORN MAP

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
