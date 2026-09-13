# Markdown 작업 인벤토리

이 문서는 `scripts/write_work_inventory.py`가 생성한다. Markdown에 남은 미완료·후속 표현을 출처 줄과 함께 전수 색인한다.
체크박스는 현재 정본(패리티 표·로드맵·계약)의 실행 후보에만 사용한다. 운영·생성 문서는 중복·현황 증거이며, `HANDOFF.md`는 역사 인계 증거다. 어느 행도 코드·원자료·검증 결과 재확인 없이는 미완료 또는 완료로 단정하지 않는다.

출처 파일 73개 · 표현 279개

## 분류

- 현재 정본 실행 후보: 92개
- 운영 문서 증거: 11개
- 생성·파생 문서 증거: 69개
- 역사 인계 증거: 107개

## 현재 정본 실행 후보

### `research/ATTENTION_CONTRACT.md`

- [ ] [research/ATTENTION_CONTRACT.md:11](../research/ATTENTION_CONTRACT.md#L11) — 현재 UTC일에서2일 이전까지를 상한으로 쓰며 가격 기준일보다 늦은 날을 요청하지 않는다. 동일 완료일/설정의 성공 확인은24시간 캐시한다. 요청 간격1초, 실패 시1시간 백오프,401/403/429이면 같은 실행의 후속 요청을 중단한다. 실패는 이전 성공 열람/성공 시각을 유지하며 최신 오류를 따로 기록한다. 가격 계산과 같은08/18 refresh에 수집기를 연결했으며 브라우저는 이미 계산한 JSON만 읽는다. 저장 용량 검사·추가 AI 호출이 없다.
- [ ] [research/ATTENTION_CONTRACT.md:17](../research/ATTENTION_CONTRACT.md#L17) — 최근 관측일이 가격 기준일보다 늦지 않고3일 이내, 성공 수집 후72시간 이내, 최근 오류 없음,14일 완전한 경우에만 가용하다. 변화가+40% 이상이면 관심도 신호+2를 한 번 합산한다. 기술 신호는 동일한 가격일로 정렬하고 열람 신호는 별도 UTC 관측일과 실제 수집 시각을 표시한다. 현재 관측 모니터이며 과거 당시에 알 수 있었던 데이터 빈티지나 백테스트 입력으로 쓰지 않는다. 전체점수/live/기대수익은 계속null이며 기업 뉴스량·감성·정량뷰 미확보를0점으로 확정하지 않는다.
- [ ] [research/ATTENTION_CONTRACT.md:23](../research/ATTENTION_CONTRACT.md#L23) — 남은 범위: 전체 기업 뉴스·감성/커뮤니티·추가 문서 및 언어·리디렉션 합산, 제목 변경 전후의 리디렉션 열람을 검증한 연속성, 원본 비공개 비교 기간/PIT 동등성. 이 기능은10기업 문서 열람이며 뉴스 전체 구현 완료가 아니다.
- [ ] [research/ATTENTION_CONTRACT.md:25](../research/ATTENTION_CONTRACT.md#L25) — 기업 상세 누락 보완: 기존701기업에 ASML 미국 상장 종목을 추가했다. 보존 가격이 없어서 기존 수집기로 ASML 1종목의3년 일봉752건을 확보하고 OHLC 범위·USD 호가를 확인한다. 공식 S&P500 구성원으로 편입하지 않으며 추가 관찰 종목으로 표시한다. 기업 상세702기업의 가격/수익률/SPY Beta/252일 상관 원장을 함께 계산하고 다음 정기 가격 갱신에도 포함한다. ASML의 미확보 재무·실적 예정일은 임의로 채우지 않는다.

### `research/CHAIN_UNIVERSE_CONTRACT.md`

- [ ] [research/CHAIN_UNIVERSE_CONTRACT.md:43](../research/CHAIN_UNIVERSE_CONTRACT.md#L43) — ## 완료 판단과 남은 범위

### `research/CLINICAL_CONTRACT.md`

- [ ] [research/CLINICAL_CONTRACT.md:22](../research/CLINICAL_CONTRACT.md#L22) — ## 화면과 남은 범위
- [ ] [research/CLINICAL_CONTRACT.md:30](../research/CLINICAL_CONTRACT.md#L30) — 원본의 정확한 검색식/기관별 인수·자회사 범위,전체 연구별 변화 이력·신규 모집 알림·규제 승인·임상 결과 해석은 남은 범위다. 13F·기업 뉴스 감성·관심량과 비공개 정량 투자뷰도 별도 구현 대상이다.

### `research/COMPANY_FINANCIAL_CONTRACT.md`

- [ ] [research/COMPANY_FINANCIAL_CONTRACT.md:21](../research/COMPANY_FINANCIAL_CONTRACT.md#L21) — ## 검증과 남은 범위

### `research/COMPANY_NEWS_CONTRACT.md`

- [ ] [research/COMPANY_NEWS_CONTRACT.md:11](../research/COMPANY_NEWS_CONTRACT.md#L11) — 원 응답 XML과 해시는 PC에 보관하며 같은 내용의 원 응답을 재복제하지 않는다. 공개 결과에는 기사 메타데이터·원문 링크·직접 계산한 관측 수만 담는다. 기사 본문·사진은 수집하거나 게시하지 않는다. 수집 전 캐시 확인, 24시간 재사용, 요청 사이1초, 오류 후1시간 재시도 대기, 401/403/429 발생 시 남은 배치 중단을 적용한다. 실패하면 이전 기사·성공 시각을 유지하고 최근 시도와 오류를 별도로 기록한다.
- [ ] [research/COMPANY_NEWS_CONTRACT.md:13](../research/COMPANY_NEWS_CONTRACT.md#L13) — 새 응답은 URL별 관측 목록과 합친다. 피드에서 사라진 기사는 과거 관측으로 남긴다. 최초 수집 시각을 보존하고 마지막 관측 시각·제목·공급처 발행 시각 정정은 새 관측으로 갱신한다. 이는 실제 발행 당시 수집 빈티지가 아니며 과거 시점 자료로 소급하지 않는다. 처음 수집하기 전의 전체 기사 이력은 미확보다.
- [ ] [research/COMPANY_NEWS_CONTRACT.md:21](../research/COMPANY_NEWS_CONTRACT.md#L21) — 기술 신호는 기존처럼 기업 가격일과 일치시킨다. 뉴스는 별도의 최근 기사 발행일·수집 시각을 기록하며 중복 피드나 반복 계산으로 뉴스1점을 중복 가산하지 않는다. 전체 점수·기대수익·실시간 종합 점수는 미산출을 유지한다. 제목에서 기업별 호재/악재를 단정하지 않으며 기업별 문맥 감성은 미확보로 유지하고, 연결된 영문 제목 전체의 톤은 아래 별도 모델 계약으로 분류한다. 문서 열람·뉴스 수·커뮤니티 반응을 서로 대체하지 않는다.
- [ ] [research/COMPANY_NEWS_CONTRACT.md:25](../research/COMPANY_NEWS_CONTRACT.md#L25) — 기업별 기사 수·최신5개 제목과 링크·나머지 기사 펼치기·발행/최초 관측/성공 수집/최근 시도·미확보 표시를 제공한다. 기업·티커·기사 제목 검색, 기사8건 조건/수집 상태 필터, 기업 상세 이동과 그 화면의 기사 패널, 신호 카드의 최신 기사/조건 근거를 연결한다. 브라우저에서는 데이터 JSON만 읽고 뉴스 사이트에 자동 요청하지 않는다.
- [ ] [research/COMPANY_NEWS_CONTRACT.md:29](../research/COMPANY_NEWS_CONTRACT.md#L29) — ## 검증과 남은 범위
- [ ] [research/COMPANY_NEWS_CONTRACT.md:43](../research/COMPANY_NEWS_CONTRACT.md#L43) — 40피드 모두 기업 상세와 연결한다. 기존 702개 상세에 ALAB·ARM·CRWV·ENTG·NBIS를 추가해 707개가 되었다. 한미사이언스(008930.KS)는 기존 KOSPI200 기업 상세를 재사용한다. 신규 미국 5개는 Nasdaq 종목 디렉터리의 종목명·시험종목 여부·ETF 여부를 확인했으며, 확인 시각과 공식 링크를 표시한다. 한미사이언스 식별자는 DART 회사 정보로 확인했다. 공식 지수 구성 및 업종은 종목 존재 확인과 별개다. 추가 5개는 공식 업종 미확보·추가 사업 관찰로 표시하고 RS를 임의로 채우지 않는다. 후속 [재무·일정 보완](COMPANY_FINANCIAL_CONTRACT.md)에서 실제 자료를 추가 연결했다.

### `research/DIGEST_CONTRACT.md`

- [ ] [research/DIGEST_CONTRACT.md:34](../research/DIGEST_CONTRACT.md#L34) — 관찰16종목은 KRX 대형주와 IVV 공식 주식 유니버스에서 기존 RS 상위8개씩이다. RS는 원래의 가중 모멘텀 규칙을 유지하고 ASK에 표시한 기간 수익률은 위 달력 규칙을 사용한다. 공식 업종과 구성 기준일을 표시한다. 기사 제목에서 정확한 이름/심볼 단어가 일치한 현재 RSS 표본만 센다. 예를 들어 `TER`를 `interest`에 매칭하지 않는다. 기준일 종료(KST) 이후 제목은 제외한다. 표본0건은 전 세계 관심0건을 뜻하지 않는다. 구루 보유는 미확보로 남긴다.
- [ ] [research/DIGEST_CONTRACT.md:40](../research/DIGEST_CONTRACT.md#L40) — 모듈 요약은 현재 계산 묶음의20개 분석 모듈에서 기준일·주요 값·표의첫2행(최대2표)·방법·남은 범위를 참조한다. ML/통합예측의 별도 기준일을 유지하고 이후 날짜 자료가 끼면 중단한다. 원본 내부 요약이18개인 것과 구분한다. 원본에 없는 분석 내용을 만들어 개수를 채우지 않는다.
- [ ] [research/DIGEST_CONTRACT.md:46](../research/DIGEST_CONTRACT.md#L46) — Python 검사는 달력 시점·매일/거래일 정렬·오래된 가격·부분 결측 평균 금지·동률·뉴스 단어 경계·위험 임계값·정보 시차·z 차이를 확인한다. 공개 스키마와 실제 기간 선택 콜백, 외부 링크/본문 이스케이프, 대표 SVG 래스터를 검사한다. 브라우저 레이아웃 QA는 아니다. 원본 자동 AI 질의 서버·구루/전체 뉴스량·실제 온톨로지 사업 가중치는 남은 범위다.

### `research/DRAGON_OPERATIONS_CONTRACT.md`

- [ ] [research/DRAGON_OPERATIONS_CONTRACT.md:11](../research/DRAGON_OPERATIONS_CONTRACT.md#L11) — 상태는 최근 오류, 자동조회 설정 필요, 미확인, 수집 대기, 빈 응답, 캐시 시간 내/경과를 구분한다. 성공 후 경과가 코드 TTL을 넘었다는 표시가 예약 실패를 의미하지는 않는다. 특히 USGS 1시간/CelesTrak 2시간 캐시는 평일 08/18시 실행 사이에 만료될 수 있다. 13F 검토 공시를 자동수집 정상으로 표시하지 않는다. 지역/기업 다건 수집기는 가장 오래된 성공 수집 시각을 표시하며 일부 실패는 이전 값이 있어도 오류 표시한다. 소스별 수량 단위가 달라 합산하지 않는다.
- [ ] [research/DRAGON_OPERATIONS_CONTRACT.md:23](../research/DRAGON_OPERATIONS_CONTRACT.md#L23) — 모듈 원장은 RS·모멘텀을 포함한 분석/콘텐츠 모듈의 구현 상태, 가격 기준일, 계산 생성 시각, 패널 수와 남은 범위 항목 수를 제공한다. 각 모듈로 이동할 수 있다. 브라우저에서 계산하는 평일 08시/18시 KST 카운트다운은 예약된 시각의 안내일 뿐 현재 PC 실행·배포 성공을 보장하지 않는다. 공휴일도 현재 승인된 평일 예약 기준을 따르고, 실제 수집은 거래소 관측일을 보존한다. 화면을 벗어나면 타이머를 해제한다.
- [ ] [research/DRAGON_OPERATIONS_CONTRACT.md:25](../research/DRAGON_OPERATIONS_CONTRACT.md#L25) — 전체 소스 30종의 독립 수집, 원본 인사이트 버스/키 연결, 실제 PC 실행 상태 스트리밍, 사용자 소스 설정을 PC에 전달하는 인증된 제어 API는 남은 범위다. 유료 서비스/새 인증 가입은 하지 않는다. 저장 용량 순회나 상한은 없다.

### `research/DRAGON_RESEARCH_CONTRACT.md`

- [ ] [research/DRAGON_RESEARCH_CONTRACT.md:17](../research/DRAGON_RESEARCH_CONTRACT.md#L17) — ## 정기 갱신과 남은 범위
- [ ] [research/DRAGON_RESEARCH_CONTRACT.md:21](../research/DRAGON_RESEARCH_CONTRACT.md#L21) — 원본 비공개 투자 리포트,167편 전체,투자뷰의 수치 기대수익,자동 해석과 팀 공용 저장소는 남은 차이다. 지금 주목과 트리거는 이 카탈로그와 주도주/발굴 관측을 연결했다. 나머지 미확보 신호와 원본 종합점수 차이는 [신호 계약](DRAGON_SIGNALS_CONTRACT.md)에 기록했다.

### `research/DRAGON_SIGNALS_CONTRACT.md`

- [ ] [research/DRAGON_SIGNALS_CONTRACT.md:5](../research/DRAGON_SIGNALS_CONTRACT.md#L5) — ## 관측과 미확보 항목
- [ ] [research/DRAGON_SIGNALS_CONTRACT.md:7](../research/DRAGON_SIGNALS_CONTRACT.md#L7) — 트리거 공개 규칙은 구루3, 주도주2, 발굴2, 관심급등2, 리서치 양의 기대수익2, 뉴스8건1, 감성양수1이다. 주도주·발굴과 지정10문서의 관심도 관측을 연결하며 같은 종목·같은 모듈은 중복 합산하지 않는다. 기업별 전체 뉴스/감성과 수치 투자뷰는 아직 없고13F의 최신 완전성과 시차 규칙은 검증 중이므로 전체점수는 null이다. 미확보를 관측0으로 확정하지 않는다. 두 기술 기반 신호는 독립 확률이나 검증된 투자 확신도가 아니다.
- [ ] [research/DRAGON_SIGNALS_CONTRACT.md:23](../research/DRAGON_SIGNALS_CONTRACT.md#L23) — 관심도 후속: Wikimedia 지정10기업 문서의 일별 열람·최근7일/직전7일·정확한 기업 연결·+40% 규칙을 연결했다. 최신10문서 중 급등0이며 기존4동시신호는 유지한다. 전체 뉴스 감성/관심도를 대표하는 값은 아니다. ATTENTION_CONTRACT.md 참조.
- [ ] [research/DRAGON_SIGNALS_CONTRACT.md:27](../research/DRAGON_SIGNALS_CONTRACT.md#L27) — [기업 뉴스 계약](COMPANY_NEWS_CONTRACT.md)에 따라23피드의UTC7일실제관측이8건이상일때1점을추가한다. 가격일과별도로기사발행일/수집일을표시하며전체뉴스량·감성·과거시점예측으로해석하지않는다. 최신기사는지금주목카드와기업상세에서원문으로연결한다. 이전본문의기업뉴스미연결상태는이후속구현이우선한다.

### `research/DYNAMICS_CONTRACT.md`

- [ ] [research/DYNAMICS_CONTRACT.md:63](../research/DYNAMICS_CONTRACT.md#L63) — 남은 범위: 공개되지 않은 최소표본·정정가격 빈티지와 수치 동등성, 결측 전 전체기간의 신뢰할 수 있는 원자료 보완, 실제 체결/펀딩/세금과 PIT 검증. 보존 원본의 캡처는 전체 페이지가 아니라 수식과 현재 3D 표면을 한 장으로 저장하는 기능임을 재확인했다. 아래 기능으로 연결했다.

### `research/EARNINGS_CONTRACT.md`

- [ ] [research/EARNINGS_CONTRACT.md:18](../research/EARNINGS_CONTRACT.md#L18) — 원본의 미국/글로벌 NI 미래 금액은 직접 NI 컨센서스가 아니라 **최근 실제 NI에 EPS 성장률을 적용한 근사**다. 원본의 모든 기업에 고정한 달력연도 표기는 그대로 옮기지 않는다. 수집 시 이미 받은 Yahoo `earningsTrend`에서 `period/endDate`만 추가 보존한다. 이 메타데이터 때문에 추가 네트워크 조회를 하지 않는다. 내부 yfinance 필드가 없어지면 기간을 미확보로 처리한다.
- [ ] [research/EARNINGS_CONTRACT.md:37](../research/EARNINGS_CONTRACT.md#L37) — 글로벌 NI는 기준일까지의 최근 환율(최대7일 경과)을 사용한다. KRW/JPY/CNY/INR/TWD/CAD는 각 `XXX=X`(현지 통화/USD)로 나누고 EUR/GBP는 `EURUSD=X`/`GBPUSD=X`로 곱한다. 회계기간 평균 환율이 아닌 **현재 환율 환산 비교**다. 환율 부호·날짜·통화를 검증하고 미확보 기업은 표본에서 제외한다. USD bn은10억 달러다.
- [ ] [research/EARNINGS_CONTRACT.md:43](../research/EARNINGS_CONTRACT.md#L43) — Python fixture는 회계기간·52주 결산·연결식·음수/미확보·매출 기준 불일치·환율 방향/신선도·국내 단위/관측일·수집 메타데이터를 검사한다. JavaScript fixture는 겹침막대/음수0축·기업 검색·연간/분기 콜백·출처 이스케이프를 검사한다. 대표 SVG를 오프라인 래스터로 확인한다. 브라우저 전체 동작·픽셀 동일성 검사가 아니다.

### `research/ETF_CONTRACT.md`

- [ ] [research/ETF_CONTRACT.md:7](../research/ETF_CONTRACT.md#L7) — 각 분류는 상품/1M/3M/YTD/1Y/12M분배율/관측주기/월평균/연환산/특성의10열을 제공한다. 분배율이 양수인 상품이 있으면 분배율, 없으면1Y 총수익률로 내림차순 정렬한다. 미확보 값은 뒤로 보내고 클릭 정렬·검색·투자금 변경을 지원한다. 월간 간격 관측 중 분배율 상위 상품은 월평균과1Y성과를 함께 강조한다. 막대와4기간 열지도는 접어서 추가 비교한다.

### `research/FUNDAMENTAL_UNIVERSE_CONTRACT.md`

- [ ] [research/FUNDAMENTAL_UNIVERSE_CONTRACT.md:13](../research/FUNDAMENTAL_UNIVERSE_CONTRACT.md#L13) — 실제 연간 또는 분기 손익 항목 및 재무 통화가 있는 자료만 정상 캐시로 인정한다. 정상 자료는 종목별 7일 동안 재사용한다. 빈 응답·통화 미확인·실패·기존 정상값을 대체할 수 없는 부분 응답은 미확보/이전 자료 보존으로 기록한다. 실패 관측을 정상 원자료 폴더에 덮어쓰지 않는다. 시도별 원응답은 저장소 밖 `company_financial/attempts/`에 남는다.
- [ ] [research/FUNDAMENTAL_UNIVERSE_CONTRACT.md:23](../research/FUNDAMENTAL_UNIVERSE_CONTRACT.md#L23) — 부모 구성 상속·자식 구성 교체·중복 제거·CSV 정규화 결과 재사용, 정상 재무 캐시와 달력 분리, 미확보/부분 응답 보존, 요청 제한 중단·유예·재개를 테스트한다. 수집 대상 등록은 해당 기업의 재무 확보나 기업 상세·시장 달력·사업관계 전체 검증 완료를 뜻하지 않는다. 실제 확보 수와 미확보 수는 실행 원장을 기준으로 별도로 보고한다.
- [ ] [research/FUNDAMENTAL_UNIVERSE_CONTRACT.md:25](../research/FUNDAMENTAL_UNIVERSE_CONTRACT.md#L25) — 2026-09-13 실제 검증: 가격 기준일2026-09-10의 구성자료 합집합945종목 중 최근 정상 재무215종목을 재사용할 수 있었다. 미확보 한국3개(000080.KS/000100.KS/000120.KS)·미국3개(A/ABBV/ABT)의 재무를 추가 수집해221종목으로 확대했다. 연간·분기 손익162값의 원자료 대조와 즉시 재실행0조회 확인을 마쳤다. 724종목은 여전히 미확보이며, 전체945종목 수집 완료를 의미하지 않는다. 별도 로컬 빈티지20260913T112310Z와 `runtime/fundamental-universe-pilot-result.json`에 보존했고 공개 스냅샷·배포에는 아직 반영하지 않았다.
- [ ] [research/FUNDAMENTAL_UNIVERSE_CONTRACT.md:32](../research/FUNDAMENTAL_UNIVERSE_CONTRACT.md#L32) — 미확보15개는 다음과 같다. 통화를 국가·티커만으로 추정하지 않았다.
- [ ] [research/FUNDAMENTAL_UNIVERSE_CONTRACT.md:39](../research/FUNDAMENTAL_UNIVERSE_CONTRACT.md#L39) — Windows의 일시적 파일 접근 거부가 배치를 중단한 실제 사례에 따라 `events_data.save`는 PermissionError에 한해 원자교체를 최대6회 재시도한다(대기0.1/0.2/0.4/0.8/1.6초). 영구실패는 예외를 전파하고 기존원장/새tmp를 보존한다. 다른 파일시스템 오류는 재시도하지 않는다. 새3검사 포함 전체390Python, 기존공개스냅샷 두자료검증기·3JS모음과 구문검사가 통과했다.
- [ ] [research/FUNDAMENTAL_UNIVERSE_CONTRACT.md:41](../research/FUNDAMENTAL_UNIVERSE_CONTRACT.md#L41) — 기존 미커밋 작업과221캐시를 보존했다. 2026-09-13 후속에서 같은 빈티지 스냅샷을 검증·게시했고, 운영 배포state는 run `20260913T123639Z`, vintage `20260913T112310Z`, commit `f4bb3269e386d82116dd3304c9af769bec5e4fc6`이다. 930개는 raw 재무 캐시 범위이며 기존 실적 연구 화면 표본197개와 혼동하지 않는다.

### `research/GEOECON_CONTRACT.md`

- [ ] [research/GEOECON_CONTRACT.md:11](../research/GEOECON_CONTRACT.md#L11) — 7개 제공처의 제목·발행 시각·링크만 수집한다. RSS2, RDF/RSS1, Atom을 읽고 timezone 없는 날짜와 HTTPS 이외 링크는 제외한다. 현재 제공처의 수집 상태를 그대로 표시한다. 최초/후속 수집 파일은 로컬 부모 빈티지에 남으며 이후 계산에서 URL 기준으로 합친다. 이전 목록에서 빠진 기사를 삭제하지 않고 최초 수집 시각을 보존한다.

### `research/GURU_CONTRACT.md`

- [ ] [research/GURU_CONTRACT.md:43](../research/GURU_CONTRACT.md#L43) — 연락처가 준비되면6개 보고 법인의 submissions 최근 목록을24시간 캐시로 확인한다. 최신부터 최대4개 보고기간의 원보고·정정을 찾고 신규 접수번호의 표지만/정보표를 받아 XML·주체·날짜·행 수·합계를 대조한다. 기존 접수번호는 재다운로드하지 않는다. 인접 보고기간의 같은 CUSIP·종류·옵션 구분별 보고 금액 차이를 별도 원장으로 표시하지만, 이는 거래일·순매수·현재 보유가 아니다. 최근 목록에13F가 없으면 과거 보유를 최신으로 승격하지 않고 미확보 상태를 남긴다. 전체 오래된 submissions 파일 탐색은 후속 범위다.
- [ ] [research/GURU_CONTRACT.md:45](../research/GURU_CONTRACT.md#L45) — 요청은1초 간격이며401/403/429는 전체 후속 요청을 중단하고 같은 연락처/구성의 재시도도 보류한다. 일반 오류는24시간 뒤 재확인한다. 실패한 실행은 이전 공시·실제 성공시각을 보존한다. 원자료는 부모 빈티지에서 상속하고 공개 화면은 정적 계산 결과만 읽는다. 용량 검사·저장/전송 상한은 없다.
- [ ] [research/GURU_CONTRACT.md:51](../research/GURU_CONTRACT.md#L51) — 6개 법인 확인 공시를 연결했으며 최신 전체13F·연속분기 편입/매도·미대응 CUSIP과 유니버스 밖 기업 확장·구루별 뉴스/관심도·16인 선택 풀과 관리자 설정 반영은 아직 미완이다. 전체 세부탭 목표의 완료를 뜻하지 않는다.
- [ ] [research/GURU_CONTRACT.md:59](../research/GURU_CONTRACT.md#L59) — 성공 대응은30일, 식별자 미확보·다중 후보는7일 캐시다. 최초5개 진단 결과를 재사용하고 나머지148개 식별자를30배치로 수집했다. 총153개 결과 중140개는 단일 대응,13개는 미확보다. 전체 공시의173개 합산 포지션 중 현재 기업 상세에73개 포지션·57기업을 연결했다. 나머지는 유니버스 밖·다른 증권 유형·미확보 사유를 각각 표시한다. 재실행은0요청이었다.
- [ ] [research/GURU_CONTRACT.md:61](../research/GURU_CONTRACT.md#L61) — 실패한 응답은 이전 정상 식별자/확인시각을 보존한다. HTTP401/403/429는 후속 배치를 중단하고 오류 실행은1시간 재요청을 보류한다. 오래된 성공 관측이30일을 넘으면 기업 연결에서 제외하며 공시 자체는 유지한다. 식별자 원응답·캐시는 PC `guru/identifiers.json.gz`에 저장한다. 평일08/18 갱신에서13F 수집 뒤 실행한다. 용량 검사는 수행하지 않는다.

### `research/IW_REVIEW_CONTRACT.md`

- [ ] [research/IW_REVIEW_CONTRACT.md:3](../research/IW_REVIEW_CONTRACT.md#L3) — 보존한 원본 IW의29행은 독립 지표29개가 아니라 월말 복기15건과 주간 연대기14건이다. 팀 화면은 같은 구성을 자체 ML 원장과 관측값으로 생성한다. 원본의 논평·이미지를 재게시하지 않는다. 원본 본문과 표의 합계가 다른 경우도 있어 방향 일치 건수와 상세 표는 반드시 같은 계산 결과에서 생성한다.
- [ ] [research/IW_REVIEW_CONTRACT.md:11](../research/IW_REVIEW_CONTRACT.md#L11) — ## 주간 연대기14건과 누적 보관
- [ ] [research/IW_REVIEW_CONTRACT.md:33](../research/IW_REVIEW_CONTRACT.md#L33) — ## 검증과 남은 범위

### `research/KR_SHORTGAMMA_CONTRACT.md`

- [ ] [research/KR_SHORTGAMMA_CONTRACT.md:24](../research/KR_SHORTGAMMA_CONTRACT.md#L24) — - 허용 기초지수는 `코스피 200`, `코스피 200 선물지수` 두 가지다. KOSPI200 IT/에너지화학 같은 업종형, KOSDAQ150, 해외 지수, 커버드콜, ETN은 제외한다. 공식 정의가 없는 후보나 순자산이 없는 상품은 미확보 행으로 남기고 전체 확보로 표시하지 않는다.
- [ ] [research/KR_SHORTGAMMA_CONTRACT.md:58](../research/KR_SHORTGAMMA_CONTRACT.md#L58) — `tests/test_kr_shortgamma.py`는 공식 대상 제외, 보고 순자산 우선, 양/음 충격·원 단위, 미확보, RV 정의, 미래 관측 불사용, 극단빈도의0범위와 분모, 고점 게이트, 공식 만기일·승수, 증분 정정과 자료 없는 화면을 검사한다. `validate_extended.py`는 실제 공개 계산 합계/단위/날짜를 대조하고 `test_extended.cjs`는 실제 하위 탭 선택과8행·두 차트 구조를 확인한다.

### `research/MAXIMUS_MODEL_CONTRACT.md`

- [ ] [research/MAXIMUS_MODEL_CONTRACT.md:50](../research/MAXIMUS_MODEL_CONTRACT.md#L50) — SEC filed 시점 분기재무·주식분할 조정 EPS, 한국 외국인 역사, SF Fed 뉴스감성 등 일부 확장 거시, 지수 이익추정 앵커, 원본 미공개 합성/규제 설정, 부분월 추론과 임의 티커 실행 서버는 추가 구현 대상이다. 현재 수정 자료에 시차를 준 OOS를 실시간 PIT 성과로 주장하지 않는다. 학습/규칙 설계 이후의 전향 검증은 별도로 축적해야 한다.

### `research/ML_MODEL_CONTRACT.md`

- [ ] [research/ML_MODEL_CONTRACT.md:13](../research/ML_MODEL_CONTRACT.md#L13) — RandomForest와 셔플 shadow를12번 적합하여 shadow 최대 중요도 초과 횟수 상위22개를 고른다. 동점은 평균 중요도, 변수명 순으로 고른다. 여기에 가용 위험/한국 강제 입력을 합친다. 원본의 설명은 엄격한 Boruta 유의성 확정검정과 다르므로 차트도 'Shadow 초과 횟수'로 표시한다. 미국 패널은 S&P500 대표이고 Nasdaq은 별도 선택한다. 강제 포함·미확보·최신 선택 목록을 남긴다.
- [ ] [research/ML_MODEL_CONTRACT.md:51](../research/ML_MODEL_CONTRACT.md#L51) — 미확보 입력은 CAPE/ERP, SF Fed 뉴스감성, 글로벌 월간 EPU, 역사 외국인 수급, VIX9D 등이다. [FRED HY OAS 안내](https://fred.stlouisfed.org/series/BAMLH0A0HYM2)는2026-04 이후 공개 이력이 최근3년으로 제한됨을 밝힌다. 현재2개월 거시 시차 뒤36개월 z 준비 기간이 부족하여 HY·HY/IG z와 이를 모두 요구하는 위험 합성 입력은 미산출이다. 대용 변수로 조용히 바꾸지 않는다.

### `research/NEW_HIGHS_CONTRACT.md`

- [ ] [research/NEW_HIGHS_CONTRACT.md:36](../research/NEW_HIGHS_CONTRACT.md#L36) — 수집 실패는 별도 상태로 보존한다. 같은 빈티지에서 반복 요청하지 않으며 이전 정상 구성을 사용하면 그 날짜와 실패 상태를 표시한다.14일을 넘으면 신고가 패널의 구성 자료를 미확보로 처리한다. 신규 편입 종목 가격은 기존 정기 수집의 회당25개 제한에 포함된다. 업종 사전 전체를 가격 수집 대상으로 확장하지 않는다.

### `research/NEWS_TONE_CONTRACT.md`

- [ ] [research/NEWS_TONE_CONTRACT.md:25](../research/NEWS_TONE_CONTRACT.md#L25) — ## 검증과 남은 범위
- [ ] [research/NEWS_TONE_CONTRACT.md:29](../research/NEWS_TONE_CONTRACT.md#L29) — 남은 범위는 전체 기업/제공처·완전한 과거 뉴스·기업을 대상으로 한 문맥감성·모델 교정/정확도 독립 평가·표본 밖 예측력이다. 제목 톤의 구현을 이 전체 범위의 완료로 세지 않는다.

### `research/OPTIONS_CONTRACT.md`

- [ ] [research/OPTIONS_CONTRACT.md:38](../research/OPTIONS_CONTRACT.md#L38) — 비활성·수집 실패 시 이전 정상 자료와 원래 시각을 유지하고 상태 원장을 남긴다. 옵션 미확보를0으로 만들거나 이전 자료의 시각을 갱신하지 않는다. 옵션 수집 중단은 Yahoo·KRX 등 별도 수급 자료의 갱신을 막지 않는다. 다른 실적 이벤트의 이전 스트래들을 새 발표에 재사용하지 않는다.

### `research/OVERVIEW_CONTRACT.md`

- [ ] [research/OVERVIEW_CONTRACT.md:56](../research/OVERVIEW_CONTRACT.md#L56) — 환산은 `earnings_details.fx_rate`와 동일한 명시적 통화 계약을 사용한다. KRW/JPY/CNY/INR/TWD/CAD는 해당 원통화/USD 호가로 나누고 EUR/GBP는 USD/원통화 호가를 곱한다. 기준일 이후 환율은 제외하고 실제 환율 심볼·관측일을 보존한다. 미지원·미확보·0 이하·유효하지 않은 환율은 미산출하며 통화 미기재를 USD로 가정하지 않는다. 환산 전 환율을 표시 정밀도로 반올림하지 않고, 임의의 시총 금액 상·하한으로 기업을 제외하지 않는다. 이 통화 지원은 해당 시장의 전체 기업·달력 검증 완료를 뜻하지 않는다.

### `research/OWNERSHIP_CONTRACT.md`

- [ ] [research/OWNERSHIP_CONTRACT.md:26](../research/OWNERSHIP_CONTRACT.md#L26) — 2026-09-08 기준 제공처 후보8행을 대조했다. 접수시각 확인7공시·9거래 행·4기업(PFE/CVNA/VST/CEG)을 집계했고, AVGO1공시는 접수시각 미확보로 제외했다. VST의 제공처1행은 실제8월31일·9월1일의2거래 행이며, CVNA1행도 같은 날 서로 다른 공시 가격의2행이다. 원문에 없는 시각을 서명일로 대신하지 않는다. 전체 미국 시장을 조사한 결과가 아니다.

### `research/PEAD_CONTRACT.md`

- [ ] [research/PEAD_CONTRACT.md:17](../research/PEAD_CONTRACT.md#L17) — 공식 S&P100을 추종하는 OEF 공시 **주식** 구성목록을 사용한다. 구성 기준일이 가격 기준일 이후이거나14일 초과 경과하면 계산하지 않는다. 현재 대상과 미확보·미선정 사유를 전체 원장으로 표시한다.
- [ ] [research/PEAD_CONTRACT.md:33](../research/PEAD_CONTRACT.md#L33) — 합성 가격의 발표 전 변화·D0 반응·후속 수익 분리, 미래 가격/발표, 미도래 기간, 오래된 가격, 중복 날짜, 최신 음수 이벤트/동시각 충돌, 공식 구성 기준일, 주말/13시 조기 폐장과 경계시각, 실패 후 정상 캐시 보존·재사용을 검사한다. 카드 기본12개/전체/검색/정밀값/음의 D0 수익/HTML 이스케이프와 실제 브라우저 표시를 확인한다. 거래비용 후 백테스트나 전체 발행사 발표시각 검증을 완료했다는 의미는 아니다.

### `research/POWER_RELATIONS_CONTRACT.md`

- [ ] [research/POWER_RELATIONS_CONTRACT.md:15](../research/POWER_RELATIONS_CONTRACT.md#L15) — 모든 수치는 발표된 계약·설비의 사실이다. 실시간 송전량·발전량(MWh)·매출·고객 수요 비중과 다르다. 가격 기준일보다 미래인 발표/후속 근거는 표시하지 않는다. 최신 검토 데이터이므로 과거 정보시점 백테스트에는 쓰지 않는다. 후속 수정의 원문이 과거 cutoff보다 늦으면 해당 수정 계약을 과거에 소급하지 않으며, 최초 계약의 완전한 PIT 이력을 재구성한 것은 아니다.
- [ ] [research/POWER_RELATIONS_CONTRACT.md:21](../research/POWER_RELATIONS_CONTRACT.md#L21) — 전파 계수는 기존가정 순방향0.28/역방향0.62 ×(0.7+0.1×weight)×0.9, weight=1이다. 계약MW나 실제 손익에 맞춰 추정한 탄력성이 아니며 미래 계약에도 ‘계약 관계의 가정 충격’을 적용한다. 확정 가동·수익률·인과 효과를 주장하지 않는다. 기술 협업은 기존 `collaborates`로 남긴다. 리서치 카탈로그는5최초 발표와 Crane 후속 발표를 URL별로 연결하고 발표일과 검토일을 분리한다.

### `research/QUANT_SCREENS_CONTRACT.md`

- [ ] [research/QUANT_SCREENS_CONTRACT.md:7](../research/QUANT_SCREENS_CONTRACT.md#L7) — - `kr_screen`의 Naver KOSPI300/KOSDAQ150 시총 표본에서 수집기가 적용한 우선주·SPAC·REIT 제외 결과를 사용한다. 실제 표본 수와 가격 미확보를 전체 원장에 남긴다. KRX 대형주와 동일한 집합이라고 부르지 않는다.
- [ ] [research/QUANT_SCREENS_CONTRACT.md:11](../research/QUANT_SCREENS_CONTRACT.md#L11) — - 숫자와 차트는 현재 빈티지다. 과거 PIT 구성/발표 빈티지, 거래비용·대차·차입비·배당/선물롤 비용 후 성과 검증은 별도 남은 범위다.
- [ ] [research/QUANT_SCREENS_CONTRACT.md:19](../research/QUANT_SCREENS_CONTRACT.md#L19) — z는 최근252시장일 평균과 모집단 표준편차(최소220관측)로 계산한다. 표준편차0은 미산출이다. |z|≥2는 진입 조건, 1≤|z|<2는 대기, 그 아래는 수렴권이다. z<0은 A Long/B Short 방향, z>0은 반대다. 이는 같은 금액의 양방향 가정이며 Beta중립을 보증하지 않는다.

### `research/REFERENCE_PARITY.md`

- [ ] [research/REFERENCE_PARITY.md:7](../research/REFERENCE_PARITY.md#L7) — | 탭/세부 화면 | 연결된 내용 | 추가 구현·검증할 내용 |
- [ ] [research/REFERENCE_PARITY.md:13](../research/REFERENCE_PARITY.md#L13) — | ETF 모니터 | 9분류·73위치 통합10열표·관측주기/월간상위·배당락일 원장·정렬/검색·금액변경·미확보 보존 | 공식 지급일/상품별 주기·별도 자본이득·ROC/세금·운용사별 대조; [ETF 계약](ETF_CONTRACT.md) |
- [ ] [research/REFERENCE_PARITY.md:29](../research/REFERENCE_PARITY.md#L29) — | 리스크 / 미국 옵션 | 게시 원장: 계약표기(모형별 제한 포함). ETF 정규화는 7~50일·행사가±15% 공급 만기 전수 기준으로 표준화되며, 주식 수급 모형은 7~45일 첫3만기 유지 | 원본 명시 범위는7~50일·행사가±15%. SPY 보존 전체 응답 검산/QQQ·IWM 전체 범위 미확보, 허용된 자동수집/API 확인 필요. CBOE SKEW 지수는 구현됨. [옵션 계약](OPTIONS_CONTRACT.md) |
- [ ] [research/REFERENCE_PARITY.md:46](../research/REFERENCE_PARITY.md#L46) — | 기업분석 / 관계지도 | 125객체·35사업/공급/경쟁/전력계약·3M293가격상관·108기업5778쌍·25386시차검정/788후보/BY기준3·3열/8행/전체검색·200행페이지/기업이동·3D전파; 공식분류 별도 | 원본159기업표기 중6미연결·추가43종목 가격 증분수집 대기·136가격기업의 정확한 구성/255객체/581관계 전체 독립 검증·BRK 클래스·시차표본밖검증·전체 사업/전력 관계; [계약](RELATION_DISCOVERY_CONTRACT.md) |
- [ ] [research/REFERENCE_PARITY.md:62](../research/REFERENCE_PARITY.md#L62) — | IW | 월말 복기15건·주간 연대기14건/누적 보존·36월3국면 띠/7계열ML 그림·주간별 그림 선택·구조화 판단/첨부/백업 | 실제 과거 발행본/PIT·작성자 논평·팀 공용 DB |
- [ ] [research/REFERENCE_PARITY.md:78](../research/REFERENCE_PARITY.md#L78) — 기업분석 리서치 후속: 공식 근거 URL별 문서 카드·검토일/보고기간 구분·전체/객체연결/공식/팀/로컬 필터·검색·기업 상세·리서치 자료실 읽기/첨부를 연결했다. 원본167편·비공개 투자뷰 수치·팀 공용 저장소는 미확보다. 지금 주목/트리거의 다중신호 합류는 계속 구현 대상이다. DRAGON_RESEARCH_CONTRACT.md 참조.
- [ ] [research/REFERENCE_PARITY.md:80](../research/REFERENCE_PARITY.md#L80) — 기업분석 지금 주목/트리거 후속: 순풍/경계·제목레이더·6테마·3M자산쌍·15카드·7규칙 상태·2종동시16카드·촬영8원장을 연결했다. 주도주/발굴2종만 확보했고 전체live/정량투자뷰/뉴스감성/13F/임상·변화감지는 남아 있다. DRAGON_SIGNALS_CONTRACT.md가 현재 계산 범위 정본이다.
- [ ] [research/REFERENCE_PARITY.md:82](../research/REFERENCE_PARITY.md#L82) — 임상 후속: 원본3범위를ClinicalTrials.gov공식API검색식으로정의하고모집/3상(전체상태)/최근5기록·전회대비·실패이전값·촉매원장·기업상세에연결했다. 원본검색식미공개/전체계열사와모든연구변화이력은계속대상이며CLINICAL_CONTRACT.md참조.
- [ ] [research/REFERENCE_PARITY.md:84](../research/REFERENCE_PARITY.md#L84) — 기업 뉴스 범위 확대: 40피드와707기업 상세(공식700/추가관찰7), 신규5기업의 공식 종목 식별·가격·뉴스·제목 톤을 연결했다. 전체 비기업 뉴스 객체와 복수 제공처, 한국 실적 일정과 전체 기업의 재무·일정, PIT 이력은 미완이다. [기업 뉴스 계약](COMPANY_NEWS_CONTRACT.md)을 참고한다.
- [ ] [research/REFERENCE_PARITY.md:91](../research/REFERENCE_PARITY.md#L91) — 전력 구매계약 후속: 공식5관계와4기업 추가로43객체·35사업관계·26가격기업의3개월 대조/전체 시차검정을 연결했다. 계약/시설 용량·예정·미확인을 분리하며 전체 공급망 완성은 아니다. [계약](POWER_RELATIONS_CONTRACT.md).
- [ ] [research/REFERENCE_PARITY.md:94](../research/REFERENCE_PARITY.md#L94) — 기업 범위 후속:159개 원본 기업 연구표기 중153개를149종목으로 대응했다. 추가43개는 거래소·KRX 식별을 확인했으며 가격은 기존 캐시 또는 다음 승인된 증분 수집 뒤에만 상관·시차·기업 상세에 반영한다. 해외 상장/클래스가 불명확한6개와 TEL 이름충돌·BRK 클래스 차이를 공개한다. 사업관계35개는 유지한다. [기업 범위 계약](RELATION_UNIVERSE_CONTRACT.md).

### `research/RELATION_CONTRACT.md`

- [ ] [research/RELATION_CONTRACT.md:10](../research/RELATION_CONTRACT.md#L10) — - 회사→사업 테마는 연구용 사업 연관이며 공식 GICS/KRX 업종·순수 테마 지수가 아니다. ADR TSM은 기존 공식700종목 밖 추가 Entity이며 공식 업종 미확보/RS 미산출로 표시한다.

### `research/RELATION_UNIVERSE_CONTRACT.md`

- [ ] [research/RELATION_UNIVERSE_CONTRACT.md:18](../research/RELATION_UNIVERSE_CONTRACT.md#L18) — `incremental.prices`는 등록부의 명시 종목을 일반 가격 유니버스와 합쳐 한 번에 최대25개 신규 시계열만 수집한다. 이는 제공처 요청을 나눈 실행 단위이며 저장 용량 상한이 아니다. 캐시가 없는 추가 식별 종목은 다음 승인된 실행에서 순차 수집하고, 가격 오류는 미확보로 남긴다.

### `research/RISK_COCKPIT_CONTRACT.md`

- [ ] [research/RISK_COCKPIT_CONTRACT.md:45](../research/RISK_COCKPIT_CONTRACT.md#L45) — **2008 금융위기형과 2020 코로나형도 팀의 가정이다.** 그 연도의 실현값을 재생한 결과가 아니다. 원본의 충격 계수는 비공개이고 현재 로컬 가격은2008년 전체를 포함하지 않으므로, 역사 자료를 확보한 것처럼 표시하지 않는다. 2008년 존재하지 않은 비트코인의 충격도 가정이다. 금리 +100bp는 +1%p 시나리오이며, 표 안의 채권 수익률은 수집한 공식 듀레이션 수치가 아니다. 원자재 +30%, 달러 +10%는 다른 자산의 동시 충격도 포함한다. 충격 기간·발생확률·비선형성·유동성·비용·후속 리밸런싱을 추정하지 않는다.
- [ ] [research/RISK_COCKPIT_CONTRACT.md:51](../research/RISK_COCKPIT_CONTRACT.md#L51) — 지수 ML은 로컬 `ml_transformer/{KOSPI,NASDAQ,SP500}_{1,3}M.json.gz` 전체 OOS 당시 선택모델 원장을 재학습 없이 읽는다. 기존 화면의 최근37개로 전체 적중률을 계산하지 않는다. 학습 타깃 종료일≤예측 원점, 타깃=원점+기간, 원점 중복 없음, 모델 계산일≤현재 가격일을 검증한다. 진행 중인 월·미만기·실현값 미확보는 제외한다.
- [ ] [research/RISK_COCKPIT_CONTRACT.md:59](../research/RISK_COCKPIT_CONTRACT.md#L59) — `build_all → extend → allocation_views → risk_cockpit.views` 순서다. 별도 네트워크 수집·모델 재학습 없이 평일08/18 기존 파이프라인에서 비중과 위험을 함께 갱신한다. 초기 적용에서는 기존 옵션·CSD 등 다른 위험 그룹과 배분 비중/성과가 변하지 않았는지 비교한다. 옵션 자동수집 권한 확인은 별도이며, 그 대기 상태가 콕핏 개발을 막지 않는다.

### `research/RISK_SIGNALS_CONTRACT.md`

- [ ] [research/RISK_SIGNALS_CONTRACT.md:7](../research/RISK_SIGNALS_CONTRACT.md#L7) — 신호등은 US12/KR7 표, 시장 점수·관측 수, KR 최근63세션 원장, 입력별 출처·관측일·수집 UTC·허용 지연과 수집 실패 상태를 표시한다. 미확보 값은 0이나 정상 신호가 아니다. 하나라도 미확보·기한 초과이면 관측된 점수만 합하고 시장 등급은 판정 보류다.
- [ ] [research/RISK_SIGNALS_CONTRACT.md:31](../research/RISK_SIGNALS_CONTRACT.md#L31) — KR 연속경계는7개 모두 관측된 합계6점 이상인 최근 연속 세션 수다. 미확보가 끼면 거기서 멈추고 확인 가능한 하한(≥)을 표시한다. 최신 세션이 불완전하면 미산출이다. 최대63세션 원장만 보며, 63개 모두 경계이면63일 이상이다.

### `research/SAURON_CONTRACT.md`

- [ ] [research/SAURON_CONTRACT.md:19](../research/SAURON_CONTRACT.md#L19) — 최초 확보는 USGS 응답37개 중 raw M=2.45 한 건을 제외한36개, stations 그룹21개다. 가격 기준일2026-09-08과 관측 시각2026-09-10을 혼동하지 않는다. 이후 건수는 자료 갱신에 따라 변한다. 관측 오류/미확보를0으로 채우지 않는다.
- [ ] [research/SAURON_CONTRACT.md:33](../research/SAURON_CONTRACT.md#L33) — 승인된 평일08/18시 refresh에 수집기를 연결했다. USGS 최소1시간, CelesTrak 최소2시간 캐시를 적용하며 브라우저는 두 관측 공급자를 조회하지 않는다. 성공/확인 시각을 구분하고 실패 시 마지막 성공 자료를 보존한다. [CelesTrak 이용 정책](https://celestrak.org/usage-policy.php)에 따라 어떤 비200 HTTP 응답도 `sauron/stations-halted.json.gz`를 남겨 후속 자동 조회를 중단한다. 원인 확인 후 운영자가 중단 기록을 검토해야 재개할 수 있다. 네트워크 오류와 자료 검증 오류도 수집 원장에 기록한다.

### `research/STRATEGY_CARD_CONTRACT.md`

- [ ] [research/STRATEGY_CARD_CONTRACT.md:30](../research/STRATEGY_CARD_CONTRACT.md#L30) — OLS는 [SciPy 공식 정의](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.linregress.html)를 따른다. 추가한 [Engle–Granger 검정](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.coint.html)은 상수 포함·maxlag5·AIC 설정이다. 귀무가설은 무공적분이며 두 계열의 I(1) 가정을 별도로 요구한다. p값만으로 거래 가능성을 확정하지 않고13쌍을 모두 표시한다. I(1) 사전검증·다중검정·수수료/차입비용과 분리된 전향 성과는 미완료다. 현재 구간 전체에서 추정한 β를 과거 진입에 이용한 백테스트가 아니다.

### `research/TOPIC_NEWS_CONTRACT.md`

- [ ] [research/TOPIC_NEWS_CONTRACT.md:17](../research/TOPIC_NEWS_CONTRACT.md#L17) — 조회 실패는 기존 성공 응답을 보존한다. 검색식이 변경된 뒤 실패해도 이전 검색 결과를 새 검색식의 결과로 표시하지 않는다. `data_query`가 원자료의 검색식을 유지한다. 데이터 미확보는‘—’, 정상 조회에서 관측한 기사0개는‘0건’이다. 과거 검색 자료는 이전 자료로 표시하며 최신 성공으로 간주하지 않는다.
- [ ] [research/TOPIC_NEWS_CONTRACT.md:19](../research/TOPIC_NEWS_CONTRACT.md#L19) — 배치 중단 뒤 요청하지 않은 항목은 `collection_aborted`로 기록한다. `checked_at`은 실제 요청 시각만 유지하고 보류 시각은 `deferred_at`, 원인은 `abort_reason`/`abort_http_status`로 분리한다. 정상 캐시의24시간 재사용 여부를 중단 여부보다 먼저 검사하므로 앞선 실패가 이미 완료된 검색을 무효화하지 않는다. 유예 후 재실행은 미완료 검색만 요청한다. 화면에는 보류/실제 요청 시각과 원인, 같은 검색식·기간의 제공처 응답 링크를 표시한다. HTTP 오류는 JSON 형태의 본문이라도 성공 처리하지 않으며, 정상 기사 JSON 안의 제한 관련 문구는 제한 안내로 분류하지 않는다.
- [ ] [research/TOPIC_NEWS_CONTRACT.md:31](../research/TOPIC_NEWS_CONTRACT.md#L31) — ## 검증과 미완 범위
- [ ] [research/TOPIC_NEWS_CONTRACT.md:33](../research/TOPIC_NEWS_CONTRACT.md#L33) — 중복 URL·잘못된 시각·HTTPS 외 링크,0건/미확보 구분, 캐시 재사용,429/시간초과 배치 중단·백오프, 실패한 검색식 변경의 이전 결과 분리를 검사한다. 실제 기존 RSS와의 날짜·제목·일치 문구·분류 결과 대조 및 브라우저의20개 상세/분류/검색/펼치기를 확인한다. 성공·빈 응답·상한 도달의 GDELT 테스트는 합성 fixture 검사이며 실서버의 성공 조회 증거가 아니다.

### `research/TRADE_CONTRACT.md`

- [ ] [research/TRADE_CONTRACT.md:3](../research/TRADE_CONTRACT.md#L3) — 국가 교역 하위 화면은 UN Comtrade의 **연간 상품 총수출(HS TOTAL, current USD)** 을 독립 수집해 표시한다. 기업 매출이나 실제 선박 항로를 표시하는 기능이 아니다. 밸류체인 유니버스의 기업별 공급·수출·물류 관계는 후속 구현 대상이다. 위성·지구관측은 [별도 계약](SAURON_CONTRACT.md)에 따라 연결했다.
- [ ] [research/TRADE_CONTRACT.md:34](../research/TRADE_CONTRACT.md#L34) — 굵기는 `1.2 + min(3.6, log10(USD/1e9+1)×1.5)`로 금액을 표시한다. 면적·거리·물동량 척도가 아니다. 화면의 큰순/작은순/이름 정렬은 표에 적용하고 지도 상위 필터는 금액 기준이다. 0은 관측0으로 표에 남기고 선은 그리지 않는다. 결측은 미확보로 남긴다. 미보고·거부·오류를0으로 표시하지 않는다. `isReported`와 `isAggregate`는 직접 보고/집계 플래그이며 `isReported=false`를 자동으로 추정치라고 해석하지 않는다.
- [ ] [research/TRADE_CONTRACT.md:42](../research/TRADE_CONTRACT.md#L42) — 최초 구축에서45지역 중42지역의2024년 수출이 확보됐고, 선택 지역 사이1840개 방향이 관측됐다. 러시아·UAE·베트남의 응답은 비어 있어 수출 방향을 미확보로 표시한다. 이 지역을 목적지로 하는 다른 보고국의 수출과 혼동하지 않는다. 실제 관측/확인 시각과 후속 변경은 화면 수집 원장에 표시한다.

## 운영 문서 증거

### `README.md`

- [README.md:33](../README.md#L33) — 밸류체인 유니버스는20개 그룹·53개 업종의151기업을 탐색합니다. 업종별 표·기업/도시 선택·151기업의105도시/행정 대표점, 공식 주소11기업과 시가총액, 공시 공급 관계 및 기업 생산·서비스·실제 물류 근거를 표시합니다. 소재국 교역은 별도 참고 스위치로 구분하며 근거 문서의 변경을30일마다 확인합니다. [기업 탐색 계약](research/CHAIN_UNIVERSE_CONTRACT.md)에 도시·통화·갱신 주기와 전체 공급/물류 근거의 남은 범위를 기록했습니다.
- [README.md:37](../README.md#L37) — 재무 기본 수집은 부모 빈티지의 구성종목을 합쳐 종목별7일 캐시와 실패 유예를 적용합니다. [재무 유니버스 계약](research/FUNDAMENTAL_UNIVERSE_CONTRACT.md)에 대상 출처, 실제 확보와 미확보 구분, 중단·재개 방식을 기록했습니다.
- [README.md:39](../README.md#L39) — 지구본의 국가 교역은 UN Comtrade45개 통계지역의 연간 총수출을 지도와 원장에 연결합니다. 수출 방향·금액별 곡선·국가 검색·정확한 USD와 분모를 표시하고 PC에서30일마다 재확인합니다. [교역 계약](research/TRADE_CONTRACT.md)에 통계지역·결측·참조연도와 기업별 밸류체인의 남은 범위를 기록했습니다.
- [README.md:92](../README.md#L92) — PDF는 제목·저자·페이지별 본문을 읽고 원문 페이지를 근거에 인용할 수 있습니다. 본문 검색·TXT 내보내기·첨부 포함 백업과 기존 기록 보존을 연결했습니다. [PDF 처리 범위와 검증](research/PDF_EXTRACTION.md)에 파서·OCR 비교와 페이지 재사용, 처리 한도 및 요약의 남은 범위를 표시합니다.
- [README.md:100](../README.md#L100) — IW는15개월 복기와14주 연대기·보존 차트를 제공합니다. ASK는3기간 추세·사업 근거10테마·RS16종목·21자산·9위험관측·4차트·20모듈 요약을 정기 재생성합니다. [IW 날짜/보존 계약](research/IW_REVIEW_CONTRACT.md)과 [ASK 계산/출처 계약](research/DIGEST_CONTRACT.md)을 참조하세요.
- [README.md:126](../README.md#L126) — 기업분석 리서치는 공식 근거의 URL 중복 제거·문서 카드·출처/연결/검색 필터와 기업 상세 이동을 제공합니다. 이 브라우저의 리서치 자료실 기록·첨부도 읽기 전용으로 불러옵니다. [리서치 연결 계약](research/DRAGON_RESEARCH_CONTRACT.md)에 날짜·개인 자료·원본 대비 남은 범위를 기록했습니다.
- [README.md:128](../README.md#L128) — 기업분석 지금 주목·트리거는 주도주/발굴 동시관측,모듈별 위험근거,지정학 제목,6테마,3개월 자산추세와 촬영일 원장을 연결합니다. 미확보 신호와 원본 전체점수의 차이는 [신호 계약](research/DRAGON_SIGNALS_CONTRACT.md)에 명시했습니다.
- [README.md:146](../README.md#L146) — 기업 뉴스의 영문 제목은 PC의 고정 FinBERT로 분류하고 같은 제목은 재사용한다. 23개 피드의 기사별 확률·피드별 평균·신호와 오류/캐시 상태를 제공한다. [제목 톤 계약](research/NEWS_TONE_CONTRACT.md)에 모델 설정·설치·집계와 기업별 문맥 감성의 남은 범위를 명시했다.
- [README.md:148](../README.md#L148) — 기업 뉴스는 40피드이며 기업 상세 707개와 연결된다. 신규 관찰 기업의 공식 종목 식별과 가격·제목 톤을 제공하고, 지수 편입·업종·재무 미확보를 구분한다. 민감도와 원장 상관은 누락 가격을 보존하여 일 수익률을 계산한다. [수집·계산 범위](research/COMPANY_NEWS_CONTRACT.md).
- [README.md:150](../README.md#L150) — [기업 재무·일정 보완](research/COMPANY_FINANCIAL_CONTRACT.md): 뉴스 대상40기업의 실제 재무와 미국 상장37기업의 제공처 일정 자료를 캐시 우선으로 갱신하며, 기업 상세와 연간·분기3지표 차트에 연결한다. 한국 예정 실적과 전체707기업 자료는 남은 범위다.
- [README.md:152](../README.md#L152) — [테마·국가·정책 뉴스](research/TOPIC_NEWS_CONTRACT.md)는20분류의 주제 검색과 기존 RSS 제목 일치를 구분한다. 현재GDELT API는429/연결시간초과로 검색자료 미확보이며 기존기사의 실제 일치만 제공한다.

## 생성·파생 문서 증거

### `research/CHART_INTERACTION_GUIDE.md`

- [research/CHART_INTERACTION_GUIDE.md:23](../research/CHART_INTERACTION_GUIDE.md#L23) — - 성장주/표면/국면 및 Overview/공식 관계망의 원근은 화면 투영이다. 원래 값과 색/크기의 의미는 변경하지 않는다. 궤적의 표시 범위는 전체 관측과 0을 포함하도록 자동 조정한다. 성장주 크기 미확보는 기존 동일 크기 규칙을 따른다. 표면의 색은 낮은 청색에서 높은 보라색으로 정리했다.
- [research/CHART_INTERACTION_GUIDE.md:48](../research/CHART_INTERACTION_GUIDE.md#L48) — ### 공간 무대 후속
- [research/CHART_INTERACTION_GUIDE.md:55](../research/CHART_INTERACTION_GUIDE.md#L55) — 사용자의 후속 요청에 따라 Overview와 국면 3D 궤적의 고정 z 표시 절단을 없앴다. 전체 유효 관측과 0을 포함하는 축별 범위에 여유를 더한다. 점, 숫자 눈금, 0 평면과 사분면은 같은 좌표 변환을 사용한다. 원래 z·원단위·시계열은 변경하지 않는다. 축마다 범위가 다르므로 화면의 각도·거리를 축 사이의 동일한 z 거리로 읽지 않는다. 고정 비교 범위를 쓰는 레이더의 계약은 유지한다.
- [research/CHART_INTERACTION_GUIDE.md:67](../research/CHART_INTERACTION_GUIDE.md#L67) — ## 흰색·무광 후속 디자인

### `research/CHART_PARITY.md`

- [research/CHART_PARITY.md:7](../research/CHART_PARITY.md#L7) — | 시장 종합 | 거시 국면6축·시장 쏠림5축·36월3D·4시점 적층·주도주 | 6/5축 원단위와 z·36시점 궤적/회전·4층 레이더·시총50표본/주도주10·현황 | 원본 z 창/극단치 설정·세계 전체 시총50·역사 발표 빈티지 동등성 미확보 |
- [research/CHART_PARITY.md:9](../research/CHART_PARITY.md#L9) — | 통합예측 | 지수·종목·거시 예측, 전문가 가중치·신호·시계열 | 지수 / 매크로 / 종목 / 추가 지수 / 방법론 | 지수 밸류배수×이익추정 대신 과거 레벨 중앙값 앵커를 사용합니다. SEC filed 정렬 재무·한국 외국인 역사·일부 확장 거시 입력은 미연결입니다. / 원본과 다른 팀 하이퍼파라미터·가용 입력을 공개합니다. 현재 수정 거시에 시차를 준 결과이며 PIT 실시간 OOS가 아닙니다. / 완료월 추론입니다. 부분월 실시간 추론·웹 임의 종목 학습 서버는 아직 연결하지 않았습니다. / 변수 영향력은 고정 게이트 occlusion이며 SHAP/인과 효과가 아닙니다. 모델 선택·조정 규칙을 정한 기간과 분리한 전향 검증은 후속 대상입니다. / 방향전략은 월말 가정·편도5bp·rf=0이며 실제 주문·차입·선물 롤 비용을 복원하지 않습니다. CPI와 금리 수준에는 투자 수익률을 표시하지 않습니다. |
- [research/CHART_PARITY.md:10](../research/CHART_PARITY.md#L10) — | 기업분석 | 11개 하위 화면, 관계·시설·관측·원장 | 관계 지도 / 지금 주목 / 위성사진 / 기업 상세 / 시나리오 / 결정 원장 / 트리거·촉매 / 리서치 / 데이터 소스 / 현황판 / 방법론 / 공식 분류 / 시장 Beta 민감도 | 사업·공급·경쟁 관계는 출처 확인한 표본이며 전체 공급망·거래금액·고객별 매출 비중이 아닙니다. 원본의 전체255객체/581관계를 독립 검증한 범위는 아닙니다. / 단계 전파와 프리셋 충격은 가정입니다. 상관은 인과 검증이 아니고 기준일·유니버스·선택 편향의 영향을 받습니다. 거시 가정 입력 중AI CapEx/전력 수요는 실제 관측 수치가 없습니다. / 일부 임상/13F 촉매·구루 원문 검증·팀 공용 DB는 남아 있습니다. 개인 확신도를 실제 성공확률이나 자동 주문으로 바꾸지 않습니다. / 위성 배경은 NASA Blue Marble 2004년 합성 영상입니다. 원본 Esri 고해상도 영상·지명 레이어는 이용권한 확인이 남아 있습니다. 시설 관측은 별도 촬영일의 Sentinel 자료이며 건설 진척·가동률을 추정하지 않습니다. / 리서치 카탈로그는 팀의 공개 검토 자료와 이 브라우저의 리서치 자료실 기록을 연결합니다. 원본의 비공개 리포트·투자 기대수익과 전체 167편을 복제하지 않으며, 자동 투자뷰 추론·팀 공유 저장소는 미연결입니다. / 주제 뉴스: GDELT 검색 20개 주제 미확보. 기존 RSS 제목 일치는 별도 표본이며 검색 결과 확보로 세지 않습니다. / 지금 주목·트리거는 주도주/발굴·공식 근거·촬영일·문서 관심도·기업 RSS 표본을 연결합니다. 전체 뉴스량/기업별 감성·13F 최신·정량 투자뷰·원본 live는 미확보이며 완전한 합성점수는 미산출입니다. / 임상 등록부는 명시된3검색범위의 모집/3상 건수와 최근5기록만 제공합니다. 원본 검색식은 미공개이며 모든 계열사·약물과 연구별 전체 변화 이력은 미확보입니다. / 13F는6개 보고 법인 공시와 확인된 CUSIP의 기업 상세를 연결합니다. 최신 전체 조회·과거 연속 변화·미대응 식별자와 구루 뉴스/관심분야 자동집계는 미완이며 신호점수에 합산하지 않습니다. |
- [research/CHART_PARITY.md:12](../research/CHART_PARITY.md#L12) — | 글로벌 공급망 | 밸류체인53세부업종·기업/도시·3종교역선·위성·지구관측 | 국가 교역 / 기업 국가 탐색 / 밸류체인 유니버스 / 위성·지구관측 | UN 자료가 없는 국가·통계지역/방향은 미확보로 표시하며 거울 수입이나 추정값으로 채우지 않습니다. / 위성·지구관측의 Google 실사3D는 별도 키가 필요합니다. Wikipedia 지명은 문서 대표 좌표이며 주소 검색과 다릅니다. 지진은 PC 수집 시점의 관측이고 위성 위치는 궤도 모델 계산입니다. / 밸류체인 유니버스의53개 업종·151기업 탐색에 공식 주소와 기업별 사업·생산·운송 근거를 추가했습니다. 지도 점은 도시·행정구역 대표 좌표이며 본사 건물이나 선박 항적이 아닙니다. 전체 기업의 공식 본사·공급·물류·경쟁우위 근거는 계속 수집하며 소재국 총수출은 별도 국가 맥락입니다. |
- [research/CHART_PARITY.md:13](../research/CHART_PARITY.md#L13) — | 리서치 자료실 | 3유형·5단 상세·제목 관계지도·키워드 구체·등록/첨부 | 리서치 아카이브 | PDF 텍스트 추출은 문서당300쪽·20만자 범위입니다. OCR은 회당30쪽·최대3분이며 완료 페이지는 재사용합니다. 숫자·표·복잡한 배치는 원문 대조가 필요하고 LLM 요약·번역은 추가 구현 대상입니다. / 이 브라우저의 IndexedDB에 저장합니다. 팀 공용 DB·서버 인증/공개 배포·서버 조회 통계는 추가 구현 대상입니다. |
- [research/CHART_PARITY.md:18](../research/CHART_PARITY.md#L18) — | 투자전략 | 전략별 후보·연간순이익·44점가격/스프레드·이벤트 결과 | 턴어라운드 / 내부자 매수 / PEAD / 스탯아브 페어 / 실적 모멘텀 | SEC 연속 자동수집은 PC HTTP 접근 상태에 따라 제한됩니다. 현재 원문 대조 표본과 미확인 후보를 구분하며 전체 미국 시장의 모든 내부자 거래를 의미하지 않습니다. Form4/A 정정 대조·13F·전략별 비용 후 OOS는 후속 대상입니다. / 전략 카드: 턴어라운드 사전표본·가격 절단·점수의 정확한 원본 임계치는 미공개로 팀 기준을 표시합니다. 재무 표본 확대·발표 당시 빈티지, 공적분의 전체 가정/다중검정과 비용 후 OOS는 남아 있습니다. / PEAD 카드: 원본 사전표본·기간/임계치의 비공개 설정, 제공처 발표시각의 발행사 전수 대조와 발표 당시 컨센서스 빈티지·비용 후 성과는 남아 있습니다. |
- [research/CHART_PARITY.md:21](../research/CHART_PARITY.md#L21) — | 자산배분 | 21자산4KPI·6군신호표·열지도/추세막대·실제지수·37자산 스캐너·배분/성과 | 자산 모니터 / 패턴 스캐너 / 자산배분 | 원본의 모든 하이퍼파라미터·74개 입력명·그룹별 상한은 공개되지 않아 팀 설정을 명시했습니다. 원본 수치와 동일하다는 주장이 아닙니다. / OECD 미국·한국·일본·중국 선행지수는 공식 API의 진폭 조정 지수(장기 평균100)입니다. OECD 전체 집계는 미확보입니다. Boruta 미확정/순위 대체와 Markov 추정 불가를 진단에 표시합니다. / 과거 발표·개정 빈티지를 복원한 PIT 성과가 아니며 사후 설계 OOS입니다. 두 모델의 방향 정합은 측정된 신뢰도·성공확률 증가를 의미하지 않습니다. / 자산 모니터: 원본의 50/200MA 신호 세부 조건은 미공개이므로 팀 정배열/역배열을 명시했습니다. 원본 장중/시장별 기준시각과 완료 종가 사이 차이가 있으며 과거 수치의 완전 동일성을 주장하지 않습니다. |
- [research/CHART_PARITY.md:27](../research/CHART_PARITY.md#L27) — | 주간 기록 | 월말15복기·주간14연대기·국면/ML2그림·판단 원장 | 월말 복기 / 주간 연대기 / 이번 주의 그림 / 주간 판단 원장 | 과거 재구성은 현재 수정 거시와 현재 팀 모형의 OOS 재생이며 과거 실제 발행본/PIT 예측이 아닙니다. 원본 본문·합계·표 사이의 불일치는 복제하지 않고 한 계산 결과에서 생성합니다. / 경제/시장/위험의 가용 입력·임계값은 공개한 팀 규칙입니다. 원본의 미공개 복합 가중치와 수치 동등성을 주장하지 않습니다. / 원본 작성자의 주간 논평·과거 개인 기록, 팀 공용 DB·LLM 자동 글쓰기는 미연결입니다. 사용자 판단과 첨부는 브라우저 로컬입니다. |

### `research/DATA_DEFINITIONS.md`

- [research/DATA_DEFINITIONS.md:54](../research/DATA_DEFINITIONS.md#L54) — - ML: Lasso·ElasticNet·BayesianRidge·KNN·RandomForest·ExtraTrees·XGBoost·LightGBM·MLP·LSTM·Transformer와 평균/중앙값 앙상블. 142후보에서 과거 학습창으로만 Shadow12회 상위22+가용 강제변수를 선택한다. 일반모형6개월·시퀀스모형12개월 재적합, 최소96개월 라벨, 과거 만기 종료120개 이내로 당시 모델을 선택한다. 1M/3M 만기를 기다리며 현재 수정 거시에2개월 시차를 둔다. 68/90%는 과거 OOS 잔차 분위, 확률은 정규 CDF이며 PIT 실시간 성과가 아니다. 전체 설정·검증·미확보 입력은 [ML 계약](ML_MODEL_CONTRACT.md).
- [research/DATA_DEFINITIONS.md:125](../research/DATA_DEFINITIONS.md#L125) — - OECD CLI: [공식 정의](https://www.oecd.org/en/data/indicators/composite-leading-indicator-cli.html)와 SDMX `OECD.SDD.STES,DSD_STES@DF_CLI`의 USA/KOR/JPN/CHN, 월간LI·진폭조정AA·IX·방법H. 장기 평균100이며 입력 수준은100을 뺀다. 2000-01~2026-08 각320개월을 확보했다. OECD 전체 집계는 미확보다. 현재 수정 빈티지에 시차를 주었을 뿐 과거 발표 당시 PIT 빈티지를 복원하지 않았다.
- [research/DATA_DEFINITIONS.md:159](../research/DATA_DEFINITIONS.md#L159) — 종가만 사용하는 수익률·배분 계산은 별도 보고된 종가를 그대로 사용한다. OHLC 불일치만으로 보고 종가 자체가 잘못됐다고 확정할 수 없으므로 종가 수익률과 캔들·기술 지표의 가용일을 구분한다. `price_quality.vendor_ohlc_exclusions`와 분석 화면의 원장에 종목·날짜·사유를 표시한다. 국내는 기존 KRX 공식 보정 경로를 유지하며, 지수·FX·선물 결제가격·암호자산을 이 주식 원장에 섞지 않는다. 제공처가 후속 빈티지에서 OHLC를 정정하면 유효성 검사 후 캔들에 복원한다.

### `research/DESIGN_SYSTEM.md`

- [research/DESIGN_SYSTEM.md:43](../research/DESIGN_SYSTEM.md#L43) — ## 직접 조작과 객체 재질 (후속 사용자 요구)
- [research/DESIGN_SYSTEM.md:62](../research/DESIGN_SYSTEM.md#L62) — 사용자의 후속 요청에 따라 Overview와 국면 3D 궤적의 고정 z 표시 절단을 없앴다. 전체 유효 관측과 0을 포함하는 축별 범위에 여유를 더한다. 점, 숫자 눈금, 0 평면과 사분면은 같은 좌표 변환을 사용한다. 원래 z·원단위·시계열은 변경하지 않는다. 축마다 범위가 다르므로 화면의 각도·거리를 축 사이의 동일한 z 거리로 읽지 않는다. 고정 비교 범위를 쓰는 레이더의 계약은 유지한다.

### `research/IMPLEMENTATION_STATUS.md`

- [research/IMPLEMENTATION_STATUS.md:9](../research/IMPLEMENTATION_STATUS.md#L9) — | 탭 | 상태 | 연결 범위 | 남은 범위 |
- [research/IMPLEMENTATION_STATUS.md:11](../research/IMPLEMENTATION_STATUS.md#L11) — | [시장 종합](modules/overview.md) | 계산·화면 연결 | 6/5축 원단위와 z·36시점 궤적/회전·4층 레이더·시총50표본/주도주10·현황 | 원본 z 창/극단치 설정·세계 전체 시총50·역사 발표 빈티지 동등성 미확보 |
- [research/IMPLEMENTATION_STATUS.md:13](../research/IMPLEMENTATION_STATUS.md#L13) — | [통합예측](modules/maximus.md) | 부분 구현 | 지수 / 매크로 / 종목 / 추가 지수 / 방법론 | 지수 밸류배수×이익추정 대신 과거 레벨 중앙값 앵커를 사용합니다. SEC filed 정렬 재무·한국 외국인 역사·일부 확장 거시 입력은 미연결입니다. / 원본과 다른 팀 하이퍼파라미터·가용 입력을 공개합니다. 현재 수정 거시에 시차를 준 결과이며 PIT 실시간 OOS가 아닙니다. / 완료월 추론입니다. 부분월 실시간 추론·웹 임의 종목 학습 서버는 아직 연결하지 않았습니다. / 변수 영향력은 고정 게이트 occlusion이며 SHAP/인과 효과가 아닙니다. 모델 선택·조정 규칙을 정한 기간과 분리한 전향 검증은 후속 대상입니다. / 방향전략은 월말 가정·편도5bp·rf=0이며 실제 주문·차입·선물 롤 비용을 복원하지 않습니다. CPI와 금리 수준에는 투자 수익률을 표시하지 않습니다. |
- [research/IMPLEMENTATION_STATUS.md:14](../research/IMPLEMENTATION_STATUS.md#L14) — | [기업분석](modules/dragonglass.md) | 부분 구현 | 관계 지도 / 지금 주목 / 위성사진 / 기업 상세 / 시나리오 / 결정 원장 / 트리거·촉매 / 리서치 / 데이터 소스 / 현황판 / 방법론 / 공식 분류 / 시장 Beta 민감도 | 사업·공급·경쟁 관계는 출처 확인한 표본이며 전체 공급망·거래금액·고객별 매출 비중이 아닙니다. 원본의 전체255객체/581관계를 독립 검증한 범위는 아닙니다. / 단계 전파와 프리셋 충격은 가정입니다. 상관은 인과 검증이 아니고 기준일·유니버스·선택 편향의 영향을 받습니다. 거시 가정 입력 중AI CapEx/전력 수요는 실제 관측 수치가 없습니다. / 일부 임상/13F 촉매·구루 원문 검증·팀 공용 DB는 남아 있습니다. 개인 확신도를 실제 성공확률이나 자동 주문으로 바꾸지 않습니다. / 위성 배경은 NASA Blue Marble 2004년 합성 영상입니다. 원본 Esri 고해상도 영상·지명 레이어는 이용권한 확인이 남아 있습니다. 시설 관측은 별도 촬영일의 Sentinel 자료이며 건설 진척·가동률을 추정하지 않습니다. / 리서치 카탈로그는 팀의 공개 검토 자료와 이 브라우저의 리서치 자료실 기록을 연결합니다. 원본의 비공개 리포트·투자 기대수익과 전체 167편을 복제하지 않으며, 자동 투자뷰 추론·팀 공유 저장소는 미연결입니다. / 주제 뉴스: GDELT 검색 20개 주제 미확보. 기존 RSS 제목 일치는 별도 표본이며 검색 결과 확보로 세지 않습니다. / 지금 주목·트리거는 주도주/발굴·공식 근거·촬영일·문서 관심도·기업 RSS 표본을 연결합니다. 전체 뉴스량/기업별 감성·13F 최신·정량 투자뷰·원본 live는 미확보이며 완전한 합성점수는 미산출입니다. / 임상 등록부는 명시된3검색범위의 모집/3상 건수와 최근5기록만 제공합니다. 원본 검색식은 미공개이며 모든 계열사·약물과 연구별 전체 변화 이력은 미확보입니다. / 13F는6개 보고 법인 공시와 확인된 CUSIP의 기업 상세를 연결합니다. 최신 전체 조회·과거 연속 변화·미대응 식별자와 구루 뉴스/관심분야 자동집계는 미완이며 신호점수에 합산하지 않습니다. |
- [research/IMPLEMENTATION_STATUS.md:16](../research/IMPLEMENTATION_STATUS.md#L16) — | [글로벌 공급망](modules/globe.md) | 부분 구현 | 국가 교역 / 기업 국가 탐색 / 밸류체인 유니버스 / 위성·지구관측 | UN 자료가 없는 국가·통계지역/방향은 미확보로 표시하며 거울 수입이나 추정값으로 채우지 않습니다. / 위성·지구관측의 Google 실사3D는 별도 키가 필요합니다. Wikipedia 지명은 문서 대표 좌표이며 주소 검색과 다릅니다. 지진은 PC 수집 시점의 관측이고 위성 위치는 궤도 모델 계산입니다. / 밸류체인 유니버스의53개 업종·151기업 탐색에 공식 주소와 기업별 사업·생산·운송 근거를 추가했습니다. 지도 점은 도시·행정구역 대표 좌표이며 본사 건물이나 선박 항적이 아닙니다. 전체 기업의 공식 본사·공급·물류·경쟁우위 근거는 계속 수집하며 소재국 총수출은 별도 국가 맥락입니다. |
- [research/IMPLEMENTATION_STATUS.md:17](../research/IMPLEMENTATION_STATUS.md#L17) — | [리서치 자료실](modules/principium.md) | 부분 구현 | 리서치 아카이브 | PDF 텍스트 추출은 문서당300쪽·20만자 범위입니다. OCR은 회당30쪽·최대3분이며 완료 페이지는 재사용합니다. 숫자·표·복잡한 배치는 원문 대조가 필요하고 LLM 요약·번역은 추가 구현 대상입니다. / 이 브라우저의 IndexedDB에 저장합니다. 팀 공용 DB·서버 인증/공개 배포·서버 조회 통계는 추가 구현 대상입니다. |
- [research/IMPLEMENTATION_STATUS.md:22](../research/IMPLEMENTATION_STATUS.md#L22) — | [투자전략](modules/strategies.md) | 부분 구현 | 턴어라운드 / 내부자 매수 / PEAD / 스탯아브 페어 / 실적 모멘텀 | SEC 연속 자동수집은 PC HTTP 접근 상태에 따라 제한됩니다. 현재 원문 대조 표본과 미확인 후보를 구분하며 전체 미국 시장의 모든 내부자 거래를 의미하지 않습니다. Form4/A 정정 대조·13F·전략별 비용 후 OOS는 후속 대상입니다. / 전략 카드: 턴어라운드 사전표본·가격 절단·점수의 정확한 원본 임계치는 미공개로 팀 기준을 표시합니다. 재무 표본 확대·발표 당시 빈티지, 공적분의 전체 가정/다중검정과 비용 후 OOS는 남아 있습니다. / PEAD 카드: 원본 사전표본·기간/임계치의 비공개 설정, 제공처 발표시각의 발행사 전수 대조와 발표 당시 컨센서스 빈티지·비용 후 성과는 남아 있습니다. |
- [research/IMPLEMENTATION_STATUS.md:25](../research/IMPLEMENTATION_STATUS.md#L25) — | [자산배분](modules/multiasset.md) | 부분 구현 | 자산 모니터 / 패턴 스캐너 / 자산배분 | 원본의 모든 하이퍼파라미터·74개 입력명·그룹별 상한은 공개되지 않아 팀 설정을 명시했습니다. 원본 수치와 동일하다는 주장이 아닙니다. / OECD 미국·한국·일본·중국 선행지수는 공식 API의 진폭 조정 지수(장기 평균100)입니다. OECD 전체 집계는 미확보입니다. Boruta 미확정/순위 대체와 Markov 추정 불가를 진단에 표시합니다. / 과거 발표·개정 빈티지를 복원한 PIT 성과가 아니며 사후 설계 OOS입니다. 두 모델의 방향 정합은 측정된 신뢰도·성공확률 증가를 의미하지 않습니다. / 자산 모니터: 원본의 50/200MA 신호 세부 조건은 미공개이므로 팀 정배열/역배열을 명시했습니다. 원본 장중/시장별 기준시각과 완료 종가 사이 차이가 있으며 과거 수치의 완전 동일성을 주장하지 않습니다. |
- [research/IMPLEMENTATION_STATUS.md:31](../research/IMPLEMENTATION_STATUS.md#L31) — | [주간 기록](modules/iw.md) | 부분 구현 | 월말 복기 / 주간 연대기 / 이번 주의 그림 / 주간 판단 원장 | 과거 재구성은 현재 수정 거시와 현재 팀 모형의 OOS 재생이며 과거 실제 발행본/PIT 예측이 아닙니다. 원본 본문·합계·표 사이의 불일치는 복제하지 않고 한 계산 결과에서 생성합니다. / 경제/시장/위험의 가용 입력·임계값은 공개한 팀 규칙입니다. 원본의 미공개 복합 가중치와 수치 동등성을 주장하지 않습니다. / 원본 작성자의 주간 논평·과거 개인 기록, 팀 공용 DB·LLM 자동 글쓰기는 미연결입니다. 사용자 판단과 첨부는 브라우저 로컬입니다. |

### `research/LOCAL_RESEARCH.md`

- [research/LOCAL_RESEARCH.md:30](../research/LOCAL_RESEARCH.md#L30) — ## 검증과 남은 범위
- [research/LOCAL_RESEARCH.md:34](../research/LOCAL_RESEARCH.md#L34) — 팀 공용 DB/로그인, 서버의 공개 게시/방문 통계, LLM 요약, ASK 자동 AI 질의 서버는 추가 구현 대상이다. PDF 파서·선택 OCR·페이지 재사용은 [PDF 처리 계약](PDF_EXTRACTION.md)을 따른다. 기간별 추세·테마·모듈별 집계는 [ASK 계산 계약](DIGEST_CONTRACT.md)을 따른다. 새 저장 기능을 이들 전체 기능의 완료로 세지 않는다. IW의15개월 복기·14주 연대기·두 그림과 날짜 보존은 [별도 계산 계약](IW_REVIEW_CONTRACT.md)을 따른다.

### `research/modules/aragorn.md`

- [research/modules/aragorn.md:11](../research/modules/aragorn.md#L11) — - 남은 범위: 원본의 매크로 인과 그래프 생성기가 없어 소속 관계를 인과관계로 표시하지 않습니다.

### `research/modules/ask_digest.md`

- [research/modules/ask_digest.md:11](../research/modules/ask_digest.md#L11) — - 남은 범위: 테마는 공식 사업 설명으로 구성한1~2기업 표본이며 전체 테마 수익률·사업 매출 순도·원본 heat 모델이 아닙니다. 현재 목록으로 과거 수익을 관찰하며 역사 편입 시점 성과가 아닙니다. / 구루 보유·전체 기업 뉴스 관심량·원본 LLM 해석은 미연결입니다. 표시한 RSS 제목 표본의 명시적 종목명 일치만 집계합니다. / 정적 사이트에는 자동 AI 질의 서버가 없습니다. 개인 질문·근거·첨부는 브라우저 로컬 기록에 저장합니다.

### `research/modules/discovery.md`

- [research/modules/discovery.md:11](../research/modules/discovery.md#L11) — - 남은 범위: 원본의 내부 정규화·버킷 임계치는 미공개여서 동일 점수 재현은 미검증입니다. 팀 산식은 설명서와 코드에 명시합니다. / 재무·애널리스트는 현재 확보된 기업만 연결됩니다. 매수 의견 비율의 과거 변화·실제 기관 수급은 아직 없으며 추정하지 않습니다. / 한국 범위는 현재 공식 대형주입니다. 원본의 KOSDAQ 포함 시가총액 상위 범위와 다릅니다.

### `research/modules/dragonglass.md`

- [research/modules/dragonglass.md:11](../research/modules/dragonglass.md#L11) — - 남은 범위: 사업·공급·경쟁 관계는 출처 확인한 표본이며 전체 공급망·거래금액·고객별 매출 비중이 아닙니다. 원본의 전체255객체/581관계를 독립 검증한 범위는 아닙니다. / 단계 전파와 프리셋 충격은 가정입니다. 상관은 인과 검증이 아니고 기준일·유니버스·선택 편향의 영향을 받습니다. 거시 가정 입력 중AI CapEx/전력 수요는 실제 관측 수치가 없습니다. / 일부 임상/13F 촉매·구루 원문 검증·팀 공용 DB는 남아 있습니다. 개인 확신도를 실제 성공확률이나 자동 주문으로 바꾸지 않습니다. / 위성 배경은 NASA Blue Marble 2004년 합성 영상입니다. 원본 Esri 고해상도 영상·지명 레이어는 이용권한 확인이 남아 있습니다. 시설 관측은 별도 촬영일의 Sentinel 자료이며 건설 진척·가동률을 추정하지 않습니다. / 리서치 카탈로그는 팀의 공개 검토 자료와 이 브라우저의 리서치 자료실 기록을 연결합니다. 원본의 비공개 리포트·투자 기대수익과 전체 167편을 복제하지 않으며, 자동 투자뷰 추론·팀 공유 저장소는 미연결입니다. / 주제 뉴스: GDELT 검색 20개 주제 미확보. 기존 RSS 제목 일치는 별도 표본이며 검색 결과 확보로 세지 않습니다. / 지금 주목·트리거는 주도주/발굴·공식 근거·촬영일·문서 관심도·기업 RSS 표본을 연결합니다. 전체 뉴스량/기업별 감성·13F 최신·정량 투자뷰·원본 live는 미확보이며 완전한 합성점수는 미산출입니다. / 임상 등록부는 명시된3검색범위의 모집/3상 건수와 최근5기록만 제공합니다. 원본 검색식은 미공개이며 모든 계열사·약물과 연구별 전체 변화 이력은 미확보입니다. / 13F는6개 보고 법인 공시와 확인된 CUSIP의 기업 상세를 연결합니다. 최신 전체 조회·과거 연속 변화·미대응 식별자와 구루 뉴스/관심분야 자동집계는 미완이며 신호점수에 합산하지 않습니다.

### `research/modules/dynamics.md`

- [research/modules/dynamics.md:11](../research/modules/dynamics.md#L11) — - 남은 범위: 원본 확장창 최소표본·0분산 세부 처리/가격정정 빈티지 동등성은 미검증입니다. 팀 설정과 실제 가용 이력을 표시합니다. / 비용은 사용자가 선택하는 가정이며 실제 스프레드·차입조건·시장충격·현금이자·세금과 과거 실시간 데이터 빈티지를 재현하지 않습니다. / 결측 이후 연속 유효 구간만 성과를 비교합니다. 일부 종목은 전체22년 이력이 없으며 과거 월말 신호가 당시 발표된 투자판단이라는 보증은 없습니다.

### `research/modules/earnings.md`

- [research/modules/earnings.md:11](../research/modules/earnings.md#L11) — - 남은 범위: 해외 직접 영업이익·순이익 컨센서스, 과거 발표 당시 빈티지, 한국 증권사별 원문 보고서 검증은 남아 있습니다. 글로벌 Top20은 현재 수집 기업 표본의 최근 실제 NI 순위이며 세계 전체 순위가 아닙니다.

### `research/modules/etfmon.md`

- [research/modules/etfmon.md:11](../research/modules/etfmon.md#L11) — - 남은 범위: 주기는 최근 배당락일 간격에서 계산한 관측 분류입니다. 세금·환전비용·향후 지급일·원금 반환 비중은 별도 원천이 필요합니다.

### `research/modules/geoecon.md`

- [research/modules/geoecon.md:11](../research/modules/geoecon.md#L11) — - 남은 범위: 제목 표현 분류는 기사 전체의 LLM 감성·사실 검증이 아닙니다. 채널 화살표는 경제적 경로 가정, 노출0~7은 현재 기사 표본 비중×7이며 피해 크기·수익률·확률이 아닙니다. 보도 이후 가격은 인과 효과가 아닙니다. / RSS 보존 이력이 짧고 제공처별 발행주기/수집 실패가 달라 전체 뉴스량이나 완전한 일별 과거 표본을 확보하지 않았습니다. 위성 배경·시설 관측과 원본 비공개 감성 가중치는 미연결입니다.

### `research/modules/glance.md`

- [research/modules/glance.md:9](../research/modules/glance.md#L9) — - 남은 범위: 원본 Mac 서버 운영 대신 승인된 PC 실행 일정 사용

### `research/modules/globe.md`

- [research/modules/globe.md:11](../research/modules/globe.md#L11) — - 남은 범위: UN 자료가 없는 국가·통계지역/방향은 미확보로 표시하며 거울 수입이나 추정값으로 채우지 않습니다. / 위성·지구관측의 Google 실사3D는 별도 키가 필요합니다. Wikipedia 지명은 문서 대표 좌표이며 주소 검색과 다릅니다. 지진은 PC 수집 시점의 관측이고 위성 위치는 궤도 모델 계산입니다. / 밸류체인 유니버스의53개 업종·151기업 탐색에 공식 주소와 기업별 사업·생산·운송 근거를 추가했습니다. 지도 점은 도시·행정구역 대표 좌표이며 본사 건물이나 선박 항적이 아닙니다. 전체 기업의 공식 본사·공급·물류·경쟁우위 근거는 계속 수집하며 소재국 총수출은 별도 국가 맥락입니다.

### `research/modules/growth.md`

- [research/modules/growth.md:11](../research/modules/growth.md#L11) — - 남은 범위: 글로벌 100종목의 FY1/FY2 영업이익 컨센서스가 없어 해외 3D 점은 제외했습니다. 해외 EPS 성장률은 별도 표로 제공합니다.

### `research/modules/iw.md`

- [research/modules/iw.md:6](../research/modules/iw.md#L6) — **부분 구현** · 가격 기준 2026-09-10. 월말 복기 / 주간 연대기 / 이번 주의 그림 / 주간 판단 원장.
- [research/modules/iw.md:10](../research/modules/iw.md#L10) — - 계산/자료 계약: 월말 복기15건은 팀 ML 원점별 예측·실현을 같은 원장에서 집계합니다. 주간 연대기14건은 지수·YTD·국면·전망을 묶습니다. 최초 과거 주간은 현재 빈티지로 재구성했다고 표시하며 이후 지나간 주간의 기록과 그림은 보존합니다.
- [research/modules/iw.md:11](../research/modules/iw.md#L11) — - 남은 범위: 과거 재구성은 현재 수정 거시와 현재 팀 모형의 OOS 재생이며 과거 실제 발행본/PIT 예측이 아닙니다. 원본 본문·합계·표 사이의 불일치는 복제하지 않고 한 계산 결과에서 생성합니다. / 경제/시장/위험의 가용 입력·임계값은 공개한 팀 규칙입니다. 원본의 미공개 복합 가중치와 수치 동등성을 주장하지 않습니다. / 원본 작성자의 주간 논평·과거 개인 기록, 팀 공용 DB·LLM 자동 글쓰기는 미연결입니다. 사용자 판단과 첨부는 브라우저 로컬입니다.
- [research/modules/iw.md:13](../research/modules/iw.md#L13) — 연결된 하위 그룹: 월말 복기, 주간 연대기, 이번 주의 그림, 주간 판단 원장.
- [research/modules/iw.md:20](../research/modules/iw.md#L20) — 주간 코멘트 연대기와 국면·ML 그림을 묶은 기록 화면.
- [research/modules/iw.md:30](../research/modules/iw.md#L30) — - 작성일·기준일·후속 수정 구분

### `research/modules/maximus.md`

- [research/modules/maximus.md:11](../research/modules/maximus.md#L11) — - 남은 범위: 지수 밸류배수×이익추정 대신 과거 레벨 중앙값 앵커를 사용합니다. SEC filed 정렬 재무·한국 외국인 역사·일부 확장 거시 입력은 미연결입니다. / 원본과 다른 팀 하이퍼파라미터·가용 입력을 공개합니다. 현재 수정 거시에 시차를 준 결과이며 PIT 실시간 OOS가 아닙니다. / 완료월 추론입니다. 부분월 실시간 추론·웹 임의 종목 학습 서버는 아직 연결하지 않았습니다. / 변수 영향력은 고정 게이트 occlusion이며 SHAP/인과 효과가 아닙니다. 모델 선택·조정 규칙을 정한 기간과 분리한 전향 검증은 후속 대상입니다. / 방향전략은 월말 가정·편도5bp·rf=0이며 실제 주문·차입·선물 롤 비용을 복원하지 않습니다. CPI와 금리 수준에는 투자 수익률을 표시하지 않습니다.

### `research/modules/ml.md`

- [research/modules/ml.md:11](../research/modules/ml.md#L11) — - 남은 범위: 원본 전체 하이퍼파라미터·선택 주기 설정과 수치 동등성은 미검증입니다. 과거 발표/수정 빈티지와 과거 모형 설계를 복원한 PIT 실시간 성과가 아닙니다. / ICE 신용스프레드는 공개자료가 최근3년으로 제한되어 장기 z-score·일부 강제 위험 입력의 준비 기간이 부족합니다. 제외된 입력을 진단에 표시합니다. / 추가 원자료가 필요한 블록: Shiller CAPE/ERP, SF Fed news sentiment, global monthly EPU, VIX9D/VIX short-term structure, historical foreign investor net flows. / TreeSHAP는 별도 LightGBM 학습표본 해석이며 당시 선택 모델의 OOS 기여도·경제적 인과 효과가 아닙니다. US 변수 선택 패널은 S&P500 대표이며 Nasdaq은 별도 선택합니다.

### `research/modules/momentum.md`

- [research/modules/momentum.md:11](../research/modules/momentum.md#L11) — - 남은 범위: 조선5Y·누적 곡선/원본 사전표본·PIT 동등성 미검증

### `research/modules/multiasset.md`

- [research/modules/multiasset.md:11](../research/modules/multiasset.md#L11) — - 남은 범위: 원본의 모든 하이퍼파라미터·74개 입력명·그룹별 상한은 공개되지 않아 팀 설정을 명시했습니다. 원본 수치와 동일하다는 주장이 아닙니다. / OECD 미국·한국·일본·중국 선행지수는 공식 API의 진폭 조정 지수(장기 평균100)입니다. OECD 전체 집계는 미확보입니다. Boruta 미확정/순위 대체와 Markov 추정 불가를 진단에 표시합니다. / 과거 발표·개정 빈티지를 복원한 PIT 성과가 아니며 사후 설계 OOS입니다. 두 모델의 방향 정합은 측정된 신뢰도·성공확률 증가를 의미하지 않습니다. / 자산 모니터: 원본의 50/200MA 신호 세부 조건은 미공개이므로 팀 정배열/역배열을 명시했습니다. 원본 장중/시장별 기준시각과 완료 종가 사이 차이가 있으며 과거 수치의 완전 동일성을 주장하지 않습니다.

### `research/modules/overview.md`

- [research/modules/overview.md:10](../research/modules/overview.md#L10) — - 남은 범위: 원본 z 창/극단치 설정·세계 전체 시총50·역사 발표 빈티지 동등성 미확보
- [research/modules/overview.md:22](../research/modules/overview.md#L22) — 2. narrative·주간 연대기, 기업분석 요약, keycharts, Tesseract, crowding을 읽고 4개 PILLARS별 카드를 만든다.

### `research/modules/pm_weekend.md`

- [research/modules/pm_weekend.md:11](../research/modules/pm_weekend.md#L11) — - 남은 범위: 원본이 공개하지 않은 CTA 변동성 창·비용·레버리지 및 z 준비 기간은 위 팀 설정으로 고정했습니다. 과거 실시간 거시 빈티지와 실제 CTA 계좌 포지션은 아닙니다.

### `research/modules/principium.md`

- [research/modules/principium.md:11](../research/modules/principium.md#L11) — - 남은 범위: PDF 텍스트 추출은 문서당300쪽·20만자 범위입니다. OCR은 회당30쪽·최대3분이며 완료 페이지는 재사용합니다. 숫자·표·복잡한 배치는 원문 대조가 필요하고 LLM 요약·번역은 추가 구현 대상입니다. / 이 브라우저의 IndexedDB에 저장합니다. 팀 공용 DB·서버 인증/공개 배포·서버 조회 통계는 추가 구현 대상입니다.

### `research/modules/quant.md`

- [research/modules/quant.md:11](../research/modules/quant.md#L11) — - 남은 범위: 현재 유니버스와 최신 정정가격의 단면 분석이며 역사 구성종목·PIT·대차/펀딩/거래비용 후 OOS 성과가 아닙니다. / 공개되지 않은 rolling/Hurst/MAX/월안정성 세부 설정은 명시한 팀 설정입니다. 가격비 평균회귀를 공적분 검증이나 베타중립으로 부르지 않습니다. / TSMOM 보존본에서 이름이 확인된6개 외 나머지6개는 팀이 선택했습니다. 금리 상대변화에 투자노출을 부여하지 않습니다.

### `research/modules/regime.md`

- [research/modules/regime.md:11](../research/modules/regime.md#L11) — - 남은 범위: 재귀성 원본의 정확한 표본70/60과 회귀 오차 보정 방식은 미공개입니다. 팀 OLS 표준오차·252일 연율을 사용합니다. 과거 군집 입력이 부족한 월은 회색/빈칸으로 표시합니다. 종목별 P/E는 지수 전체의 역사 밸류에이션을 대체하지 않습니다. / 거시 지표의 미래 발표 달력과 과거 발표 당시 빈티지별 국면은 추가 연결 대상입니다. / 전산업 이익 관측기간과 공표 시점은 다릅니다. 한국2025/26년 이익을 임의 추정하지 않으며 현재 비율은 최신 실제 연간 이익을 기준으로 합니다. 해당 지수 구성기업의 역사 P/E와 발표시점 빈티지는 별도 과제입니다. / 달력은 계획이며 변경될 수 있습니다. 원문 미표기 발표시각·국가데이터처 미공개 다음 연도·계획에 없는 긴급회의와 과거 발표 당시 PIT 국면은 별도 대상입니다.

### `research/modules/risk.md`

- [research/modules/risk.md:10](../research/modules/risk.md#L10) — - 계산/자료 계약: US·KR 조기경보와 변동성·신용·쏠림을 계산합니다. 옵션은 수집 당시 현물·OI·IV로 계산한 콜 + / 풋 − 부호 가정 GEX입니다. ETF별 원장에 7~50일·행사가 ±15% 전체 제공 범위와 기존 제한만기를 구분합니다. 현재 종가로 과거 옵션을 재평가하지 않으며 실제 딜러 보유 포지션이 아닙니다. CFTC TFF는 선물만의 주간 보고값이며 레버리지펀드는 CTA 전체와 같지 않습니다. 계약별 단위가 달라 계약 수를 자산 간 달러 익스포저처럼 합하지 않습니다. 파생 Wag-the-Dog는 행사가 가로축·GEX 세로 막대·현물/플립/기대폭과 콜 위/풋 아래 OI 구조입니다. OI의 상하 배치는 매수·매도 방향을 뜻하지 않습니다. 30일 기대폭은30일에 가장 가까운 수집 만기의 같은 ATM 행사가 콜/풋 IV 평균×√(30/365.25) 근사입니다. 감마는IV 유효 계약만, OI는IV 결측도 포함합니다. 수집 시각의 현물과 만기를 그대로 사용하며 현재 시세로 재평가하지 않습니다. 수집 범위 메타데이터(예: DTE, 행사가 밴드, 만기 제한)는 `옵션 관측 범위`에서 표시합니다. 비펀더멘탈 수급의 미국20종목·LETF 리밸런싱·한국 대형주 투자자·국내 테마 ETF 패널을 독립 계산합니다. 국내 숏감마 화면은 KRX 공식 KOSPI200 OHLC·ETF 배율/순자산·월간 옵션 최종거래일의8개 관측입니다. 딜러 옵션감마와 구분한 리밸런싱 민감도와 팀 취약성 설정을 표시합니다. 콕핏은 멀티에셋의 ML 국면 현재 목표비중을 공유합니다. 최근120개 완료월에 같은 비중을 매월 적용한 USD 가상 장부로, 월 VaR/CVaR는 수익률 하위 분위·평균(손실은 음수), MDD는 월말 기준입니다. 실제 보유·동적 배분 성과와 구분합니다. 9요인은 최근60개월 ETF 대용 수익률의 동시 OLS이며, 스트레스5종은 공개한 팀 충격 가정표의 가중합입니다. 신호 신뢰도는 비용 후 배분 OOS와 만기 종료 ML을 각각 집계합니다. 과거 발표 빈티지를 복원한 실시간 성과는 아닙니다. 신호등은 US12·KR7 관측의 값·단위·기준일을 표시합니다. 단계·합산점수는 공개한 팀 규칙이며, 미확보·허용 지연을 넘긴 자료는 회색과 판정 보류로 처리합니다. SF Fed 뉴스감성은 원지수의252관측 백분위 대용으로 기사 긍정비율이 아닙니다. 선제위험4개는 가격 수익률의 CSD·변동성 군집 진단으로 옵션 딜러 감마나 보정된 급락 확률이 아닙니다.
- [research/modules/risk.md:11](../research/modules/risk.md#L11) — - 남은 범위: 전체 만기 딜러 포지션 및 레버리지 ETF 실제 순유입 원장은 연결되지 않았습니다. 옵션 IV를 고정한 가격 시나리오는 변동성 곡면 변화를 반영하지 않습니다. / 레버리지 ETF는 수집 원장의 명시적 표본으로 전 세계 모든 상품이 아닙니다. 국내 단일주식/해외 한국주식 LETF, 전 만기 옵션·실제 딜러 inventory는 미포함입니다. 공매도·AUM 제공처 지연을 확인해야 합니다. / 국내 취약성의 원본 비공개 가중치·예측력과 실제 딜러 포지션은 미확인입니다. 공식 ETF 현재 정의는 역사 PIT 구성 이력이 아니며 실제 설정/환매·헤지는 리밸런싱 시나리오에 미포함입니다. / 신호등의 원본 다단계 점수·상대강도 기간·뉴스감성 분모와 CSD/군집의 세부 산식은 미공개입니다. 팀 설정과 SF Fed 백분위 대용을 명시했으며, 당시 관측 빈티지나 급락 예측력의 동등성은 미검증입니다.

### `research/modules/rs.md`

- [research/modules/rs.md:11](../research/modules/rs.md#L11) — - 남은 범위: 조선 신규 상장으로 5Y 준비 구간 부족, z 비공개 세부 설정 미검증

### `research/modules/strategies.md`

- [research/modules/strategies.md:11](../research/modules/strategies.md#L11) — - 남은 범위: SEC 연속 자동수집은 PC HTTP 접근 상태에 따라 제한됩니다. 현재 원문 대조 표본과 미확인 후보를 구분하며 전체 미국 시장의 모든 내부자 거래를 의미하지 않습니다. Form4/A 정정 대조·13F·전략별 비용 후 OOS는 후속 대상입니다. / 전략 카드: 턴어라운드 사전표본·가격 절단·점수의 정확한 원본 임계치는 미공개로 팀 기준을 표시합니다. 재무 표본 확대·발표 당시 빈티지, 공적분의 전체 가정/다중검정과 비용 후 OOS는 남아 있습니다. / PEAD 카드: 원본 사전표본·기간/임계치의 비공개 설정, 제공처 발표시각의 발행사 전수 대조와 발표 당시 컨센서스 빈티지·비용 후 성과는 남아 있습니다.

### `research/modules/watch.md`

- [research/modules/watch.md:11](../research/modules/watch.md#L11) — - 남은 범위: ADX14·±DI·ATR·MA4조건·12개 지표 합계를 추가했습니다. 원본의 미공개 패턴 판정·신뢰도·개별 임계 설정과 수치 동등성은 미검증입니다. 현재 후보의 향후 수익 성과를 의미하지 않습니다.

### `research/MODULES.md`

- [research/MODULES.md:23](../research/MODULES.md#L23) — - [주간 기록](modules/iw.md) — 주간 코멘트 연대기와 국면·ML 그림을 묶은 기록 화면.

### `research/PDF_EXTRACTION.md`

- [research/PDF_EXTRACTION.md:42](../research/PDF_EXTRACTION.md#L42) — - 문서당300쪽·20만 JavaScript 문자열 문자. 파서90초, OCR 포함180초. OCR은 회당30쪽이며 남은 페이지는 대기로 표시한다. 다시 읽으면 완료 페이지를 재사용하고 다음30쪽을 처리한다. 문자/쪽수 한도는 계속 적용된다.
- [research/PDF_EXTRACTION.md:43](../research/PDF_EXTRACTION.md#L43) — - 원문 해시·처리 버전·모드·언어·배치·DPI가 같을 때만 완료 페이지를 재사용한다. 실패·대기·잘린 페이지는 다시 처리한다. 파서/OCR/빈 페이지/대기/실패 상태, 인식 점수·시간·실제 DPI를 저장·백업한다.

### `research/SUBVIEWS.md`

- [research/SUBVIEWS.md:3](../research/SUBVIEWS.md#L3) — 가격 기준 2026-09-10. 연결은 해당 화면에 실자료 계산·탐색이 있다는 뜻이며 원본 알고리즘의 완전 복제를 뜻하지 않습니다. 각 탭의 남은 범위도 함께 확인하세요. 공통 화면 그룹 목록: 연결 141개, 미연결 0개. 이 숫자는 완성된 원본 세부 기능 수가 아닙니다. RS/모멘텀의 별도 필터는 아래에 기록하며 원본의 중첩 화면·그룹 내부 기능은 [원본 기능 대조](REFERENCE_PARITY.md)에서 관리합니다.
- [research/SUBVIEWS.md:110](../research/SUBVIEWS.md#L110) — | 주간 기록 | 주간 연대기 | 연결 | 1 | |

### `research/UPDATE_PIPELINE.md`

- [research/UPDATE_PIPELINE.md:14](../research/UPDATE_PIPELINE.md#L14) — - `runtime/pending_publish.json`: 푸시 또는 Vercel 확인 대기. 다음 실행은 동일 커밋의 게시를 먼저 재시도한다.
- [research/UPDATE_PIPELINE.md:25](../research/UPDATE_PIPELINE.md#L25) — 수집 중단 후에는 `--resume-run <미완료 빈티지>`로 같은 부모의 완료된 수집 결과를 재사용할 수 있다. 정상 게시가 확인된 빈티지 자체에는 재수집하지 않는다.
- [research/UPDATE_PIPELINE.md:61](../research/UPDATE_PIPELINE.md#L61) — 모든 API 실패를 자동으로 해결할 수는 없다. 실패 시 로컬 로그를 확인하고 같은 명령으로 재시도한다. 최신 데이터가 없는 종목/옵션/지표는 개별 날짜와 미확보 범위를 확인한다. QuantiWise 원본 DB가 오래되었으면 수집 실행일이 새로워도 컨센서스 기준일은 그대로 표시한다.
- [research/UPDATE_PIPELINE.md:65](../research/UPDATE_PIPELINE.md#L65) — 교역은 `pipeline.trade_data`에서 실행 연도보다2년 전의 상품 총수출을45개 통계지역별로 확인한다. 30일 이내 지역 캐시와180일 코드 사전을 재사용하며, 같은 값은 원자료를 복제하지 않고 확인 시각만 원장에 남긴다. 500행 검사·직렬2초 간격이며401/403/429는 해당 실행의 후속 요청을 중단한다. 실패 또는 기존 자료의 갑작스러운 소실은 이전 관측·성공시각을 유지한다. [교역 데이터 계약](TRADE_CONTRACT.md)을 따른다.

## 역사 인계 증거

### `HANDOFF.md`

- [HANDOFF.md:3](../HANDOFF.md#L3) — 2026-09-13 임상 모집 상태 후속: 최근5건 표본에서 이전 성공 관측의 상태가 비모집이고 현재 `RECRUITING`인 연구만 촉매 원장에 ‘임상 모집 상태 변경’으로 남긴다. 최초 표본의 모집 상태·등록일·기관 전체 모집·임상 효능/허가/투자 결과는 추정하지 않으며, 알림은 점수에 합산하지 않는다. 새 외부 관측이 생긴 뒤에만 화면에 나타나므로 주말 수집·스냅샷·배포는 하지 않았다. Python6·임상 JS·dashboard JS 검사를 통과했다.
- [HANDOFF.md:5](../HANDOFF.md#L5) — 2026-09-13 내부자 Form4/A 후속: `ownership_views.amendment_resolution`은 기준일 전 접수된 정정본이 동일 발행사·동일 보고자 CIK 집합·원공시일로 정확히 하나의 Form4에 대응할 때만 최신 정정본 행으로 원공시를 대체한다. 여러 후보·원공시일 부재·기준일 후 정정은 모두 보류하며, 이전 정정본을 합산하지 않는다. 카드에는 원공시 accession을 더하지 않고 대체한 사실을 표시한다. 실제 SEC 수집은 주말이라 실행하지 않았고 Python12·소유권 JS·dashboard JS 검사를 통과했다. 전체 시장 연속수집과 모호한 정정의 원공시 확정은 남은 범위다.
- [HANDOFF.md:7](../HANDOFF.md#L7) — 2026-09-13 관심도 문서 정체성 후속: `attention_data.py`가 30일마다 MediaWiki의 고정 page ID를 정규 제목과 고정 Wikidata ID로 대조한다. 대조 실패는 기존 성공 열람을 보존하고 오류·1시간 백오프를 기록하며, 제목이 실제 변경되면 이전 제목 열람을 합치지 않고 새60일 표본과 변경 원장을 시작한다. 화면은 정규 제목 확인 시각과 변경 사실을 표시한다. 이는 10개 영문 문서 관측에 한정하며 리디렉션/다국어 전체 관심도와 개명 전후의 연속성 검증은 미확보다. 주말이라 외부 MediaWiki 수집·스냅샷·배포는 하지 않았고 Python5·관심도 JS·dashboard JS 검사를 통과했다.
- [HANDOFF.md:9](../HANDOFF.md#L9) — 2026-09-13 임상 등록부 후속 구현: `clinical_data.py`는 각 검색조건의 최근5건 표본에 실제로 나타난 연구에 한해 상태·단계·제목·책임/공동기관·등록부 갱신일의 상태 이력과 최초/최근 성공 관측/API 버전을 누적한다. 같은 상태를 재확인하면 별도 상태를 중복 생성하지 않고 최근 확인만 갱신하며, 변경 필드는 현재 표본 카드에 표시한다. 표본 밖 연구·표본 진입 전 변화·전체 등록부 이력, 원본 비공개 검색식과 기관별 계열사 범위는 계속 미확보다. 주말이어서 ClinicalTrials.gov 외부 수집·공개 스냅샷 재생성·배포는 하지 않았다. Python5·임상 JS·dashboard/extended JS 검사를 통과했다.
- [HANDOFF.md:11](../HANDOFF.md#L11) — 2026-09-13 연속13F 후속 구현: `guru_data.py`가 SEC recent submissions의 최신부터 최대4개 보고기간을 수집·정정해결하고, 기존 접수번호는 재다운로드하지 않는다. `guru_views.py`/`guru-views.js`는 보고기간 원장과 최신 인접분기 동일 CUSIP·주식종류·수량단위·옵션별 보고금액 비교를 보여준다. 이는 공시상 차이일 뿐 거래일·순매수·현재보유·신호점수가 아니다. 외부 SEC 수집은 주말이라 실행하지 않았고, 다음 평일08/18시 기존SEC 접근/연락처·백오프 규칙으로 실제 자료를 채운다. 13F Python11·identifier18·dashboard/extended JS 검사는 통과했다.
- [HANDOFF.md:13](../HANDOFF.md#L13) — 2026-09-13 관계 유니버스 후속 준비: 저장소 밖 `runtime/relation-listings-audit.json`의 공식 Nasdaq/NYSE·KRX 대조 결과를 공개 `config/relation_universe_additions.json`으로 옮겼다. 43개 연구표기(42새 종목, STM 두별칭)는 종목 식별을 확인했고, 기존 목록과 합쳐153/159표기·149종목이다. Tokyo Electron을 뜻하는TEL은 미국TE Connectivity와 혼동되므로, BESI·ASMI·SHINETSU·ABB·FOXCORP와 함께6개 미연결로 유지했다. `incremental.prices`와 초기 core 수집 모두 명시 등록부를 포함하되, 신규가격은 실행당25개로 순차 수집한다. 이는 공급처 요청 배치이며 저장용량 제한이 아니다. 현시점은 주말이므로 외부 수집/빌드/배포를 하지 않았다. 다음 승인된 평일08/18시 갱신에서 현재빈티지의 기존캐시를 재사용하고, 새 시계열 확보 뒤 관계 상관/시차와 기업 상세가 자동 재계산된다. 관계단위검사4개·Python 구문·diff 검사는 통과했고 전체검사는 실행 시간 초과로 완료 확인이 남아 있다.
- [HANDOFF.md:15](../HANDOFF.md#L15) — 2026-09-13 재무 유니버스 전체 잔여 수집 실행: 미게시 raw `20260913T112310Z`(부모 `20260911T054825Z`, 가격 기준2026-09-10)의 기존221캐시를 모두 재사용하고, 남은724종목을 종목별1회씩 시도해709개 추가 확보했다. 현재930/945 사용 가능·신선 캐시, 15개 미확보(손익표 없음9·손익표 있으나 재무통화 미확인6)이며 부분 응답을 성공으로 바꾸지 않았다. 즉시 전체 재실행은930재사용/15유예, 외부조회0. 원자료와 원장은 저장소 밖 같은빈티지에 있으며 `runtime/fundamental-universe-resume-result.json`/`resume-collection.json`/`resume-retry.json` 및 수집·검사 로그에 근거를 남겼다.
- [HANDOFF.md:17](../HANDOFF.md#L17) — 수집 중154개 추가확보 시점에 Windows `collection.json.gz` 원장 교체가 WinError5로 중단됐다. 미교체tmp와 기존원장을 별도보존하고 `events_data.save`의 PermissionError 원자교체만 최대6회(대기합3.1초) 재시도하도록 보완했다. 영구실패는 기존파일/새tmp를 보존한 채 오류를 전파한다. 재개는154개도 재사용했고 추가555개를 확보했다. 원인 프로그램은 확정하지 않았다. 신규저장3시험 포함 전체390Python(91.676초), 두자료검증기·3JS모음·변경JS/Python구문·diff검사 통과. 신규709파일의 원응답 동일성/해시와 연간·분기 NI/OP/매출18,577값 대조 통과. 이는 제공처 응답/정규화 일치 검증이며 공시 원문 독립감사는 아니다. 기존221캐시·작업시작시 미커밋파일·공개docs·배포state 해시보존 확인 후 이 인수인계와 정본계약에 결과만 추가했다.
- [HANDOFF.md:19](../HANDOFF.md#L19) — 후속 게시 완료: 동일 빈티지로 스냅샷을 재생성해 Python391·자료/확장·JS 검사를 통과했고, 코드 commit `412e730c1918508d48a7a38c4a261c02b71977a1`과 생성 결과 commit `f4bb3269e386d82116dd3304c9af769bec5e4fc6`을 `main`과 Vercel에 게시했다. 운영 `refresh.json`/`status.json`은 run `20260913T123639Z`, vintage `20260913T112310Z`를 반환하며, 변경 공개파일27개의 원격 SHA-256 일치를 확인했다. 930/945는 raw 재무 캐시 범위이고 기존 실적 연구 화면 표본은 정의상197개로 유지된다. 미확보15개와 49미연결기업·해외달력·GDELT·연속13F 등은 완료되지 않았다.
- [HANDOFF.md:22](../HANDOFF.md#L22) — 2026-09-13 재무 유니버스 후속: `fundamental_universe.py`가 부모별 최신5구성자료의 정규화 members+기존연구/전략지원 종목을 합쳐945종목과 출처/해시 원장을 만든다. acquire.py의 이전미완 확장에서 부모구성누락·OEF CSV를JSON으로읽기·비결정적순서를 해결했다. 기존company_fundamentals의 재무전용경로/별도원장/종목별7일캐시·실패1시간유예·제공처제한배치중단/보류/재개를 재사용한다. refresh는 폴더mtime 대신 매회대상/종목신선도를 확인한다. 부분캐시는 부분표시유지, 장시간배치는 기업별실제시각사용. 기존뉴스40기업의 실적달력경로는 별도유지. 정본research/FUNDAMENTAL_UNIVERSE_CONTRACT.md.
- [HANDOFF.md:24](../HANDOFF.md#L24) — 실제캐시215→221/945: 한국000080.KS/000100.KS/000120.KS·미국A/ABBV/ABT의6재무추가,162연간/분기수치 원자료대조통과·즉시재실행0조회. raw빈티지20260913T112310Z(부모20260911T054825Z),가격9/10. runtime/fundamental-universe-pilot-result.json/로그/원자료해시보존. 전체385Python(87.933초)·두자료검증기·3JS모음통과 후 마지막부분캐시/장시간시각보완의 신규9+기존기업6테스트/구문/diff검사통과. 공개스냅샷재생성·배포없음. 다음수집은 미게시raw20260913T112310Z를 이어쓰면 기확보221캐시를 재사용할 수 있다(`SANGSANGIN_VINTAGE`를 해당빈티지로 지정하고 `python -m pipeline.acquire fundamentals --as-of 2026-09-10`). 재무724종목미확보·49미연결기업/해외달력·GDELT20실검색·연속13F 등 전체목표는 계속미완료. 아래문단의acquire미검증기록은 이번구현/검증으로 대체한다.
- [HANDOFF.md:26](../HANDOFF.md#L26) — 2026-09-13 재개 완료 묶음: 기존 미커밋 변경을 보존하며 주제 뉴스 중단/재개와 Overview 환산을 보완했다. topic_news는 일반HTTP오류 검사·정상기사의 제한문구 오인 방지, 실패/보류 원인과 실제요청/보류 시각 분리, 정상24시간캐시 유지 및 유예 후 미완료만 재요청한다. 화면에 동일검색식/기간 링크와 보류근거를 추가했다. 실제1요청이 제한응답(429분류)으로 끝나19검색보류·즉시재실행0요청, 확보0/20. private raw빈티지20260913T110342Z(부모20260911T054825Z), 가격9/10, runtime/topic-news-resume-collection.json/preview.json에 검증자료 보존. 실패수집은 미배포.
- [HANDOFF.md:30](../HANDOFF.md#L30) — 전체목표 미완료. 다음은 GDELT제한 해소 후20검색확보/다중제공처,49미연결기업·시장달력/전체관계,연속13F/리포트정량뷰 등REFERENCE_PARITY 목록을 따른다. 중단전 acquire.py의 재무유니버스확대 변경은 실제수집 검증이 남는다. 사용자요청대로 기능단위 작업·관련코드/변경분 탐색·기존스크립트/캐시 재사용으로 토큰소비를 줄인다.
- [HANDOFF.md:51](../HANDOFF.md#L51) — 후속 보완: 발표 시점 데이터/ALFRED, 역사 구성종목, 글로벌 영업이익 컨센서스, SEC 제출 시점 원장·13F, 원본 모델과 공정한 비교, 팀 공유 저장·권한 서버.
- [HANDOFF.md:69](../HANDOFF.md#L69) — 후속 추가: 리스크 Wag-the-Dog 연결. option_analytics.py와 wagdog.py는 동일 packets를 사용한다. 기존 가로 막대 GEX를 원본과 같은 행사가 가로축/수직 감마 막대로 교체했고 현물·플립·30D IV 기대폭을 표시한다. SPY OI는 콜 위/풋 아래이며 방향 의미가 없다. OI는 IV 결측도 포함하고 GEX만 IV 필터한다. 플립은±20% 탐색의 교차, 교차 없음 또는 감마 전부0은 None. 기대폭은 ATM IV의30D 정규 근사로 옵션이 예측한 확정 범위가 아니다. VVIX를 추가했다. 실제배포기준/빈티지는 runtime/state.json을 확인한다. 다음 우선: flows 주식·ETF AUM/공매도·KR 투자자 수급과 PM 개별 실적 ATM 스트래들.
- [HANDOFF.md:73](../HANDOFF.md#L73) — 수급 후속: flows_data.py는 Yahoo 공개 요약(US20종목·LETF50상품), Cboe주식20+예정실적 최대8종목, KRX공식8대형주 투자자 거래량/1168ETF를 분리 수집한다. flows.py는 1%충격 LETF/21D ADV, |GEX|/시총, 옵션명목/시총, Short/Float 단면z를4개모두 있을 때만 평균한다. 리밸런싱은 Σ(L²−L)AUM×가정충격, 원본 금액막대+ADV다이아 구조·±20% 입력. 지수는 ADV 비율 미표시. KR12테마는 비레버리지명칭첫일치·공식순자산우선/NAV×좌수대용, 1M NAV변화·회전률. 주식 수급은 최근5거래일 순매수 주식수/동일기간 전체거래량. PM/실적은 같은행사가/만기 bid/ask mid 합계÷현물, ORCL/COST 최초2개 관측. Yahoo AUM은 보고일미제공, shorts는dateShortInterest일자. 모든ETF세계목록이라는 주장이 아니며 원장에등록범위표시. MSTR 가격 추가필요시 catalog DETAIL에포함. 공공API품질90%미달이면자동배포중단.
- [HANDOFF.md:75](../HANDOFF.md#L75) — 국면 후속: valuation.py 3시장×3단(실제지수/전산업이익 로그이중축, 비율25/50/75분위, CPI+정책금리)·5/10/15년전환. CP FRED, ECOS501Y002 ZZZ00/A/270000 연간당기순손익백만원→조원(1e6) 신규수집. 연간/분기 관측기간말부터 월별유지, 마지막 실제기간 이후 점선은carry이며 이익추정아님. 원본설명엔KR GDP라고남았으나JSON은전산업순이익; 2025~원본추정 산식은없으니동일수치주장불가. calendar_data.py는 FRED8releaseID+BEA(최초50예정발표), UTCoffset/DST→KST. BLS직접ICS403은 FRED공개일정으로대체. refresh주간달력/매회CP·ECOS계열갱신. 검사52unittest+6표준/구문/전체subview+21SVG래스터. macro53.
- [HANDOFF.md:78](../HANDOFF.md#L78) — DRAGONGLASS 후속: `entities.py` 현재공식유니버스 합집합700개(재무132/향후일정59)·64거래일14점가격·동일가격구간252Beta(최소200)·RS유니버스표시. `decision-ledger.js` v2로 가설/방향/확신/시계/크기/촉매/무효화/3상태/최근50이력/휴지통/JSON/Entity상호이동. localStorage기존v1원문보존, 명시적가져오기, 500건2MiB상한, stale-tab compare-before-write와quota오류시원본유지. 실행만NAV집계, 누락비중/Beta전체값null, 0가중치0. 가정EV는사용자입력만. `test_decisions.cjs`는상태엔진및실제화면콜백을offline미니DOMfixture로검사, 브라우저QA아님. test_extended가호출하므로자동갱신검사에포함. `write_status_docs.py` 반복실행빈줄누적수정. 원본프리모템·군집·8관계전파는후속대상.
- [HANDOFF.md:92](../HANDOFF.md#L92) — 지수 ML 후속(2026-09-09): `ml_features.py`142후보, `ml_ensemble.py`10종/Shadow12회/6개월일반·12개월LSTM, `ml_transformer.py`Transformer 추가·선택/잔차 재생, `ml_views.py`10세부그룹16섹션. 원본 설명10종과 실제 평가표13열(11종+2앙상블)이 달라 실제 chart 구조를 따랐다. 1M164·3M162원점, 최소96라벨,3M만기·당시120개평가선택/24잔차검사. TreeSHAP는 full available-label 별도 LightGBM의최근120개15변수 해석으로OOS/인과 아님. 최신3개 MLP수렴경고를진단에표시. 최종선택은SP5001M XGBoost/3M ExtraTrees,KOSPI1M LightGBM/3M Lasso,NASDAQ1M·3M ExtraTrees.
- [HANDOFF.md:98](../HANDOFF.md#L98) — MAXIMUS 후속(2026-09-09): `maximus_features.py` 가격223/CPI201후보·자기기술/US·KR레버리지/6부문 순차HP/3합성·훈련창ADF/SIS, `maximus_moe.py`10전문가·추가1개월엠바고·6개월재학습·과거48개OOS 로지스틱25%/프라이어75%·붕괴보정. `maximus_views.py` PT/DM·68/95팬·R/I occlusion·24원점/전체진단·방향전략. 기본2지수/추가지수Nasdaq/6매크로/13종목=22대상, 7섹션/5그룹. PLTR·LG에너지솔루션은8년미만 제외; 삼성바이오로직스21원점/19잔차로확률·팬없음. MLP수렴경고8타깃을진단에보존한다.
- [HANDOFF.md:104](../HANDOFF.md#L104) — 다음은콘텐츠기능: 보존principium.js에article/report/primer별문서보드·5단상세·키워드구체/공동출현그래프·등록/수정/첨부구조가있다. 자체콘텐츠로구현하며원본관리자/비밀번호/저자기록을복제하지않는다. IW원본은월말복기15건+주간연대기14건과2차트, ASK digest는brief/기간별trends·테마10·주식16·21crossasset·위험양/음·4차트·모듈요약schema다. 이들현재기본메모만으로완료처리하지말것. 이후관계전파/위성/추정상세등은REFERENCE_PARITY지속확장.
- [HANDOFF.md:106](../HANDOFF.md#L106) — 로컬 리서치 후속(2026-09-09): `research-store.js` IndexedDB(meta+files)·500건/UTF8메타2MiB/첨부64MiB·파일8MiB/기록12개·SHA256동일파일공유. 같은트랜잭션에메타/Blob저장·고아파일삭제, 중간quota실패롤백·revision및기록history충돌방지. 가져오기90MiB·첨부hash/크기/형식검사·동일건중복건너뛰기·충돌사본. 이전localStorage키보존/명시적가져오기·내용hash기반ID. 영구삭제는휴지통만, 다른글이참조한첨부유지. PDF다운로드·래스터이미지만Blob미리보기, 네트워크전송없음. 실제브라우저저장소를도구로열거나사용자자료를추가하지않았다.
- [HANDOFF.md:115](../HANDOFF.md#L115) — IW 후속(2026-09-09): 원본29행은15월말 복기+14주간 연대기였으며29독립판단 지표라는 이전 해석을 정정했다. `iw_review.py`는1M ML 원장과같은표에서 방향집계·3지수/6전망/4거시·36완료월3국면띠/7계열ML을 생성한다. 성장/CPI/M2/Sahm2개월·NFCI7일팀정보시차, 위험5필수조건 결측은회색. 첫과거13주는재구성표시,지난주는기록/차트동결,현재주만갱신/최초시각보존. private iw_journal.json.gz 전체누적·공개14주,모형hash/빈티지/방법버전저장. 월중확정국면제외·표시구간z재계산, 상세계약 research/IW_REVIEW_CONTRACT.md. `subview_modules.extend`끝에서연결하므로정기갱신에포함. 개발raw빈티지20260909T131712Z(부모114624Z),추가외부/원본요청0. 검사89Python·두검증기·3JS/11구문·38SVG래스터,국면/과거ML배치확인;브라우저QA없음. 공개JSON약5.99MiB로현재6MiB한도에가까움;이후작은파생탭추가시필요하면공개한도만합리적으로확장하고raw512MiB승인한도유지. 다음ASK brief/기간별추세/테마/종목/crossasset/위험·모듈요약을기존수치로구현. 게시실행ID 20260909T133351Z의실제완료는runtime/state.json확인.
- [HANDOFF.md:118](../HANDOFF.md#L118) — ASK 후속(2026-09-09): `digest.py`와config/digest_themes.json으로10세부화면연결. brief·1M/6M/2Y선택·공식기업사업근거10테마(1~2기업표본)·공식US/KR RS각8총16·21자산·9임계관측·4핵심비율/스트레스·20분석모듈요약·RSS·로컬질문. 원본 heat/구루/전체뉴스량/자동LLM서버 미연결. 회사공식사업설명근거의역할이며GICS공식테마분류아님. 수익률은달력7일/월/연도이전마지막가격(7일초과오래되면결측);암호자산504일을2년으로간주하지않도록수정. starts실제기준날짜보존,테마는모든구성원기간가용때만단순평균·가용목록3Mrank0~100/동률평균. 주간조회원장그림외기존모듈의21/63/252관측계약은변경하지않았다.
- [HANDOFF.md:132](../HANDOFF.md#L132) — DRAGONGLASS 후속(2026-09-09): 관계39객체(기업22/테마13/관측2/가정2), 공식 사업/공급/경쟁/협업30+실현상관6, 원본255/581전체 검증 아님. `relation_views.py`가`extend`에서Entity추가후호출되어정기갱신에포함. Entity700공식+TSM ADR1(공식업종미확보/RS없음), 모든기업가격을관계확신도처럼사용하지않음. 가격추가요청0,원본요청0. 기업공식/SEC자료만근거확인했으며 config/relation_evidence와digest_themes에URL/역할보관. 노드좌표3Dspring seed832/k1.2, SVG라벨겹침회피·드래그/휠/핀치/선택/필터/자동회전·탭이동시프레임취소. 초기과밀레이아웃을래스터에서발견해수정.
- [HANDOFF.md:134](../HANDOFF.md#L134) — `relation-views.js`는공개8가정Python결과와정확일치. 최대3단계/최강경로/다중입력합/출처, 중심성·부호대조·상하8순위/도달범위,원장실행비중·최악가정·Long쌍별상관. 상대강도를수익률이나%NAV손익으로표시하지않음. 무입력/미연결/경로없음/0비중분리. 이전Beta/공식분류별도하위화면보존. 상관전체Entity701창252/min200 아래삼각Int16×10000+Uint8관측수·결측32767·자기상관분산검사. 원장스토리지변경없고가정확률/권장비중자동생성없음. 상세 research/RELATION_CONTRACT.md, source미확보범위 REFERENCE_PARITY.
- [HANDOFF.md:139](../HANDOFF.md#L139) — Overview 후속(2026-09-09): overview_state.py/overview-views.js로TESSERACT6축·CROWDING5축·36시점궤적/4시점적층·회전/드래그/프레임취소·주도주웜홀/선택/원단위표 연결. z최대120/최소60/ddof0, SPY/EEM50:50, Wilshire가격지수/GDP상대변화는실제시총/GDP아님. 시총50표본중가격/분기NI가용49에서상위10;전체글로벌시총상위아님. 단위/발표시차/셧다운보정은 research/OVERVIEW_CONTRACT.md. CPQ4+3개월, 2025Q3GDP/CP는2025-12-23, 2025Q4GDP2026-03-13/CP2026-04-09로확인된지연보정;최신수정치PIT아님.
- [HANDOFF.md:144](../HANDOFF.md#L144) — 지정학 후속(2026-09-10): geoecon_views.py/geo-views.js로15주제4카테고리·상위6상황·5관심지역·19키워드30일/7일비중·6채널·3복합z/밴드·시장3이중축1년·GPR3지수/8역사분류/8국가1/3/10년 연결. RSS2/RDF/Atom 파싱을수정해BIS/DW미검출해소;이번7요청6성공/IMF HTTP실패,143응답. 부모빈티지URL합집합·KST가격기준일종료/수집미래제외·first_seen보존으로79제목. 짧은수집역사를당시완전한뉴스량이라고주장하지않는다. 제목단어/3단어부정어·주목도기사+위험표현2배는팀규칙. 채널노출=기사비중×7·주제중복제외,27자산/기사관측경로D0~20은인과효과아님.
- [HANDOFF.md:148](../HANDOFF.md#L148) — 검사121Python·두검증기·3JS(geo추가)/14구문·59SVG래스터통과,8신규이미지확인,브라우저QA없음. 원자료/실행파일98.18MiB/512·공개JSON7.405MiB/8. 게시실행ID20260909T152214Z/raw빈티지20260909T150119Z,실제공개상태는runtime/state.json. 전체목표는진행;다음estimate_verify/us_consensus분기/연간세부·위성실관측·SEC13F/P·KR달력/옵션·RS기간계약등REFERENCE_PARITY의미완료를계속구현한다.
- [HANDOFF.md:151](../HANDOFF.md#L151) — 실적 후속(2026-09-10): earnings_details.py/earnings-views.js로global NI표본Top20 굵은FY1/얇은FY2/실제tick,한국2기업 OP/지배NI(과거3A/다음2E),미국10기업 NI근사/직접매출(1A/2E),197기업 검색·연간4/분기8 NI/OP/매출3패널 연결. 손실0축왼쪽·누락대시·가격/재무/추정일분리·원천링크. 원본글로벌/US의미래NI는EPS성장연결근사였으며직접NI컨센서스아님을명시. 세계전체표본아닌198연구기업중환산196가용의실제NI상위20이다. AAPL/BRK-B를명시적연구목록에추가해앞으로주간갱신.
- [HANDOFF.md:155](../HANDOFF.md#L155) — 검사129Python·두검증기·3JS(earnings추가)/15구문·64SVG래스터통과,새5이미지확인,브라우저QA없음. 데이터가격1136/거시62/재무연결197,개발raw빈티지20260909T152436Z. 로컬106.33MiB/512·공개JSON7.609MiB/8(배포패키지생성전). 게시실행ID 20260909T224449Z 실제공개완료는runtime/state.json. 전체목표는계속진행;한국증권사별원문/해외직접NI·OP/PIT,위성실관측,SEC코드P/13F,KR거시일정/옵션,RS/모멘텀/ETF기간계약등REFERENCE_PARITY 미완료를계속한다.
- [HANDOFF.md:160](../HANDOFF.md#L160) — SEC 내부자 후속(2026-09-10): sec_ownership.py/ownership_views.py/ownership-views.js로비파생P·취득A·접수시각확인90일카드/미니선/검색/복수보고주체필터·공시원장·SPY대비D0~20관측연결. 제공처후보8행대조→7공시9거래행4기업(PFE/CVNA/VST/CEG), AVGO1공시는원문P확인했으나접수시각미확보로집계제외. VST1제공처행은8/31·9/1의2실거래행,CVNA도2가격행. 공시/행/보고CIK수를분리하고가중가격·D/I·원문/색인·검토시각표시. P는공개시장또는사적매수,주체CIK는독립된경제주체보장아님. 10b5체크미확인은미확인그대로보존.
- [HANDOFF.md:169](../HANDOFF.md#L169) — 국내 거시 달력 후속(2026-09-10): kr_calendar.py/calendar_views.py/calendar-views.js로기존미국달력에한국은행통계127·통화정책방향회의8·국가데이터처통계181연간일정을연결. 향후90일(9/10~12/8) 한국77/미국52총129,출처13. 국가/7·30·90일/분류/검색·원문·출처별확인/마지막성공시각·stale표시. 한국은행상단월간격자대신하단연간표·정책선택연도검사,국가데이터처제목관측연도와공표연도분리·전체262행중연도명시통계181선별. 교육/행정/기준연도미표기제목은제외한범위다.
- [HANDOFF.md:176](../HANDOFF.md#L176) — 위성 후속(2026-09-10): satellite_data.py/satellite_views.py/satellite-views.js는22시설 슬롯·14검증위치/실제Sentinel2 C1 L2A·RGB/NDVI·평면Mercator지도/드래그/키보드/확대/3크기·시설 Entity와 기업 연결을 구현했다. 8미확인(M15X/평택/IntelOhio·Magdeburg/Vandenberg/Sabine/Ghawar/Permian)은 위치 대조 중으로 유지. 공식주소·OSM객체대표점 구분, Colossus1은FCC9쪽 공식gateway좌표. Magdeburg2025-07-24중단발표 반영. 원본좌표의도심/잘못된시설을 복제하지 않았다. 자세한 SATELLITE_CONTRACT.md/registry 참조.
- [HANDOFF.md:183](../HANDOFF.md#L183) — 위성22곳 후속(2026-09-10): 남은8기준점을 대조해22/22 실제 RGB/NDVI를 확보했다. 평택은삼성캠퍼스복지1동공식지도,청주M15X는공식4공장주소/배치와기존M15지도기준점(개별M15X중심아님),Ohio는Umbra 공개METADATA sceneCenterPointLla(3754bytes만,대형SAR미다운로드),Magdeburg는시의회DS0471/25계획도/EulenbergOSM지형점·중단계획부지,Vandenberg는SpaceX안내서PDF73쪽발사대,Sabine은Cheniere공식지도장소핀. Ghawar는Uthmaniyah가스처리시설,Permian은NASA Yates사진중심의4km한정관측이다. 유전/분지전체생산·매장량대표로표시하지않는다. 공식PDF/좌표/검색응답은private satellite_research에보존.
- [HANDOFF.md:190](../HANDOFF.md#L190) — 가격 세부 후속(2026-09-10): RS는KOSPI200 KPI/4개강약8표·시장필터·강8+최약6막대, 고정−3.2~3.2축/정수눈금/±1±2가이드/클립/원값툴팁을연결했다. 순위 pct_rank*98+1오류를1+98*(평균rank−1)/(N−1),단일50으로수정해다른rank소비모듈도전체재계산. 모멘텀32곡선은상위16이아닌강8+약8을짝3M/6M으로선택,막대순country/sector/factor/asset·그룹별3M정렬열지도,오래된자산이전체기준일을뒤로잡는문제수정. nice눈금/0눈금추가·SVG XML hidden속성값명시.
- [HANDOFF.md:192](../HANDOFF.md#L192) — etf_details.py는9분류73위치(미확보삭제금지)·10열통합비교/주기간격/월간상위/금액입력/정렬검색/배당락일원장.12M창좌측제외·미래가격제외·Dividends현금합/시장종가·분할이중보정금지·미확보와0분리.기존Yahoo원자료만재사용하며공식YieldMax주간/QYLD매도구조/TQQQ일간배수자료는웹대조.원본NVDY등월배당오류미복제;원장날짜는지급일아님.별도Capital Gains/ROC/공식지급일·전상품운용사대조는남음.ETF_CONTRACT.md 참조.
- [HANDOFF.md:199](../HANDOFF.md#L199) — 신고가 발굴 후속(2026-09-10): us100_data.py는 iShares OEF 공식 CSV의 Equity만 선별한다. 9/4 구성101개·BRKB→BRK-B·주식 클래스 보존, 현금/선물 제외·날짜/펀드명/가중합/중복/SHA256 검사. 7일1회·최대1MiB·실패 별도 기록/같은빈티지 재시도없음·14일초과 미확보. refresh와 신규25종목 제한에 연결했다. 첫17323bytes 한 요청, 새가격/원본사이트 요청0. raw 빈티지20260910T011831Z(부모20260910T002037Z), 가격 기준9/8.
- [HANDOFF.md:206](../HANDOFF.md#L206) — 2026-09-10 배포 출처 제외 요청: 사용자는 배포 웹사이트의 참조 제작자 이름·관련 출처 표기를 전부 제외하도록 지시했다. 현재 docs 정적 파일과 실제 열린 모멘텀 화면에서 이름/참조사이트 링크는 발견되지 않았다. scripts/validate.py에 배포 docs 전체의 이름 변형·HTML/URL/Unicode escape 및 참조 도메인 검사 추가, 정기 갱신 시 재등장하면 게시 중단. 연구용 대조 문서는 docs 밖에 유지한다. 현재 PDF 본문 추출 후속은 원본 principium.js 업로드 계약/PDF.js 공식문서·npm 메타 확인까지만 수행했고 다운로드/코드변경은 아직 없다. 다음 목표 턴에서 이어갈 것.
- [HANDOFF.md:209](../HANDOFF.md#L209) — PDF 본문 후속(2026-09-10): pdf-text.js/notebook-pdf.js를 PRINCIPIUM/IW/ASK에 연결. 공식 npm PDF.js6.3.289 legacy파서/worker+CMap168+표준font14+license4=188파일3811556bytes, tarball8503425bytes SHA512/개별SHA256 검증. 같은사이트lazy import/worker이며 문서업로드/API/외부CDN없음. .gitattributes로업스트림byte를Windowscheckout에서도유지. public_assets.py가파일누락/추가/해시/8MiB한도검사,패키지.mjs/.bcmap/.pfb/.ttf허용·정기JS구문검사23파일확장. PDF runtime assets는정상오픈소스배포라이선스를보존한다.
- [HANDOFF.md:218](../HANDOFF.md#L218) — 국내 숏감마 후속(2026-09-10): 보존 risk.json은 옵션 GEX가 아닌 ETF 리밸런싱·가격 진단8행이었다. 이전 OI/IV 필요 판정을 정정. kr_shortgamma_data.py/kr_shortgamma.py로 KRX 지수1028 실제OHLC728·공식기초지수/배율19ETF·보고순자산·월간옵션실제최종거래일을 연결했다. 현물/선물지수 분리·업종형/해외/KOSDAQ/커버드콜/ETN제외. ±1%1881.7479억원·1σ5869.2748억원(2026-09-08 기준),실제딜러보유/주문/설정환매/영향예측아님. RV21표본단순수익률49.513459%,비율1.073815·고저15%극단7/20·D-2(9/10)이다.
- [HANDOFF.md:227](../HANDOFF.md#L227) — 전 지구 배경 후속(2026-09-10): satellite-tiles.js/satellite-views.js에NASA GIBS BlueMarble_ShadedRelief_Bathymetry 고정2004-08 배경을 연결했다. 공식EPSG3857 WMTS,256px/level0~8,배경500m 원자료와시설10m/촬영일을분리. 드래그/키보드/날짜변경선·전체시설fit·실제폭ResizeObserver·높이400/560/760·확대19(배경8이후확대표시)·RGB/NDVI·해안선전환. 관측아래불투명matte로구름/결측에과거배경이비치지않게했다. 원본Esri고해상도/지명레이어는구독권한질문중이며NASA로동등성완료선언금지. 추가원본사이트/시세/시설원밴드요청0;같은raw빈티지20260910T023239Z의44PNG재생해시불변.
- [HANDOFF.md:234](../HANDOFF.md#L234) — 멀티에셋 자산 모니터 후속(2026-09-10): 보존 multiasset.json/app.js의4KPI→21자산6기간열지도→1M내림차순/중앙0/좌우대칭막대→6자산군4열표를 asset_monitor.py와 전용 렌더러로 연결했다. 막대색은 수익률 부호가 아닌50/200MA 추세이며 범례/툴팁에 표시한다. S&P500/Nasdaq Composite/Russell2000/금은 SPY/QQQ/IWM/GLD 대용에서 실제 ^GSPC/^IXIC/^RUT/GC=F로 수정했다. 별도 배분/스캐너의15개섹션은 기존 계산값 그대로 유지했음을 객체 비교와 화면 전환으로 확인했다.
- [HANDOFF.md:242](../HANDOFF.md#L242) — 게시 run 20260910T035436Z; 최종 커밋/URL/성공은 runtime/state.json과 해당 file-verification 보고서를 확인한다. 전체목표는 계속 진행: 원본 미공개MA/모멘텀누적곡선/모델설정, 관계망확대·본사/교역, Esri고해상도/지명(권한 질문 대기), SEC13F/연속수집, 직접글로벌NI/OP/PIT, OCR/LLM/팀공유DB/로그인 등 REFERENCE_PARITY의 남은 범위는 미완료다.
- [HANDOFF.md:245](../HANDOFF.md#L245) — 전략 카드 후속(2026-09-10): strategy_cards.py/strategy-cards.js/config strategy_screens.json은 턴어라운드의 연간3개년 이익 저점반등·흑자전환/4점근거/252종가 저점·고점·MA200·FY EPS·44점과 지정 US9/KR4 페어카드를 연결했다. 기존 분기흑자전환+8대형캔들과 퀀트 자동발굴 한국10쌍의 재사용은 전략 화면에서 교체했다. 퀀트 자체는 불변, 내부자/PEAD/실적모멘텀11개섹션은 객체 동일성 확인. 모듈 요약 스키마는 cards=[[label,value]]이며 별도 kpis 필드는 쓰지 않는다(재등장 검사 추가).
- [HANDOFF.md:249](../HANDOFF.md#L249) — 페어는252공통조정종가 로그OLS·120스프레드평균/표본sd1·252일수익ρ·130관측3간격44점, |z|내림차순/±2방향. 원본 미니선은 log(A)−βlog(B), 점선은 표시min/max중앙이며 z0/평균선아님. 미국9쌍은원본9/4가격β2자리/z2자리 모두일치, KR은정정/기준시각차이유지. 추가Engle–Granger 상수/maxlag5/AIC p값은I(1)/다중검정전진성과완료의미아님; p미통과도13지정자리를보존. 미확보/252미만/7일초과/상수/비양수β는표시구분. 지연/미래행/중복/정렬/분기혼용/점수경계 검사.
- [HANDOFF.md:260](../HANDOFF.md#L260) — 페이지300/20만자·회당OCR30/180s·최대8M화소, 해시/버전/언어/모드/배치/DPI 일치 완료페이지재사용 및 대기이어읽기, OCR실패파서보존, 취소시activecanvas해제, 백업메타검사/구버전호환. docs/index.html은pdf-text.js앞에pdf-ocr.js추가. 사진·PDF 원문·벤치마크·이미지는private runtime/pdf-ocr-fixtures. 상세research/PDF_EXTRACTION.md. 새로운시세/원본사이트요청0, raw빈티지20260910T040459Z/가격기준2026-09-08유지.
- [HANDOFF.md:267](../HANDOFF.md#L267) — PEAD 카드 후속(2026-09-10): 공식 S&P100 OEF 공시 주식101개 중 기존35재사용·66발표일 추가조회로101개 확보. pead_data.py는3일 이내 정상 earnings_dates 재사용, 실패 시 이전 정상값·조회시각 보존; 평일08/18 refresh에 연결했다. raw빈티지20260910T052642Z, 부모20260910T040459Z, 신규38258bytes. 시세/원본사이트 추가 요청0. 수집 당시 source_url 힌트 중 이전 /quote/.../calendar/ 형식이 있을 수 있으나, 공개 링크와 후속 수집은 공식 calendar/earnings?symbol= 형식으로 구성한다.
- [HANDOFF.md:278](../HANDOFF.md#L278) — 미국 옵션 수집·범위 후속(2026-09-10): 공개 설명의SPY GEX는7~50일·행사가±15%이며 전체시장전만기를 요구한 이전TODO를 바로잡았다. options_data 정규화는제공범위의모든만기/중복·경계검사, 별도주식수급은기존7~45일첫3만기 유지. 만기별OI/GEX집계·같은행사가ATM·수집당시현물/금리를사용하는과거체인처리와갱신상태표코드를구현. Cboe자동추출금지안내를확인하여index/stock/eventstraddle 두수집경로모두기본비활성화했고사용자허용API질문응답대기. refresh는설정boolean true만명시플래그전달,이번에권한설정변경없음. 다른Yahoo/KRX갱신은옵션중단으로실패하지않는다.
- [HANDOFF.md:284](../HANDOFF.md#L284) — 리스크 콕핏 후속(2026-09-10): allocation_views가 allocation_book(33상품 현재 ML 국면 목표비중·원점/적용월·기존96월 비용후성과)을 함께 내보내고, subview_modules에서 배분 계산 직후 risk_cockpit.views를 실행한다. macro_modules의 임의6ETF비중/단일SPY스트레스를 제거했다. 완료월 마지막SPY세션 정렬·BTC전날UTC·정규 월격자/결측무보간으로 현재비중120월 변동성/음수VaR·CVaR/MDD/HHI·BIL현금을 계산한다. 원점2026-08-31/적용9월, 표본2016-09~2026-08, VaR95 -4.304004%, CVaR95 -6.668368%, 변동성11.195272%, 월말MDD -22.546602%. 현재배분 비중·성과와 콕핏 외 위험그룹은 적용전후 동일 대조했다.
- [HANDOFF.md:288](../HANDOFF.md#L288) — 추가원본사이트/시세수집0·새raw0, 기존빈티지20260910T052642Z 유지. 옵션추가수집권한은 여전히응답대기이며 다른옵션GEX/OI/수급값은 변경하지 않았다. 공개JSON약7.894MiB/8. 콕핏9개 신규단위테스트·공개비중/원장/충격/분모검증 추가. 실제로컬Edge1440/1024/390에서4패널·33비중정렬·원장펼침/120월·ML30행·n0표시·하위탭왕복·페이지넘침0/JS오류0. 전체회귀228Python(146.162초)·두자료검증기·3JS회귀·30공개JS/MJS구문통과. 실행ID20260910T065158Z, 실제게시상태는runtime보고서/state.json 참조. 전체목표미완료: 다음리스크신호등/선제위험 세부 입력 및REFERENCE_PARITY의남은항목을계속할것.
- [HANDOFF.md:291](../HANDOFF.md#L291) — 신호등·선제위험 후속(2026-09-10): risk_signals.py/config risk_signal_rules.json은 US12/KR7 신호·시장요약·KR63세션/연속경계와 S&P500/KOSPI의 CSD/변동성군집4진단을 연결한다. 새로운2보조곡선은252관측·0–100축·40/66선·두계열이며원본옵션차트가아니다. 공개 대표임계값은유지하되비공개 다단계점수/기간/가중치·뉴스분모는팀설정/대용임을표시한다. 미확보/기한초과는회색·시장판정보류, 완전관측만KR경계6점이상연속집계하며결측/63세션경계하한을보존한다. 단위/수치6자리표시·출처/원관측일/실제성공시각/수집실패원장을추가했다. 연구정본research/RISK_SIGNALS_CONTRACT.md.
- [HANDOFF.md:299](../HANDOFF.md#L299) — 전체목표는계속진행. REFERENCE_PARITY의사업/공급관계255객체581관계·본사/교역·SEC13F/연속수집·직접NI/OP/PIT·LLM/공유DB와원본비공개계산/기간등은아직남아있다. Cboe허용API/자동수집권한질문은응답대기이며추가수집/새옵션범위공개는하지않았다. 새세션은사용자문의에분담방식만답했고생성하지않았다. 다음에는새확보지표의ML/MAXIMUS입력대응또는미완관계/교역을실제소스와재대조해진행할수있다.
- [HANDOFF.md:302](../HANDOFF.md#L302) — 교역 후속(2026-09-10): trade_data.py/trade_views.py/trade-views.js, config/trade_areas.json은 UN Comtrade45통계지역의2024년 상품 TOTAL 수출을 독립 수집·표시한다. 자료42지역/1840방향, RU/AE/VN 수출 응답은빈값이고 상대국의이들지역향수출은별개다. 미국842/프랑스251/스위스757/노르웨이579/인도699/UN490(S19)를 공식reporter/partner두사전과대조. UN490을대만전용통계로단정하지말것. World0 분모·원금액decimal문자열·보고/집계플래그를보존하며incoming도상대보고국수출이다. 원본교역금액은회사매출/특정품목/물리적항로가아니라국가TOTAL이었고이전TODO의품목필수조건을정정했다. 계약research/TRADE_CONTRACT.md.
- [HANDOFF.md:304](../HANDOFF.md#L304) — 정사영/10도경위선/대권곡선/지평선클립/방향삼각/로그굵기·상위10/20/전체·검색/UN코드/정렬·정확USD/분모/출처·포인터/키보드/휠/회전/확대·명시적자동회전/탭해제취소를연결. 기존기업소재국2섹션과다른계산은그대로다. 보존globe.js의별도SAURON은3D카메라·USGS지진·CelesTrak궤도·센서스타일/검색/투어기능이며기존DRAGONGLASS시설관측과다르다. 원본밸류체인20그룹/53업종/159배치/151기업/96도시와3관계선/본사/시총근거, SAURON을미연결subview로명시해후속에서누락하지말것.
- [HANDOFF.md:306](../HANDOFF.md#L306) — raw빈티지20260910T081012Z(부모20260910T070347Z), 초기지역별수출45요청(1회probe재사용+수집44)·코드사전3요청,원본사이트/시세/미국옵션추가요청0. 본수집전송8036094bytes+USprobe210532bytes,새raw약132KB,DATA약235.4MiB/512·공개JSON약7.98MiB/8. 평일08/18 refresh호출·30일지역캐시/180일코드·응답1MiB/500행거부·직렬2초·401/403/429후속중단. 동일값재확인은확인원장만추가하며실패/기존관측소실시전값/성공시각유지. 실제다시실행해45지역신규요청0확인. 공개/원자료예산한도변경없음.
- [HANDOFF.md:308](../HANDOFF.md#L308) — 전체249Python(234.791초)·두자료검증기·3JS모음·31JS/MJS구문통과. 후속교역12단위검사(기존10+응답바이트/정확소수·캐시미래시각2추가)와변경관련검사재통과. 단위fixture쓰기의사용자캐시전체용량탐색을mock해교역12검사는1초이내이며운영예산검사는유지. 실제Edge1440/1024/390에서양방향금액/서로다른World분모·지도선20/전체·44파트너·검색/정렬·포인터/드래그/키보드/확대/회전·탭왕복·45수집원장·페이지넘침0/JS오류0/외부요청0과지도실패시표대체확인. 최초collapsible필드명오류를collapsed로고쳐원장접기를검증. private runtime/trade-validation.log,trade-browser-qa.json,trade-cache-verification.json. 실제게시커밋/실행은runtime/state.json과발행보고서확인.
- [HANDOFF.md:310](../HANDOFF.md#L310) — 전체목표미완료: 다음은53업종기업등록·본사도시/사업및공급물류근거연결또는SAURON공개관측부터보존소스와대조. 모든종목의모호한시총순위/AI생성공급망문장을사실로복사하지않는다. 새세션/Claude는검증분담권장만안내했으며별도생성없음. 옵션권한질문여전히미응답.
- [HANDOFF.md:313](../HANDOFF.md#L313) — SAURON 후속(2026-09-10): sauron_data.py/sauron_views.py/sauron-views.js로 보존 원본의 Cesium 3D 카메라,22시설·USGS M≥2.5 지진·CelesTrak stations OMM/SGP4,3레이어/6색상효과/시설투어/지명검색/키보드/HUD/전체화면/관측원장을 연결했다. 효과는 실제 열·야간센서가 아니며 지진 스냅샷과 현재 UTC 궤도 계산을 분리한다. 원본의200km 최저고도 강제보정은 재현하지 않고 유효 실제 계산고도를 표시한다. 요소7일 초과/계산실패는 위치를 숨긴다.
- [HANDOFF.md:321](../HANDOFF.md#L321) — 게시 run 20260910T091629Z; raw 20260910T084457Z (부모 20260910T081012Z), 가격 2026-09-08. 실제 커밋/게시 완료는 runtime/state.json 및 해당 file-verification을 확인. 전체 목표는 미완료이며 REFERENCE_PARITY의53세부업종/151기업·96도시의 본사/사업/공급/수출/물류, 전체 관계망과 나머지 데이터·모델 범위를 계속한다. 새 세션은 검증 전담 방식만 권고했으며 생성하거나 Claude를 실행하지 않았다.
- [HANDOFF.md:324](../HANDOFF.md#L324) — 밸류체인 유니버스 후속(2026-09-10): chain_data/chain_geo/chain_views와chain-views.js로20그룹·53업종·159배치·151고유기업의탐색구조를연결했다. Yahoo프로필151기업·시총150(영국LSEG GBp단위미확인1제외), GeoNames정확도시매칭140기업/95도시. 나머지도시는근거확인전좌표없음. 프로필소재지를모든기업의공식글로벌본사검증이라고표현하지않는다. 공급관계는기존SEC NVIDIA10-K의4개만,소재국수출은기존2024 UN TOTAL상위5지역이며기업수출이아니다. 물류실측경로·전체경쟁우위/공급망근거는계속수집대상이다. 상세연구정본CHAIN_UNIVERSE_CONTRACT.md.
- [HANDOFF.md:330](../HANDOFF.md#L330) — 정사영·10도경위선·국가간대권곡선/금액별굵기·기업수별도시점·도시선택/기업선택·53바로가기/53표·관계근거3패널·마우스/키보드/확대/회전·이탈정리를구현. 실제Edge1440/1024/390에서151선택/159행·NVDA공급4관계·국내관계원장유지/지도3곡선·총수출5곡선·토글/도시/업종이동/드래그/회전/재진입/가로넘침0/JS오류0/외부요청0검수. 선택점이가까운다른도시에가려지는문제를마지막그리기와도시목록으로보완했다. 전체검사및실제게시완료는후속기록/runtime state로확인. 새세션은검증분담권장만안내했고생성하지않았으며Claude미실행이다.
- [HANDOFF.md:332](../HANDOFF.md#L332) — Claude관련후속확인: 로컬CLI auth status 읽기는성공했고로그인상태를확인했다. 인증값/계정식별자는출력·복사하지않았으며Claude에모델작업을보내거나새세션을생성하지않았다.
- [HANDOFF.md:337](../HANDOFF.md#L337) — 기업 공식 위치·관계 후속(2026-09-10): config/chain_evidence.json과chain_evidence.py로11기업의공식주소/10추가지명/18관계표시/5사업요약을연결했다. GeoNames500추출8지명과공식RDF2지명으로151기업105도시·행정대표점까지표시한다. 기존140도시매칭은유지했다. 더큰지명집전체교체시기존5기업이동명으로모호해지는것을확인해공식주소보정만추가했다. InditexArteixo등기/Richemont등기/Toyota아이치Honsha/SDI용인행정점과기흥건물구분,프로필국가·도시(미국주포함)가변하면보정중단. 전체공식글로벌본사검증은11기업범위를넘어완성한것이아니다.
- [HANDOFF.md:343](../HANDOFF.md#L343) — Edge1440/1024/390기업151선택/53표/159행·전11보정소재지·NVO3/MA3/SDI6관계·BYD기업공급1/물류1/토글/국가참고off→5·도시105/회전줌드래그/탭왕복·넘침0/오류0/외부요청0검수. 날짜라벨후속BYD1440/390검수. 단위14개·확장JS통과,전체회귀/게시완료는runtime/company-evidence-validation.json과runtime/state.json및발행보고서를확인할것. DATA검사시321.837MiB/512,공개JSON8.262MiB/10. 전체관계/공식본사/경쟁우위확장및REFERENCE_PARITY의남은세부기능은계속구현대상이다.
- [HANDOFF.md:352](../HANDOFF.md#L352) — 갱신 복구(2026-09-11): 수집1139시도/1138변경/1실패 이후 watch TRGP9/10 시가>고가로 엄격 OHLC 검사가 게시를 차단했다. Yahoo 표본1재조회도 동일, 전체 점검25건(미국주식/ETF 최근22건·영국주식 과거3건). cache.valid_ohlc로 불일치 일봉을 캔들·기술지표 입력에서 제외하고 원자료는 보존한다. 종가만 사용하는 가격 수익률은 제공처 보고 종가를 유지하며 관측일을 구분한다. 고저 범위를 넓히지 않으며 후속 공급처 정정 시 복원한다. price_quality.vendor_ohlc_exclusions·분석탭 원장·캔들 설명에 종목/일자/유효 관측일을 표시한다. raw빈티지20260910T222302Z를 오프라인 재계산해 추가수집 없이 검증·게시를 복구한다.
- [HANDOFF.md:356](../HANDOFF.md#L356) — DRAGONGLASS 리서치 후속: dragon_research.py/dragon-research.js로 관계 근거를 URL별 통합한 공식 문서·팀4방법론과 사용자 명시적 불러오기의 로컬 PRINCIPIUM 기록을 연결했다. 원문·날짜종류·객체태그/Entity360·출처/연결/검색·개인방향/기간/확신·첨부 내려받기를 제공하며 로컬DB 읽기만 사용한다. 가격상관은 문서근거가 아니므로 제외. 원본167편/비공개투자뷰/자동추론은 미확보; 지금 주목·트리거합류는 다음 작업이다. 수집·모델 추가호출0이며 기존08/18 build_all에서 카탈로그를 재생성한다.
- [HANDOFF.md:360](../HANDOFF.md#L360) — 리서치/용량 후속 검증 완료:281 Python·두 자료 검증기·3 JS 검사 모음·168 JS/MJS 구문 통과(158.531초), 후속 PNG 용량 조건 삭제는 두 검증기와 refresh 단위검사를 재실행했다. Edge1440/390에서 공개22편(공식18/팀4) 필터·검색·빈결과·Entity360·로컬1편/휴지통및IW제외·XSS·첨부원문동일·읽기전후revision동일·PRINCIPIUM제한표시삭제·넘침0/오류0/외부요청0 확인,390px이미지 육안검수. runtime/dragon-research-* 및storage-final-validation 보고서,게시후보run20260910T233752Z. 실제게시완료는state.json과dragon-research-publication/file-verification을 확인한다. 전체목표는미완이며지금주목·트리거합류와REFERENCE_PARITY의나머지기능을계속한다.
- [HANDOFF.md:362](../HANDOFF.md#L362) — DRAGONGLASS 신호 후속: dragon_signals.py/dragon-signals.js는 원본 watch/alert의 카드·규칙·순풍/경계·레이더·테마·크로스에셋·촬영 로그 구조에 기존 RS/발굴/ASK/지경학/관계/리서치/위성 데이터를 결합한다. 날짜일치·7일최대연령·미확보전체점수null·중복신호 방지·사업문서중복제거를 지킨다. 조회/LLM호출0이며 전체goal은미완. 원본live/전체기업뉴스/13F/정량뷰/임상/신규변화감지 및모든관계는후속. 공개동작/회귀/게시결과는추가검증기록확인.
- [HANDOFF.md:364](../HANDOFF.md#L364) — 신호 검증 완료:285 Python·두 자료 검증기·3 JS모음·169 JS/MJS구문 통과(112.247초). 최초검수에서 ASK 기간패널1/6/24개월과원본3개월혼동으로빈자산패널을발견,별도21자산원장3M열로수정하고실제값·날짜대조를추가했다. 기존전체보기검사의옛제목참조도새화면제목으로갱신했다. Edge1440/1024/390에서15카드/4동시신호/21자산상하위각3/8촬영로그·시장/검색/빈결과·기업/시설선택·근거펼치기·넘침0/JS오류0/외부요청0을확인하고1440·390이미지육안검수했다. 701기업/93후보,주도주30/발굴113입력중동일가격일60이며시점불일치는원장기록. raw빈티지20260910T222302Z유지·추가수집0. 게시후보run20260910T235826Z,실제커밋과Vercel검증은runtime/state.json및dragon-signals-publication/file-verification확인. 전체goal은미완이다.
- [HANDOFF.md:366](../HANDOFF.md#L366) — 임상 후속: clinical_data/clinical_views/clinical-views.js와clinical_scopes.json으로원본3범위ClinicalTrials.gov의모집/전체상태3상/최신5연구를연결. API버전시작종료일치·24시간캐시·버전같으면1조회·달라지면11조회·전체원자저장/실패이전관측/1시간백오프. 가격적재없는경로조회,원본사이트추가0·용량검사0. 원본검색식미공개로독립명시검색:모집비만1624/Lilly186/UNH0,3상890/709/5,전체16204/2897/38. 공식등록부dataTimestamp2026-09-10T09:00:04시간대미표기. 신규변화가아니며신호점수가산없음. 전체회귀/실제게시상태는후속검증/runtime보고서확인.
- [HANDOFF.md:369](../HANDOFF.md#L369) — raw20260911T001009Z(부모20260910T222302Z),가격9/10유지. 공식API수집11요청·재실행0;별도탐색version1/모집1/공식OAS4041 및웹문서조회는수집카운트와구분. 원본사이트요청0. 게시후보run20260911T001604Z,실제commit/state/clinical-publication/file-verification확인. 전체goal미완;13F·기업뉴스감성/관심도·정량뷰·전체관계및임상별변화이력등계속구현대상.
- [HANDOFF.md:372](../HANDOFF.md#L372) — 용량 검사 완전 제거 후속: 사용자 재지시에 따라 남아 있던 다운로드 응답·압축 해제·SEC XML·지도 타일·PDF/OCR 설치·위성 요청별/실행별 바이트 상한도 제거했다. 총용량 순회/저장 한도 없음. 형식·해시·HTTP Range 일치와 필요한 관측 구역 읽기, 요청 간격·캐시·실패 시 이전 자료 보존은 유지한다. 기존 크기 거부 테스트는 실제 대형 응답 허용·내용/프로토콜 검증으로 갱신했다. 전체 검사와 게시 결과는 runtime/no-size-validation.json 및 runtime/no-size-publication.json을 확인한다. 전체 세부탭 목표는 미완이며 이번 작업은 용량 검사 제거다.
- [HANDOFF.md:375](../HANDOFF.md#L375) — 13F 후속: guru_data/guru_views/guru-views.js와6보고법인 설정을 추가했다. 원본6구루카드·상위6포지션 구조/보고일/원문과235행 전체원장·CUSIP/종류/PUTCALL검색을 연결했다. SEC 직접 Archives XML1요청403(이전submissions403) 후 중단; 브라우징으로 공식표6개를 확보해코드로파싱하고private보존. 최초95/1/89/15/8/27행→95/0/29/14/8/27포지션. Thiel0원placeholder·Scion2025-09-30지연·Pershing기존1336528 NT→모회사2026053범위를명시. Duquesne표합5210856/표지5210860=-4차이를유지하며보고금액의단위규모추가검토를표시,임의1000배보정없음. 나머지5합일치.
- [HANDOFF.md:377](../HANDOFF.md#L377) — 새raw20260911T004356Z(부모20260911T001009Z),가격2026-09-10/Overview바이트불변. 새source별vintage만status.supplemental_vintages.guru에표시,가격status.vintage는유지. 신호+3은CUSIP기업대응/분기시차검증전보류하며기존4동시신호불변. 확인공시는최신전체조회아님. 코드정기08/18에연결,private runtime/sec-contact.json의email필요(질문응답대기);없으면0요청,403시같은설정재요청보류·24h정상/오류캐시·신규accession만수집·이전자료보존. 원본사이트0요청/용량검사없음.
- [HANDOFF.md:379](../HANDOFF.md#L379) — 299Python·두자료검증기·3JS회귀·171JS/MJS구문통과. Edge1440/1024/390에서6카드/18필터조합/235원문행·검색/빈값/옵션·NT/0원/단위차이·탭왕복·가로넘침0/오류0/외부요청0검사,390px이미지육안확인. 정본research/GURU_CONTRACT.md 및runtime/guru-source-verification/guru-browser-qa/guru-validation.json,게시후보20260911T004834Z. 실제게시완료는runtime/state.json과guru-publication.json을확인한다. 전체goal미완:13F연속과거/최신확인/기업대응/구루뉴스16인관리·전체뉴스감성/관심도·정량뷰·나머지관계등은계속구현대상.
- [HANDOFF.md:382](../HANDOFF.md#L382) — 13F 식별자 후속: guru_identifiers.py는OpenFIGI 공식공개API의CUSIP/exchCodeUS를5개씩3초간격조회. 공식iShares기존CSV에CUSIP없음을확인하고초기5진단응답재사용+148개/30배치=153개관측을확보(140단일/13미확보). 30일정상/7일미확보캐시·실패이전성공시각/원자료보존·401/403/429후속중단·1시간오류백오프. 재실행0요청. 동일CUSIP다중FIGI는거부,티커정확일치와주식종류구분자변환만사용,기업명유사도0. 기업주식/ADR/REIT/NYregistered/MLP와SH만허용하며ETP/폐쇄형펀드제외.
- [HANDOFF.md:388](../HANDOFF.md#L388) — 정본GURU_CONTRACT.md,private guru-identity-collection/source-verification/build-verification/validation.json. 게시후보run20260911T010319Z,실제커밋/배포는state.json과guru-identity-publication.json확인. 전체goal미완:유니버스밖종목·미대응식별자·최신/연속13F·구루16인관리/뉴스·기타REFERENCE_PARITY세부기능계속.
- [HANDOFF.md:391](../HANDOFF.md#L391) — 데이터 소스·현황판 후속(2026-09-11): dragon_operations.py/dragon-operations.js로19소스5분류의카드·상태집계·날짜/단위원장·필터/검색과23모듈기준일/생성시각/이동을연결. RSS7/임상/13F/FIGI/위성/지진/궤도/교역/기업프로필/거시제공처를명시적으로투영하며private설정/키/원문오류본문은읽거나게시하지않음. SEC검토공시6법인을자동조회정상으로표시하지않음. 소스별시도/성공/관측일구분·날짜만있는거시수집시간미확인·일부실패이전값있어도오류·USGS1h/궤도2h코드캐시를평일08/18주기와구분.
- [HANDOFF.md:395](../HANDOFF.md#L395) — 309Python·두자료검증기·3JS회귀·172JS/MJS구문통과(152.760초). Edge1440/1024/390에서19소스날짜/계열수·5분류/5상태/검색/빈결과·23모듈/7계열/4기간·RS왕복·예정KST/타이머0복귀·가로넘침0/오류0/외부요청0통과. 390현황/소스이미지육안확인. 기존legacy journal가져오기의1MB와500건제한잔여를제거;최종JS회귀및구문재통과. 원본사이트/신규외부수집/모델호출0,용량검사0,가격Overview바이트동일. raw빈티지20260911T005706Z/가격2026-09-10유지. 게시후보run20260911T012438Z;실제커밋/배포는runtime/state.json,operations-publication.json및operations-browser-qa/validation/build-verification.json확인. 전체goal미완이며REFERENCE_PARITY잔여작업계속.
- [HANDOFF.md:398](../HANDOFF.md#L398) — 기업 관심도 후속(2026-09-11): 원본attn10기업의영문Wikipedia기업문서구조를대조하고MediaWiki제목API1회로정규제목/pageid/Wikidata확인(ASMLHolding→ASML). WikipediaPageviews all-access/user 일별UTC를초기60일/이후7일겹침정정으로수집. NVIDIA초기61일probe재사용+나머지9요청=10문서601일관측;재실행0요청. 관련API공식문서검토는별도. 최근7일9/3~9/9 vs직전7일8/27~9/2,10가용/+40%0문서. 원본비교기간미공개로팀규칙명시,전체뉴스/검색/고유투자자/감성아님.
- [HANDOFF.md:402](../HANDOFF.md#L402) — 첫브라우저검사에서ASML에Entity없음을발견. ASML1종목가격history를기존수집기로받아3년752일·USD·OHLC유효확인. 실제마지막9/9를9/10으로늘리지않음. ASML추가관찰(공식S&P500편입아님),Entity702·원장702상관재계산(합집합252일창/ASML245유효관측). 공식700+TSMC/ASML2. 가격추가갱신대상에attention_pages를포함. 재무/일정미확보는비움. 기존13F57기업73포지션유지,가격Overview바이트동일.
- [HANDOFF.md:404](../HANDOFF.md#L404) — 최종314Python·두자료검증기·3JS회귀·173JS/MJS구문통과. Edge1440/1024/390에서10문서/601원장/각60점·기간수치·검색/빈값·모든Entity이동/원문/신호3규칙/기존4합류·Wikimedia소스·가로넘침0/오류0/외부요청0통과.390이미지육안확인. 초기수치검증에서ASML대각관측수를무조건252라고둔검사전제를245로정정(전체시장합집합창에비거래일포함),source시각원장확인. raw20260911T013531Z(부모20260911T005706Z),가격기준9/10. 최종게시후보run20260911T014736Z. 정본ATTENTION_CONTRACT.md;실제배포는state.json/attention-publication.json과attention-validation/browser-qa/build-verification/asml-verification확인. 원본사이트추가0,새AI세션0. 전체goal미완:전체기업뉴스/감성/정량뷰·13F연속/관계확장·REFERENCE_PARITY잔여계속.
- [HANDOFF.md:409](../HANDOFF.md#L409) — 25스냅샷 287750숫자·11055식별자/URL 불변·225표시 문자열 변경 검증. 315Python·두 자료 검증기·3JS회귀·173JS/MJS구문 통과. Edge1440/1024/390에서25주화면·137공통하위그룹·기업이동·현황 모듈명·위성사진·탐색 검사, 기존390px 종목발굴 점수/자산배분 막대 가로넘침2곳만 CSS수정후 전범위 재통과. JS오류0/외부요청0/옛 표시명0/가로넘침0. 실제 수치/차트 구조/저장기록 유지, 전체 세부기능 목표는 여전히 미완. 가격9/10·raw20260911T013531Z 유지. 정본 UI_NAMES.md, runtime/names-build-verification/validation/browser-qa.json 및 names-followup-validation.log. 실제 게시 완료는 state.json/names-publication.json을 확인한다.
- [HANDOFF.md:412](../HANDOFF.md#L412) — 2026-09-11 관계 대조/시차 후속: 보존된 관계지도 edge_insights의3M·비연결12/부호불일치8/일치6·동일시장시차8행구조를오프라인대조. relation_discovery.py/relation-discovery.js로22기업(US20/KR2),231무순서상관쌍·1146방향/시차를독립계산. 3달전초과~가격기준9/10,SPY63세션6/11~9/10,KOSPI63세션6/11~9/9(실제공급일). 조정종가/시장달력재배열후수익률·시차생성,45개최소/7일최신/결측미채움. 비연결|상관|>=.6의36쌍을그래프에연결,사업30/총66관계·부호일치6/불일치5. 과거252일/기업별최대연결방식대체. 기존702원장행렬/기본8시나리오/중심성/기업/13F/문서관심도/가격Overview는불변.
- [HANDOFF.md:416](../HANDOFF.md#L416) — 최초검증기는예전그래프최소200일계약으로차단; 새명시적3개월/45개메타를추가하고별도분기검증. 원장200개검증은유지. 321Python(독립statsmodelsF일치/방향/결측시차비압축/미래불변/상수·시차달력오래됨/재실행중복방지포함)·두검증기·3JS모음·174JS/MJS구문통과. Edge1440/1024/390에서3열/요약/전체36+45/검색/1146원장날짜·rho·q/22기업이동/36상관선/전파옵션/현황66관계·왕복/가로넘침0/오류0/외부요청0확인,모바일/데스크톱이미지육안확인. raw20260911T013531Z/가격9/10유지. 정본RELATION_DISCOVERY_CONTRACT.md와runtime/relation-discovery-build-verification/validation/browser-qa.json;실제게시commit/state는relation-discovery-publication.json확인. 전체goal미완:원본136가격기업/255객체581관계전체·OOS/PIT·기업뉴스/기타REFERENCE_PARITY잔여계속.
- [HANDOFF.md:417](../HANDOFF.md#L417) — 2026-09-11 기업 뉴스 후속: company_news.py/company-news.js와23기업 RSS설정으로 기업분석의 지금 주목·기업 상세·신호 합류·소스 운영을 연결했다. Yahoo Finance 종목별 RSS 최초1응답 재사용+22요청,23피드 정상; 재실행0요청. 정규화426관측 중 가격기준2026-09-10까지 최근7UTC일381피드항목/중복URL제거317기사. 이후 날짜 기사는 원자료에 보존하되 집계에서 제외한다. 종목 연관 피드이므로 해당 기업만 다룬 기사/전체 뉴스라고 표시하지 않는다. 감성·전체종합점수·live·기대수익은 미산출을 유지한다.
- [HANDOFF.md:419](../HANDOFF.md#L419) — 24h캐시/1초간격/1h오류백오프/401403429후속중단/실패시직전성공보존. XML형식/타임존날짜/HTTPS링크/URL중복/원문SHA검증, 저장·전송 크기상한 없음. 원문XML은 private SHA별보존, 기사 URL별 최초/최근관측 보존. 최신36h 성공·오류없음·기간내8건이상 표본 관측만+1로 연결:23피드충족/표시합류16기업/7규칙중4연결. 관심도와뉴스 관측일은 가격일과 구분한다. 소스카드21개, 기존08/18 refresh에수집연결. 가격·관계·관심도 결과 불변. raw20260911T024219Z(부모20260911T013531Z), 게시후보run20260911T024911Z.
- [HANDOFF.md:421](../HANDOFF.md#L421) — 326Python·두자료검증기·3JS회귀·175JS/MJS구문통과(124.742초). Edge1440/1024/390에서23피드/381항목·검색/필터/빈결과/펼치기·23기업상세·16합류/4규칙·원문링크·소스카드/가로넘침0/오류0/외부요청0 확인,390px육안검수. 원문426행과날짜별381게시항목 직접대조/SHA일치. 정본COMPANY_NEWS_CONTRACT.md, runtime/company-news-collection/reuse/source-verification/build-verification/validation/browser-qa.json; 실제게시commit/state는company-news-publication.json 확인. 원본사이트추가요청0/새AI세션0. 전체goal미완:뉴스다중제공처·감성·정량뷰·최신/연속13F·전체관계와REFERENCE_PARITY잔여계속.
- [HANDOFF.md:423](../HANDOFF.md#L423) — 2026-09-11 퀀트5세부화면 후속: 보존 quant.json/방법설명/페어PNG10개와 대조하여 기존 임의160유동성·회귀잔차·EG조건을 가격비/Hurst 전체표본 선별로 교체했다. 원본 사이트/추가 수집/모델/AI세션 호출0, raw20260911T024219Z·가격9/10 유지. quant_modules는 quant_screens의기존진입점이며08/18전체빌드에연결된다. 359한국표본·353가격준비·62128쌍→상관1572/Hurst1143→10페어. 252시장일z선·0/±2·마지막점·조건/방향/반감기·원장,8팩터통과100/상위15막대/기여·전체359통과/제외, BAB41Long/70Short 분포·역Beta검산,TSMOM12관측/막대·반전8개를연결한다.
- [HANDOFF.md:425](../HANDOFF.md#L425) — 초기 엄격253일조건에서352개가제외되어원가격조사:2025-09-19가대부분종목에누락되어있음을확인. 시장달력을삭제하거나일수익을압축하지않고 최근127일·252일전기준점필수/최근253일가격최소220·실제결측일·일수익관측수를명시했다. 결측팩터0채움제거;완료12개월안정성·복리5D수익z. BAB가격일과Beta종료/관측수분리(KOSPI실제9/9). TSMOM달력12/3개월전이하최근가격·기준일원장,금리는상대변화만/노출null,crypto365·나머지252연환산. 원본명시6+팀추가6구분. 정밀평균/표준편차문자열보존으로화면반올림후역산오차제거. Hurst후보는NumPy배열선별하고상세OU는최종선택만계산;전체자료적재포함약34초. 전체원본PIT/비공개설정·비용후성과는미완이다.
- [HANDOFF.md:427](../HANDOFF.md#L427) — 333Python·두자료검증기·3JS회귀·176JS/MJS구문 초기전체통과. 마지막Beta/TSMOM날짜원장 추가 및 외부에서병합된시장종합디자인910dbbb를보존한새stage20260911T032411Z에서전체재검증한다. 정본결과runtime/quant-screens-validation.json의run_id/status를확인할것. Edge1440/1024/390에서5그룹·10곡선점직접일치/±2·515원장행·검색/정렬/빈결과/펼침/왕복·가로넘침0/오류0/외부요청0,이미지육안검수. 원가격10페어/모든252차트점·100팩터점수독립검산,다른22JSON바이트불변. 정본QUANT_SCREENS_CONTRACT.md;runtime/quant-screens-source-verification/build-verification/browser-qa.json과실제게시quant-screens-publication.json/state.json확인. 전체goal미완이며REFERENCE_PARITY잔여계속.
- [HANDOFF.md:433](../HANDOFF.md#L433) — 2026-09-11 시장 역학 후속 및 최신 디자인 통합: dynamics_model.py/dynamics_validation.py/dynamics-views.js로18대상·표면60개월×8기간·위상36개월·위험60개월/65음영·월이력최대144·실제 거래일을 연결했다. β21일/α5일/∇τ후방차분·확장창252/ddof0·전일노출·결측보존을 명시. 표면 재생/정지/초기화/이탈 타이머 정리, 비용0/5bp/5bp+연3%/10bp+연5%의4가정·동일기간2곡선·최근252일 거래/비용원장·BOM CSV를 제공한다. 드리프트 후 비중 기준 거래비용·최초매수비용·차입비용·자본소진 중단을 계산. 누락 가격/신호 뒤 마지막 연속 유효 구간만 평가해 한국5종목은209거래일이며 전체 이력을 연결한 성과라고 표시하지 않는다.
- [HANDOFF.md:437](../HANDOFF.md#L437) — 원본 사이트/새 데이터 수집/모델/새 AI세션 요청0. raw20260911T024219Z·가격9/10 유지(KOSPI실제9/9), stage20260911T034033Z. 계산은 기존 평일08/18전체빌드에 연결. 정본DYNAMICS_CONTRACT.md 및private runtime/dynamics-source-verification/build-verification/browser-qa/validation.json. 실제 게시 commit은dynamics-publication.json/state.json 확인. 전체goal미완: 수식/전체캡처·선택링크공유, 원자료결측/PIT·실제비용과REFERENCE_PARITY의나머지 세부기능 계속.
- [HANDOFF.md:440](../HANDOFF.md#L440) — 2026-09-11 시장 역학 내보내기 후속: 보존 원본 app.js 1340~1390의 캡처가 전체 페이지가 아니라 수식+현재3D표면 PNG임을 재확인했다. dynamics-export.js는 현재SVG/계산식/종목/실제가격일·최신신호일·표면기간/단위를 2배PNG로 저장한다. 현재카메라/기간/결측면/따뜻한색을 보존하고 실제팀계산 후방차분·21일·확장252·전일노출을 설명한다. 과거표면의표식은‘선택 시점’, 마지막은‘최신’으로 정정했다. 별도전체페이지 캡처가 원본요구라는 이전기록은폐기한다.
- [HANDOFF.md:444](../HANDOFF.md#L444) — 검증: Edge1440/1024/390 각각18링크, 데스크톱18PNG/태블릿2PNG/모바일2PNG 실제파일시그니처·1800px폭·그려진종목/수식/각날짜·과거표식·표면좌표불변·클립보드거부·toBlob실패·변환중이탈·URL해제 확인. 오류/외부요청/문서가로넘침0, 삼성전자390PNG한글·수식·기울기와기간 육안확인. 정확한최종전체회귀결과는runtime/dynamics-export-validation.json,브라우저결과dynamics-export-browser-qa.json. stage20260911T040404Z/가격data_run20260911T034033Z/raw20260911T024219Z. 실제게시commit은dynamics-export-publication.json/state.json 확인. 정본DYNAMICS_CONTRACT.md/REFERENCE_PARITY,전체goal미완이며나머지세부기능계속.
- [HANDOFF.md:453](../HANDOFF.md#L453) — 검증: 6개추가Python검사(캐시/수정/실패/확률/부분집계/미래기사/날짜시차1점),전체346Python·두자료검증기·3JS모음·구문통과(151.01초). Edge1440/1024/390각23피드/381라벨·확률·평균·필터·펼침/23기업상세·5규칙·소스22·가로넘침0/오류0/외부요청0,390이미지검수. 원문/캐시381값전수일치,12제목별도batch+float64softmax재계산최대오차1.41e-7/3라벨포함,비영문·602토큰미분류검사. runtime/news-tone-collection/reuse/build-verification/source-verification/browser-qa/validation.json,실제게시는news-tone-publication.json/state.json. 정본NEWS_TONE_CONTRACT.md. 전체goal미완:다중제공처/전체기업·기업별문맥감성·정량투자뷰·최신연속13F·전체관계/팀DB등REFERENCE_PARITY계속.
- [HANDOFF.md:458](../HANDOFF.md#L458) — Nasdaq 디렉터리1회로ALAB/ARM/CRWV/ENTG/NBIS의공식종목명·TestIssue=N/ETF=N 확인, DART로008930 식별. 기존Hanmi는KOSPI200이며중복추가안함. 신규미국5Entity→공식700+추가7=707. 지수편입/업종확정으로간주하지않고추가관찰/RS·재무·예정실적미확보유지.4가격history(ALAB621/CRWV365/ENTG753/NBIS473)초기수집·ARM/Hanmi기존재사용,뉴스설정종목의가격유지갱신을08/18 incremental에추가. 상장확인URL/시각/공식종목명 표시.
- [HANDOFF.md:464](../HANDOFF.md#L464) — raw20260911T043351Z(부모20260911T041510Z),stage20260911T044500Z,가격9/10. runtime/news-universe-source-verification/build-verification/browser-qa/validation.json과실제게시는news-universe-publication.json/state.json. COMPANY_NEWS_CONTRACT.md/RELATION_CONTRACT.md정본. 최신디자인8c0adfd유지·용량검사0.전체goal미완:비기업20객체뉴스/다중제공처/기업문맥감성·신규기업재무일정·정량뷰/관계확장/연속13F/PIT및REFERENCE_PARITY계속.
- [HANDOFF.md:471](../HANDOFF.md#L471) — 원자료213기업5291재무값·기간/통화전수일치,40기업금융요약·37일정/90일컷오프독립대조,다른22JSON바이트불변. 6새단위검사포함353Python·두자료검증기·3JS모음·전체JS구문통과128.146초. Edge1440/1024/390 각각40기업재무/예정·40기업연간/분기3차트1067막대좌표/단위·213선택목록·검색/빈결과·새소스2·가로넘침0/오류0/외부요청0확인. ASML390분기EUR단위3패널육안확인. 한국일정/전체707재무·직접NI/OP컨센서스/PIT등미완.
- [HANDOFF.md:476](../HANDOFF.md#L476) — 2026-09-11 주제 뉴스 후속: 보존된 비기업20객체(테마9/국가2/지정학5/정책4)의 탐색 화면을 추가했다. 자체20검색식/제목 일치 기준을 공개하고 GDELT API 검색 결과와 기존 기업·정책 RSS 제목 일치 표본을 별도 집합으로 표시한다. 현재 GDELT 실조회는429와 간격을 둔 TLS ReadTimeout으로0/20 미확보이며, 미확보를0건 성공으로 표시하지 않는다. 기존 캐시에서는11주제23기사/23고유URL이 일치하고9주제는 이 표본에서0건. Google RSS 시험 응답은 private에만 보존하고 게시/분류/추가수집에 사용하지 않았다.
- [HANDOFF.md:480](../HANDOFF.md#L480) — 전체360Python·두자료검증기·3JS모음·전체JS구문 통과122.423초. Edge1440/1024/390에서20주제·두집합·4분류·검색/빈값·날짜/원문/일치어/톤·펼침·이동·소스카드 확인, 오류/외부요청/가로넘침0. 390이미지 육안 확인. 독립 원자료/캐시 검사23기사 전수일치, 기존 회사뉴스/기업/신호/관계 보존 및 다른23JSON 바이트 불변. raw20260911T052309Z(부모20260911T050000Z),stage20260911T052857Z,가격9/10. 정본TOPIC_NEWS_CONTRACT.md; 실제 게시는runtime/topic-news-publication.json/state.json 확인. 디자인 작업 최신8c0adfd가 메인 조상임을 재확인하고 production의3개 디자인 자산이 로컬과 바이트 동일함을 검증했다. 전체goal미완:20실검색·다중제공처/전체관계/정량뷰/연속13F 등 REFERENCE_PARITY 계속.
- [HANDOFF.md:483](../HANDOFF.md#L483) — 2026-09-11 전력 구매계약 관계 확장: 공식 발표6문서(계약5/Crane 후속1)를 웹 도구에서 검토해 Constellation→Microsoft/Meta,Vistra→Meta,NextEra→Alphabet(Google),AES→Microsoft5관계를 추가. 공용계통 구매/예정/현재가동미확인과 기술협업을 구분. Crane835MW20년·최초2028→후속2027목표,Clinton1121MW20년/2027-06개시(30증설중복금지),Vistra2176+433=2609MW20년/2026말~2034단계,DuaneArnold시설615MW25년/Google배분미확인(CIPCO잔여),AES3사업475MW/개별계약MW·기간·현재가동미확인. 시설MW를계약MW·실송전·매출·가정전달계수로바꾸지않음. 사업가정powers0.28/0.62·weight1유지. 원본요청/새모델/시세추가수집/용량검사0.
- [HANDOFF.md:487](../HANDOFF.md#L487) — Meta/Vistra/NextEra/AES4기존공식기업을관계노드에추가,39→43객체/30→35사업관계/22→26가격기업. 325쌍(이전231상관값불변),1662동일시장방향/시차회귀와전체BY재계산;76탐색후보/보정통과0. 707기업상세·원장행렬·회사/주제뉴스·관심도·위성·23다른JSON불변. 공식리서치카탈로그6URL추가(후속발표포함),신호점수는기존관측규칙이고문서/관계수동점순위만재계산. 새기업공식지수편입이나실제수익률예측주장없음.
- [HANDOFF.md:489](../HANDOFF.md#L489) — 5새단위검사포함365Python·두자료검증기·3JS모음·전체JS구문통과128.032초. Edge1440/1024/390마다43노드/5계약·기간/계약/시설MW·미확인·원문/날짜·필터/검색/기업이동·8시나리오·리서치6문서·운영소스/왕복·오류0/외부요청0/가로넘침0. NextEra390화면육안검수. 원자료325쌍독립검산·계약5수치·4원문해시·707보존검사통과. raw20260911T054825Z(부모20260911T052309Z),stage20260911T055052Z,가격9/10. 정본POWER_RELATIONS_CONTRACT.md, runtime/power-relations-source-verification/build-verification/validation/browser-qa.json;실제게시는power-relations-publication.json/state.json확인. 최신디자인유지. 전체goal미완:원본전체관계/계약연속이력·Talen기업가격/전체뉴스·13F/PIT등REFERENCE_PARITY계속.
- [HANDOFF.md:498](../HANDOFF.md#L498) — 독립검산:5778상관/관측수전수,이전1662검정의p/F/관측기간불변(q/보정통과는전체집합변경),statsmodels별도OLS124건(모든보정통과포함)F/p검산. 원본159별칭집합·107기존기업명/시장전수대조. 4새단위검사포함최종369Python·두자료검증기·3JS모음·전체JS구문통과146.824초. 초기전체회귀171.006초통과후모바일원장표시수정에따라재검증. Edge1440/1024/390마다108기업선택/125노드/107범위행/별칭검색/전체25386검정200행·이전/다음/BRK-B검색540행3페이지중복누락0·빈값·기업이동·8시나리오·왕복·오류0/외부요청0/가로넘침0. 최초QA는details의비동기toggle후행생성을기다리지않아0행으로실패,행생성대기후통과. 그래프1440와최종390원장육안확인.
- [HANDOFF.md:500](../HANDOFF.md#L500) — raw20260911T054825Z/가격9/10유지,stage20260911T060314Z. runtime/relation-universe-source-verification/build-verification/validation/browser-qa.json및실제게시는relation-universe-publication.json/state.json확인. 정본RELATION_UNIVERSE_CONTRACT.md/REFERENCE_PARITY. 전체goal미완:49미연결표기·외국시장달력/추가가격/기업상세·전체사업관계·GDELT20실검색·13F/PIT/팀공유등계속.
