# 멀티에셋 모니터링

<!-- implementation:start -->
## 현재 팀 구현

**부분 구현** · 가격 기준 2026-09-08. 자산 모니터 / 패턴 스캐너 / 자산배분.

- 계산 코드: [market_modules.py](../../pipeline/market_modules.py) · [subview_modules.py](../../pipeline/subview_modules.py) · [asset_monitor.py](../../pipeline/asset_monitor.py) · [allocation_model.py](../../pipeline/allocation_model.py) · [allocation_views.py](../../pipeline/allocation_views.py) · [technical_scan.py](../../pipeline/technical_scan.py) · [oecd_data.py](../../pipeline/oecd_data.py)
- 화면: [research-dashboard.js](../../docs/research-dashboard.js) · [계산 결과](../../docs/data/multiasset.json)
- 계산/자료 계약: 자산 모니터는 실제 S&P500·Nasdaq Composite·Russell2000 지수와 금 선물을 포함한21자산을 비교합니다. YTD는 원본과 같은 연초 첫 종가 대비이며, 아래 ETF 배분 모형과 구분합니다. 33개 대표 ETF·BTC의 USD 배분을 기존 자산·스캐너에 추가했습니다. 74개 팀 피처의 월별 Boruta, 3개 회귀 앙상블, 분류·Markov·LSTM 리스크온, 4개 경기국면을 독립 계산합니다. 성장=OECD 미국 선행지수의3개월 변화, 물가=CPI YoY의3개월 변화. 거시 입력·국면 학습은2개월 시차이며 최신 수정 빈티지입니다. 자산별 μ는 대표자산 예측×36개월 Beta(최소24개월); FXE/FXY도 달러 대표 ETF에 대한 실제 Beta로 부호를 정합니다. 비중은 역변동성×수축 틸트(0.5, λ1.1), Ledoit-Wolf 공분산·그룹/종목 상한·연10%변동성 타깃, 현금은BIL입니다. 최근96개 적용월(현재 월은 가격 기준일까지)의 배분을 비교합니다. 월말 정보로 다음 첫 거래일 종가에 리밸런싱하고 다음날부터 새 비중 수익률을 적용하며 총 절대 비중 변화에10bp를 차감합니다. BTC는 미국 종가 시점 이미 종료된 전날UTC봉입니다.
- 남은 범위: 원본의 모든 하이퍼파라미터·74개 입력명·그룹별 상한은 공개되지 않아 팀 설정을 명시했습니다. 원본 수치와 동일하다는 주장이 아닙니다. / OECD 미국·한국·일본·중국 선행지수는 공식 API의 진폭 조정 지수(장기 평균100)입니다. OECD 전체 집계는 미확보입니다. Boruta 미확정/순위 대체와 Markov 추정 불가를 진단에 표시합니다. / 과거 발표·개정 빈티지를 복원한 PIT 성과가 아니며 사후 설계 OOS입니다. 두 모델의 방향 정합은 측정된 신뢰도·성공확률 증가를 의미하지 않습니다. / 자산 모니터: 원본의 50/200MA 신호 세부 조건은 미공개이므로 팀 정배열/역배열을 명시했습니다. 원본 장중/시장별 기준시각과 완료 종가 사이 차이가 있으며 과거 수치의 완전 동일성을 주장하지 않습니다.

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
