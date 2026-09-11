# 퀀트전략

<!-- implementation:start -->
## 현재 팀 구현

**부분 구현** · 가격 기준 2026-09-10. Stat Arb / 멀티팩터 / BAB / TSMOM / 단기반전.

- 계산 코드: [quant_modules.py](../../pipeline/quant_modules.py) · [quant_screens.py](../../pipeline/quant_screens.py) · [quant-screens.js](../../docs/quant-screens.js)
- 화면: [research-dashboard.js](../../docs/research-dashboard.js) · [계산 결과](../../docs/data/quant.json)
- 계산/자료 계약: 현재 Naver KOSPI300·KOSDAQ150 필터 유니버스. 가격비 A/B의 상관0.5~0.95·Hurst<0.5 순 페어10개, 8팩터 횡단면 z±2.5 상위15, KOSPI Beta5분위/레그 역Beta, 12M·3M TSMOM과 추세 내5D 반전. 실제 날짜·결측·제외 및 점수 기여를 원장에 표시합니다.
- 남은 범위: 현재 유니버스와 최신 정정가격의 단면 분석이며 역사 구성종목·PIT·대차/펀딩/거래비용 후 OOS 성과가 아닙니다. / 공개되지 않은 rolling/Hurst/MAX/월안정성 세부 설정은 명시한 팀 설정입니다. 가격비 평균회귀를 공적분 검증이나 베타중립으로 부르지 않습니다. / TSMOM 보존본에서 이름이 확인된6개 외 나머지6개는 팀이 선택했습니다. 금리 상대변화에 투자노출을 부여하지 않습니다.

연결된 하위 그룹: Stat Arb, 멀티팩터, BAB, TSMOM, 단기반전.

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
