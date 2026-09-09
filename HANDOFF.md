# 다음 작업 인수인계

최신 기준은 [구현 현황](research/IMPLEMENTATION_STATUS.md), [데이터 정의](research/DATA_DEFINITIONS.md), docs/data/status.json이다. 초기 RS만 구현했던 TODO보다 현재 코드·스냅샷을 우선한다.

- 사용자 목표: 가능한 모든 탭 실제 구현. 색은 자유롭지만 축·기간·패널 구조 유지. 외부 공식 지수·업종 정의를 적극 활용한다.
- 사용자가 기존 KRX 계정 인증 조회를 허용했다. --allow-krx-auth가 있어야 pykrx를 import한다. 설치된 pykrx는 import 때 인증할 수 있어 stdout/stderr를 억제하고 계정 정보를 출력하지 않는다.
- 기존 GitHub Pages main/docs에 코드·문서·작은 파생 결과 게시가 허용되었다. Sites/Cloudflare로 옮기지 않는다.
- 원본 보존본은 형제 aragorn_investium_study. 다시 크롤링하지 않는다. 원본 서술·차트·소스를 공개 저장소에 복사하지 않는다.
- 원자료는 형제 sangsangin-investment-data/expanded/2026-09-08, 초기 가격은 sangsangin-investment-data/2026-09-08. 사용자 승인 한도 512 MiB. JSON gzip 변환은 압축 해제 해시를 검증했고 원본 DB는 변경하지 않았다.
- KRX 대형주1002의 100종목, KOSPI200 공식 조회 목록, IVV 공시 주식504개. KOSPI200 응답201개는 그대로 표시한다. 역사 구성종목 백테스트라고 주장하지 않는다.
- KR 페어는 공식 상품명으로 정의를 확정했다. IT266370, 대형주337140, 가치275290/성장325010, 필수소비재266410, 지주307520. 조선0115D0은 역사 부족으로 5Y z가 비어 있을 수 있다.
- Yahoo 국내 과거 종가의 일부 OHLC 범위 오류를 KRX로 확인했다. 별도 price_corrections.json.gz를 적용하고 원본 CSV는 보존한다. 시가·고가·저가의 일치 배율로 분할 조정을 정렬하고 기존 배당 조정 계수를 유지한다. 정렬 불가는 격리한다. FX·선물 settlement 범위 차이와 구분한다.
- 23개 분석·콘텐츠 탭이 연결되었으나 모두 완전한 원본 복제는 아니다. 삭제 요청한 소유자 전용 탭과 만든이 표시는 제거했다. 각 탭의 missing 항목을 유지한다.
- ML은 월별 3모델 기준모형. macro를 가격의 월 인덱스에 먼저 reindex한 뒤 shift(2)한다. 순서를 바꾸면 예측월이 잘린다. 최신 수정 거시 빈티지의 결과는 PIT 실시간 성과가 아니다.
- MAXIMUS는 3-expert OOS 역 MSE 게이트이며 원본 10-expert MoE가 아니다. Python 서버 실행·임의 종목 입력은 Pages에 없다.
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
