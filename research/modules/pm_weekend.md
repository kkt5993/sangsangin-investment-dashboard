# PM 주말 브리프

<!-- implementation:start -->
## 현재 팀 구현

**부분 구현** · 가격 기준 2026-09-08. PM 키 게이지 / 금리·성장 / 크로스에셋 속보 / CTA 시스템 트렌드 / 매크로 z-score / 다이버전스·실적 / 기초 매크로 시계열 / CFTC 포지션.

- 계산 코드: [macro_modules.py](../../pipeline/macro_modules.py) · [subview_modules.py](../../pipeline/subview_modules.py) · [cot_data.py](../../pipeline/cot_data.py) · [pm_details.py](../../pipeline/pm_details.py) · [gpr_data.py](../../pipeline/gpr_data.py) · [flows.py](../../pipeline/flows.py) · [flows_data.py](../../pipeline/flows_data.py)
- 화면: [research-dashboard.js](../../docs/research-dashboard.js) · [계산 결과](../../docs/data/pm_weekend.json)
- 계산/자료 계약: PM 6개 세부 화면: 임계 게이지·금리/성장·7계열 위험선호·10자산 CTA·z 분포·다이버전스/실적. 금리·GDP는 관측기간을 맞추며 한국 명목성장은 실질 GDP YoY+CPI 근사입니다. 게이지는 관찰 규칙이며 침체 확률이나 수익 보장이 아닙니다. CTA는 21/63/126/252일 수익 부호 평균, 63일 변동성에 자산별10% 타깃·레버리지2배 상한·동일 평균을 적용하고 하루 지연한 비중과 5bp 회전비용을 사용합니다. ETF 조정가격·USD 수익률 기준이며 현금 이자·차입/펀딩 비용은 미반영입니다. CFTC TFF는 선물만의 주간 보고값이며 레버리지펀드는 CTA 전체와 같지 않습니다. 계약별 단위가 달라 계약 수를 자산 간 달러 익스포저처럼 합하지 않습니다.
- 남은 범위: 원본이 공개하지 않은 CTA 변동성 창·비용·레버리지 및 z 준비 기간은 위 팀 설정으로 고정했습니다. 과거 실시간 거시 빈티지와 실제 CTA 계좌 포지션은 아닙니다.

연결된 하위 그룹: PM 키 게이지, 금리·성장, 크로스에셋 속보, CTA 시스템 트렌드, 매크로 z-score, 다이버전스·실적, 기초 매크로 시계열, CFTC 포지션.

[공식 분류·단위·날짜](../DATA_DEFINITIONS.md) · [차트 대응표](../CHART_PARITY.md) · [재계산 및 검사](../../README.md)

아래는 원본을 학습하며 작성한 설계 가이드다. 초기의 “필요/미확인” 표현은 위 현재 구현 상태를 우선해 읽는다.
<!-- implementation:end -->











주말에 거시·금리 분해·CTA·리스크선호·뉴스를 함께 읽는 PM 브리프.

## 구현 순서

1. table의 게이지·뉴스·CTA·매크로 그룹과 각 차트 note를 근거로 자료를 모은다.
2. 실질금리=명목−물가, r−g 비교, SPY/TLT 등 자산비율·VIX·달러의 z 합성을 별도 변수로 만든다.
3. 한국 기대인플레이션 대신 실현 CPI를 쓰는 근사와 명목성장률 근사 정의를 화면에 보존한다.

## 검증 과제

- 금리·성장률·물가의 주기 및 연율 단위 일치
- Sahm 등 발표일과 사용가능 시점
- CTA가 실제 포지션인지 룰 기반 추정인지 구분

## 확인이 더 필요한 부분

주말 발표 당시 정보 집합과 전체 룰 코드가 없어 재현 구현에서 확정해야 한다.

[전체 화면 목록](../MODULES.md)
