# 탭별 구현 현황

가격 기준 2026-09-08 · 공개 탭 25개 · 분석/콘텐츠 연결 **23개** · Overview/At a Glance 2개.

연결은 완전 복제와 다르다. 공개된 차트 구조를 맞추면서 실자료 계산과 탐색 기능을 구현했다. 비공개 산식·관측치가 필요한 부분은 아래와 각 화면에 남겨 둔다. 원본 계산 서버와 수치 동등성 인증을 완료한 탭은 없다.

로컬 가격 1109계열, 거시 35계열, 재무·가격 연결 195기업. 국내 컨센서스 빈티지 2026-08-07. KRX 대형주100·KOSPI200 공식 응답201·IVV 주식504를 사용한다.

| 탭 | 상태 | 연결 범위 | 남은 범위 |
|---|---|---|---|
| [Summary](modules/overview.md) | 계산·화면 연결 | 25탭 상태, 데이터 수, 바로가기 | 원본의 개인 서술·Tesseract·crowding 보조 엔진은 제외 |
| [At a Glance](modules/glance.md) | 계산·화면 연결 | PC 수집→검증→Vercel·평일08/18시 갱신·512MiB 변경분 캐시 | 원본 Mac 서버 운영 대신 승인된 PC 실행 일정 사용 |
| [MAXIMUS](modules/maximus.md) | 부분 구현 | 지수 · S&P500 / 지수 · KOSPI / 지수 · NASDAQ / 종목 · NVIDIA / 종목 · Microsoft / 종목 · Apple / 종목 · Alphabet / 종목 · Amazon / 종목 · Meta / 종목 · Broadcom / 종목 · Tesla / 종목 · Netflix / 종목 · 삼성전자 / 종목 · SK하이닉스 / 종목 · 삼성바이오로직스 / 종목 · 현대차 / 매크로 · 미국 10Y 금리 변화 / 매크로 · CPI MoM | 원본 10-expert MoE·SIS·ADF 파이프라인과 다른 명시적 기준모형입니다. 원본 모델을 실행했다고 표시하지 않습니다. / GitHub Pages에서 Python 재학습·임의 종목 서버 요청은 실행하지 않습니다. 로컬 명령으로 캐시를 갱신합니다. |
| [DRAGONGLASS](modules/dragonglass.md) | 부분 구현 | 관계 지도 / 지금 주목 / Entity 360 / 시나리오 / 결정 원장 / 트리거·촉매 / 리서치 / 데이터 소스 / 현황판 / 방법론 | 위성 현장은 시설별 좌표·실관측 시계열이 없어 남아 있습니다. 시나리오는 원본의 공급망 인과 전파 엔진과 다릅니다. 결정 원장은 브라우저 로컬 저장입니다. |
| [ARAGORN MAP](modules/aragorn.md) | 부분 구현 | 종합 | 원본의 매크로 인과 그래프 생성기가 없어 소속 관계를 인과관계로 표시하지 않습니다. |
| [GLOBAL UNIVERSE](modules/globe.md) | 부분 구현 | 종합 | UN Comtrade 품목·교역량·물류 경로를 수집하지 않아 무역선이나 금액을 생성하지 않았습니다. |
| [PRINCIPIUM](modules/principium.md) | 부분 구현 | primer / article / report / 종합 | 관리자 인증·PDF 업로드·팀 공용 저장 서버는 GitHub Pages에서 제공되지 않습니다. |
| [경제·시장 국면 (미국·한국)](modules/regime.md) | 부분 구현 | 월별 국면 / 미국 경제국면 / 한국 시장국면 / 시장국면 / 국면별 성과 / 국면 전이 / 밸류에이션 / 실적 이벤트 | 지수 전체의 역사 이익·밸류에이션 3단 게이지, 원본 Soros 합성 엔진·거시 발표 달력은 남아 있습니다. 종목 P/E를 지수 P/E로 표시하지 않습니다. |
| [주간 상대강도 (RS)](modules/rs.md) | 부분 구현 | 공식 상품 35페어·KR/US 종목 1W선별 1M막대·3유니버스 순위 | 조선 신규 상장으로 5Y 준비 구간 부족, z 비공개 세부 설정 미검증 |
| [모멘텀 (섹터·절대·초과수익)](modules/momentum.md) | 부분 구현 | 동일 그룹 수·5기간·3M/6M 짝·0선·양음 영역 | 조선 5Y z 없음, 누적 비율/달력 월 계약은 팀 설정 |
| [종목 발굴 (변곡·가속)](modules/discovery.md) | 부분 구현 | 종합 / 가격 선행 / 과매도 / 관찰 / 성장 동행 / 실적↑ 가격↓ | 원본의 내부 점수 정규화·서술형 리서치 엔진은 미공개로 수치 동등성은 미검증입니다. |
| [🎯 전략 스캐너 (신규 알파)](modules/strategies.md) | 부분 구현 | 턴어라운드 / 내부자 매수 / PEAD / 스탯아브 페어 / 실적 모멘텀 | 내부자 거래의 SEC 원문 코드P·제출시점 교차검증과 전략별 거래비용 후 OOS는 남아 있습니다. 신규 수집 대상은 미국 60개 기업이며 전체 미국 시장을 의미하지 않습니다. |
| [실적 모멘텀 (대형주)](modules/earnings.md) | 부분 구현 | US / KR / 종합 / 추정치 변화 | 해외 영업이익·순이익 FY1/FY2 컨센서스는 EPS와 다른 항목이므로 동일 지표로 대체하지 않았습니다. |
| [글로벌 성장주 모니터링](modules/growth.md) | 부분 구현 | FY1 / FY2 / 종합 | 글로벌 100종목의 FY1/FY2 영업이익 컨센서스가 없어 해외 3D 점은 제외했습니다. 해외 EPS 성장률은 별도 표로 제공합니다. |
| [멀티에셋 모니터링](modules/multiasset.md) | 부분 구현 | 자산 모니터 / 패턴 스캐너 / 자산배분 | 원본의 ML 자산배분 모델·가중치가 없어 기준모형을 구분해 제공합니다. |
| [멀티 위험지표 (선제위험·감마)](modules/risk.md) | 부분 구현 | 리스크 콕핏 / 신호등 US·KR / 파생·옵션 / 쏠림·신용 / CFTC 포지션 | 전체 만기 딜러 포지션 및 레버리지 ETF 실제 순유입 원장은 연결되지 않았습니다. 옵션 IV를 고정한 가격 시나리오는 변동성 곡면 변화를 반영하지 않습니다. / 원본 CSD 임계값의 예측력, 실제 포트폴리오 스트레스와 회복력은 미검증입니다. |
| [워칭 차트 · 패턴 스캐너 (📈상승·📉하락)](modules/watch.md) | 부분 구현 | KR · 상승 패턴 / KR · 약세 추세 / US · 상승 패턴 / US · 약세 추세 | 원본의 미공개 패턴 판정·신뢰도·ADX 합성 신호와 수치 동등성은 미검증입니다. 현재 후보의 향후 수익 성과를 의미하지 않습니다. |
| [ML·DL 지수예측 (KOSPI·NASDAQ·S&P)](modules/ml.md) | 부분 구현 | S&P500 · 1M / S&P500 · 3M / KOSPI · 1M / KOSPI · 3M / NASDAQ · 1M / NASDAQ · 3M / 종합 | 원본의 Boruta·SHAP·LSTM·모델 선택 규칙을 복제한 모델이 아닙니다. 최종 모델의 표준화 Ridge 계수를 별도로 표시합니다. / 거시 데이터는 최신 수정 빈티지에 2개월 시차를 적용했습니다. 발표일·개정치를 복원한 point-in-time 실시간 성과는 아닙니다. |
| [Quant Hedge (Multi Quant)](modules/quant.md) | 부분 구현 | Stat Arb / 멀티팩터 / BAB / 단기반전 / TSMOM | 현재 유니버스의 스크리닝이며 역사 구성종목을 복원한 성과 검증이 아닙니다. 공적분 p값은 다중검정 보정 전이고 전체 구간 추정 헤지비율은 진입 시점 백테스트에 사용할 수 없습니다. |
| [🌀 시장 속도·붕괴 취약성](modules/dynamics.md) | 계산·화면 연결 | S&P500 / KOSPI / NASDAQ / NVIDIA / Microsoft / Apple / Alphabet / Amazon / Meta / Broadcom / Tesla / Netflix / Palantir / 삼성전자 / SK하이닉스 / LG에너지솔루션 / 삼성바이오로직스 / 현대차 | 21D/5D/expanding252는 명시적 팀 파라미터, 거래비용·차입금리 미반영 |
| [Images & Words (주간 기록)](modules/iw.md) | 부분 구현 | 종합 | 원본 작성자의 주간 논평·과거 개인 기록은 제공되지 않습니다. 팀 동시 편집은 별도 서버가 필요합니다. |
| [PM 주말 브리프](modules/pm_weekend.md) | 부분 구현 | 매크로 브리프 / CFTC 포지션 | 원본의 CTA 추정 포지션·매매자금 예측은 실제 포지션 데이터가 없어 제외했습니다. |
| [💸 글로벌 ETF 큐레이션](modules/etfmon.md) | 계산·화면 연결 | 월급형 (Monthly Paycheck) / 초고배당 커버드콜·YieldMax (⚠️ 양날의 검) / 배당성장 귀족 (Dividend Growth) / 채권·현금 인컴 사다리 (Fixed Income Ladder) / 자산군 벨웨더 (One per Asset Class) / 파괴적 혁신 테마 (Disruption) / 국가 원픽 (Country Single-Play) / 팩터·스마트베타 (Smart Beta) / 레버리지·인버스 (Turbo, ⚠️위험) | 분배는 과거12M의 세전 월평균; 미래 지급액·실제 자금유입 추정 아님 |
| [🌍 geo-economics](modules/geoecon.md) | 부분 구현 | 주목 상황 / 지역 모니터 / 복합지표 / 키워드 트렌드 / 시장 지표 / 뉴스 원장 | 원본의 LLM 감성·인과 전파·위성 시설 관측은 연결되지 않았습니다. RSS 수집 범위와 실패 제공처를 표시합니다. |
| [ask_digest](modules/ask_digest.md) | 부분 구현 | 최근 뉴스 / 시장 / 방법론 / 종합 | 원본의 ASK 토론·외부 리서치 요약 아카이브와 연동되는 수집 서버는 별도 데이터 원장이 필요합니다. |

## 이번 검증 범위

Python 날짜·수익률·학습 타깃·미래 변경 불변성·기하 패턴 검증, 실제 스냅샷의 OHLC/행렬/그래프 검증, JS 전체 23개 데이터 탭과 모든 하위 섹션의 오프라인 렌더링을 검사한다. 7종 대표 SVG는 브라우저 없이 래스터화하여 차트 배치와 한글을 확인한다. 브라우저 이벤트 전체나 원본 픽셀 일치 검증을 완료했다는 뜻은 아니다.

재계산은 [README](../README.md), 공개 정의는 [DATA_DEFINITIONS](DATA_DEFINITIONS.md), 다음 보완은 [ROADMAP](ROADMAP.md)을 따른다.
