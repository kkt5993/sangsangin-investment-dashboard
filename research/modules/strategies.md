# 🎯 전략 스캐너 (신규 알파)

<!-- implementation:start -->
## 현재 팀 구현

**부분 구현** · 가격 기준 2026-09-08. 턴어라운드 / 내부자 매수 / PEAD / 스탯아브 페어 / 실적 모멘텀.

- 계산 코드: [financial_modules.py](../../pipeline/financial_modules.py) · [subview_modules.py](../../pipeline/subview_modules.py) · [events_data.py](../../pipeline/events_data.py) · [sec_ownership.py](../../pipeline/sec_ownership.py) · [ownership_views.py](../../pipeline/ownership_views.py) · [strategy_cards.py](../../pipeline/strategy_cards.py) · [pead.py](../../pipeline/pead.py) · [pead_data.py](../../pipeline/pead_data.py)
- 화면: [research-dashboard.js](../../docs/research-dashboard.js) · [계산 결과](../../docs/data/strategies.json)
- 계산/자료 계약: 턴어라운드는 연간3개년 이익 저점반등과 가격 조건을 검사하며, 페어는 미국9쌍·한국4쌍의 지정 목록을 비교합니다. EPS 서프라이즈와 최근 수익률은 각각 별도 열로 표시합니다. 공급자의 earnings_history 날짜는 발표일이 아니라 실적 대상 분기말입니다. 내부자 후보는 제공처 Purchase 행에서 시작하며, 클러스터에는 SEC 비파생 코드P·취득A·양의 수량/가격과 기준일 이내 접수시각을 확인한 공시만 포함합니다. P는 공개시장 또는 사적 매수여서 공개시장 매수만이라고 단정하지 않습니다. PEAD는 실제 발표 시각을 미국 동부시간으로 정렬해 첫 반응 세션(D0) 이후 5·20거래일 수익률과 SPY 대비를 계산합니다. 현재 관측 이벤트 연구이며 매매 백테스트가 아닙니다. 접수시각은 SEC 색인의 미국 동부시각 또는 API의 명시된 시간대를 UTC로 변환합니다. SEC가 문서를 처음 공개한 실제 시각은 별도 없으므로 접수 기반 가격 관측은 참고이며 체결 백테스트가 아닙니다. 정정공시는 자동 합산하지 않습니다. PEAD 카드의 표시구간 변화는 발표5달력일 전부터이며 D0 이후 수익과 분리합니다.
- 남은 범위: SEC 연속 자동수집은 PC HTTP 접근 상태에 따라 제한됩니다. 현재 원문 대조 표본과 미확인 후보를 구분하며 전체 미국 시장의 모든 내부자 거래를 의미하지 않습니다. Form4/A 정정 대조·13F·전략별 비용 후 OOS는 후속 대상입니다. / 전략 카드: 턴어라운드 사전표본·가격 절단·점수의 정확한 원본 임계치는 미공개로 팀 기준을 표시합니다. 재무 표본 확대·발표 당시 빈티지, 공적분의 전체 가정/다중검정과 비용 후 OOS는 남아 있습니다. / PEAD 카드: 원본 사전표본·기간/임계치의 비공개 설정, 제공처 발표시각의 발행사 전수 대조와 발표 당시 컨센서스 빈티지·비용 후 성과는 남아 있습니다.

연결된 하위 그룹: 턴어라운드, 실적 모멘텀, 내부자 매수, 스탯아브 페어, PEAD.

[공식 분류·단위·날짜](../DATA_DEFINITIONS.md) · [차트 대응표](../CHART_PARITY.md) · [재계산 및 검사](../../README.md)

아래는 원본을 학습하며 작성한 설계 가이드다. 초기의 “필요/미확인” 표현은 위 현재 구현 상태를 우선해 읽는다.
<!-- implementation:end -->

턴어라운드·기관/스마트머니·PEAD·상대가치 등 신규 알파 후보의 룰 기반 스캐너.

## 구현 순서

1. strategies 객체의 실제 하위 키를 독립 전략 출력으로 나눈다.
2. app.js strategiesHTML에 있는 전략별 설명·필터·출력 열을 읽고 동일한 입력 JSON을 만든다.
3. 점수와 근거를 함께 저장하고 전략별 후보를 분리해 표시한다.

## 검증 과제

- 실적·13F 등 정보의 발표일 지연 반영
- 전략별 단위·유니버스·후보 수 확인
- 후보 점수를 실현 알파로 표현하지 않기

## 확인이 더 필요한 부분

선별기 코드·시점별 유니버스·거래비용 포함 검증 결과는 미공개다.

[전체 화면 목록](../MODULES.md)
