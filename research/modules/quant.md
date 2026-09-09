# Quant Hedge (Multi Quant)

<!-- implementation:start -->
## 현재 팀 구현

**부분 구현** · 가격 기준 2026-09-08. Stat Arb / 멀티팩터 / BAB / 단기반전 / TSMOM.

- 계산 코드: [quant_modules.py](../../pipeline/quant_modules.py)
- 화면: [research-dashboard.js](../../docs/research-dashboard.js) · [계산 결과](../../docs/data/quant.json)
- 계산/자료 계약: Naver 시가총액 KOSPI 상위 300·KOSDAQ 상위 150에서 우선주·SPAC·REIT를 제외합니다. 팩터는 8개 z-score(±2.5 제한) 가중합. BAB는 1년 KOSPI beta, TSMOM은 12M·3M 일치 및 변동성 10% 타게팅입니다. Stat Arb는 거래대금 상위 160 내 Hurst<0.5·Engle–Granger p<0.05로 선별합니다.
- 남은 범위: 현재 유니버스의 스크리닝이며 역사 구성종목을 복원한 성과 검증이 아닙니다. 공적분 p값은 다중검정 보정 전이고 전체 구간 추정 헤지비율은 진입 시점 백테스트에 사용할 수 없습니다.

연결된 하위 그룹: Stat Arb, 멀티팩터, BAB, 단기반전, TSMOM.

[공식 분류·단위·날짜](../DATA_DEFINITIONS.md) · [차트 대응표](../CHART_PARITY.md) · [재계산 및 검사](../../README.md)

아래는 원본을 학습하며 작성한 설계 가이드다. 초기의 “필요/미확인” 표현은 위 현재 구현 상태를 우선해 읽는다.
<!-- implementation:end -->



StatArb·멀티팩터·BAB·TSMOM·단기 리버설 5개 퀀트 전략 후보를 제공한다.

## 구현 순서

1. 공개 docs의 유니버스는 KOSPI 300+KOSDAQ 150, ETF·스팩·리츠·우선주 제외, 가격은 yfinance 2년이다.
2. StatArb는 상관 0.5~0.95 후보에서 Hurst<0.5를 채택하고 OU 반감기·z 밴드를 사용한다고 설명한다.
3. 멀티팩터는 8팩터 z 및 ±2.5 winsorize 가중합, BAB는 1년 베타 분위와 레그별 1/β, TSMOM은 12M·3M 부호와 10% 변동성 타게팅(2x 상한)이다.
4. subviews의 그룹 문자열로 5개 표를 필터하고 페어 차트 10개를 표시한다.

## 검증 과제

- Hurst/상관 필터와 공적분 검정은 별개임을 명확히 하기
- 가격비 스프레드와 회귀 헤지비율 스프레드 구분
- 달러중립과 베타중립은 별개
- 대차·공매도·거래비용·회전율을 반영한 순성과

## 확인이 더 필요한 부분

docs에는 공적분이라는 이름이 있으나 공개 설명의 선별은 상관·Hurst 중심이다. 실제 공적분 검정 여부를 추정하지 않는다.

[전체 화면 목록](../MODULES.md)
