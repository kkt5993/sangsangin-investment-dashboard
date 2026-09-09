# 다음 작업 인수인계

최신 기준은 [구현 현황](research/IMPLEMENTATION_STATUS.md), [데이터 정의](research/DATA_DEFINITIONS.md), docs/data/status.json이다. 초기 RS만 구현했던 TODO보다 현재 코드·스냅샷을 우선한다.

- 사용자 목표: 가능한 모든 탭 실제 구현. 색은 자유롭지만 축·기간·패널 구조 유지. 외부 공식 지수·업종 정의를 적극 활용한다.
- 사용자가 기존 KRX 계정 인증 조회를 허용했다. --allow-krx-auth가 있어야 pykrx를 import한다. 설치된 pykrx는 import 때 인증할 수 있어 stdout/stderr를 억제하고 계정 정보를 출력하지 않는다.
- 코드·문서·작은 파생 결과는 기존 GitHub에 보관한다. 2026-09-09 사용자가 사이트 호스팅을 Vercel로 변경 요청했다. 검증된 docs 정적 결과만 Vercel에 게시한다.
- 원본 보존본은 형제 aragorn_investium_study. 다시 크롤링하지 않는다. 원본 서술·차트·소스를 공개 저장소에 복사하지 않는다.
- 원자료는 형제 sangsangin-investment-data/expanded/2026-09-08, 초기 가격은 sangsangin-investment-data/2026-09-08. 사용자 승인 한도 512 MiB. JSON gzip 변환은 압축 해제 해시를 검증했고 원본 DB는 변경하지 않았다.
- KRX 대형주1002의 100종목, KOSPI200 공식 조회 목록, IVV 공시 주식504개. KOSPI200 응답201개는 그대로 표시한다. 역사 구성종목 백테스트라고 주장하지 않는다.
- KR 페어는 공식 상품명으로 정의를 확정했다. IT266370, 대형주337140, 가치275290/성장325010, 필수소비재266410, 지주307520. 조선0115D0은 역사 부족으로 5Y z가 비어 있을 수 있다.
- Yahoo 국내 과거 종가의 일부 OHLC 범위 오류를 KRX로 확인했다. 별도 price_corrections.json.gz를 적용하고 원본 CSV는 보존한다. 시가·고가·저가의 일치 배율로 분할 조정을 정렬하고 기존 배당 조정 계수를 유지한다. 정렬 불가는 격리한다. FX·선물 settlement 범위 차이와 구분한다.
- 23개 분석·콘텐츠 탭이 연결되었으나 모두 완전한 원본 복제는 아니다. 삭제 요청한 소유자 전용 탭과 만든이 표시는 제거했다. 각 탭의 missing 항목을 유지한다.
- 지수 ML은 ml_ensemble의10종+ml_transformer의 Transformer와 평균/중앙값을 비교한다. ml_models의 legacy3종 함수는 MAXIMUS 호환용이며 지수 ML 화면에 쓰지 않는다. macro를 가격의 월 인덱스에 먼저 reindex한 뒤 shift(2)한다. 순서를 바꾸면 예측월이 잘린다. 최신 수정 거시 빈티지의 결과는 PIT 실시간 성과가 아니다.
- MAXIMUS는 3-expert OOS 역 MSE 게이트이며 원본 10-expert MoE가 아니다. Python 서버 실행·임의 종목 입력은 정적 웹에 없다.
- 성장 3D 축은 FY1/FY2 영업이익 성장×YTD×영업이익률. 로컬 컨센서스 기준2026-08-07을 가격일과 구분한다. 해외 EPS를 영업이익으로 대체하지 않는다.
- 옵션은 SPY·QQQ·IWM의 제한된 3개 만기 OI·IV 관측. 콜+/풋− 부호 가정이며 실제 딜러 inventory가 아니다.
- 그래프는 공식 시장/업종 소속. 교역·위성 관측을 만들지 않는다. 라이브러리는 자체 노트, 기록은 브라우저 localStorage이며 팀 공용 DB가 아니다.
- 새 화면은 schema_version2, RS/모멘텀은 v1. ml_models와 maximus_model 계산 후 build_all을 마지막 실행해 status.json/status.js를 갱신한다.
- 배포 전 README의 6개 검사와 JS 구문 검사를 실행한다. 대표 SVG는 scripts/render_chart_samples.cjs로 래스터 검증한다. 브라우저 UI 검사 완료라고 주장하지 않는다.

후속 보완: 발표 시점 데이터/ALFRED, 역사 구성종목, 글로벌 영업이익 컨센서스, SEC 제출 시점 원장·13F, 원본 모델과 공정한 비교, 팀 공유 저장·권한 서버.

현재 게시용 검증 기준: 가격1,084계열·거시35계열·재무 연결195기업, KR99/100·US500/504·KOSPI200199/201 순위. 미산출은 신규 종목 역사 부족 및 HOLX 유효 가격 부재이며 결과에 종목별 사유를 표시한다. RS34/35(조선 준비 구간 부족), 모멘텀32자산/23유효 z섹터/32곡선이다. 데이터 크기와 실행 빈티지는 runtime 보고서 및 공개 status/refresh.json을 확인한다.

워칭 차트는 patterns.py의 공개5종 기하 규칙과 확정 피벗/저항선을 연결했다. 원본과 모델 동등성을 주장하지 않는다. 멀티에셋 월중 비중은 수익률에 따라 drift하며 최초 거래 비용도 부과한다. MDD에 최초 투자금을 포함한다.

2026-09-09 확장: 발표시각 PEAD·내부자 매수·EPS 추정 변화·실적 달력·국면 성과·RSS 뉴스/지역/키워드·CFTC TFF·DRAGONGLASS 10개 세부 화면 연결. 정확한 연결/미연결 목록은 research/SUBVIEWS.md. 원본과 같은 이름이어도 비공개 모델 전체 복제로 주장하지 않는다.

승인된 정기 갱신은 한국시간 평일08시·18시. PC+Codex 앱에서 pipeline.refresh --publish를 실행한다. runtime/config.json의 기존 로컬 ECOS 설정·QW DB·KRX 허용을 사용한다. 값이나 절대 경로를 공개하지 않는다. 가격 변경분은 parent.json 체인·SHA256으로 검증한다. 실패한 staging은 게시하지 않으며, pending_publish.json은 동일 커밋으로 재시도한다. 자세한 절차는 research/UPDATE_PIPELINE.md.

Vercel 프로젝트: sangsangin-investment-dashboard. 운영 도메인 https://sangsangin-investment-dashboard.vercel.app. 사용자 직접 인증한 CLI를 이용하며 .vercel과 .env.local을 Git/정적 패키지에서 제외한다. Vercel GitHub OAuth 연결은 필요하지 않다.

2026-09-09 목표 확장: 사용자가 `/goal`로 모든 세부 탭 구현을 요청했다. 큰 탭/버튼 연결만으로 완료 판단하지 않는다. research/REFERENCE_PARITY.md의 중첩 화면·내부 기능도 작업 대상이다. PM6개 하위 화면·14핵심 차트, 13산업39지표, 재귀성5기둥/3시장36개월홀로그램/4시점5축레이더를 추가했다. Soros 핵심 산식은 공개 app.js 2053행 이후와 _RX_CFG에 존재했다; 미공개라고 일괄 분류한 이전 기록을 따르지 않는다. 현재 macro51·price1124이며 이전 35/1084는 초기 기준이다.

새 코드: pm_details.py, industry_details.py, reflexivity.py, gpr_data.py. 국내 GDP는 ECOS200Y104/1400(Q 계절조정 실질), 기초화학 수출물량403Y003/3051AA, 수출액의 ECOS 단위 '천불'→USD bn은1e6으로 나눈다. 시총 확보 범위에서 현재 공식 US70/KR60 표본을 고르므로 과거 구성종목 주장이 아니다. AR1은 창 내부 n−1쌍, 회귀 t는 OLS. 홀로그램 표시 z는36개월 분포이며 예측 입력으로 사용하지 않는다.

원본 대비 아직 여러 세부 기능이 남는다: PM 실적종목 ATM 내재변동폭, 국면 지수 밸류에이션·거시 발표달력, 리스크 flows/Wag-the-Dog와 KOSPI 옵션, DRAGONGLASS 관계·위성·원장 필드·전파, ML/MAXIMUS/배분 모델, 실적/성장 추정 상세, 발굴 버킷·기타 콘텐츠 동작. 각 화면 missing과 REFERENCE_PARITY.md를 갱신하면서 이어간다. 정기 갱신은 활성 heartbeat automation ID automation 하나만 유지한다.

후속 추가: 리스크 Wag-the-Dog 연결. option_analytics.py와 wagdog.py는 동일 packets를 사용한다. 기존 가로 막대 GEX를 원본과 같은 행사가 가로축/수직 감마 막대로 교체했고 현물·플립·30D IV 기대폭을 표시한다. SPY OI는 콜 위/풋 아래이며 방향 의미가 없다. OI는 IV 결측도 포함하고 GEX만 IV 필터한다. 플립은±20% 탐색의 교차, 교차 없음 또는 감마 전부0은 None. 기대폭은 ATM IV의30D 정규 근사로 옵션이 예측한 확정 범위가 아니다. VVIX를 추가했다. 실제배포기준/빈티지는 runtime/state.json을 확인한다. 다음 우선: flows 주식·ETF AUM/공매도·KR 투자자 수급과 PM 개별 실적 ATM 스트래들.

옵션 공급처 수정: Yahoo의936/829/450계약 중 양의 OI가16/30/19개뿐이고 현물 부근은 대부분0으로 전달되는 문제가 실제 차트검사에서 발견됐다. 이를 0의 실제 포지션으로 해석하지 않는다. options_data.py를 Cboe 공개 지연호가 JSON으로 교체했다(ETF당1요청). OCC심볼을 파싱해 일반계약·7~45일중첫3만기만 로컬 저장하고 ±10% ATM범위 양의 OI20계약 이상·콜풋양쪽 존재를 검사한다. 시세와 옵션 현물의1.5%초과불일치도 게시 중단. Cboe timestamp는 타임존미표기 그대로 보존하고 실제 수집UTC와 구분한다. 과거Yahoo원자료는 변경하지 않았다.

수급 후속: flows_data.py는 Yahoo 공개 요약(US20종목·LETF50상품), Cboe주식20+예정실적 최대8종목, KRX공식8대형주 투자자 거래량/1168ETF를 분리 수집한다. flows.py는 1%충격 LETF/21D ADV, |GEX|/시총, 옵션명목/시총, Short/Float 단면z를4개모두 있을 때만 평균한다. 리밸런싱은 Σ(L²−L)AUM×가정충격, 원본 금액막대+ADV다이아 구조·±20% 입력. 지수는 ADV 비율 미표시. KR12테마는 비레버리지명칭첫일치·공식순자산우선/NAV×좌수대용, 1M NAV변화·회전률. 주식 수급은 최근5거래일 순매수 주식수/동일기간 전체거래량. PM/실적은 같은행사가/만기 bid/ask mid 합계÷현물, ORCL/COST 최초2개 관측. Yahoo AUM은 보고일미제공, shorts는dateShortInterest일자. 모든ETF세계목록이라는 주장이 아니며 원장에등록범위표시. MSTR 가격 추가필요시 catalog DETAIL에포함. 공공API품질90%미달이면자동배포중단.

국면 후속: valuation.py 3시장×3단(실제지수/전산업이익 로그이중축, 비율25/50/75분위, CPI+정책금리)·5/10/15년전환. CP FRED, ECOS501Y002 ZZZ00/A/270000 연간당기순손익백만원→조원(1e6) 신규수집. 연간/분기 관측기간말부터 월별유지, 마지막 실제기간 이후 점선은carry이며 이익추정아님. 원본설명엔KR GDP라고남았으나JSON은전산업순이익; 2025~원본추정 산식은없으니동일수치주장불가. calendar_data.py는 FRED8releaseID+BEA(최초50예정발표), UTCoffset/DST→KST. BLS직접ICS403은 FRED공개일정으로대체. refresh주간달력/매회CP·ECOS계열갱신. 검사52unittest+6표준/구문/전체subview+21SVG래스터. macro53.


DRAGONGLASS 후속: `entities.py` 현재공식유니버스 합집합700개(재무132/향후일정59)·64거래일14점가격·동일가격구간252Beta(최소200)·RS유니버스표시. `decision-ledger.js` v2로 가설/방향/확신/시계/크기/촉매/무효화/3상태/최근50이력/휴지통/JSON/Entity상호이동. localStorage기존v1원문보존, 명시적가져오기, 500건2MiB상한, stale-tab compare-before-write와quota오류시원본유지. 실행만NAV집계, 누락비중/Beta전체값null, 0가중치0. 가정EV는사용자입력만. `test_decisions.cjs`는상태엔진및실제화면콜백을offline미니DOMfixture로검사, 브라우저QA아님. test_extended가호출하므로자동갱신검사에포함. `write_status_docs.py` 반복실행빈줄누적수정. 원본프리모템·군집·8관계전파는후속대상.


현재 진행 묶음(2026-09-09): `allocation_model.py` MODEL_SPEC3, Boruta100회·74팀피처·ElasticNet/RF/LightGBM7대표수익률·분류/Markov/LSTM 리스크온·OECD 미국CLI/CPI 국면. 원점별 전체재학습·2개월거시시차·125예측, 마지막 완료월2026-08. `allocation_views.py`의33자산8그룹·상한·10%예측변동성·BIL현금·다음첫종가체결/다음날수익률·10bp총변동비용·96월성과·12월가중치를 원본배치에 연결한다. 이전 Boruta12 및 산업생산 대용 모델은 개인 연구빈티지에 보존하고 새 게시에 쓰지 않는다. CPU Torch2.11.0은 이미 있었고 LightGBM4.7.0/Boruta0.4.3만 추가 설치했다.

`oecd_data.py`는 공식 OECD SDMX 1요청으로 USA/KOR/JPN/CHN CLI 각320개월(2000-01~2026-08)을 확보. IX·AA·H·배율0·월연속·3개월신선도검사; 조회기록을 따로 보존해 동일값 중복삭제 후 매 실행 재조회하지 않는다. 7일주기이며 자산배분모델은 완료월·버전 변경 때 계산한다. 현재거시57·가격1126, raw 최신개발빈티지20260909T102452Z. 실제 게시상태는 항상 runtime/state.json 확인.

`technical_scan.py`는37자산12지표,90봉캔들/MA20·60/오른쪽가격축/9·전체/패턴/분류 필터. ADX는Wilder정확한warmup, 거래량없는지수결측. 워칭120D/52W가격·거래량패널에ADX/DI/MA4조건/12점수를 추가. `discovery.py`는598공식기술스캔·114후보·4분류·3평가축·45/30/25가중치, 미국78종목종합가용. 시장/분류/검색/30개더보기/근거상세를 연결했고 스마트머니는실제기관매매가아닌애널리스트의견이라고 명시. 한국은KRX대형주라원본KOSDAQ범위와다름. 새모듈은공개임계치팀기준이며모델수치동등성주장없음.

FOMC 공식연도/월/종료일/SEP달력을추가. 현재52예정·10원천. 월경계회의·서면표결배제·시간미확인검사; FOMC한국시간임의입력금지. 한국경제일정은여전히남음. 다음실제구현은 REFERENCE_PARITY의관계증거/시나리오/위성,ML6그룹본모델,MAXIMUS10전문가,실적추정상세,콘텐츠등록/첨부부터확인한다. 이문서의이전'남음'문장은현재표와대조한다.

배포 준비 검사: Python73개, 두 데이터 검증기, 3개 JS 렌더/동작 검사, JS9개 구문, SVG24개 래스터 통과. 스캐너/배분 이미지를 확인했다. 공개 JSON 약4.87MiB, 로컬 원자료/실행파일 약72MiB. 학습 선택 상태는 확정84·미확정19·순위대체22원점이며 세 리스크온 모형은125원점 모두 산출. ML 성과를60/40보다 우수하다고 주장하지 않는다. 최신 run_id=20260909T104824Z; 게시 성공 여부는 runtime/state.json.


지수 ML 후속(2026-09-09): `ml_features.py`142후보, `ml_ensemble.py`10종/Shadow12회/6개월일반·12개월LSTM, `ml_transformer.py`Transformer 추가·선택/잔차 재생, `ml_views.py`10세부그룹16섹션. 원본 설명10종과 실제 평가표13열(11종+2앙상블)이 달라 실제 chart 구조를 따랐다. 1M164·3M162원점, 최소96라벨,3M만기·당시120개평가선택/24잔차검사. TreeSHAP는 full available-label 별도 LightGBM의최근120개15변수 해석으로OOS/인과 아님. 최신3개 MLP수렴경고를진단에표시. 최종선택은SP5001M XGBoost/3M ExtraTrees,KOSPI1M LightGBM/3M Lasso,NASDAQ1M·3M ExtraTrees.

신규 ECOS901Y056 M S23A/S23E는 원 단위272개월. raw빈티지20260909T105501Z,부모102452Z,거시59. XGBoost3.4.1 Windows46.7MiB패키지를추가했고기존CPU Torch를재사용. 공개JSON약5.09MiB로상한6MiB, DATA전체약51.6MiB(스테이징정리후)로승인512MiB이내. 캐시는입력/코드해시별타깃gzip,코드변경시전체과거재생; 증분학습이라고표현하지않는다. refresh가model_spec2변경도검사. legacy ml_models.features/walk_forward는MAXIMUS3전문가가쓰므로삭제금지.

검사78unittest·두검증기·3JS검사·9JS구문·31SVG래스터통과,새ML7종이미지중모형/SHAP/36월/컴포짓/상관/변수배치확인. 브라우저QA없음. 공개커밋의원본사이트요청0. 지수ML남은차이는 ML_MODEL_CONTRACT와REFERENCE_PARITY,다음은MAXIMUS·관계근거/전파·위성·추정상세·콘텐츠기능. run_id=20260909T113437Z; 실제게시확인은runtime/state.json.

MAXIMUS 후속(2026-09-09): `maximus_features.py` 가격223/CPI201후보·자기기술/US·KR레버리지/6부문 순차HP/3합성·훈련창ADF/SIS, `maximus_moe.py`10전문가·추가1개월엠바고·6개월재학습·과거48개OOS 로지스틱25%/프라이어75%·붕괴보정. `maximus_views.py` PT/DM·68/95팬·R/I occlusion·24원점/전체진단·방향전략. 기본2지수/추가지수Nasdaq/6매크로/13종목=22대상, 7섹션/5그룹. PLTR·LG에너지솔루션은8년미만 제외; 삼성바이오로직스21원점/19잔차로확률·팬없음. MLP수렴경고8타깃을진단에보존한다.

CPI는YoY의다음%p변화이고관측월M→정보월M+1. DGS10은상대금리수준변화와bp, 채권수익률아님. 두타깃에는전략성과미표시. 원본이익추정앵커대신과거120/최소36월중앙레벨15%수렴, R/I는고정게이트평균치환민감도로SHAP/인과아님. S&P상대강도는KOSPI, KOSPI/Nasdaq은S&P기준. 교차벤치수정시21타깃의입력해시불변을검증해캐시서명을이관하고변경된S&P만실제재학습했다. 모델코드변경을무조건캐시서명갱신으로처리하면안된다.

raw빈티지20260909T114624Z(부모105501Z), KODEX레버리지122630.KS4041봉추가·총가격1127/거시59, catalog에TQQQ/122630/069500반영. 로컬약58.4MiB,공개JSON약5.57MiB. MODEL_SPEC1추가시정기갱신도재학습판정한다. legacy `maximus_model.baseline_build`는이전3전문가연구용이고현재build에서호출하지않는다. 검사84unittest·두검증기·3JS·9JS구문·33SVG래스터,팬/네트워크배치확인. 브라우저QA와원본요청없음. 새실행/게시ID는public refresh.json과private runtime/state.json확인.

다음은콘텐츠기능: 보존principium.js에article/report/primer별문서보드·5단상세·키워드구체/공동출현그래프·등록/수정/첨부구조가있다. 자체콘텐츠로구현하며원본관리자/비밀번호/저자기록을복제하지않는다. IW원본은29판단행과2차트, ASK digest는brief/기간별trends·테마10·주식16·21crossasset·위험양/음·4차트·모듈요약schema다. 이들현재기본메모만으로완료처리하지말것. 이후관계전파/위성/추정상세등은REFERENCE_PARITY지속확장.
