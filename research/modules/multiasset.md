# 멀티에셋 모니터링

<!-- implementation:start -->
## 현재 팀 구현

**부분 구현** · 가격 기준 2026-09-08. 자산 모니터 / 패턴 스캐너 / 자산배분.

- 계산 코드: [market_modules.py](../../pipeline/market_modules.py) · [subview_modules.py](../../pipeline/subview_modules.py)
- 화면: [research-dashboard.js](../../docs/research-dashboard.js) · [계산 결과](../../docs/data/multiasset.json)
- 계산/자료 계약: 21자산 수익률·37자산 스캐너를 계산합니다. FX는 표시 환율의 변화율, 선물은 제공처 연속선물 가격입니다. 자산배분은 월 리밸런싱 역변동성 기준모형(63일, 편도 5bp)입니다.
- 남은 범위: 원본의 ML 자산배분 모델·가중치가 없어 기준모형을 구분해 제공합니다.

연결된 하위 그룹: 자산 모니터, 패턴 스캐너, 자산배분.

[공식 분류·단위·날짜](../DATA_DEFINITIONS.md) · [차트 대응표](../CHART_PARITY.md) · [재계산 및 검사](../../README.md)

아래는 원본을 학습하며 작성한 설계 가이드다. 초기의 “필요/미확인” 표현은 위 현재 구현 상태를 우선해 읽는다.
<!-- implementation:end -->







21개 자산 모니터, ML 국면 배분, 기술적 시그널 스캐너를 결합한 화면.

## 구현 순서

1. 수익률·로테이션용 공통 table/bars/charts를 만든다.
2. alloc.weights/stats/bt/group_history로 현재 비중·과거 성과·그룹 이력을 구현한다. alloc의 as_of는 부모 스냅샷과 다를 수 있다.
3. scanner.items에 OHLC·패턴·지표를 저장하고 signalscan.js로 12지표·패턴 분류·캔들 화면을 만든다.
4. allocHTML의 방법 설명과 데이터에 있는 note/method를 구현 명세로 사용한다.

## 검증 과제

- 비중 합계·현금·상한·반올림
- 월별 리밸런스 신호 시점과 익월 수익률 정렬
- 고정 현재비중 위험 추정과 전략 과거 비중 백테스트 구분

## 확인이 더 필요한 부분

배분 최적화·유니버스·학습 및 검증 전체 코드는 미공개. 현재 데이터에서는 alloc 기준일이 부모보다 오래되어 신선도 검사가 필요하다.

[전체 화면 목록](../MODULES.md)
