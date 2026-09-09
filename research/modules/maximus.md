# MAXIMUS

<!-- implementation:start -->
## 현재 팀 구현

**부분 구현** · 가격 기준 2026-09-08. 지수 / 매크로 / 종목 / 추가 지수 / 방법론.

- 계산 코드: [maximus_model.py](../../pipeline/maximus_model.py) · [maximus_features.py](../../pipeline/maximus_features.py) · [maximus_moe.py](../../pipeline/maximus_moe.py) · [maximus_views.py](../../pipeline/maximus_views.py)
- 화면: [research-dashboard.js](../../docs/research-dashboard.js) · [계산 결과](../../docs/data/maximus.json)
- 계산/자료 계약: 3모드 1개월 Mixture of Experts입니다. 예측은 이 PC의 완료월 자료로 계산한 캐시입니다. 10개 전문가·ADF/SIS·과거 OOS 로지스틱/성능 게이트·붕괴 보정을 적용합니다. 금리의 변화율은 채권 수익률이 아니며 CPI는 YoY의 %p 변화입니다. 68/95% 팬은 당시 과거 OOS 잔차의 정규 근사입니다.
- 남은 범위: 지수 밸류배수×이익추정 대신 과거 레벨 중앙값 앵커를 사용합니다. SEC filed 정렬 재무·한국 외국인 역사·일부 확장 거시 입력은 미연결입니다. / 원본과 다른 팀 하이퍼파라미터·가용 입력을 공개합니다. 현재 수정 거시에 시차를 준 결과이며 PIT 실시간 OOS가 아닙니다. / 완료월 추론입니다. 부분월 실시간 추론·웹 임의 종목 학습 서버는 아직 연결하지 않았습니다. / 변수 영향력은 고정 게이트 occlusion이며 SHAP/인과 효과가 아닙니다. 모델 선택·조정 규칙을 정한 기간과 분리한 전향 검증은 후속 대상입니다. / 방향전략은 월말 가정·편도5bp·rf=0이며 실제 주문·차입·선물 롤 비용을 복원하지 않습니다. CPI와 금리 수준에는 투자 수익률을 표시하지 않습니다.

연결된 하위 그룹: 지수, 매크로, 종목, 추가 지수, 방법론.

[공식 분류·단위·날짜](../DATA_DEFINITIONS.md) · [차트 대응표](../CHART_PARITY.md) · [재계산 및 검사](../../README.md)

아래는 원본을 학습하며 작성한 설계 가이드다. 초기의 “필요/미확인” 표현은 위 현재 구현 상태를 우선해 읽는다.
<!-- implementation:end -->

지수·매크로·입력 종목의 1개월 예측을 수행하는 MoE 콘솔. 공개 캐시 결과와 실계산 서버가 분리되어 있다.

## 구현 순서

1. data/maximus.json의 modes.idx/macro/stock을 읽어 targets, features_report, 전문가 가중치, 예측 범위와 결과 차트를 먼저 재현한다.
2. 원문 method에는 ADF 정상화→훈련창 SIS 30~50개 선택+코어 피처→10 experts→soft gate→예측·잔차 밴드 흐름이 설명되어 있다. 이 절차를 Python에서 따로 구현해야 한다.
3. 게이트 설명은 다항 로지스틱 25%와 성능 프라이어 75%, 전문가 예측 ±2.5σ 제한, 붕괴 오버라이드가 포함된다. 자세한 원문은 데이터 문서를 확인한다.
4. 온라인 실행은 POST /maximus/run, GET /maximus/status를 통해 진행률을 표시한다. 학습용 사본에서는 캐시만 사용한다.

## 검증 과제

- 금리 수준·수익률·CPI MoM/YoY의 단위와 타깃 정의 일치
- 공시 filed 날짜와 가격 스플릿 정렬
- SIS·표준화·HP 필터·게이트 학습이 각 훈련창 안에서만 수행되는지 검증
- 최종 홀드아웃을 모델 선택·게이트 선택과 분리; 등가중·단일모델·추세 벤치 비교

## 확인이 더 필요한 부분

실제 Python 모델 코드와 가중치·학습 데이터는 미공개. OOS나 룩어헤드 차단이라는 설명만으로 검증 완료라고 판단할 수 없다. 실계산 버튼은 누르지 않았다.

[전체 화면 목록](../MODULES.md)
