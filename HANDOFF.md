# 다음 작업 인수인계

최신 기준은 [구현 현황](research/IMPLEMENTATION_STATUS.md), [데이터 정의](research/DATA_DEFINITIONS.md), docs/data/status.json이다. 초기 RS만 구현했던 TODO보다 현재 코드·스냅샷을 우선한다.

- 사용자 목표: 가능한 모든 탭 실제 구현. 색은 자유롭지만 축·기간·패널 구조 유지. 외부 공식 지수·업종 정의를 적극 활용한다.
- 사용자가 기존 KRX 계정 인증 조회를 허용했다. --allow-krx-auth가 있어야 pykrx를 import한다. 설치된 pykrx는 import 때 인증할 수 있어 stdout/stderr를 억제하고 계정 정보를 출력하지 않는다.
- 코드·문서·작은 파생 결과는 기존 GitHub에 보관한다. 2026-09-09 사용자가 사이트 호스팅을 Vercel로 변경 요청했다. 검증된 docs 정적 결과만 Vercel에 게시한다.
- 원본 보존본은 형제 aragorn_investium_study. 다시 크롤링하지 않는다. 원본 서술·차트·소스를 공개 저장소에 복사하지 않는다.
- 원자료는 형제 sangsangin-investment-data/expanded/2026-09-08, 초기 가격은 sangsangin-investment-data/2026-09-08. 2026-09-11 사용자 요청으로 누적 저장 용량 검사·상한 차단을 제거했다. 아래 날짜별 과거 한도 기록은 현재 정책이 아니다. JSON gzip 변환은 압축 해제 해시를 검증했고 원본 DB는 변경하지 않았다.
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

다음은콘텐츠기능: 보존principium.js에article/report/primer별문서보드·5단상세·키워드구체/공동출현그래프·등록/수정/첨부구조가있다. 자체콘텐츠로구현하며원본관리자/비밀번호/저자기록을복제하지않는다. IW원본은월말복기15건+주간연대기14건과2차트, ASK digest는brief/기간별trends·테마10·주식16·21crossasset·위험양/음·4차트·모듈요약schema다. 이들현재기본메모만으로완료처리하지말것. 이후관계전파/위성/추정상세등은REFERENCE_PARITY지속확장.

로컬 리서치 후속(2026-09-09): `research-store.js` IndexedDB(meta+files)·500건/UTF8메타2MiB/첨부64MiB·파일8MiB/기록12개·SHA256동일파일공유. 같은트랜잭션에메타/Blob저장·고아파일삭제, 중간quota실패롤백·revision및기록history충돌방지. 가져오기90MiB·첨부hash/크기/형식검사·동일건중복건너뛰기·충돌사본. 이전localStorage키보존/명시적가져오기·내용hash기반ID. 영구삭제는휴지통만, 다른글이참조한첨부유지. PDF다운로드·래스터이미지만Blob미리보기, 네트워크전송없음. 실제브라우저저장소를도구로열거나사용자자료를추가하지않았다.

`research-notes.js` PRINCIPIUM3유형/5단상세·문서제목노드/공유키워드선·첫100문서/상위30단어구체·회전/드래그/글이동, IW4판단필드·방향/기간/확신/무효화/재검토, ASK질문/해석/근거/추가확인. 공개팀노트는사본으로편집; 로컬입력·백업은운영서버에올리지않는다. `platform_modules.libraries`에notebook섹션추가. root `package.json`은검사전용 fake-indexeddb6.2.5. 이PC는tools/test-dependencies에52,568byte tarball을원격1회받아설치했고stage검사는SANGSANGIN_DATA_DIR의형제tools를해석한다. 런타임·토큰·사용자파일은공개하지않는다.

`test_research_store.cjs` 실제IndexedDB API를메모리어댑터로검사하고 `test_research_notes.cjs`는기존test_dom_stub의실제양식콜백을호출한다. test_extended가두검사를순서대로await하여quota실패주입이겹치지않는다. 기존84Python·두검증기·3JS(새2개포함)·11JS구문·35SVG래스터통과. 긴한국어제목의관계도잘림을래스터검사에서수정했다. 문서키워드가겹치지않는공개4노트에는선0개가정상이며공유키워드양성fixture도검사한다. 브라우저QA없음.

실제공개기준은runtime/state.json. 원자료/실행파일64.2MiB·공개JSON5.573MiB(배포패키지생성전). 다음은원본IW29판단행/두차트·ASKbrief/기간별추세/테마/종목/위험모듈집계,관계근거/전파/위성/추정상세다. PDF자동추출/LLM요약·팀공용DB/로그인·서버방문통계는아직미연결이며이번로컬저장을그기능완료로세지않는다. 자세한계약은LOCAL_RESEARCH.md.


IW 후속(2026-09-09): 원본29행은15월말 복기+14주간 연대기였으며29독립판단 지표라는 이전 해석을 정정했다. `iw_review.py`는1M ML 원장과같은표에서 방향집계·3지수/6전망/4거시·36완료월3국면띠/7계열ML을 생성한다. 성장/CPI/M2/Sahm2개월·NFCI7일팀정보시차, 위험5필수조건 결측은회색. 첫과거13주는재구성표시,지난주는기록/차트동결,현재주만갱신/최초시각보존. private iw_journal.json.gz 전체누적·공개14주,모형hash/빈티지/방법버전저장. 월중확정국면제외·표시구간z재계산, 상세계약 research/IW_REVIEW_CONTRACT.md. `subview_modules.extend`끝에서연결하므로정기갱신에포함. 개발raw빈티지20260909T131712Z(부모114624Z),추가외부/원본요청0. 검사89Python·두검증기·3JS/11구문·38SVG래스터,국면/과거ML배치확인;브라우저QA없음. 공개JSON약5.99MiB로현재6MiB한도에가까움;이후작은파생탭추가시필요하면공개한도만합리적으로확장하고raw512MiB승인한도유지. 다음ASK brief/기간별추세/테마/종목/crossasset/위험·모듈요약을기존수치로구현. 게시실행ID 20260909T133351Z의실제완료는runtime/state.json확인.


ASK 후속(2026-09-09): `digest.py`와config/digest_themes.json으로10세부화면연결. brief·1M/6M/2Y선택·공식기업사업근거10테마(1~2기업표본)·공식US/KR RS각8총16·21자산·9임계관측·4핵심비율/스트레스·20분석모듈요약·RSS·로컬질문. 원본 heat/구루/전체뉴스량/자동LLM서버 미연결. 회사공식사업설명근거의역할이며GICS공식테마분류아님. 수익률은달력7일/월/연도이전마지막가격(7일초과오래되면결측);암호자산504일을2년으로간주하지않도록수정. starts실제기준날짜보존,테마는모든구성원기간가용때만단순평균·가용목록3Mrank0~100/동률평균. 주간조회원장그림외기존모듈의21/63/252관측계약은변경하지않았다.

ASK 핵심비율은HG/GC·SPY/TLT·XLY/XLP 비조정공통종가180관측/63관측변화,4번째EPU/VIX/HY252D z는차이(퍼센트아님). 9위험임계값과정확한동일값별도,뉴스제목단어일치(TER가interest와일치금지)/KST기준일이후제외. 20모듈은현재build객체+동일날짜RS/momentum+별도기준ML/MAXIMUS에서읽는다. 원본내부18개라는것과구분. 상세 research/DIGEST_CONTRACT.md.

개발raw빈티지20260909T133557Z(부모131712Z),새시세/원본사이트요청0·기업공식자료웹검증은수행. 로컬약76.27MiB/512MiB,공개JSON6.059MiB로자체공개한도8MiB조정. 검사96Python·두검증기·3JS/11구문·43SVG래스터통과,2Y암호자산달력회귀검사추가. 브라우저QA없음. 게시실행ID 20260909T135520Z 실제완료는runtime/state.json. 다음은DRAGONGLASS관계/근거/8시나리오전파·원장프리모템/군집,위성좌표/NDVI,실적/컨센서스세부,Overview TESS/5축,마지막RS/모멘텀/ETF기간계약등REFERENCE_PARITY에따라계속.


다음 묶음 착수: DRAGONGLASS 관계/전파. 개발빈티지20260909T135843Z(부모133557Z),아직공개build안함. `relation_model.py`와7fixture검사통과:최대3hop·방향별계수·한seed최강절대경로/다중seed합·루프배제·경로근거·중심성·실현상관370달력일내252/min200. 원본공개전달계수11종을설정으로독립구현,협업만팀0.35추가;실제수익률/확률아님. 상관은기본전파제외,선택시실측음수부호를보존(원본은correlated항상양의계수). 이엔진은아직화면에연결안됨.

`config/relation_evidence.json` SEC NVIDIA FY2026 10-K 제조/경쟁(원문링크포함)기반4공급·5경쟁,Vertiv AI hub2기술협업(전력판매계약아님),Lilly tirzepatide제품확인. ASK의digest_themes.json 사업근거도재사용가능. 현재실제기업노드+테마를만들고예측가중치와사실관계를구분해야함. 원본8시나리오:금리재상승/AI CapEx둔화/TSMC공급차질/전력병목/HBM가속/지정학/GLP1/위험선호후퇴. 원본SCN shock0.2~0.7은정규화가정,실제%수익률아님. 공급순방향.28/역.72,경쟁−.5,partof.42/.55 등은TRANSFER. multiseed0.12이상종목breadth/0.06이상상하8행,단일전파.03이상/중심성.05이상. scenario/Entity/decision영향표·원장최악경로/상관군집UI와연결하는것이다음.

원본 `_decisionIntel`은확신도에서확률/상방/권장비중을기계적으로만들지만,우리화면의기존EV는사용자입력만사용하므로이를실측확률처럼넣지말것. 준비도·최악시나리오·노출누락/상관coverage를연결한다. 원본코드는형제study/source/assets/dragonglass.js 773~820,1074~1154,1191~1282에서확인했고원본사이트요청0. 현재최종공개64530e7,run135520Z,42/42바이트검증완료. 신규relation파일/이인계는미커밋이며다음묶음완료시게시.


DRAGONGLASS 후속(2026-09-09): 관계39객체(기업22/테마13/관측2/가정2), 공식 사업/공급/경쟁/협업30+실현상관6, 원본255/581전체 검증 아님. `relation_views.py`가`extend`에서Entity추가후호출되어정기갱신에포함. Entity700공식+TSM ADR1(공식업종미확보/RS없음), 모든기업가격을관계확신도처럼사용하지않음. 가격추가요청0,원본요청0. 기업공식/SEC자료만근거확인했으며 config/relation_evidence와digest_themes에URL/역할보관. 노드좌표3Dspring seed832/k1.2, SVG라벨겹침회피·드래그/휠/핀치/선택/필터/자동회전·탭이동시프레임취소. 초기과밀레이아웃을래스터에서발견해수정.

`relation-views.js`는공개8가정Python결과와정확일치. 최대3단계/최강경로/다중입력합/출처, 중심성·부호대조·상하8순위/도달범위,원장실행비중·최악가정·Long쌍별상관. 상대강도를수익률이나%NAV손익으로표시하지않음. 무입력/미연결/경로없음/0비중분리. 이전Beta/공식분류별도하위화면보존. 상관전체Entity701창252/min200 아래삼각Int16×10000+Uint8관측수·결측32767·자기상관분산검사. 원장스토리지변경없고가정확률/권장비중자동생성없음. 상세 research/RELATION_CONTRACT.md, source미확보범위 REFERENCE_PARITY.

검사106Python·두검증기·3JS(새relation포함)/12구문·46SVG래스터통과,브라우저QA없음. 원자료/실행파일 82.60MiB/512,공개JSON 7.107MiB/8. 게시실행ID 20260909T143022Z, 빈티지 20260909T135843Z;실제공개완료는runtime/state.json확인. 다음전체목표계속: OverviewTESS/5축,위성실관측,Geoecon시간/사건자산경로,글로벌추정상세/SEC13F·P/KR거시달력,최종RS/모멘텀/ETF기간계약. 이묶음은진행이며전체완료아님.


Overview 후속(2026-09-09): overview_state.py/overview-views.js로TESSERACT6축·CROWDING5축·36시점궤적/4시점적층·회전/드래그/프레임취소·주도주웜홀/선택/원단위표 연결. z최대120/최소60/ddof0, SPY/EEM50:50, Wilshire가격지수/GDP상대변화는실제시총/GDP아님. 시총50표본중가격/분기NI가용49에서상위10;전체글로벌시총상위아님. 단위/발표시차/셧다운보정은 research/OVERVIEW_CONTRACT.md. CPQ4+3개월, 2025Q3GDP/CP는2025-12-23, 2025Q4GDP2026-03-13/CP2026-04-09로확인된지연보정;최신수정치PIT아님.

WTREGEN1거시/SPHB·SPLV·^W5000역사추가, ^FTW5000은37개관측으로긴창미사용. 원자료빈티지20260909T143552Z,가격1131/거시60/재무195. 원본사이트요청0;공식FRED/BEA/지수정의검증. 검사114Python·두검증기·3JS/13구문·51SVG래스터통과,새5이미지확인;브라우저QA없음. 로컬90.34MiB/512·공개JSON7.177MiB/8(게시패키지생성전). 실행ID20260909T145933Z,실제공개완료는runtime/state.json. 전체목표는진행이며다음은지정학상황/키워드기간변화/영향채널/공식GPR세부,위성/실적추정/SEC/KR달력과REFERENCE_PARITY의남은계약이다.


지정학 후속(2026-09-10): geoecon_views.py/geo-views.js로15주제4카테고리·상위6상황·5관심지역·19키워드30일/7일비중·6채널·3복합z/밴드·시장3이중축1년·GPR3지수/8역사분류/8국가1/3/10년 연결. RSS2/RDF/Atom 파싱을수정해BIS/DW미검출해소;이번7요청6성공/IMF HTTP실패,143응답. 부모빈티지URL합집합·KST가격기준일종료/수집미래제외·first_seen보존으로79제목. 짧은수집역사를당시완전한뉴스량이라고주장하지않는다. 제목단어/3단어부정어·주목도기사+위험표현2배는팀규칙. 채널노출=기사비중×7·주제중복제외,27자산/기사관측경로D0~20은인과효과아님.

GPR Stata1요청764625bytes/gzip334921을private빈티지보존, GPR/GPRT/GPRA272개월/상세120개월. SHAREH8은3신문기사%,국가GPRC8은10신문기사%,3최근지수1985–2019=100과가산금지. refresh는gpr_details7일기준으로정기갱신. 기존ASK네번째핵심도3복합중VIX/HY참조로정렬;과거3입력EPU/VIX/HY와차이문서화. 상세research/GEOECON_CONTRACT.md,코드/검사에공개. 새가격/원본사이트요청0.

검사121Python·두검증기·3JS(geo추가)/14구문·59SVG래스터통과,8신규이미지확인,브라우저QA없음. 원자료/실행파일98.18MiB/512·공개JSON7.405MiB/8. 게시실행ID20260909T152214Z/raw빈티지20260909T150119Z,실제공개상태는runtime/state.json. 전체목표는진행;다음estimate_verify/us_consensus분기/연간세부·위성실관측·SEC13F/P·KR달력/옵션·RS기간계약등REFERENCE_PARITY의미완료를계속구현한다.


실적 후속(2026-09-10): earnings_details.py/earnings-views.js로global NI표본Top20 굵은FY1/얇은FY2/실제tick,한국2기업 OP/지배NI(과거3A/다음2E),미국10기업 NI근사/직접매출(1A/2E),197기업 검색·연간4/분기8 NI/OP/매출3패널 연결. 손실0축왼쪽·누락대시·가격/재무/추정일분리·원천링크. 원본글로벌/US의미래NI는EPS성장연결근사였으며직접NI컨센서스아님을명시. 세계전체표본아닌198연구기업중환산196가용의실제NI상위20이다. AAPL/BRK-B를명시적연구목록에추가해앞으로주간갱신.

Yahoo이미받은earningsTrend의period/endDate만추가보존(추가요청없음),이번22기업재조회와FX5개수집. FY연속8일허용·통화일치·전년매출/FY2기준EPS5%이상차이차단·양의이전NI/EPS요구. NVIDIA의SEC FY2026실제말일1/25와제공처1/31구분,MSFT6월결산확인. BRK매출정의/TSMADREPS통화/SoftBank·Toyota전년기준불일치는NI근사미산출;원본의임의보수적보정복제없음. KR는QuantiWiseE121500/E122710/E121000 최신as_of≤가격기준,억원÷10000조원;현재2026-08-07추정날짜유지,2024/25AS를실제라고가장하지않음. FX는현재환율(최대7일경과)환산이며평균환율아님. 상세research/EARNINGS_CONTRACT.md.

검사129Python·두검증기·3JS(earnings추가)/15구문·64SVG래스터통과,새5이미지확인,브라우저QA없음. 데이터가격1136/거시62/재무연결197,개발raw빈티지20260909T152436Z. 로컬106.33MiB/512·공개JSON7.609MiB/8(배포패키지생성전). 게시실행ID 20260909T224449Z 실제공개완료는runtime/state.json. 전체목표는계속진행;한국증권사별원문/해외직접NI·OP/PIT,위성실관측,SEC코드P/13F,KR거시일정/옵션,RS/모멘텀/ETF기간계약등REFERENCE_PARITY 미완료를계속한다.

실적 게시 완료: 4ad84a5, run20260909T224449Z, Vercel47/47파일바이트일치확인. 최초deploy Not authorized였지만whoami/project inspect로기존계정·프로젝트접근확인후동일패키지재시도성공. 토큰만료원인확정아님. vercel_deploy.py에whoami사전검사추가(인증갱신은CLI소유,계정출력로그제외),실패시패키지/업로드미실행2fixture추가. 이운영코드변경은대시보드정적결과가같아추가Vercel배포불필요;다음정기실행부터적용. tests전체129+신규2=131,새운영검사는test_refresh전체로통과. 현재진행중exec없고배포pending없음.


SEC 내부자 후속(2026-09-10): sec_ownership.py/ownership_views.py/ownership-views.js로비파생P·취득A·접수시각확인90일카드/미니선/검색/복수보고주체필터·공시원장·SPY대비D0~20관측연결. 제공처후보8행대조→7공시9거래행4기업(PFE/CVNA/VST/CEG), AVGO1공시는원문P확인했으나접수시각미확보로집계제외. VST1제공처행은8/31·9/1의2실거래행,CVNA도2가격행. 공시/행/보고CIK수를분리하고가중가격·D/I·원문/색인·검토시각표시. P는공개시장또는사적매수,주체CIK는독립된경제주체보장아님. 10b5체크미확인은미확인그대로보존.

config/sec_ownership_reviews.json은공개SEC원문/색인에서검토한사실8공시이며자동갱신결과아님. 직접XML수집은같은accession을대체;Form4/A와관련원공시는격리. PC의company_tickers/submissions2요청은HTTP403로중단,추가원본사이트요청0·시세요청0. sec_collection.json.gz실패상태보존/화면표시,refresh에24시간단위시도연결(전체401/403/429즉시중단·최근120일·최대새300공시·최근목록기간부족partial·원자료512MiB). 전체미국시장/연속자동SEC피드성공이라고표현하지말것. raw개발빈티지20260909T225247Z(부모20260909T152436Z),기준2026-09-08. 상세research/OWNERSHIP_CONTRACT.md.

전체목표는여전히진행: 위성실관측·KR옵션/거시달력·SEC13F/연속수집·글로벌직접NI/OP·본사/교역·PDF추출/팀DB·RS/모멘텀/ETF계약은REFERENCE_PARITY에서계속. 새차트66개래스터중내부자2개육안확인,브라우저QA없음. 갱신에따라90일창이비어도동작하도록JS는실출력검사+날짜고정소스fixture로검사. 새검사/게시ID·커밋은아래최종기록과runtime/state.json을기준으로확인.

최종검사143Python·두자료검증기·3JS/16JS구문·66SVG래스터통과. 공개JSON약7.631MiB/8,PC원자료/실행약114.28MiB/512(배포패키지생성전). 게시실행ID 20260909T231908Z; 실제게시완료는runtime/state.json확인.


국내 거시 달력 후속(2026-09-10): kr_calendar.py/calendar_views.py/calendar-views.js로기존미국달력에한국은행통계127·통화정책방향회의8·국가데이터처통계181연간일정을연결. 향후90일(9/10~12/8) 한국77/미국52총129,출처13. 국가/7·30·90일/분류/검색·원문·출처별확인/마지막성공시각·stale표시. 한국은행상단월간격자대신하단연간표·정책선택연도검사,국가데이터처제목관측연도와공표연도분리·전체262행중연도명시통계181선별. 교육/행정/기준연도미표기제목은제외한범위다.

달력기준은가격일9/8과별도로최신달력수집일의KST날짜·90일양끝포함. 미국실시간대DST/KST날짜이월·미표기회의미국일자유지·임의발표시각없음. BOK금통위모든정기회의가아니라정책결정회의8건목록. HTML원자료·해시private보존,구축5공식요청(월간/진입확인2포함),기본정기3요청/7일·연도교차한국은행추가표. 실패한출처는이전성공시각/원일정그대로유지;새정상표로대체하며취소일정합집합복원금지. collect_raw현재실행재사용. 상세research/CALENDAR_CONTRACT.md.

개발raw빈티지20260909T232154Z(부모20260909T225247Z),가격1136/거시62/재무197변동없음. 부모파일필드는vintage(다른키아님)이며Data정상상속확인. 검사151Python·두자료검증기·3JS/17구문·66SVG래스터통과,원본사이트요청0·브라우저QA없음. 공개JSON7.703MiB/8,PC122.38MiB/512(새배포패키지생성전). 실행ID 20260909T233734Z;실제게시여부는runtime/state.json확인. 전체목표는아직진행: 위성실관측·국내옵션·직접글로벌NI/OP·SEC13F/연속수집·교역/본사·PDF추출/팀DB·RS/모멘텀/ETF최종계약등REFERENCE_PARITY를계속.


위성 후속(2026-09-10): satellite_data.py/satellite_views.py/satellite-views.js는22시설 슬롯·14검증위치/실제Sentinel2 C1 L2A·RGB/NDVI·평면Mercator지도/드래그/키보드/확대/3크기·시설 Entity와 기업 연결을 구현했다. 8미확인(M15X/평택/IntelOhio·Magdeburg/Vandenberg/Sabine/Ghawar/Permian)은 위치 대조 중으로 유지. 공식주소·OSM객체대표점 구분, Colossus1은FCC9쪽 공식gateway좌표. Magdeburg2025-07-24중단발표 반영. 원본좌표의도심/잘못된시설을 복제하지 않았다. 자세한 SATELLITE_CONTRACT.md/registry 참조.

공개COG 사용자opener로206/ContentRange/4MiB요청·192MiB실행전송한도,전체200응답본문거부. 4×4km/400×400/10m원밴드·20mSCL,band별scale+offset후NDVI,음수/분모0/구름제외. 전체70%/coverage98%에추가로중심1km85%·100m95%검사. QA에서Taylor/JASM/Meta공장위구름 발견해이전맑은장면으로교체. 14장면촬영2026-08-23~09-09,가격09-08과별개. 이전관측상속·위치서명변경시미표시·주간시도실패시stale. 건설진척/가동률미추정. 전체Esri배경미구현;로컬해안선과실제장면표시.

refresh의staging→공개복사에PNG가누락되는경로를수정하고회귀검사추가. rasterio1.5.1/affine3.0.1/click8.5.0설치,기존Pillow12.2.0선언. 원자료빈티지20260909T234733Z(부모20260909T232154Z),PC캐시약147.12MiB/512(새배포패키지전),공개JSON7.733MiB/8·PNG7.312MiB/24. 160전체Python+신규게시1검사=161,운영/위성24검사통과,2검증기·3JS·18구문·69SVG래스터·28PNG해시/품질확인. 브라우저QA/원본사이트추가요청0. 새게시run 20260910T001619Z;실제배포완료는runtime/state.json. 목표계속진행:8시설/전지구배경,KR옵션,SEC13F/연속수집,직접NI·OP/PIT,본사/교역,PDF추출/팀DB,RS/모멘텀/ETF기간계약 등REFERENCE_PARITY 남은범위를진행한다.


위성22곳 후속(2026-09-10): 남은8기준점을 대조해22/22 실제 RGB/NDVI를 확보했다. 평택은삼성캠퍼스복지1동공식지도,청주M15X는공식4공장주소/배치와기존M15지도기준점(개별M15X중심아님),Ohio는Umbra 공개METADATA sceneCenterPointLla(3754bytes만,대형SAR미다운로드),Magdeburg는시의회DS0471/25계획도/EulenbergOSM지형점·중단계획부지,Vandenberg는SpaceX안내서PDF73쪽발사대,Sabine은Cheniere공식지도장소핀. Ghawar는Uthmaniyah가스처리시설,Permian은NASA Yates사진중심의4km한정관측이다. 유전/분지전체생산·매장량대표로표시하지않는다. 공식PDF/좌표/검색응답은private satellite_research에보존.

후보12개로Magdeburg맑은장면누락을확인해60일최대36개로확장,조회캐시에위치/범위서명·후보상한을포함했다. 청주출입구대신캠퍼스내기존M15시설기준점으로확정하고9/8영상·공식배치대조. Ghawar RGB0~0.3에서대부분사막이잘려고정0~0.65로표시,원장/상세에노출하고NDVI/통계불변시험통과. 품질70%/중심1km85%/100m95%기준유지,22촬영일8/13~9/9. 8새원밴드만추가,raw빈티지20260910T002037Z(부모20260909T234733Z).

검사163Python·두자료검증기·3JS·18구문·69SVG래스터·44PNG해시통과,신규8RGB와Ghawar보정RGB/NDVI육안확인. 원본사이트추가요청0·브라우저QA없음. PC약193.04MiB/512(게시패키지전),공개JSON약7.743MiB/8·PNG약11.694MiB/24. 게시run 20260910T004737Z;성공상태는runtime/state.json. 전체목표는계속:전지구위성배경·KR옵션·SEC13F/연속수집·해외직접NI/OP/PIT·관계망/본사/교역·PDF추출/팀DB·RS/모멘텀/ETF등최종기간계약. 다음은쉽게검증가능한RS/모멘텀/ETF원본계약부터보존소스와대조가능하다.


가격 세부 후속(2026-09-10): RS는KOSPI200 KPI/4개강약8표·시장필터·강8+최약6막대, 고정−3.2~3.2축/정수눈금/±1±2가이드/클립/원값툴팁을연결했다. 순위 pct_rank*98+1오류를1+98*(평균rank−1)/(N−1),단일50으로수정해다른rank소비모듈도전체재계산. 모멘텀32곡선은상위16이아닌강8+약8을짝3M/6M으로선택,막대순country/sector/factor/asset·그룹별3M정렬열지도,오래된자산이전체기준일을뒤로잡는문제수정. nice눈금/0눈금추가·SVG XML hidden속성값명시.

etf_details.py는9분류73위치(미확보삭제금지)·10열통합비교/주기간격/월간상위/금액입력/정렬검색/배당락일원장.12M창좌측제외·미래가격제외·Dividends현금합/시장종가·분할이중보정금지·미확보와0분리.기존Yahoo원자료만재사용하며공식YieldMax주간/QYLD매도구조/TQQQ일간배수자료는웹대조.원본NVDY등월배당오류미복제;원장날짜는지급일아님.별도Capital Gains/ROC/공식지급일·전상품운용사대조는남음.ETF_CONTRACT.md 참조.

compare_reference.py는부모/보정빈티지와공식이름별칭을사용.원본RS9/6(가격9/4) vs모멘텀9/8작성일을분리.현재34페어대조US17/17스프레드정밀도일치/z최대.0393;KR17중11일치·공식상품대응차이포함최대21.2593pp/z2.3913.현재모멘텀가격비/일간합/복리후보가원본PNG끝점과불일치하며임의피팅없음.보존원본new_highs에서S&P100/KOSPI200·RS≥65/52주고점5%이내/미니선기능을발견했고다음구현대상으로명시.IVV500으로이기능을대체완료하지않을것.

raw추가없음(빈티지20260910T002037Z),원본추가요청0.170Python·두검증기·3JS/18구문·74SVG래스터·44기존PNG검증통과.5가격래스터육안확인·브라우저QA없음.공개JSON7.794MiB/8·PC212.85MiB/512(새게시패키지전).실행ID20260910T011449Z;실제게시완료는runtime/state.json.현재exec모두검사종료이며새배포핸들은진행시확인.전체목표계속:모멘텀신고가/OEF공식100유니버스·원본누적곡선,세계위성배경·KR옵션·SEC13F/연속수집·직접NI/OP·교역/본사·PDF추출/팀DB등REFERENCE_PARITY.


신고가 발굴 후속(2026-09-10): us100_data.py는 iShares OEF 공식 CSV의 Equity만 선별한다. 9/4 구성101개·BRKB→BRK-B·주식 클래스 보존, 현금/선물 제외·날짜/펀드명/가중합/중복/SHA256 검사. 7일1회·최대1MiB·실패 별도 기록/같은빈티지 재시도없음·14일초과 미확보. refresh와 신규25종목 제한에 연결했다. 첫17323bytes 한 요청, 새가격/원본사이트 요청0. raw 빈티지20260910T011831Z(부모20260910T002037Z), 가격 기준9/8.

momentum_highs.py/momentum-highs.js는 OEF101중RS100/후보9와 공식KOSPI200201중RS199/후보4를 계산했다. HONA/0126Z0.KS/0220W0.KS는 가격 준비 부족. 전체 가격가용 구성에서 RS1~99 순위 후 RS≥65/고점−5% 조건 적용, 조정OHLC를 현재시장종가단위로 환산·252관측 장중고점·130관측의44점 가격선/고점 점선. 마지막고가가 전일까지252고점을 엄격히 초과할 때 장중갱신 배지. 시장/검색/갱신 필터, 전체구성/제외원장/44점 상세를 추가했다. 원본 미국9/8작성가격은9/4종가에 부합, REGN/VRTX는현재공식OEF에없어 임의추가금지. 한국원본 '시총상위' 미공개절단 대신 공식전체 사용. NEW_HIGHS_CONTRACT.md에 차이를 공개했다.

179Python·2자료검증기·3JS/19구문·76SVG래스터·44PNG검사통과, 신규2가격미니선 육안확인·브라우저QA없음. README와 생성SUBVIEWS에RS/모멘텀 별도필터 기록. 공개JSON약7.885MiB/8, PC512MiB 한도유지. 실행ID 20260910T014245Z; 실제배포상태는runtime/state.json 및 해당 file-verification 보고서 기준. 전체목표는계속:원본모멘텀누적곡선/정확한사전표본·전지구위성배경·KR옵션·SEC13F/연속수집·직접글로벌NI/OP/PIT·본사/교역·PDF추출/팀DB 등 REFERENCE_PARITY 남은범위.


2026-09-10 배포 출처 제외 요청: 사용자는 배포 웹사이트의 참조 제작자 이름·관련 출처 표기를 전부 제외하도록 지시했다. 현재 docs 정적 파일과 실제 열린 모멘텀 화면에서 이름/참조사이트 링크는 발견되지 않았다. scripts/validate.py에 배포 docs 전체의 이름 변형·HTML/URL/Unicode escape 및 참조 도메인 검사 추가, 정기 갱신 시 재등장하면 게시 중단. 연구용 대조 문서는 docs 밖에 유지한다. 현재 PDF 본문 추출 후속은 원본 principium.js 업로드 계약/PDF.js 공식문서·npm 메타 확인까지만 수행했고 다운로드/코드변경은 아직 없다. 다음 목표 턴에서 이어갈 것.


PDF 본문 후속(2026-09-10): pdf-text.js/notebook-pdf.js를 PRINCIPIUM/IW/ASK에 연결. 공식 npm PDF.js6.3.289 legacy파서/worker+CMap168+표준font14+license4=188파일3811556bytes, tarball8503425bytes SHA512/개별SHA256 검증. 같은사이트lazy import/worker이며 문서업로드/API/외부CDN없음. .gitattributes로업스트림byte를Windowscheckout에서도유지. public_assets.py가파일누락/추가/해시/8MiB한도검사,패키지.mjs/.bcmap/.pfb/.ttf허용·정기JS구문검사23파일확장. PDF runtime assets는정상오픈소스배포라이선스를보존한다.

본문은파일당25MiB(보존원본상한대응),300쪽/20만문자/90초. 한글·영문·부호/단위,물리페이지+문서라벨,파일SHA256,제목/저자·본문·부분범위를보존. 저장 전인용발췌/12000자한도·기존입력보존,전체추출본문검색·TXT. 스캔본문없음/OCR필요,손상·암호화·취소구분;원문배치/표순서별도확인. auto-core는추출기록임을표시하고AI요약으로주장하지않음. Node현재runtime은지원폭이넓은legacybuild사용;@napi-rs/canvas미설치경고는Node이미지렌더용이며텍스트실제파서검사정상,브라우저기능도정상. 실제PDF미리보기/그림렌더는제품에없으며PDF원문다운로드가능.

research-store DB/schema2,기존같은DB의meta/files보존·oldversion연결닫기·v1백업/본문/Blob보존. 기존2MiB메타/64MiB첨부한도유지하고전체추출본문은메타한도에포함;초과시atomic실패/입력유지. 원문첨부없거나페이지/문자/부분범위모순은거부. 첨부제거시해당글의추출본문도제거. 파일당25MiB확대는사용자선택로컬첨부이며PC raw512MiB정책과별개.

181Python·2검증기·3JSsuite(실제PDF파서/신규저장UI검사포함)·23JS/MJS구문통과. 합성PDF4(혼합한글영문+스캔·암호·손상·302쪽),3페이지래스터중영문/한글육안확인. CUA localhost에서선택→실제worker→한글2쪽/라벨ii→원문근거→저장→새로고침→본문에만있는숫자검색→페이지전환·화면검사. 테스트자료만사용,localhost의 [QA] PDF 추출 검증 기록은공개사이트개인DB와별개. 전체25탭브라우저QA라는뜻아님. pdf-browser-qa.json과pdf-fixtures,검사로그는private runtime. 새price/원본사이트요청0,raw빈티지20260910T011831Z동일,원자료추가없음(의존성archive/합성fixtures만추가). run 20260910T021913Z,게시최종상태는runtime/state.json/file-verification. 목표여전히진행:OCR·분류/번역/LLM요약/팀공유DB·로그인과REFERENCE_PARITY의세계위성배경·KR옵션·SEC13F/연속수집·직접NI/OP/PIT·본사/교역·원본기간등.


국내 숏감마 후속(2026-09-10): 보존 risk.json은 옵션 GEX가 아닌 ETF 리밸런싱·가격 진단8행이었다. 이전 OI/IV 필요 판정을 정정. kr_shortgamma_data.py/kr_shortgamma.py로 KRX 지수1028 실제OHLC728·공식기초지수/배율19ETF·보고순자산·월간옵션실제최종거래일을 연결했다. 현물/선물지수 분리·업종형/해외/KOSDAQ/커버드콜/ETN제외. ±1%1881.7479억원·1σ5869.2748억원(2026-09-08 기준),실제딜러보유/주문/설정환매/영향예측아님. RV21표본단순수익률49.513459%,비율1.073815·고저15%극단7/20·D-2(9/10)이다.

원본 미공개 점수는252일장중고점90~100%gate와RV252z/21일가속/RSI14/63일속도40/25/20/15팀규칙.0~100축/45·70선·252거래일곡선, RV5/21두계열·25/40선,60거래일최대/펼침원장,8행표줄바꿈·19ETF표·기초별양음금액. 새2차트는팀추가이며원본의별도옵션차트라고주장하지않는다. 현재정의조회9/10 vs가격/AUM9/8분리·PIT구성이력아님. 원자료 +215447bytes, 빈티지20260910T023239Z(부모20260910T011831Z). 일반가격/미국옵션등기존모듈수치는변경없고 risk/ASK요약·상태/Overview빈티지만부모상속동일가격기준으로갱신.

refresh의기존allow_krx_auth 경로에연결·index10달력일겹침의신규/정정행만추가·정의/만기7일주기·실패이전파일보존. 실제수집시코드조회3파트(index2구간)외추가원본요청0. 승인계정로그전체억제,필요한공식기초정보만로컬보존. collector모의실패/증분1검사포함190Python·2검증기·3JS·23JS/MJS구문통과. CUA localhost에서8지표·252일두SVG육안·계산원장접힘/펼침·122630검색/초기화검증. 테스트증거runtime/kr-shortgamma-browser-qa.json,최종검사로그kr-shortgamma-final-validation.log. PC약306.4MiB/512,공개JSON약7.925MiB/8(배포패키지전). 게시run 20260910T025609Z;실제최종성공은runtime/state.json 및 file-verification을확인.

전체목표는여전히진행: 모든공통그룹에콘텐츠가연결됐다는사실은전체원본동등성완료가아니다. REFERENCE_PARITY의세계위성배경·관계망확대/본사/교역·SEC13F/연속수집·직접글로벌NI/OP/PIT·원본미공개기간/모델·OCR/LLM/공유DB등을계속한다. 참조제작자이름/출처사이트링크의배포제외검사를항상유지한다.


전 지구 배경 후속(2026-09-10): satellite-tiles.js/satellite-views.js에NASA GIBS BlueMarble_ShadedRelief_Bathymetry 고정2004-08 배경을 연결했다. 공식EPSG3857 WMTS,256px/level0~8,배경500m 원자료와시설10m/촬영일을분리. 드래그/키보드/날짜변경선·전체시설fit·실제폭ResizeObserver·높이400/560/760·확대19(배경8이후확대표시)·RGB/NDVI·해안선전환. 관측아래불투명matte로구름/결측에과거배경이비치지않게했다. 원본Esri고해상도/지명레이어는구독권한질문중이며NASA로동등성완료선언금지. 추가원본사이트/시세/시설원밴드요청0;같은raw빈티지20260910T023239Z의44PNG재생해시불변.

viewport타일만동시3/180ms,12초/1MiB/최대100화면타일,48Blob/8MiB캐시·화면밖/숨김/drag/탭전환abort·URL해제.401/403/429/503추가요청중단과명시재시도; 앱지속저장/전지구수집없음,브라우저HTTPcache는별개. 구체계약은SATELLITE_CONTRACT.md. 기존Sentinel주간증분/평일08·18파이프라인유지,새JS검사기와배경메타검증을정기게이트에연결.

190Python(117.726초)·2검증기·3JS suite·24JS/MJS구문통과. 신규offline타일검사에원점/극지/날짜변경선/확대·동시성·중단·429·JPEG스트림/1MiB·48LRU·URL해제포함. CUA로NASA전지구12/12·TSMC14배1/1·RGB/NDVI·3높이·방향키·배경off/on·다른subview이동시지도제거및console오류0확인. 전체25탭브라우저검증이라는뜻아님. 검증기록은private runtime/satellite-basemap-validation.log 및 satellite-basemap-browser-qa.json. 게시run=20260910T032324Z;실제성공commit/URL은runtime/state.json과file-verification을확인. 전체목표여전히진행:Esri고해상도/지명(권한확인)·원본추가터치/비행애니메이션대조,관계망/본사/교역·SEC13F/연속수집·NI/OP/PIT·원본모델/기간·OCR/LLM/공유DB등.


멀티에셋 자산 모니터 후속(2026-09-10): 보존 multiasset.json/app.js의4KPI→21자산6기간열지도→1M내림차순/중앙0/좌우대칭막대→6자산군4열표를 asset_monitor.py와 전용 렌더러로 연결했다. 막대색은 수익률 부호가 아닌50/200MA 추세이며 범례/툴팁에 표시한다. S&P500/Nasdaq Composite/Russell2000/금은 SPY/QQQ/IWM/GLD 대용에서 실제 ^GSPC/^IXIC/^RUT/GC=F로 수정했다. 별도 배분/스캐너의15개섹션은 기존 계산값 그대로 유지했음을 객체 비교와 화면 전환으로 확인했다.

수익률은1/5/21/63/252관측 간격, YTD는 전년 말이 아닌 연초 첫 종가다. 미국9/4·한국/일본9/8·유럽/선물/FX/크립토9/8장중 가설로 원본6기간의 반올림 가격구간이21자산 모두 양립함을 대조했다. 유럽9/7 가설은 불일치해 폐기; 추론된 가격은 공개 결과에 넣지 않았다. 원본MA 세부 조건 미공개로 팀 가격>MA50>MA200/역배열/동률중립을 명시한다. 200관측 미만·7일초과 지연은 미산출, 크립토 주말 유지·미래행 선제 제외·ETF6개 조정종가/나머지 원종가·환율방향·선물비용 미포함. 실제 심볼/단위/종가/MA/관측수/6기간 분모날짜를 펼침표에 표시한다. 자세한 MULTIASSET_MONITOR_CONTRACT.md 참조.

새 ^RUT만3년752행 수집, raw +17721bytes, 빈티지20260910T033238Z(부모20260910T023239Z), 가격1137종/기준2026-09-08. 기존 가격은 상속, 원본사이트 추가 요청0. 정기 가격목록에 ^RUT 추가; ACTIVE인 기존 automation의 평일08/18 refresh --publish 경로 확인, 새 예약 없음. PC약353.865MiB/512(게시패키지전), 공개JSON약7.934MiB/8.

196Python(122.685초)·2자료검증기·3JSsuite·24JS/MJS구문 통과. CUA localhost에서4KPI/21×6열지도/21정렬막대·추세색·0선, 6표의4열노출·상세가격 비축약·21기준일원장·숫자정렬·Russell검색·스캐너/배분 전환·console오류0 확인. QA에서 표 min-width로 신호열이 가려진 문제를 전용 CSS로 수정하고 수평overflow0 재확인; 마지막 UI 변경 후 관련 JS suite/구문 재통과. 전체탭 브라우저 동등성 선언 아님. 증거는 private runtime/asset-monitor-validation.log, asset-monitor-browser-qa.json, asset-monitor-reference-audit.json. 공개 출처 제외검사 유지.

게시 run 20260910T035436Z; 최종 커밋/URL/성공은 runtime/state.json과 해당 file-verification 보고서를 확인한다. 전체목표는 계속 진행: 원본 미공개MA/모멘텀누적곡선/모델설정, 관계망확대·본사/교역, Esri고해상도/지명(권한 질문 대기), SEC13F/연속수집, 직접글로벌NI/OP/PIT, OCR/LLM/팀공유DB/로그인 등 REFERENCE_PARITY의 남은 범위는 미완료다.


전략 카드 후속(2026-09-10): strategy_cards.py/strategy-cards.js/config strategy_screens.json은 턴어라운드의 연간3개년 이익 저점반등·흑자전환/4점근거/252종가 저점·고점·MA200·FY EPS·44점과 지정 US9/KR4 페어카드를 연결했다. 기존 분기흑자전환+8대형캔들과 퀀트 자동발굴 한국10쌍의 재사용은 전략 화면에서 교체했다. 퀀트 자체는 불변, 내부자/PEAD/실적모멘텀11개섹션은 객체 동일성 확인. 모듈 요약 스키마는 cards=[[label,value]]이며 별도 kpis 필드는 쓰지 않는다(재등장 검사 추가).

공식706합집합 중 수집141/연간3개년140, 후보13(기본8/전체13/KR6), 미수집565와 ISRG연간부족을 전체검사완료로 표시하지 않는다. 연간간격330~400·최신550일·최근이익양수/직전저점, 가격저점+10이상/고점−15이하; 점수기본1+흑전1+MA200상회1+FY EPS성장15초과1. 이절단/사전표본은 명시한 팀규칙, 원본 비공개Python과 같다고 하지 않는다. Fiscal2027인 CSCO 추정기간과 실제2024~26 NI를 분리, 통화/조회시각/정확한 수치 표시. STRATEGY_CARD_CONTRACT.md에 계약 기록.

페어는252공통조정종가 로그OLS·120스프레드평균/표본sd1·252일수익ρ·130관측3간격44점, |z|내림차순/±2방향. 원본 미니선은 log(A)−βlog(B), 점선은 표시min/max중앙이며 z0/평균선아님. 미국9쌍은원본9/4가격β2자리/z2자리 모두일치, KR은정정/기준시각차이유지. 추가Engle–Granger 상수/maxlag5/AIC p값은I(1)/다중검정전진성과완료의미아님; p미통과도13지정자리를보존. 미확보/252미만/7일초과/상수/비양수β는표시구분. 지연/미래행/중복/정렬/분기혼용/점수경계 검사.

부족했던CSCO/PYPL/BA/003670.KS/010130.KS/024110.KS/030200.KS의7재무를기존수집기로추가(23523bytes); 일반시세/원본사이트요청0. 원자료 정본은 DATA/expanded/20260910T040459Z, 부모20260910T033238Z. cache.chain은 expanded를사용한다. 새파일은초기경로오류후경계확인하여expanded로옮겼으며기존빈티지/자료는변경없음. 로컬펀더멘털객체212·가격1137; 기존전역 financial_companies는financial_rows 표본197의뜻으로유지. default재무수집에7심볼합집합추가·기존7일주기/평일08·18검증게시연결.

205Python(119.512초)·2자료검증기·3JSsuite·25JS/MJS구문통과. CUA localhost: 요약13/140of706/13, 기본8/전체13·한국6·003670검색/연간원장,13페어/13미니선/13중간점선·미국/ADBE검색·252/120/β/p 상세·console오류0·가로overflow0. 상세는비축약숫자,카드는원본처럼티커/이름·요약정밀도구분. private runtime/strategy-cards-validation.log, strategy-cards-browser-qa.json, strategy-card-reference-audit.json 참조. 전체탭동등성QA아님. run 20260910T042518Z; 실제성공은state.json/file-verification으로확인.

전체목표계속. 다음직접확인가능범위는PEAD 원본12카드/발표후가격미니선이다: 보존12행은서프라이즈+드리프트내림차순과부합하나정확한이벤트기간/가격시작점을추가대조할것. 원본종목을고정후보로복사하지않고 실제발표시각/현재표본으로재계산한다. 나머지미수집재무/발표빈티지·본사/교역/관계망·Esri권한·SEC13F/연속수집·직접글로벌NI/OP/PIT·OCR/LLM/공유DB등 REFERENCE_PARITY 남은범위유지. 배포제작자이름/소스사이트링크/Rosenbach 제외검사유지.


PDF 파서/OCR 최적화(2026-09-10): docs/pdf-ocr.js·pdf-text.js·notebook-pdf.js로 파서 우선/필요 페이지 OCR·파서만/전체OCR·한영/영어·한단/다단 선택을 연결. PDF.js6.3.289, Tesseract.js6.0.1/core6.0.0, eng fast4.1.0/kor best4.1.0 선택. 합성6쪽에서 정밀전체13.73s→선택9.11s(약34% 단축), 같은 결과 재사용0.157s, 렌더링40% 감소. 정밀 선택은 숫자 문자열24/25 일치(남은1개는 천단위쉼표 누락), 한글 일부오인식은 남아 원문대조. 경량kor는 숫자값오류가 있어 기본에서 제외. 공식고정해시/라이선스11파일21,660,329bytes, 개별필요시동일출처로만로드, 문서외부업로드0.

페이지300/20만자·회당OCR30/180s·최대8M화소, 해시/버전/언어/모드/배치/DPI 일치 완료페이지재사용 및 대기이어읽기, OCR실패파서보존, 취소시activecanvas해제, 백업메타검사/구버전호환. docs/index.html은pdf-text.js앞에pdf-ocr.js추가. 사진·PDF 원문·벤치마크·이미지는private runtime/pdf-ocr-fixtures. 상세research/PDF_EXTRACTION.md. 새로운시세/원본사이트요청0, raw빈티지20260910T040459Z/가격기준2026-09-08유지.

prune_staging이날짜가붙은작업만최신2개유지하고검증게시뒤에도실행. 수동검토폴더·원자료유지, 실제21개임시복사본정리265,229,784bytes회수. 검사207Python/두검증기/3JS/30JS·MJS구문통과. 실제로컬브라우저첨부→OCR→인용→저장→새로고침→본문검색→캐시재사용통과. 게시실행20260910T050723Z, 실제배포는runtime/state.json확인. 전체목표진행: 원본PEAD카드·관계/교역·실적입력·SEC자동수집·LLM요약/공유DB 등REFERENCE_PARITY의남은범위계속.

Grok 디자인분담수신: 별도worktree grok/dashboard-design-20260910, 기준0097d49. 공동sangsangin-investment-collaboration/ASTRA_STATUS.md에PDF새select/스크립트순서계약기록. Grok미착수확인, 완료커밋이오면현재기능위에서검토/통합/검증/게시한다. 사용자일정예측요청은철회됨; 기능구현과측정기반최적화를계속한다.


PEAD 카드 후속(2026-09-10): 공식 S&P100 OEF 공시 주식101개 중 기존35재사용·66발표일 추가조회로101개 확보. pead_data.py는3일 이내 정상 earnings_dates 재사용, 실패 시 이전 정상값·조회시각 보존; 평일08/18 refresh에 연결했다. raw빈티지20260910T052642Z, 부모20260910T040459Z, 신규38258bytes. 시세/원본사이트 추가 요청0. 수집 당시 source_url 힌트 중 이전 /quote/.../calendar/ 형식이 있을 수 있으나, 공개 링크와 후속 수집은 공식 calendar/earnings?symbol= 형식으로 구성한다.

pead.py/strategy-cards.js는 최근60일 최신 확정 EPS·양의 서프라이즈·양의 표시구간 변화 조건으로48후보/기본12개, 모든 일별가격선·서프라이즈·달력일/기간·검색/전체보기·원장과 제외53종목 사유를 연결했다. 원본12카드의 '드리프트'는 발표5일 전부터인 작은선의 첫→끝 변화와 전부일치했다. 실제 발표 후 드리프트로 잘못 해석하지 않도록 표시구간 변화와 D0 이후 수익을 분리했다. 사전표본/60일/양수절단/합산순서는 팀설정이며 비공개 원본 엔진 동등성 주장이 아니다. 상세PEAD_CONTRACT.md.

가격 첫반응16시/공식13시 조기폐장(2026~2028), 미래/중복/지연/미도래기간·SPY날짜분모·5일 전 가격준비·최신음수/동시각충돌 검사. 다른전략그룹 객체불변 확인; 기존60기업180일원장은 제목으로 별도범위 표시. 원본8개 큰 초과수익 scatter는 미니카드로 교체하고 D0~20 관측은 상세원장에 보존. 전체기간가격(최대60+5달력일)이며44점으로다운샘플하지않는다.

첫 전체213Python/두검증기/3JS/30JS·MJS구문 통과. 실제 Edge1440/1024/390에서12/48·검색/상세·미도래D20·가로넘침0·console오류0; CUA에서NVDA표시구간+5.127606% vsD0후−0.986929%·SPY관측·출처링크 확인. 마지막출처링크/중복날짜수정후 최종검사 상태는runtime/pead-final-validation.log, 배포run 20260910T054223Z 결과는state.json/file-verification 보고서를 확인한다. 원본가격선 대조·검수이미지는private runtime/pead-*에만 둔다. 전체원본세부탭 구현완료는 아직아님.

전체목표계속: 관계망전체/본사/교역·Esri고해상도/지명권한·SEC13F/연속수집·직접글로벌NI/OP/PIT·LLM요약/공유DB·원본기간/모델설정 등REFERENCE_PARITY의남은범위유지. Grok worktree는확인당시 HEAD0097d49/완료커밋없음; 별도세션/Claude전환은문의만있고아직생성하지않았다. 최종통합은이메인에서수행.


미국 옵션 수집·범위 후속(2026-09-10): 공개 설명의SPY GEX는7~50일·행사가±15%이며 전체시장전만기를 요구한 이전TODO를 바로잡았다. options_data 정규화는제공범위의모든만기/중복·경계검사, 별도주식수급은기존7~45일첫3만기 유지. 만기별OI/GEX집계·같은행사가ATM·수집당시현물/금리를사용하는과거체인처리와갱신상태표코드를구현. Cboe자동추출금지안내를확인하여index/stock/eventstraddle 두수집경로모두기본비활성화했고사용자허용API질문응답대기. refresh는설정boolean true만명시플래그전달,이번에권한설정변경없음. 다른Yahoo/KRX갱신은옵션중단으로실패하지않는다.
보존SPY12086계약응답에서2328계약/11만기/OI유효1836/GEX유효1825를로컬검산,만기합계반올림오차1e-6. 새네트워크0회·새시세관측아님·3%금리시험가정. private runtime/options-offline-qa.json. 게시JSON과raw빈티지는PEAD게시본을유지하며새범위결과는아직게시하지않았다. 정확한상태는research/OPTIONS_CONTRACT.md. 코드·공통차트통합후전체검사예정.

디자인통합(2026-09-10): 완료커밋eba8931을main의0eb47e1로통합. 별도원본작업과데이터변경없음. 검토중2D시계열필터교체후이벤트누락/중복연결가능성을발견해상위영역위임과SVG별WeakMap으로보완. 실제Edge5대표화면×3너비,keyboard한날짜이동/DOM교체후End·3D회전/확대/선택/터치/초기화통과. 219Python(127.636초)·두자료검증기·3JS모음·30구문통과. 신옵션메타없는게시스냅샷은이전계산종가/옵션시각을구분하는캡션을유지. 가격JSON/빈티지는PEAD것그대로,새SPY11만기결과미게시. 게시run20260910T062723Z,완료는runtime/state.json확인.


리스크 콕핏 후속(2026-09-10): allocation_views가 allocation_book(33상품 현재 ML 국면 목표비중·원점/적용월·기존96월 비용후성과)을 함께 내보내고, subview_modules에서 배분 계산 직후 risk_cockpit.views를 실행한다. macro_modules의 임의6ETF비중/단일SPY스트레스를 제거했다. 완료월 마지막SPY세션 정렬·BTC전날UTC·정규 월격자/결측무보간으로 현재비중120월 변동성/음수VaR·CVaR/MDD/HHI·BIL현금을 계산한다. 원점2026-08-31/적용9월, 표본2016-09~2026-08, VaR95 -4.304004%, CVaR95 -6.668368%, 변동성11.195272%, 월말MDD -22.546602%. 현재배분 비중·성과와 콕핏 외 위험그룹은 적용전후 동일 대조했다.

콕핏 기준4패널(위험/9요인/5스트레스/신호신뢰도)과 비중·회귀·충격/기여·ML분모·120월 원장을 구현했다. 요인은60개월 동시OLS, rank10/R²/조건수/기간·대용명/공선성 설명. config/risk_stress.json은5×12 팀 충격 가정이며2008/2020도 실측 재현 아님, 숨은 원본행렬로 오인하지 말것. ml_transformer 전체OOS원장을 재학습 없이 읽어3지수1M/3M의±1%중립3분류를 계산한다. 중립예측제외 방향/전체/각클래스 n·적중수·n0미산출, 만기·학습종료 검증. 기본1M 각163실현타깃,3M159; 방향분모는 중립예측 제외로 다르다. research/RISK_COCKPIT_CONTRACT.md 정본.

추가원본사이트/시세수집0·새raw0, 기존빈티지20260910T052642Z 유지. 옵션추가수집권한은 여전히응답대기이며 다른옵션GEX/OI/수급값은 변경하지 않았다. 공개JSON약7.894MiB/8. 콕핏9개 신규단위테스트·공개비중/원장/충격/분모검증 추가. 실제로컬Edge1440/1024/390에서4패널·33비중정렬·원장펼침/120월·ML30행·n0표시·하위탭왕복·페이지넘침0/JS오류0. 전체회귀228Python(146.162초)·두자료검증기·3JS회귀·30공개JS/MJS구문통과. 실행ID20260910T065158Z, 실제게시상태는runtime보고서/state.json 참조. 전체목표미완료: 다음리스크신호등/선제위험 세부 입력 및REFERENCE_PARITY의남은항목을계속할것.


신호등·선제위험 후속(2026-09-10): risk_signals.py/config risk_signal_rules.json은 US12/KR7 신호·시장요약·KR63세션/연속경계와 S&P500/KOSPI의 CSD/변동성군집4진단을 연결한다. 새로운2보조곡선은252관측·0–100축·40/66선·두계열이며원본옵션차트가아니다. 공개 대표임계값은유지하되비공개 다단계점수/기간/가중치·뉴스분모는팀설정/대용임을표시한다. 미확보/기한초과는회색·시장판정보류, 완전관측만KR경계6점이상연속집계하며결측/63세션경계하한을보존한다. 단위/수치6자리표시·출처/원관측일/실제성공시각/수집실패원장을추가했다. 연구정본research/RISK_SIGNALS_CONTRACT.md.

공식KRX 파생및기타지수화면과검색에서코스피200변동성지수1300(1/300)/MDCSTAT01201을확인했다. VKOSPI/시장전체코스피주식금액수급각244일과SF Fed Excel Data시트감성1088일을수집,raw빈티지20260910T070347Z(부모052642Z)다. 기준9/8 VK47.34·외국인6482.245269억원·기관6426.900246억원. 외국인은기타외국인제외,기관1~7합·전체11분류순매수합0·정수원/OHLC/코드/미래/중복을검사. 뉴스최신8/30 원지수−0.0050573768…의252중간순위백분위47.817460이며기사긍정비율이아니다. US12/12·1점정상,KR7/7·5점주의,KR연속경계0일.

수집기는기존평일08/18 refresh에연결. 승인KRX만조회·동일마감재사용·10달력일겹침의신규/정정·VK정의30일캐시,뉴스7일/최대2MiB전송/최근3년변경분. 인증로그억제,실패이전관측과성공시각유지·같은빈티지재처리시기존delta지워지지않게수정. 원본사이트추가요청0·일반가격/미국옵션신규요청0. 원자료/인증HTML은private에만보관하며현재PC약234.3MiB/512,공개JSON약7.899MiB/8이다.

검사239Python(216.513초)·두검증기·3JS·30구문통과. 실제Edge1440/1024/390에서19행/4진단/2×252차트·0/100/40/66·63원장·수집3행·정렬·키보드/탭왕복·가로넘침0/오류0. 첫이미지검수에서readable-table의4열비율이추가열을0폭으로만드는문제를발견해5열이상은자동폭/최소960px로수정,숫자줄분할/모든열실제폭검사를추가후재통과했다. 기존콕핏및다른리스크64섹션의데이터객체불변대조. runtime/risk-signals-validation.log 및risk-signals-browser-qa.json, run 20260910T075346Z 보고서참조. 실제게시완료는state.json/file-verification을확인한다.

전체목표는계속진행. REFERENCE_PARITY의사업/공급관계255객체581관계·본사/교역·SEC13F/연속수집·직접NI/OP/PIT·LLM/공유DB와원본비공개계산/기간등은아직남아있다. Cboe허용API/자동수집권한질문은응답대기이며추가수집/새옵션범위공개는하지않았다. 새세션은사용자문의에분담방식만답했고생성하지않았다. 다음에는새확보지표의ML/MAXIMUS입력대응또는미완관계/교역을실제소스와재대조해진행할수있다.


교역 후속(2026-09-10): trade_data.py/trade_views.py/trade-views.js, config/trade_areas.json은 UN Comtrade45통계지역의2024년 상품 TOTAL 수출을 독립 수집·표시한다. 자료42지역/1840방향, RU/AE/VN 수출 응답은빈값이고 상대국의이들지역향수출은별개다. 미국842/프랑스251/스위스757/노르웨이579/인도699/UN490(S19)를 공식reporter/partner두사전과대조. UN490을대만전용통계로단정하지말것. World0 분모·원금액decimal문자열·보고/집계플래그를보존하며incoming도상대보고국수출이다. 원본교역금액은회사매출/특정품목/물리적항로가아니라국가TOTAL이었고이전TODO의품목필수조건을정정했다. 계약research/TRADE_CONTRACT.md.

정사영/10도경위선/대권곡선/지평선클립/방향삼각/로그굵기·상위10/20/전체·검색/UN코드/정렬·정확USD/분모/출처·포인터/키보드/휠/회전/확대·명시적자동회전/탭해제취소를연결. 기존기업소재국2섹션과다른계산은그대로다. 보존globe.js의별도SAURON은3D카메라·USGS지진·CelesTrak궤도·센서스타일/검색/투어기능이며기존DRAGONGLASS시설관측과다르다. 원본밸류체인20그룹/53업종/159배치/151기업/96도시와3관계선/본사/시총근거, SAURON을미연결subview로명시해후속에서누락하지말것.

raw빈티지20260910T081012Z(부모20260910T070347Z), 초기지역별수출45요청(1회probe재사용+수집44)·코드사전3요청,원본사이트/시세/미국옵션추가요청0. 본수집전송8036094bytes+USprobe210532bytes,새raw약132KB,DATA약235.4MiB/512·공개JSON약7.98MiB/8. 평일08/18 refresh호출·30일지역캐시/180일코드·응답1MiB/500행거부·직렬2초·401/403/429후속중단. 동일값재확인은확인원장만추가하며실패/기존관측소실시전값/성공시각유지. 실제다시실행해45지역신규요청0확인. 공개/원자료예산한도변경없음.

전체249Python(234.791초)·두자료검증기·3JS모음·31JS/MJS구문통과. 후속교역12단위검사(기존10+응답바이트/정확소수·캐시미래시각2추가)와변경관련검사재통과. 단위fixture쓰기의사용자캐시전체용량탐색을mock해교역12검사는1초이내이며운영예산검사는유지. 실제Edge1440/1024/390에서양방향금액/서로다른World분모·지도선20/전체·44파트너·검색/정렬·포인터/드래그/키보드/확대/회전·탭왕복·45수집원장·페이지넘침0/JS오류0/외부요청0과지도실패시표대체확인. 최초collapsible필드명오류를collapsed로고쳐원장접기를검증. private runtime/trade-validation.log,trade-browser-qa.json,trade-cache-verification.json. 실제게시커밋/실행은runtime/state.json과발행보고서확인.

전체목표미완료: 다음은53업종기업등록·본사도시/사업및공급물류근거연결또는SAURON공개관측부터보존소스와대조. 모든종목의모호한시총순위/AI생성공급망문장을사실로복사하지않는다. 새세션/Claude는검증분담권장만안내했으며별도생성없음. 옵션권한질문여전히미응답.


SAURON 후속(2026-09-10): sauron_data.py/sauron_views.py/sauron-views.js로 보존 원본의 Cesium 3D 카메라,22시설·USGS M≥2.5 지진·CelesTrak stations OMM/SGP4,3레이어/6색상효과/시설투어/지명검색/키보드/HUD/전체화면/관측원장을 연결했다. 효과는 실제 열·야간센서가 아니며 지진 스냅샷과 현재 UTC 궤도 계산을 분리한다. 원본의200km 최저고도 강제보정은 재현하지 않고 유효 실제 계산고도를 표시한다. 요소7일 초과/계산실패는 위치를 숨긴다.

최초 USGS37 중 raw M2.45를 제외한36, stations21; 보존 가격9/8과 관측9/10을 구분. refresh08/18에 연결, USGS1시간/CelesTrak2시간 캐시·응답1MiB·실패 이전 성공자료 보존·CelesTrak 비200 응답은 영속 중단기록으로 재요청 중단. 공식 정책을 대조했으며 원본사이트 추가요청0. 코드의 공개JSON cap만8→10MiB(현재8.02), 사용자 DATA512MiB 유지(배포 전258.6MiB).

Cesium1.145.0 Apache2/browser394파일 약17.1MiB, satellite.js7.1.0 MIT/22파일, npm SHA512·개별 SHA256·gitattributes 검증. 기본 Natural Earth II는 로컬, 선택 OSM은 viewport/정상 캐시·미리읽기 없음; headless QA에서는 OSM을 전부 fixture로 대체했다. Google 실사3D 키는 없음. 한국어 Wikipedia 좌표 미제공을 실제 조회로 확인하고 ko→공식 영어 langlink→좌표 일괄조회로 보완, Api-User-Agent/최대2조회·5후보·15초/검색간격2초/캐시50. 외부주소 지오코딩과 다르다.

검사261Python(188.966초)·2검증기·3JS·166JS/MJS구문, CelesTrak 별도 구현의3객체×4시점 TEME 오차0km·좌표 허용오차 통과. Edge1440/1024/390 WebGL·레이어/효과/카메라/투어정지/마커/3초갱신/검색캐시/전체화면/이탈destroy/재진입/넘침0·오류0; 추가 실제 한국어 검색2조회·초기 로드 중 이탈·오래된 요소·WebGL 미지원 원장 보존. 이후 검색 보완에 JS suite/구문 재검사. private runtime/sauron-* 보고서 참조.

게시 run 20260910T091629Z; raw 20260910T084457Z (부모 20260910T081012Z), 가격 2026-09-08. 실제 커밋/게시 완료는 runtime/state.json 및 해당 file-verification을 확인. 전체 목표는 미완료이며 REFERENCE_PARITY의53세부업종/151기업·96도시의 본사/사업/공급/수출/물류, 전체 관계망과 나머지 데이터·모델 범위를 계속한다. 새 세션은 검증 전담 방식만 권고했으며 생성하거나 Claude를 실행하지 않았다.


밸류체인 유니버스 후속(2026-09-10): chain_data/chain_geo/chain_views와chain-views.js로20그룹·53업종·159배치·151고유기업의탐색구조를연결했다. Yahoo프로필151기업·시총150(영국LSEG GBp단위미확인1제외), GeoNames정확도시매칭140기업/95도시. 나머지도시는근거확인전좌표없음. 프로필소재지를모든기업의공식글로벌본사검증이라고표현하지않는다. 공급관계는기존SEC NVIDIA10-K의4개만,소재국수출은기존2024 UN TOTAL상위5지역이며기업수출이아니다. 물류실측경로·전체경쟁우위/공급망근거는계속수집대상이다. 상세연구정본CHAIN_UNIVERSE_CONTRACT.md.

Roche원본ROG.SW가조회실패해공식2026-03-16공지로3/17 ROP.SW전환을확인했다. 기업구성151을유지하고설정의이전코드/근거URL을표시한다. 전체Catalent소유주처럼표현됐던중복NVO는단일NovoNordisk로연결한다. 교역UN490을대만회사국가TW로동일시하지않고공급관계용대표점을따로둔다.

신규raw빈티지20260910T093819Z(부모20260910T084457Z),가격9/8유지. 기업get_info153호출(초기NVDAprobe1+151기업+Roche정정1;라이브러리내HTTP요청수아님),GeoNames15000/5000두자료를공식덤프에서각1번받음. GLEIF가능성probe2회는이번표시자료로쓰지않았다. 원본사이트/가격/옵션신규요청0. 이후재확인151기업새조회0. 프로필24시간캐시/요청간격1초/제한또는연속3실패중단/실패1시간백오프/이전성공보존. GeoNames180일캐시/전송8MiB·압축해제40MiB상한,도시입력과해시가같으면좌표재계산도재사용. 기존08/18refresh에수집기를연결했다.

정사영·10도경위선·국가간대권곡선/금액별굵기·기업수별도시점·도시선택/기업선택·53바로가기/53표·관계근거3패널·마우스/키보드/확대/회전·이탈정리를구현. 실제Edge1440/1024/390에서151선택/159행·NVDA공급4관계·국내관계원장유지/지도3곡선·총수출5곡선·토글/도시/업종이동/드래그/회전/재진입/가로넘침0/JS오류0/외부요청0검수. 선택점이가까운다른도시에가려지는문제를마지막그리기와도시목록으로보완했다. 전체검사및실제게시완료는후속기록/runtime state로확인. 새세션은검증분담권장만안내했고생성하지않았으며Claude미실행이다.

Claude관련후속확인: 로컬CLI auth status 읽기는성공했고로그인상태를확인했다. 인증값/계정식별자는출력·복사하지않았으며Claude에모델작업을보내거나새세션을생성하지않았다.

밸류체인검사완료:269Python·2검증기·3JS모음·167구문검사,전체272.033초. 브라우저3너비와캐시새조회0·좌표재사용1.72초확인. DATA290.661MiB/512,공개JSON8.237MiB/10. 게시후보run20260910T100555Z;실제커밋및배포완료는runtime/state.json확인.


기업 공식 위치·관계 후속(2026-09-10): config/chain_evidence.json과chain_evidence.py로11기업의공식주소/10추가지명/18관계표시/5사업요약을연결했다. GeoNames500추출8지명과공식RDF2지명으로151기업105도시·행정대표점까지표시한다. 기존140도시매칭은유지했다. 더큰지명집전체교체시기존5기업이동명으로모호해지는것을확인해공식주소보정만추가했다. InditexArteixo등기/Richemont등기/Toyota아이치Honsha/SDI용인행정점과기흥건물구분,프로필국가·도시(미국주포함)가변하면보정중단. 전체공식글로벌본사검증은11기업범위를넘어완성한것이아니다.

기업3관계토글(공급/시장공급/물류)과국가TOTAL별도기본off스위치. BYD2024-06-01발표CN→BRSuape5,459대·27일과7,000대적재능력구분;동일사건을시장인도/물류에각표시해합산금지. Novo3시설US/IT/BE인수완료2024-12-18은위치발표/완료발표2근거;Catalent전체소유주NovoHoldings와구분. TSMC4서비스국가/MA3지역본부/SDI6사업R&D국가점선은상품흐름이아니다. 기존NVIDIA4공급/다른지구본5섹션유지.

원문14출처중11로컬확보,자동조회실패3은웹에서내용검토한기록과분리. 30일/2초/4MiB문서확인기를기존chain_data/08시18시refresh에추가;SHA동일원문재복제없음·실패성공시각유지·동일호스트실패후보류·URL변경성공승계금지·내용변경검토필요. 자동조회성공을사실의현재유효성검토라고표시하지않는다. 재실행14출처신규요청0. raw20260910T103914Z(부모20260910T093819Z),가격2026-09-08. PC추가문서수집11요청과별도6probe(GeoNamesRDF2포함);앞선GeoNames500덤프1회재사용. 원본사이트/가격/옵션요청0. Cboe허용여전히미응답·비활성유지.

Edge1440/1024/390기업151선택/53표/159행·전11보정소재지·NVO3/MA3/SDI6관계·BYD기업공급1/물류1/토글/국가참고off→5·도시105/회전줌드래그/탭왕복·넘침0/오류0/외부요청0검수. 날짜라벨후속BYD1440/390검수. 단위14개·확장JS통과,전체회귀/게시완료는runtime/company-evidence-validation.json과runtime/state.json및발행보고서를확인할것. DATA검사시321.837MiB/512,공개JSON8.262MiB/10. 전체관계/공식본사/경쟁우위확장및REFERENCE_PARITY의남은세부기능은계속구현대상이다.

기업위치/관계 전체검사275Python·2자료검증기·3JS·167구문 통과,301.860초. 게시후보run 20260910T105206Z; 실제게시완료는runtime/state.json 및 해당file-verification이정본이다.


2026-09-11 운영 변경: 사용자가 누적 용량 검사를 완전히 제거하도록 지시했다. acquire/satellite/초기 collect의 전체 디스크 순회와512MiB 차단, 개별 수집기·스테이징·배포의 budget 호출, 정적 JSON/PNG/라이브러리의 합산 용량 상한을 삭제했다. 원자료 변경분·해시 무결성·응답 전송 제한·갱신 잠금·실패 시 이전 사이트 보존은 기존 동작을 따른다. 테스트의 삭제된 함수 mock도 제거했다. 예약 automation의 평일08/18시·ACTIVE는 유지하며 용량 제한 지침을 없앴다. 반복 수집·계산·검증·상태 확인은 코드와 캐시에 맡기며 새 AI 세션을 추가하지 않는다. 기능 전체 목표는 계속 진행 중이다.

용량 검사 제거 검증: 전체275 Python 검사·두 자료 검증기·3 JavaScript 검사 모음·167 JS/MJS 구문 검사 통과(117.624초). 137개 Python 파일 AST 검사에서 budget 함수/호출/수입 및 DATA 전체 rglob 검사0개를 확인했다. 기존 갱신을 사용자 요청 반영을 위해 중단했고 20260910T222302Z 빈티지의 체크포인트301시도/오류0·압축파일 해시를 확인했다. 같은 빈티지 --resume-run으로 완료된 수집을 재사용한다. 최종 게시 상태는 runtime/state.json을 확인한다.

갱신 복구(2026-09-11): 수집1139시도/1138변경/1실패 이후 watch TRGP9/10 시가>고가로 엄격 OHLC 검사가 게시를 차단했다. Yahoo 표본1재조회도 동일, 전체 점검25건(미국주식/ETF 최근22건·영국주식 과거3건). cache.valid_ohlc로 불일치 일봉을 캔들·기술지표 입력에서 제외하고 원자료는 보존한다. 종가만 사용하는 가격 수익률은 제공처 보고 종가를 유지하며 관측일을 구분한다. 고저 범위를 넓히지 않으며 후속 공급처 정정 시 복원한다. price_quality.vendor_ohlc_exclusions·분석탭 원장·캔들 설명에 종목/일자/유효 관측일을 표시한다. raw빈티지20260910T222302Z를 오프라인 재계산해 추가수집 없이 검증·게시를 복구한다.

복구 검증 완료:278 Python·두 자료 검증기·3 JS 검사 모음·167 JS/MJS 구문 통과. 재계산/검사270.282초. 실제 Edge1440/390에서 제외 원장25건·열기·기준일·차트 렌더링·가로 넘침0·JS오류0·외부 요청0을 확인했고390px 이미지를 육안 확인했다. TRGP는120유효일봉/52주봉·마지막 캔들9/9·제외 일자9/10 설명을 확인했다. 실제 게시 완료는 runtime/state.json과ohlc-repair-publication.json을 확인한다.

DRAGONGLASS 리서치 후속: dragon_research.py/dragon-research.js로 관계 근거를 URL별 통합한 공식 문서·팀4방법론과 사용자 명시적 불러오기의 로컬 PRINCIPIUM 기록을 연결했다. 원문·날짜종류·객체태그/Entity360·출처/연결/검색·개인방향/기간/확신·첨부 내려받기를 제공하며 로컬DB 읽기만 사용한다. 가격상관은 문서근거가 아니므로 제외. 원본167편/비공개투자뷰/자동추론은 미확보; 지금 주목·트리거합류는 다음 작업이다. 수집·모델 추가호출0이며 기존08/18 build_all에서 카탈로그를 재생성한다.

용량 검사 추가 정리(2026-09-11): 브라우저 ResearchStore/결정 원장의 글 수·첨부 수·25MiB 개별파일·64MiB 첨부합산·2MiB 메타·90MiB 백업 검사, PDF 파일 크기 검사와 용량 합산 표시를 제거했다. 위성 타일의8MiB 합산 차단은 제거하고 화면 밖48장 재사용/URL 해제를 유지했다. PNG 게시 검사의 개별1MiB 상한도 제거하고 형식/400×400/해시·원본 크기 일치 검증을 유지한다. 브라우저 자체 QuotaExceeded 실패의 트랜잭션 롤백은 운영체제/브라우저 오류 처리이며 앱이 정한 저장 상한이 아니다. 수집 응답의 전송 제한과 PDF 작업당 쪽수/시간/문자 처리 범위는 저장 용량 검사와 별개다.

리서치/용량 후속 검증 완료:281 Python·두 자료 검증기·3 JS 검사 모음·168 JS/MJS 구문 통과(158.531초), 후속 PNG 용량 조건 삭제는 두 검증기와 refresh 단위검사를 재실행했다. Edge1440/390에서 공개22편(공식18/팀4) 필터·검색·빈결과·Entity360·로컬1편/휴지통및IW제외·XSS·첨부원문동일·읽기전후revision동일·PRINCIPIUM제한표시삭제·넘침0/오류0/외부요청0 확인,390px이미지 육안검수. runtime/dragon-research-* 및storage-final-validation 보고서,게시후보run20260910T233752Z. 실제게시완료는state.json과dragon-research-publication/file-verification을 확인한다. 전체목표는미완이며지금주목·트리거합류와REFERENCE_PARITY의나머지기능을계속한다.

DRAGONGLASS 신호 후속: dragon_signals.py/dragon-signals.js는 원본 watch/alert의 카드·규칙·순풍/경계·레이더·테마·크로스에셋·촬영 로그 구조에 기존 RS/발굴/ASK/지경학/관계/리서치/위성 데이터를 결합한다. 날짜일치·7일최대연령·미확보전체점수null·중복신호 방지·사업문서중복제거를 지킨다. 조회/LLM호출0이며 전체goal은미완. 원본live/전체기업뉴스/13F/정량뷰/임상/신규변화감지 및모든관계는후속. 공개동작/회귀/게시결과는추가검증기록확인.

신호 검증 완료:285 Python·두 자료 검증기·3 JS모음·169 JS/MJS구문 통과(112.247초). 최초검수에서 ASK 기간패널1/6/24개월과원본3개월혼동으로빈자산패널을발견,별도21자산원장3M열로수정하고실제값·날짜대조를추가했다. 기존전체보기검사의옛제목참조도새화면제목으로갱신했다. Edge1440/1024/390에서15카드/4동시신호/21자산상하위각3/8촬영로그·시장/검색/빈결과·기업/시설선택·근거펼치기·넘침0/JS오류0/외부요청0을확인하고1440·390이미지육안검수했다. 701기업/93후보,주도주30/발굴113입력중동일가격일60이며시점불일치는원장기록. raw빈티지20260910T222302Z유지·추가수집0. 게시후보run20260910T235826Z,실제커밋과Vercel검증은runtime/state.json및dragon-signals-publication/file-verification확인. 전체goal은미완이다.

임상 후속: clinical_data/clinical_views/clinical-views.js와clinical_scopes.json으로원본3범위ClinicalTrials.gov의모집/전체상태3상/최신5연구를연결. API버전시작종료일치·24시간캐시·버전같으면1조회·달라지면11조회·전체원자저장/실패이전관측/1시간백오프. 가격적재없는경로조회,원본사이트추가0·용량검사0. 원본검색식미공개로독립명시검색:모집비만1624/Lilly186/UNH0,3상890/709/5,전체16204/2897/38. 공식등록부dataTimestamp2026-09-10T09:00:04시간대미표기. 신규변화가아니며신호점수가산없음. 전체회귀/실제게시상태는후속검증/runtime보고서확인.

임상 검증 완료:289 Python·두 자료검증기·3 JS모음·170 JS/MJS구문 통과(105.610초). Edge1440/1024/390에서3범위×3조건/0모집표시/최초증감null/NCT원문·날짜·기관/LLY기업이동·임상촉매2건/기존동시신호4/넘침0/오류0/외부요청0확인,390px육안검수.9응답의totalCount/NCT목록과게시JSON직접대조,가격Overview바이트동일검증. 최초전용build에서상태빈티지와기존가격Overview빈티지충돌을검출하여가격계산빈티지는보존하고clinical supplemental_vintages/source_vintage로별도계보명시.
raw20260911T001009Z(부모20260910T222302Z),가격9/10유지. 공식API수집11요청·재실행0;별도탐색version1/모집1/공식OAS4041 및웹문서조회는수집카운트와구분. 원본사이트요청0. 게시후보run20260911T001604Z,실제commit/state/clinical-publication/file-verification확인. 전체goal미완;13F·기업뉴스감성/관심도·정량뷰·전체관계및임상별변화이력등계속구현대상.


용량 검사 완전 제거 후속: 사용자 재지시에 따라 남아 있던 다운로드 응답·압축 해제·SEC XML·지도 타일·PDF/OCR 설치·위성 요청별/실행별 바이트 상한도 제거했다. 총용량 순회/저장 한도 없음. 형식·해시·HTTP Range 일치와 필요한 관측 구역 읽기, 요청 간격·캐시·실패 시 이전 자료 보존은 유지한다. 기존 크기 거부 테스트는 실제 대형 응답 허용·내용/프로토콜 검증으로 갱신했다. 전체 검사와 게시 결과는 runtime/no-size-validation.json 및 runtime/no-size-publication.json을 확인한다. 전체 세부탭 목표는 미완이며 이번 작업은 용량 검사 제거다.


13F 후속: guru_data/guru_views/guru-views.js와6보고법인 설정을 추가했다. 원본6구루카드·상위6포지션 구조/보고일/원문과235행 전체원장·CUSIP/종류/PUTCALL검색을 연결했다. SEC 직접 Archives XML1요청403(이전submissions403) 후 중단; 브라우징으로 공식표6개를 확보해코드로파싱하고private보존. 최초95/1/89/15/8/27행→95/0/29/14/8/27포지션. Thiel0원placeholder·Scion2025-09-30지연·Pershing기존1336528 NT→모회사2026053범위를명시. Duquesne표합5210856/표지5210860=-4차이를유지하며보고금액의단위규모추가검토를표시,임의1000배보정없음. 나머지5합일치.

새raw20260911T004356Z(부모20260911T001009Z),가격2026-09-10/Overview바이트불변. 새source별vintage만status.supplemental_vintages.guru에표시,가격status.vintage는유지. 신호+3은CUSIP기업대응/분기시차검증전보류하며기존4동시신호불변. 확인공시는최신전체조회아님. 코드정기08/18에연결,private runtime/sec-contact.json의email필요(질문응답대기);없으면0요청,403시같은설정재요청보류·24h정상/오류캐시·신규accession만수집·이전자료보존. 원본사이트0요청/용량검사없음.

299Python·두자료검증기·3JS회귀·171JS/MJS구문통과. Edge1440/1024/390에서6카드/18필터조합/235원문행·검색/빈값/옵션·NT/0원/단위차이·탭왕복·가로넘침0/오류0/외부요청0검사,390px이미지육안확인. 정본research/GURU_CONTRACT.md 및runtime/guru-source-verification/guru-browser-qa/guru-validation.json,게시후보20260911T004834Z. 실제게시완료는runtime/state.json과guru-publication.json을확인한다. 전체goal미완:13F연속과거/최신확인/기업대응/구루뉴스16인관리·전체뉴스감성/관심도·정량뷰·나머지관계등은계속구현대상.


13F 식별자 후속: guru_identifiers.py는OpenFIGI 공식공개API의CUSIP/exchCodeUS를5개씩3초간격조회. 공식iShares기존CSV에CUSIP없음을확인하고초기5진단응답재사용+148개/30배치=153개관측을확보(140단일/13미확보). 30일정상/7일미확보캐시·실패이전성공시각/원자료보존·401/403/429후속중단·1시간오류백오프. 재실행0요청. 동일CUSIP다중FIGI는거부,티커정확일치와주식종류구분자변환만사용,기업명유사도0. 기업주식/ADR/REIT/NYregistered/MLP와SH만허용하며ETP/폐쇄형펀드제외.

현재57기업73포지션을Entity360에연결. 카드/표의기업버튼·티커검색→기업상세,기업상세에서6법인중해당포지션·보고/접수일·비중/수량/금액·CUSIP/FIGI조회시각과양쪽원문제공. AlphabetA/C분리,PUT/CALL은기초종목연결일뿐주식보유로전환하지않음. 매핑조회시각은보고시점PIT티커보증아님. 최신전체SEC/분기시차가미검증이라+3보류·기존4동시신호유지. 기존235원문/173합산포지션/가격Overview불변.

raw20260911T005706Z(부모20260911T004356Z),가격2026-09-10. status.supplemental_vintages.guru_identifiers와섹션별실제source_vintage를보존. 기존08/18refresh의guru_data뒤에식별자수집연결. 원본사이트0요청/용량검사0/새AI세션0.306Python·두자료검증기·3JS회귀·171JS/MJS구문통과(149.95초). Edge1440/1024/390전체57기업/73포지션·GOOGL/GOOG/NVDA세클릭·옵션표시·4동시신호불변통과. 첫390검수에서기존종목select가393px까지넘침을확인해Entity360에한정해min-width0/width100%적용후전체브라우저재통과,오류0/외부요청0/가로넘침0·이미지육안확인. 최종runtime/guru-identity-browser-qa.json(3행)이정본이며diagnostic파일은검수증거로사용하지않는다.

정본GURU_CONTRACT.md,private guru-identity-collection/source-verification/build-verification/validation.json. 게시후보run20260911T010319Z,실제커밋/배포는state.json과guru-identity-publication.json확인. 전체goal미완:유니버스밖종목·미대응식별자·최신/연속13F·구루16인관리/뉴스·기타REFERENCE_PARITY세부기능계속.


데이터 소스·현황판 후속(2026-09-11): dragon_operations.py/dragon-operations.js로19소스5분류의카드·상태집계·날짜/단위원장·필터/검색과23모듈기준일/생성시각/이동을연결. RSS7/임상/13F/FIGI/위성/지진/궤도/교역/기업프로필/거시제공처를명시적으로투영하며private설정/키/원문오류본문은읽거나게시하지않음. SEC검토공시6법인을자동조회정상으로표시하지않음. 소스별시도/성공/관측일구분·날짜만있는거시수집시간미확인·일부실패이전값있어도오류·USGS1h/궤도2h코드캐시를평일08/18주기와구분.

현황은관계객체39/관계36/공식팀문서22/화면신호기업15/시설22/국가객체0/인사이트null. Entity360701과객체분모다름. 원본7계열공통건수축/관측일순서/4기간/원장구조를구현하며이력은이전게시JSON+당일KST관측만보존. 첫1일이며과거원본수치소급0. 타이머는08/18KST평일예정안내이고PC실행/배포성공보증이아님;탭이탈해제검사. 소스화면필터는수집설정변경아님. 미연결30전체소스/원본인사이트버스/키/실시간PC상태/인증제어API는DRAGON_OPERATIONS_CONTRACT.md와REFERENCE_PARITY에남김.

309Python·두자료검증기·3JS회귀·172JS/MJS구문통과(152.760초). Edge1440/1024/390에서19소스날짜/계열수·5분류/5상태/검색/빈결과·23모듈/7계열/4기간·RS왕복·예정KST/타이머0복귀·가로넘침0/오류0/외부요청0통과. 390현황/소스이미지육안확인. 기존legacy journal가져오기의1MB와500건제한잔여를제거;최종JS회귀및구문재통과. 원본사이트/신규외부수집/모델호출0,용량검사0,가격Overview바이트동일. raw빈티지20260911T005706Z/가격2026-09-10유지. 게시후보run20260911T012438Z;실제커밋/배포는runtime/state.json,operations-publication.json및operations-browser-qa/validation/build-verification.json확인. 전체goal미완이며REFERENCE_PARITY잔여작업계속.


기업 관심도 후속(2026-09-11): 원본attn10기업의영문Wikipedia기업문서구조를대조하고MediaWiki제목API1회로정규제목/pageid/Wikidata확인(ASMLHolding→ASML). WikipediaPageviews all-access/user 일별UTC를초기60일/이후7일겹침정정으로수집. NVIDIA초기61일probe재사용+나머지9요청=10문서601일관측;재실행0요청. 관련API공식문서검토는별도. 최근7일9/3~9/9 vs직전7일8/27~9/2,10가용/+40%0문서. 원본비교기간미공개로팀규칙명시,전체뉴스/검색/고유투자자/감성아님.

attention_data/attention_views/attention-views.js/config으로수집·Entity360·지금주목10카드/60일선/전체일원장/검색/원문·트리거+2를연결. 단위/project/title/agent/UTC/중복/정수검사,결측0채움금지,분모0신호가용false,14일완전/가격일이전3일내/성공72h내/최근오류없음조건. 가격기술신호는동일가격일,열람은별도관측일/성공일. 미래정보PIT/백테스트에쓰지않음. 현재급등0으로가짜신호없음,연결규칙3/7·기존4동시신호유지. 전체점수/live/기대수익null유지. Source운영카드Wikimedia추가20개.24h캐시/1초간격/1h오류backoff/401403429중단/실패이전성공보존/용량검사0. 기존08/18refresh에수집/가격/계산연결.

첫브라우저검사에서ASML에Entity없음을발견. ASML1종목가격history를기존수집기로받아3년752일·USD·OHLC유효확인. 실제마지막9/9를9/10으로늘리지않음. ASML추가관찰(공식S&P500편입아님),Entity702·원장702상관재계산(합집합252일창/ASML245유효관측). 공식700+TSMC/ASML2. 가격추가갱신대상에attention_pages를포함. 재무/일정미확보는비움. 기존13F57기업73포지션유지,가격Overview바이트동일.

최종314Python·두자료검증기·3JS회귀·173JS/MJS구문통과. Edge1440/1024/390에서10문서/601원장/각60점·기간수치·검색/빈값·모든Entity이동/원문/신호3규칙/기존4합류·Wikimedia소스·가로넘침0/오류0/외부요청0통과.390이미지육안확인. 초기수치검증에서ASML대각관측수를무조건252라고둔검사전제를245로정정(전체시장합집합창에비거래일포함),source시각원장확인. raw20260911T013531Z(부모20260911T005706Z),가격기준9/10. 최종게시후보run20260911T014736Z. 정본ATTENTION_CONTRACT.md;실제배포는state.json/attention-publication.json과attention-validation/browser-qa/build-verification/asml-verification확인. 원본사이트추가0,새AI세션0. 전체goal미완:전체기업뉴스/감성/정량뷰·13F연속/관계확장·REFERENCE_PARITY잔여계속.


2026-09-11 화면 명칭 변경: 25개 주화면을 기능별 한국어 이름으로 통일했다. 통합예측·기업분석·업종/자산지도·글로벌 공급망·리서치 자료실·국면·수급/위험·실적/컨센서스·주간 기록·시장 요약, 세부 기업 상세·위성사진·위성/지구관측과 거시 국면/시장 쏠림을 반영했다. 표시 제목·탐색·현재 위치·요약/운영 카드·가이드 일치. URL 해시·JSON/개인 기록 식별자·실제 OCR 라이브러리명은 보존. build_all 최종 공개 단계의 display_names가 캐시 문구도 정리한다. 원자료/원본 사이트/모델 추가 호출0. 학습 캐시가 불필요하게 무효화되지 않도록 모델 소스 바이트/개행을 직전 검증 스테이지와 동일하게 유지했다.

25스냅샷 287750숫자·11055식별자/URL 불변·225표시 문자열 변경 검증. 315Python·두 자료 검증기·3JS회귀·173JS/MJS구문 통과. Edge1440/1024/390에서25주화면·137공통하위그룹·기업이동·현황 모듈명·위성사진·탐색 검사, 기존390px 종목발굴 점수/자산배분 막대 가로넘침2곳만 CSS수정후 전범위 재통과. JS오류0/외부요청0/옛 표시명0/가로넘침0. 실제 수치/차트 구조/저장기록 유지, 전체 세부기능 목표는 여전히 미완. 가격9/10·raw20260911T013531Z 유지. 정본 UI_NAMES.md, runtime/names-build-verification/validation/browser-qa.json 및 names-followup-validation.log. 실제 게시 완료는 state.json/names-publication.json을 확인한다.


2026-09-11 관계 대조/시차 후속: 보존된 관계지도 edge_insights의3M·비연결12/부호불일치8/일치6·동일시장시차8행구조를오프라인대조. relation_discovery.py/relation-discovery.js로22기업(US20/KR2),231무순서상관쌍·1146방향/시차를독립계산. 3달전초과~가격기준9/10,SPY63세션6/11~9/10,KOSPI63세션6/11~9/9(실제공급일). 조정종가/시장달력재배열후수익률·시차생성,45개최소/7일최신/결측미채움. 비연결|상관|>=.6의36쌍을그래프에연결,사업30/총66관계·부호일치6/불일치5. 과거252일/기업별최대연결방식대체. 기존702원장행렬/기본8시나리오/중심성/기업/13F/문서관심도/가격Overview는불변.

동일시장1/3/5시차 |rho|>=.25·동시상관대비절대차>=.1의45방향탐색후보. 전체1146가설의제한/비제한OLS SSR F검정+BY보정; q<=.1통과0,매매점수가산0/인과·OOS주장0. F는최대시차까지선행계수공동검정,모든가설먼저보정후후보선택. 원본세부임계값비공개로명시적팀설정. 원장요청시만렌더/검색·전체/빈결과/기업이동·전파연결. 정기08/18 subview_modules에연결,원본/외부자료/모델추가요청0·용량검사0.

최초검증기는예전그래프최소200일계약으로차단; 새명시적3개월/45개메타를추가하고별도분기검증. 원장200개검증은유지. 321Python(독립statsmodelsF일치/방향/결측시차비압축/미래불변/상수·시차달력오래됨/재실행중복방지포함)·두검증기·3JS모음·174JS/MJS구문통과. Edge1440/1024/390에서3열/요약/전체36+45/검색/1146원장날짜·rho·q/22기업이동/36상관선/전파옵션/현황66관계·왕복/가로넘침0/오류0/외부요청0확인,모바일/데스크톱이미지육안확인. raw20260911T013531Z/가격9/10유지. 정본RELATION_DISCOVERY_CONTRACT.md와runtime/relation-discovery-build-verification/validation/browser-qa.json;실제게시commit/state는relation-discovery-publication.json확인. 전체goal미완:원본136가격기업/255객체581관계전체·OOS/PIT·기업뉴스/기타REFERENCE_PARITY잔여계속.
2026-09-11 기업 뉴스 후속: company_news.py/company-news.js와23기업 RSS설정으로 기업분석의 지금 주목·기업 상세·신호 합류·소스 운영을 연결했다. Yahoo Finance 종목별 RSS 최초1응답 재사용+22요청,23피드 정상; 재실행0요청. 정규화426관측 중 가격기준2026-09-10까지 최근7UTC일381피드항목/중복URL제거317기사. 이후 날짜 기사는 원자료에 보존하되 집계에서 제외한다. 종목 연관 피드이므로 해당 기업만 다룬 기사/전체 뉴스라고 표시하지 않는다. 감성·전체종합점수·live·기대수익은 미산출을 유지한다.

24h캐시/1초간격/1h오류백오프/401403429후속중단/실패시직전성공보존. XML형식/타임존날짜/HTTPS링크/URL중복/원문SHA검증, 저장·전송 크기상한 없음. 원문XML은 private SHA별보존, 기사 URL별 최초/최근관측 보존. 최신36h 성공·오류없음·기간내8건이상 표본 관측만+1로 연결:23피드충족/표시합류16기업/7규칙중4연결. 관심도와뉴스 관측일은 가격일과 구분한다. 소스카드21개, 기존08/18 refresh에수집연결. 가격·관계·관심도 결과 불변. raw20260911T024219Z(부모20260911T013531Z), 게시후보run20260911T024911Z.

326Python·두자료검증기·3JS회귀·175JS/MJS구문통과(124.742초). Edge1440/1024/390에서23피드/381항목·검색/필터/빈결과/펼치기·23기업상세·16합류/4규칙·원문링크·소스카드/가로넘침0/오류0/외부요청0 확인,390px육안검수. 원문426행과날짜별381게시항목 직접대조/SHA일치. 정본COMPANY_NEWS_CONTRACT.md, runtime/company-news-collection/reuse/source-verification/build-verification/validation/browser-qa.json; 실제게시commit/state는company-news-publication.json 확인. 원본사이트추가요청0/새AI세션0. 전체goal미완:뉴스다중제공처·감성·정량뷰·최신/연속13F·전체관계와REFERENCE_PARITY잔여계속.

2026-09-11 퀀트5세부화면 후속: 보존 quant.json/방법설명/페어PNG10개와 대조하여 기존 임의160유동성·회귀잔차·EG조건을 가격비/Hurst 전체표본 선별로 교체했다. 원본 사이트/추가 수집/모델/AI세션 호출0, raw20260911T024219Z·가격9/10 유지. quant_modules는 quant_screens의기존진입점이며08/18전체빌드에연결된다. 359한국표본·353가격준비·62128쌍→상관1572/Hurst1143→10페어. 252시장일z선·0/±2·마지막점·조건/방향/반감기·원장,8팩터통과100/상위15막대/기여·전체359통과/제외, BAB41Long/70Short 분포·역Beta검산,TSMOM12관측/막대·반전8개를연결한다.

초기 엄격253일조건에서352개가제외되어원가격조사:2025-09-19가대부분종목에누락되어있음을확인. 시장달력을삭제하거나일수익을압축하지않고 최근127일·252일전기준점필수/최근253일가격최소220·실제결측일·일수익관측수를명시했다. 결측팩터0채움제거;완료12개월안정성·복리5D수익z. BAB가격일과Beta종료/관측수분리(KOSPI실제9/9). TSMOM달력12/3개월전이하최근가격·기준일원장,금리는상대변화만/노출null,crypto365·나머지252연환산. 원본명시6+팀추가6구분. 정밀평균/표준편차문자열보존으로화면반올림후역산오차제거. Hurst후보는NumPy배열선별하고상세OU는최종선택만계산;전체자료적재포함약34초. 전체원본PIT/비공개설정·비용후성과는미완이다.

333Python·두자료검증기·3JS회귀·176JS/MJS구문 초기전체통과. 마지막Beta/TSMOM날짜원장 추가 및 외부에서병합된시장종합디자인910dbbb를보존한새stage20260911T032411Z에서전체재검증한다. 정본결과runtime/quant-screens-validation.json의run_id/status를확인할것. Edge1440/1024/390에서5그룹·10곡선점직접일치/±2·515원장행·검색/정렬/빈결과/펼침/왕복·가로넘침0/오류0/외부요청0,이미지육안검수. 원가격10페어/모든252차트점·100팩터점수독립검산,다른22JSON바이트불변. 정본QUANT_SCREENS_CONTRACT.md;runtime/quant-screens-source-verification/build-verification/browser-qa.json과실제게시quant-screens-publication.json/state.json확인. 전체goal미완이며REFERENCE_PARITY잔여계속.


2026-09-11 차트 배치 밀도 개선: 시장 종합의 36개월 궤적과 적층 레이더를 같은 행에 배치하고 날짜/원수치 설명을 공유 행으로 옮겼다. 6/5축 KPI는 넓은 화면에서 한 줄, 원단위 4시점 원장은 펼침 영역에 보존했다. 주도주 리본은 760px 이상 실제 차트 폭에서 5종목씩 두 열, 그 아래에서 10종목 한 열로 재배치하며 공통 로그 축/실제 수익률/시총 두께/성장 색과 클릭·직접 카메라 조작을 보존한다. ResizeObserver는 탭 이탈 시 해제한다. 비교 가능한 시계열/산점도와 통합예측 카드는 데스크톱 두 열, 작은 화면 한 열로 조정했다. 데이터/모델/관측 계약 변경 및 수집 없음. 검증/배포 결과는 private runtime/density-validation.json과density-publication.json 확인.


2026-09-11 시장 역학 후속 및 최신 디자인 통합: dynamics_model.py/dynamics_validation.py/dynamics-views.js로18대상·표면60개월×8기간·위상36개월·위험60개월/65음영·월이력최대144·실제 거래일을 연결했다. β21일/α5일/∇τ후방차분·확장창252/ddof0·전일노출·결측보존을 명시. 표면 재생/정지/초기화/이탈 타이머 정리, 비용0/5bp/5bp+연3%/10bp+연5%의4가정·동일기간2곡선·최근252일 거래/비용원장·BOM CSV를 제공한다. 드리프트 후 비중 기준 거래비용·최초매수비용·차입비용·자본소진 중단을 계산. 누락 가격/신호 뒤 마지막 연속 유효 구간만 평가해 한국5종목은209거래일이며 전체 이력을 연결한 성과라고 표시하지 않는다.

사용자 요청으로 다른 디자인 작업의 최종8c0adfd(흰 배경/나란한 공간·레이더/넓은 화면5+5 주도주/비교2열)을 확인하고 현재 기능 stage에 반영했다. 디자인 작업에서 이미 main/Vercel에 반영했으므로 중복 병합하지 않았다. 최신 디자인을 포함해340Python·두자료검증기·3JS모음·177JS/MJS구문 통과(130.244초). Edge1440/1024/390 각각18대상×4가정72/위상643/원장17284행·차트좌표·65음영·표면 유효셀·CSV·재생/정지/초기화/화면이탈·디자인 주도주10개·가로넘침0/오류0/외부요청0 검증, 데스크톱/모바일 이미지 확인. 원가격 기반18대상5지표/72전체성과·비용 독립 재계산 일치, 다른22JSON 불변.

원본 사이트/새 데이터 수집/모델/새 AI세션 요청0. raw20260911T024219Z·가격9/10 유지(KOSPI실제9/9), stage20260911T034033Z. 계산은 기존 평일08/18전체빌드에 연결. 정본DYNAMICS_CONTRACT.md 및private runtime/dynamics-source-verification/build-verification/browser-qa/validation.json. 실제 게시 commit은dynamics-publication.json/state.json 확인. 전체goal미완: 수식/전체캡처·선택링크공유, 원자료결측/PIT·실제비용과REFERENCE_PARITY의나머지 세부기능 계속.


2026-09-11 시장 역학 내보내기 후속: 보존 원본 app.js 1340~1390의 캡처가 전체 페이지가 아니라 수식+현재3D표면 PNG임을 재확인했다. dynamics-export.js는 현재SVG/계산식/종목/실제가격일·최신신호일·표면기간/단위를 2배PNG로 저장한다. 현재카메라/기간/결측면/따뜻한색을 보존하고 실제팀계산 후방차분·21일·확장252·전일노출을 설명한다. 과거표면의표식은‘선택 시점’, 마지막은‘최신’으로 정정했다. 별도전체페이지 캡처가 원본요구라는 이전기록은폐기한다.

종목링크는 동일origin/하위경로의 ?dynamics=정확한티커#dynamics. 미등록값/다른모듈은 적용하지않고 기존임의쿼리를복사하지않는다. 링크는 열때 최신데이터이며 과거빈티지/카메라/비용가정 고정링크가 아님을표시. 클립보드거부시 직접복사입력, 저장실패후버튼복원, 탭/종목이탈시작업취소와Blob해제. 메시지외부전송/추가수집/원본사이트/새AI세션0. 기존27공개JSON바이트불변, 모든가격/계산/모델/정기08/18파이프라인불변. 최신디자인8c0adfd 유지.

검증: Edge1440/1024/390 각각18링크, 데스크톱18PNG/태블릿2PNG/모바일2PNG 실제파일시그니처·1800px폭·그려진종목/수식/각날짜·과거표식·표면좌표불변·클립보드거부·toBlob실패·변환중이탈·URL해제 확인. 오류/외부요청/문서가로넘침0, 삼성전자390PNG한글·수식·기울기와기간 육안확인. 정확한최종전체회귀결과는runtime/dynamics-export-validation.json,브라우저결과dynamics-export-browser-qa.json. stage20260911T040404Z/가격data_run20260911T034033Z/raw20260911T024219Z. 실제게시commit은dynamics-export-publication.json/state.json 확인. 정본DYNAMICS_CONTRACT.md/REFERENCE_PARITY,전체goal미완이며나머지세부기능계속.


2026-09-11 기업 뉴스 제목 톤: ProsusAI/finbert revision4556d13015211d73dccd3fdd39d39232506f3e43/6파일SHA 고정. 가중치는private models/finbert에만저장, 공개는config/news_tone.json·코드·직접산출확률. 영문 Yahoo RSS의356정규화고유제목을CPU4/16배치·eval/inference_mode로40.298초분류,즉시재실행모델로드0·356캐시재사용. 두번초기환경실패(huggingface-hub버전/torchvision NMS)를명시적으로수정후동일빈티지 --retry;전역환경변경없음. 전용tools/news-tone-dependencies에hub0.36.0/tokenizers0.22.1/torchvision0.26.0+cpu설치,requirements/모델계약에기록.

news_tone.py는모델+제목해시재사용·파일해시검증·로컬전용읽기·weights_only,영문범위/512토큰모델범위초과미분류(저장한도아님),오류이전값보존/1h백오프. 기존08/18 company_news뒤분류연결;정기실행에서모델다운로드0. 최근7UTC일/가격일이하필터후피드내중복제목제거·P긍정−P부정평균,전체유효분류/신선피드/평균>0에별도1점. 기업별호재/악재·수익률/전체기업감성·PIT아님을명시. 기사별3확률/라벨·계산시각·토큰,기업카드/상세/양수음수미분류필터·트리거·로컬분류소스카드(총22)연결.

23피드·381게시기사/317URL·23피드분류완료·15양수·7규칙중5연결·16동시신호카드. 가격/관계/관심도등23JSON불변. raw20260911T041510Z(부모20260911T024219Z),가격9/10유지;모델계산04:20UTC,기사원자료는기존02:42빈티지. source_vintage와tone_source_vintage/status.supplemental_vintages.news_tone분리. stage20260911T042425Z. 추가뉴스/원본사이트/외부추론API/새AI세션0.

검증: 6개추가Python검사(캐시/수정/실패/확률/부분집계/미래기사/날짜시차1점),전체346Python·두자료검증기·3JS모음·구문통과(151.01초). Edge1440/1024/390각23피드/381라벨·확률·평균·필터·펼침/23기업상세·5규칙·소스22·가로넘침0/오류0/외부요청0,390이미지검수. 원문/캐시381값전수일치,12제목별도batch+float64softmax재계산최대오차1.41e-7/3라벨포함,비영문·602토큰미분류검사. runtime/news-tone-collection/reuse/build-verification/source-verification/browser-qa/validation.json,실제게시는news-tone-publication.json/state.json. 정본NEWS_TONE_CONTRACT.md. 전체goal미완:다중제공처/전체기업·기업별문맥감성·정량투자뷰·최신연속13F·전체관계/팀DB등REFERENCE_PARITY계속.


2026-09-11 기업 뉴스 범위 확대: 보존된54개 뉴스 객체를 회사34/테마·국가·정책·지정학20으로 구분했다. 회사34를 모두 설정에 포함하고 기존팀6기업을 유지해40피드. 새17개 RSS만 수집, 재실행0요청. 39피드에서 기준일9/10이하7UTC일625피드항목, 한미사이언스는 기간내0건/톤미산출·뉴스신호없음. 기업별 관측 합계를 고유 전체뉴스량으로 표시하지 않는다. FinBERT 신규231고유제목33.324초·기존356재사용,27피드양수·5/7연결·16합류, 모델/원본사이트/새AI세션 추가0.

Nasdaq 디렉터리1회로ALAB/ARM/CRWV/ENTG/NBIS의공식종목명·TestIssue=N/ETF=N 확인, DART로008930 식별. 기존Hanmi는KOSPI200이며중복추가안함. 신규미국5Entity→공식700+추가7=707. 지수편입/업종확정으로간주하지않고추가관찰/RS·재무·예정실적미확보유지.4가격history(ALAB621/CRWV365/ENTG753/NBIS473)초기수집·ARM/Hanmi기존재사용,뉴스설정종목의가격유지갱신을08/18 incremental에추가. 상장확인URL/시각/공식종목명 표시.

민감도의concat.dropna.pct_change를결측보존후수익률계산으로수정해누락전후의다일압축제거. 원장상관도종목별시장달력으로먼저reindex후일수익률계산·합집합252창/최소200유지.707Beta전수독립검산,기존200개값변경.249571쌍관측수전수·5648쌍상관독립검산통과.공식유니버스/관계발견/30사업링크/관심도및다른23JSON불변. 단위현지통화·관측일/누락개수명시,시장휴일을무조건공통휴일로치환안함.

전체347Python·두자료검증기·3JS모음·전체JS구문통과134.03초. Edge1440/1024/390 각각40피드/625항목·기사확률/기간·40기업이동·6공식식별/5신규상세·5신호규칙/27양수·빈뉴스/미산출필터·707행렬새6종목디코드·가로넘침0/오류0/외부요청0확인. 최초QA가미분류0개를가정한오류는Hanmi0기사의미산출1개를확인후데이터기반기대로정정했으며UI를가용으로조작하지않음. 코드/수치수정없이최종설명문서만동기화.

raw20260911T043351Z(부모20260911T041510Z),stage20260911T044500Z,가격9/10. runtime/news-universe-source-verification/build-verification/browser-qa/validation.json과실제게시는news-universe-publication.json/state.json. COMPANY_NEWS_CONTRACT.md/RELATION_CONTRACT.md정본. 최신디자인8c0adfd유지·용량검사0.전체goal미완:비기업20객체뉴스/다중제공처/기업문맥감성·신규기업재무일정·정량뷰/관계확장/연속13F/PIT및REFERENCE_PARITY계속.


2026-09-11 기업 재무·일정 보완: company_fundamentals.py로뉴스40기업의재무7일/미국상장37기업일정3일캐시를기존08/18 refresh에연결했다. 기존acquire재사용16재무+12일정=28조회작업(HTTP요청수아님),재무24/일정25캐시재사용. 즉시재실행0조회. 신규응답/실패시도는private company_financial,유효재무는fundamentals,시간대있는일정은company_events에저장. 기존PEAD/events/company_events중최신일정을기업상세에병합,다른이벤트필드보존. 실패/빈값은이전자료유지/1h백오프,기존완전재무에부분실패를덮어쓰지않음. 용량검사/새모델/원본사이트요청/새AI세션0.

뉴스40모두재무연결(ARM은기존캐시도활용),37일정자료·36기업향후90일예정(AVGO는기간내예정없음),한국3예정실적미수집. 707Entity중77개의재무/일정필드만갱신,가격·RS·민감도·관계/뉴스/관심도보존. 금융정보추가가공식업종/지수편입을뜻하지않음. 실적 연간·분기 상세197→213기업(신규16),NI/OP/매출3막대·연간4/분기최대8·원통화원장·KRW조원/기타각통화bn유지. 세계NI Top20/미국10기업추정등다른실적패널은불변. 데이터소스재무/일정2카드추가24개,가장오래된조회/보유/오류수를표시.

원자료213기업5291재무값·기간/통화전수일치,40기업금융요약·37일정/90일컷오프독립대조,다른22JSON바이트불변. 6새단위검사포함353Python·두자료검증기·3JS모음·전체JS구문통과128.146초. Edge1440/1024/390 각각40기업재무/예정·40기업연간/분기3차트1067막대좌표/단위·213선택목록·검색/빈결과·새소스2·가로넘침0/오류0/외부요청0확인. ASML390분기EUR단위3패널육안확인. 한국일정/전체707재무·직접NI/OP컨센서스/PIT등미완.

raw20260911T050000Z(부모20260911T043351Z),stage20260911T050337Z,가격9/10유지. 정본COMPANY_FINANCIAL_CONTRACT.md, runtime/company-financial-collection/reuse/build-verification/source-verification/browser-qa/validation.json. 실제게시commit은company-financial-publication.json/state.json확인. 최신디자인보존;전체goal는REFERENCE_PARITY범위를계속수행한다.


2026-09-11 주제 뉴스 후속: 보존된 비기업20객체(테마9/국가2/지정학5/정책4)의 탐색 화면을 추가했다. 자체20검색식/제목 일치 기준을 공개하고 GDELT API 검색 결과와 기존 기업·정책 RSS 제목 일치 표본을 별도 집합으로 표시한다. 현재 GDELT 실조회는429와 간격을 둔 TLS ReadTimeout으로0/20 미확보이며, 미확보를0건 성공으로 표시하지 않는다. 기존 캐시에서는11주제23기사/23고유URL이 일치하고9주제는 이 표본에서0건. Google RSS 시험 응답은 private에만 보존하고 게시/분류/추가수집에 사용하지 않았다.

topic_news.py는7UTC일 ArtList/공급자250건한도/24h캐시/6초간격/1h백오프/401403429·요청오류시배치중단/이전성공보존을 구현했다. 검색식 변경 실패시 이전 검색 결과를 새 검색 결과로 표시하지 않으며 색인 관측시각과 RSS 발행시각을 구분한다. 기존08/18 refresh에서 기업뉴스→주제뉴스→로컬FinBERT 순서. 신규21제목31.140초·기존587재사용, 재실행608재사용/0분류. 금융제목 모델의 정치·재난 주제 적용 한계를 명시하고 매매 신호 가산은 없다. API 성공/빈검색/응답상한은 현재 fixture 검증이며 실제 성공 수집 완료가 아니다.

전체360Python·두자료검증기·3JS모음·전체JS구문 통과122.423초. Edge1440/1024/390에서20주제·두집합·4분류·검색/빈값·날짜/원문/일치어/톤·펼침·이동·소스카드 확인, 오류/외부요청/가로넘침0. 390이미지 육안 확인. 독립 원자료/캐시 검사23기사 전수일치, 기존 회사뉴스/기업/신호/관계 보존 및 다른23JSON 바이트 불변. raw20260911T052309Z(부모20260911T050000Z),stage20260911T052857Z,가격9/10. 정본TOPIC_NEWS_CONTRACT.md; 실제 게시는runtime/topic-news-publication.json/state.json 확인. 디자인 작업 최신8c0adfd가 메인 조상임을 재확인하고 production의3개 디자인 자산이 로컬과 바이트 동일함을 검증했다. 전체goal미완:20실검색·다중제공처/전체관계/정량뷰/연속13F 등 REFERENCE_PARITY 계속.


2026-09-11 전력 구매계약 관계 확장: 공식 발표6문서(계약5/Crane 후속1)를 웹 도구에서 검토해 Constellation→Microsoft/Meta,Vistra→Meta,NextEra→Alphabet(Google),AES→Microsoft5관계를 추가. 공용계통 구매/예정/현재가동미확인과 기술협업을 구분. Crane835MW20년·최초2028→후속2027목표,Clinton1121MW20년/2027-06개시(30증설중복금지),Vistra2176+433=2609MW20년/2026말~2034단계,DuaneArnold시설615MW25년/Google배분미확인(CIPCO잔여),AES3사업475MW/개별계약MW·기간·현재가동미확인. 시설MW를계약MW·실송전·매출·가정전달계수로바꾸지않음. 사업가정powers0.28/0.62·weight1유지. 원본요청/새모델/시세추가수집/용량검사0.

power_relations.py/config으로 관계/공식 문서·발표/검토일·계약펼침/기업이동/5전력필터·8시나리오·현황소스 연결. 기존chain_evidence수집기의저장namespace만매개변수화해08/18 refresh에재사용;문서30일캐시/실패이전값/같은호스트배치보류/변경감지표시. 최초5조회작업4성공+다음실행보류1조회실패=6작업;Constellation투자자2문서는ConnectionError/ReadTimeout으로로컬미확인,웹검토와구분. 세번째실행0요청검증. 변경감지는계약이행·신규발표해석이아님. 전체원문4개private저장/해시·용량숫자/예정일본문확인.

Meta/Vistra/NextEra/AES4기존공식기업을관계노드에추가,39→43객체/30→35사업관계/22→26가격기업. 325쌍(이전231상관값불변),1662동일시장방향/시차회귀와전체BY재계산;76탐색후보/보정통과0. 707기업상세·원장행렬·회사/주제뉴스·관심도·위성·23다른JSON불변. 공식리서치카탈로그6URL추가(후속발표포함),신호점수는기존관측규칙이고문서/관계수동점순위만재계산. 새기업공식지수편입이나실제수익률예측주장없음.

5새단위검사포함365Python·두자료검증기·3JS모음·전체JS구문통과128.032초. Edge1440/1024/390마다43노드/5계약·기간/계약/시설MW·미확인·원문/날짜·필터/검색/기업이동·8시나리오·리서치6문서·운영소스/왕복·오류0/외부요청0/가로넘침0. NextEra390화면육안검수. 원자료325쌍독립검산·계약5수치·4원문해시·707보존검사통과. raw20260911T054825Z(부모20260911T052309Z),stage20260911T055052Z,가격9/10. 정본POWER_RELATIONS_CONTRACT.md, runtime/power-relations-source-verification/build-verification/validation/browser-qa.json;실제게시는power-relations-publication.json/state.json확인. 최신디자인유지. 전체goal미완:원본전체관계/계약연속이력·Talen기업가격/전체뉴스·13F/PIT등REFERENCE_PARITY계속.
