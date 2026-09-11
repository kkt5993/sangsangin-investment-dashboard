# 상상인 투자 리서치 플랫폼

25개 공개 탭 중 **23개 분석·콘텐츠 탭에 계산 또는 탐색·기록 기능을 연결**했습니다. Overview와 At a Glance는 전체 현황을 표시합니다. 연결된 대형 탭도 세부 기능은 부분 구현일 수 있으며, 화면의 세부 탭과 아래 현황 문서에서 범위를 구분합니다.

- [팀 페이지](https://sangsangin-investment-dashboard.vercel.app/)
- [탭별 현황](research/IMPLEMENTATION_STATUS.md)
- [공식 유니버스·단위·날짜](research/DATA_DEFINITIONS.md)
- [차트 구조 대응표](research/CHART_PARITY.md)
- [25개 탭 구현 문서](research/MODULES.md)
- [세부 화면 연결·미연결 목록](research/SUBVIEWS.md)
- [원본 세부 기능 대조·남은 작업](research/REFERENCE_PARITY.md)
- [정기 갱신 운영 방법](research/UPDATE_PIPELINE.md)

## 화면과 데이터

RS·모멘텀, ETF·멀티에셋, 국면·리스크·주말 매크로, 퀀트·패턴·시장 역학, 실적·성장·종목 발굴, 11종 ML·10전문가 MAXIMUS, 관계 지도·지구본·연간 수익률 퀼트, 라이브러리·기록 화면을 제공합니다. 원본의 비공개 모델이나 수집되지 않은 관측값을 구현 완료로 표시하지 않습니다.

추가 연결: PEAD·내부자·EPS 변화·실적 달력·국면 성과·RSS·CFTC, PM의 6개 세부 화면과 14개 핵심 차트, 13개 산업39개 지표, 재귀성5기둥과3개 시장의36개월3D/5축 레이더를 독립 계산합니다. 지수 ML은 6타깃, 11종 모형과 2앙상블, 변수 선택·TreeSHAP·3패널 평가·선행/가격·24개월 원점 표를 제공합니다. [학습 설정과 자료 한계](research/ML_MODEL_CONTRACT.md)를 확인할 수 있습니다. 출처 기반 관계망과8개 가정 시나리오·원장 프리모템은 [계산 계약](research/RELATION_CONTRACT.md)에 따라 연결했습니다. 위성 현장은22시설의 실제 RGB/NDVI 관측과 지도·시설 상세를 연결했습니다. 관측 기준점·범위를 시설마다 명시하며, NASA 전 지구 배경을 추가했으며 원본 고해상도 배경·지명 레이어와 전체 사업 관계는 계속 구현할 대상입니다. 버튼 연결 수를 완성된 원본 기능 수로 표시하지 않습니다.

Vercel은 검증한 docs 결과를 게시하고, GitHub에는 코드·문서·작은 계산 결과를 보관합니다. 화면을 열 때 원본 사이트나 시세 API를 호출하지 않습니다. 자체 SVG 차트와 로컬 지도 데이터를 사용합니다. 위성 현장의 NASA 배경을 선택하면 지도에 보이는 영상만 GIBS에 요청하며, 해안선 배경으로 끌 수 있습니다.

Overview는 TESSERACT6축·CROWDING5축의36시점 궤적, 4시점 적층 레이더와 시총 표본 내 주도주10개를 표시합니다. [축·정보 시차·표본 계약](research/OVERVIEW_CONTRACT.md)에 원본 구조와 팀 계산 설정의 차이를 기록했습니다.

지정학은15주제·4카테고리, 19키워드의30일 분포와7일 비교, 3개 복합지표, 6개 영향 채널 및 보도 후 가격 관측을 제공합니다. 공식 GPR의 전체/위협/행위 지수와8분류·8국가 자료는 [별도 단위와 표본](research/GEOECON_CONTRACT.md)으로 표시합니다.

```powershell
python -m http.server 8769 --bind 127.0.0.1 --directory docs
```

SAURON은 22시설·USGS 지진·CelesTrak 궤도 요소를 Cesium 3D 지구본에 연결합니다. 카메라·투어·3개 레이어·6개 색상 효과·지명 검색과 관측 원장을 제공합니다. [SAURON 계약](research/SAURON_CONTRACT.md)에 자료 시각, SGP4 계산, 배경 선택과 요청 제한을 기록했습니다.

밸류체인 유니버스는20개 그룹·53개 업종의151기업을 탐색합니다. 업종별 표·기업/도시 선택·151기업의105도시/행정 대표점, 공식 주소11기업과 시가총액, 공시 공급 관계 및 기업 생산·서비스·실제 물류 근거를 표시합니다. 소재국 교역은 별도 참고 스위치로 구분하며 근거 문서의 변경을30일마다 확인합니다. [기업 탐색 계약](research/CHAIN_UNIVERSE_CONTRACT.md)에 도시·통화·갱신 주기와 전체 공급/물류 근거의 남은 범위를 기록했습니다.

## 로컬 수집과 계산

지구본의 국가 교역은 UN Comtrade45개 통계지역의 연간 총수출을 지도와 원장에 연결합니다. 수출 방향·금액별 곡선·국가 검색·정확한 USD와 분모를 표시하고 PC에서30일마다 재확인합니다. [교역 계약](research/TRADE_CONTRACT.md)에 통계지역·결측·참조연도와 기업별 밸류체인의 남은 범위를 기록했습니다.

Python 3.13과 [requirements.txt](requirements.txt)의 환경을 사용합니다. 원자료는 형제 폴더 sangsangin-investment-data에 저장합니다. SANGSANGIN_DATA_DIR로 경로를 바꿀 수 있습니다. 사용자가 승인한 실행 시간은 **한국시간 평일 오전8시·오후6시**입니다. 이 PC와 Codex 앱이 실행 중이어야 합니다. 예약은 Codex 앱의 자동화에서 관리하며, 아래 명령은 예약과 수동 실행이 공통으로 사용합니다.

```powershell
# 수집 → 별도 폴더 계산 → 검사 → 커밋/푸시 → Vercel 확인
python -m pipeline.refresh --publish
# 네트워크 수집·게시 없이 직전 정상 빈티지 재계산 및 검사
python -m pipeline.refresh --offline
```

변경 중인 작업 파일이 있으면 자동 게시를 중단합니다. 아래 개별 명령은 초기 구축·자료별 점검용입니다. 이후 전체 갱신은 refresh를 사용합니다.

```powershell
python -m pipeline.acquire universes --as-of 2026-09-08
# 기존 KRX 계정 인증을 사용자가 명시적으로 허용했을 때만 실행
python -m pipeline.krx_members --allow-krx-auth --as-of 2026-09-08
python -m pipeline.acquire core --as-of 2026-09-08
python -m pipeline.acquire stocks --as-of 2026-09-08
python -m pipeline.acquire macro --as-of 2026-09-08
python -m pipeline.acquire fundamentals --as-of 2026-09-08
python -m pipeline.options_data --as-of 2026-09-08
python -m pipeline.ecos_data --key-file '<로컬 ECOS 키 설정 파일>' --as-of 2026-09-08
python -m pipeline.local_consensus '<로컬 qw_consensus.duckdb>' --as-of 2026-09-08
python -m pipeline.krx_reconcile --allow-krx-auth --as-of 2026-09-08
python -m pipeline.risk_signals_data --allow-krx-auth --as-of 2026-09-08
python -m pipeline.oecd_data --as-of 2026-09-08
# 아래 계산은 네트워크를 사용하지 않음
python -m pipeline.ml_models --as-of 2026-09-08
python -m pipeline.maximus_model --as-of 2026-09-08
python -m pipeline.allocation_model --as-of 2026-09-08
python -m pipeline.build_all --as-of 2026-09-08
```

사용자 요청(2026-09-11)에 따라 누적 저장 용량 검사와 상한 차단을 제거했습니다. 수집·계산·검증·반복 확인은 기존 코드로 수행하고 캐시를 재사용합니다. 전체 가격 복사 대신 부모 빈티지와 변경분을 저장하고, 수정주가 배당 계수는 검증 후 적용합니다. 비균일 정정·분할·기존 OHLC 부족 시에만 해당 종목의 전체 역사를 다시 받습니다. 원자료·인증·실행 로그는 저장소 밖에 두고 코드·문서·작은 계산 결과만 게시합니다.

## 검증

브라우저 저장 트랜잭션 검사에는 `package.json`의 개발 의존성 `fake-indexeddb`가 필요합니다. 일반 환경은 `npm install`로 준비합니다. 이 PC의 정기 실행은 저장소 밖 테스트 도구 디렉터리의 같은 버전을 사용합니다. 웹 화면에는 이 테스트 라이브러리를 배포하지 않습니다.

```powershell
python -m unittest discover -s tests
python scripts/validate.py
python scripts/validate_extended.py
node scripts/test_charts.cjs
node scripts/test_dashboard.cjs
node scripts/test_extended.cjs
```

날짜, 학습 타깃 만기, OHLC, 행렬·그래프 무결성과 SVG 구조를 검사합니다. 대표 SVG는 브라우저 없이 래스터화해 확인합니다. 전체 브라우저 동작·픽셀 동일성 검사를 완료했다는 의미는 아닙니다.

PRINCIPIUM·IW·ASK의 글과 PDF/이미지 첨부는 브라우저에 저장하며 백업 JSON으로 이동합니다. 저장 범위·이전 메모 가져오기는 [로컬 리서치 가이드](research/LOCAL_RESEARCH.md)를 참조하세요.

PDF는 제목·저자·페이지별 본문을 읽고 원문 페이지를 근거에 인용할 수 있습니다. 본문 검색·TXT 내보내기·첨부 포함 백업과 기존 기록 보존을 연결했습니다. [PDF 처리 범위와 검증](research/PDF_EXTRACTION.md)에 파서·OCR 비교와 페이지 재사용, 처리 한도 및 요약의 남은 범위를 표시합니다.

리스크의 신호등은 미국12·한국7개 지표, 선제위험은 CSD·변동성 군집4진단을 제공합니다. 공식 KRX VKOSPI·코스피 순매수 금액과 SF Fed 뉴스감성을 PC에서 갱신하며, [신호등 계산 계약](research/RISK_SIGNALS_CONTRACT.md)에 단위·관측일·팀 임계값과 원본의 미공개 범위를 기록했습니다.

## 학습 출처

설계 학습의 출발점은 [ARAGORN-INVESTIUM](https://aragorn-investium.pages.dev/#glance)입니다. 원본 HTML/JS/차트/리서치 보존본은 별도 로컬 연구 폴더에 있으며 재게시하지 않습니다. 이번 확장 중 원본 사이트 요청은 하지 않았습니다. [지도 데이터 라이선스](research/MAP_LICENSE.md)를 별도로 표시합니다.

IW는15개월 복기와14주 연대기·보존 차트를 제공합니다. ASK는3기간 추세·사업 근거10테마·RS16종목·21자산·9위험관측·4차트·20모듈 요약을 정기 재생성합니다. [IW 날짜/보존 계약](research/IW_REVIEW_CONTRACT.md)과 [ASK 계산/출처 계약](research/DIGEST_CONTRACT.md)을 참조하세요.

실적은 글로벌 NI 표본Top20의 겹침 막대, 한국2기업 OP/지배NI와 미국10기업 NI근사/매출 상세, 기업 검색·연간/분기3패널을 제공합니다. 회계연도·환율·추정 기준과 직접 컨센서스/근사의 차이는 [실적 계산 계약](research/EARNINGS_CONTRACT.md)에 기록했습니다.

내부자 매수는 SEC 비파생 코드P·취득A와 접수시각을 확인한 공시의90일 카드·미니 가격선·거래 원장을 제공합니다. 원문 대조 표본과 PC 자동수집 상태를 구분하며, [집계·날짜·제외 규칙](research/OWNERSHIP_CONTRACT.md)을 공개합니다.

국면의 거시 발표 달력은 한국은행 통계·정책회의, 국가데이터처 보도계획과 미국10개 출처를 함께 표시합니다. 국가·7/30/90일·통계분류·검색, 미표기 시각과 수집실패 이전일정을 [달력 계약](research/CALENDAR_CONTRACT.md)에 따라 구분합니다.

위성 관측은 [시설·보정·용량 계약](research/SATELLITE_CONTRACT.md)에 따라 공개 Sentinel-2의4km 구역만 읽습니다. 화면은 보정한 RGB/NDVI와 촬영일을 표시하며 건설 진척률·가동률로 해석하지 않습니다.

RS는 KOSPI200 주도주·한국/미국 강약8종목 표·고정5Y축, 모멘텀은 강8/약8의3M/6M쌍을 제공합니다. ETF9분류의 통합 비교표·관측주기·금액 환산·배당락일 원장은 [ETF 계약](research/ETF_CONTRACT.md)에 따라 갱신합니다.

모멘텀의 **신고가 발굴**은 OEF 공시 주식101개와 공식 KOSPI200 구성201개에서 RS≥65·52주 고점5% 이내 종목을 선별합니다. 미국/한국 카드·44점 가격선·고점 점선·시장/업종 검색·장중 고점 갱신 필터를 제공하며, 구성과 가격의 기준일·제외 사유를 표시합니다. [신고가 계약](research/NEW_HIGHS_CONTRACT.md)의 수집과 계산을 정기 갱신에 연결했습니다.

국내 숏감마는 KRX KOSPI200 시세·공식 ETF 배율/순자산·실제 월간 만기를 바탕으로 원본의8개 지표를 연결했습니다. 전체지수형19개 ETF의 리밸런싱 민감도·실현변동성과 팀 취약성을 표시합니다. [국내 리스크 계약](research/KR_SHORTGAMMA_CONTRACT.md)에 딜러 감마와의 차이·날짜·현재 정의·미공개 설정을 기록했습니다.

멀티에셋 자산 모니터는 실제 S&P500·Nasdaq Composite·Russell2000 지수와 금 선물을 포함한21자산의4개요약·6개자산군 신호표·열지도·추세별막대를 제공합니다. [자산 모니터 계약](research/MULTIASSET_MONITOR_CONTRACT.md)에 ETF 대용과의 차이, 연초 첫 종가 YTD, 시장별 관측일과 계산 분모를 기록했습니다.

전략의 턴어라운드는 공식 대상의 연간3개년 이익 반등·가격 조건·44점 카드와 상세 근거를 제공합니다. 페어는 미국9쌍/한국4쌍을252회귀·120관측 z로 계산하며 [전략 카드 계약](research/STRATEGY_CARD_CONTRACT.md)에 표본·점수·검정의 범위를 기록했습니다.

PEAD는 공식 S&P100 주식101개 발표 자료에서48후보를 계산해 기본12개 가격 카드·전체보기·검색·발표/EPS/가격 원장을 제공합니다. 표시구간 변화에는 발표5달력일 전 가격이 포함되므로 실제 D0 이후 수익과 분리하며, [PEAD 계약](research/PEAD_CONTRACT.md)에 선별·시간·정기 갱신을 기록했습니다.

미국 옵션은 [범위·시각·갱신 계약](research/OPTIONS_CONTRACT.md)에 따라 보존 관측과 현재 참고 종가를 분리합니다. 자동수집 권한 확인 전 Cboe 추가 수집은 기본 비활성화하며, 기존 자료의 날짜를 유지합니다. 새7~50일·±15% 범위는 로컬 검산 단계이고 게시 자료는 이전 첫3만기 표본입니다.

리스크 콕핏은 자산배분의 ML 국면33개 목표비중을 공유해120개월 VaR/CVaR·변동성·낙폭·집중도,9요인 노출,5개 충격 가정,배분/지수 ML 신뢰도를 계산합니다. 비중·충격 기여·ML 분모 원장을 제공하며, [콕핏 계약](research/RISK_COCKPIT_CONTRACT.md)에 고정 장부와 동적 OOS의 차이·팀 스트레스 가정·월말 정렬을 명시했습니다.

DRAGONGLASS 리서치는 공식 근거의 URL 중복 제거·문서 카드·출처/연결/검색 필터와 Entity360 이동을 제공합니다. 이 브라우저의 PRINCIPIUM 기록·첨부도 읽기 전용으로 불러옵니다. [리서치 연결 계약](research/DRAGON_RESEARCH_CONTRACT.md)에 날짜·개인 자료·원본 대비 남은 범위를 기록했습니다.

DRAGONGLASS 지금 주목·트리거는 주도주/발굴 동시관측,모듈별 위험근거,지정학 제목,6테마,3개월 자산추세와 촬영일 원장을 연결합니다. 미확보 신호와 원본 전체점수의 차이는 [신호 계약](research/DRAGON_SIGNALS_CONTRACT.md)에 명시했습니다.

DRAGONGLASS 트리거의 임상 등록부는 비만·GLP-1/Lilly/UnitedHealth3범위의 모집 중·전체상태3상·최근 갱신5연구와 원문을 제공합니다. [조회 정의·갱신 계약](research/CLINICAL_CONTRACT.md)에 원본 검색식과의 차이를 기록했습니다.
