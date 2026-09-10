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

추가 연결: PEAD·내부자·EPS 변화·실적 달력·국면 성과·RSS·CFTC, PM의 6개 세부 화면과 14개 핵심 차트, 13개 산업39개 지표, 재귀성5기둥과3개 시장의36개월3D/5축 레이더를 독립 계산합니다. 지수 ML은 6타깃, 11종 모형과 2앙상블, 변수 선택·TreeSHAP·3패널 평가·선행/가격·24개월 원점 표를 제공합니다. [학습 설정과 자료 한계](research/ML_MODEL_CONTRACT.md)를 확인할 수 있습니다. 출처 기반 관계망과8개 가정 시나리오·원장 프리모템은 [계산 계약](research/RELATION_CONTRACT.md)에 따라 연결했습니다. 위성 현장은22시설 중14곳의 실제 RGB/NDVI 관측과 지도·시설 상세를 연결했습니다. 나머지8곳 위치 검증·전체 사업 관계·국내 옵션 숏감마 등은 계속 구현할 대상입니다. 버튼 연결 수를 완성된 원본 기능 수로 표시하지 않습니다.

Vercel은 검증한 docs 결과를 게시하고, GitHub에는 코드·문서·작은 계산 결과를 보관합니다. 화면을 열 때 원본 사이트나 시세 API를 호출하지 않습니다. 자체 SVG 차트와 로컬 지도 데이터로 표시합니다.

Overview는 TESSERACT6축·CROWDING5축의36시점 궤적, 4시점 적층 레이더와 시총 표본 내 주도주10개를 표시합니다. [축·정보 시차·표본 계약](research/OVERVIEW_CONTRACT.md)에 원본 구조와 팀 계산 설정의 차이를 기록했습니다.

지정학은15주제·4카테고리, 19키워드의30일 분포와7일 비교, 3개 복합지표, 6개 영향 채널 및 보도 후 가격 관측을 제공합니다. 공식 GPR의 전체/위협/행위 지수와8분류·8국가 자료는 [별도 단위와 표본](research/GEOECON_CONTRACT.md)으로 표시합니다.

```powershell
python -m http.server 8769 --bind 127.0.0.1 --directory docs
```

## 로컬 수집과 계산

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
python -m pipeline.oecd_data --as-of 2026-09-08
# 아래 계산은 네트워크를 사용하지 않음
python -m pipeline.ml_models --as-of 2026-09-08
python -m pipeline.maximus_model --as-of 2026-09-08
python -m pipeline.allocation_model --as-of 2026-09-08
python -m pipeline.build_all --as-of 2026-09-08
```

기본 누적 로컬 한도는 사용자 승인에 따라 **512 MiB**입니다. 전체 가격 복사 대신 부모 빈티지와 변경분을 저장하고, 수정주가 배당 계수는 검증 후 적용합니다. 비균일 정정·분할·기존 OHLC 부족 시에만 해당 종목의 전체 역사를 다시 받습니다. 원자료·인증·실행 로그는 저장소 밖에 두고 코드·문서·작은 계산 결과만 게시합니다.

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

PRINCIPIUM·IW·ASK의 글과 PDF/이미지 첨부는 브라우저에 저장하며 백업 JSON으로 이동합니다. 저장 범위·이전 메모 가져오기·한도는 [로컬 리서치 가이드](research/LOCAL_RESEARCH.md)를 참조하세요.

## 학습 출처

설계 학습의 출발점은 [ARAGORN-INVESTIUM](https://aragorn-investium.pages.dev/#glance)입니다. 원본 HTML/JS/차트/리서치 보존본은 별도 로컬 연구 폴더에 있으며 재게시하지 않습니다. 이번 확장 중 원본 사이트 요청은 하지 않았습니다. [지도 데이터 라이선스](research/MAP_LICENSE.md)를 별도로 표시합니다.

IW는15개월 복기와14주 연대기·보존 차트를 제공합니다. ASK는3기간 추세·사업 근거10테마·RS16종목·21자산·9위험관측·4차트·20모듈 요약을 정기 재생성합니다. [IW 날짜/보존 계약](research/IW_REVIEW_CONTRACT.md)과 [ASK 계산/출처 계약](research/DIGEST_CONTRACT.md)을 참조하세요.

실적은 글로벌 NI 표본Top20의 겹침 막대, 한국2기업 OP/지배NI와 미국10기업 NI근사/매출 상세, 기업 검색·연간/분기3패널을 제공합니다. 회계연도·환율·추정 기준과 직접 컨센서스/근사의 차이는 [실적 계산 계약](research/EARNINGS_CONTRACT.md)에 기록했습니다.

내부자 매수는 SEC 비파생 코드P·취득A와 접수시각을 확인한 공시의90일 카드·미니 가격선·거래 원장을 제공합니다. 원문 대조 표본과 PC 자동수집 상태를 구분하며, [집계·날짜·제외 규칙](research/OWNERSHIP_CONTRACT.md)을 공개합니다.

국면의 거시 발표 달력은 한국은행 통계·정책회의, 국가데이터처 보도계획과 미국10개 출처를 함께 표시합니다. 국가·7/30/90일·통계분류·검색, 미표기 시각과 수집실패 이전일정을 [달력 계약](research/CALENDAR_CONTRACT.md)에 따라 구분합니다.

위성 관측은 [시설·보정·용량 계약](research/SATELLITE_CONTRACT.md)에 따라 공개 Sentinel-2의4km 구역만 읽습니다. 화면은 보정한 RGB/NDVI와 촬영일을 표시하며 건설 진척률·가동률로 해석하지 않습니다.
