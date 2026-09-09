# 정기 갱신 운영

사용자 승인: 한국시간 평일 08:00·18:00, 이 PC에서 수집·검증·Vercel 게시. 로컬 데이터 최대512MiB. 예약은 Codex 앱의 자동화에서 관리한다. PC가 꺼져 있거나 앱이 실행 중이지 않으면 정시 실행을 보장하지 않는다. 거래 기능은 없다.

## 실행과 저장 위치

저장소에서 `python -m pipeline.refresh --publish`를 실행한다. `--offline`은 마지막 정상 빈티지로 계산·검사만 한다. `--force-models`는 주간 모델 갱신을 앞당기는 점검용 옵션이다.

- `../sangsangin-investment-data/expanded/<run_id>/`: 원자료의 변경분, 부모 빈티지, 해시.
- `../sangsangin-investment-data/runtime/config.json`: 로컬 설정. KRX 인증 허용 여부, 기존 ECOS 키 파일 경로, 기존 컨센서스 DB 경로, 이벤트 기업 수60. 키·경로·DB는 Git에 올리지 않는다.
- `runtime/state.json`: Vercel 게시 확인을 마친 빈티지.
- `runtime/<run_id>.json`, `.log`: 결과·오류, 외부 공개하지 않음.
- `runtime/staging/`: 최근 계산·검사용 프로젝트 복사. 오래된 복사만 정리하며 원자료 빈티지는 보존한다.
- `runtime/pending_publish.json`: 푸시 또는 Vercel 확인 대기. 다음 실행은 동일 커밋의 게시를 먼저 재시도한다.
- 공개 `docs/data/refresh.json`: 마지막 검증 시각, 기준일, 수집 건수. 홈페이지에서 확인한다.

## Vercel 연결

Vercel CLI59.13.1을 별도 로컬 도구 폴더에 설치했다. 최초 사용자 계정 인증과 `.vercel/project.json` 프로젝트 연결이 필요하며 이 파일과 `.env.local`은 Git에서 제외한다. 설정의 `vercel_cli`·`node_executable`은 로컬 실행 경로이고 `publish_target`은 `vercel`이다. `site_url`은 확인된 운영 도메인으로 설정한다. GitHub OAuth 연결 없이도 이 PC의 CLI 인증으로 배포할 수 있다.

`vercel.json`은 Other 프레임워크, 빌드/설치 명령 없음, 출력 docs다. 예약 실행은 검증된 정적 파일만 `.vercel/output/static`으로 복사하고 Build Output API v3의 `deploy --prebuilt --prod`로 배포한다. Python·KRX/ECOS 인증·컨센서스 DB를 Vercel에 올리지 않는다. 공개 결과 JSON은 갱신 확인이 가능하도록 재검증 캐시 정책을 사용한다.

수집 중단 후에는 `--resume-run <미완료 빈티지>`로 같은 부모의 완료된 수집 결과를 재사용할 수 있다. 정상 게시가 확인된 빈티지 자체에는 재수집하지 않는다.

근거: [Vercel 정적 빌드](https://vercel.com/docs/builds), [Build Output API](https://vercel.com/docs/build-output-api), [CLI 배포](https://vercel.com/docs/cli/deploy).

## 수집 주기

| 데이터 | 주기 | 범위·저장 방식 |
|---|---|---|
| 가격 | 매 실행, 완료 세션만 | 이전35일 겹침을 대조한 변경 행. 신규 구성원은 회당최대25종목의3년 이력 |
| 미국 IVV·한국 공식 구성/업종 | 7일 | 공식 목록 보존. 개별 종목의 확보/제외 사유 표시 |
| FRED·ECOS | 매 실행 | 바뀐 계열만 새 CSV 보존, 기존 수정 빈티지 유지 |
| 재무·로컬 QuantiWise | 7일 | 압축 JSON. DB를 읽기만 하며 DB 자체를 외부에서 갱신하지는 않음 |
| 미국 발표 일정·내부자·EPS 추정 | 3일 | 확보된 미국 재무 종목 중 시총상위60개, 4종 API |
| RSS | 매 실행 | Fed·ECB·BIS·WTO·IMF·BBC World·DW의 제목/시각/링크. 실패 제공처 표시 |
| CFTC TFF | 7일 | S&P500/Nasdaq/미국채10년·2년 선물, 최근2년, 최대1000행 |
| 미국 옵션·수급 | 매 실행 | Cboe ETF3·주식20(7~45일 첫3만기), Yahoo공매도·등록LETF50개 AUM; 기준일/coverage검사 |
| 한국 수급·ETF | 매 실행 | 승인된 KRX인증, 현재 대형주상위8의5D투자자매매량·전ETF 현재/1M전 NAV·순자산 |
| 실적 ATM스트래들 | 매 실행 | 보유달력의 향후21일중가까운8종목, 발표 후 첫만기 동일행사가·호가/OI검사 |
| 거시 발표 일정 | 7일 | FRED8종 releaseID + BEA 공식90일; Central/Eastern DST→KST, 오류/시간미상 표시 |
| ML·MAXIMUS | 7일 또는 월 변경 | 마지막 완료 월부터 계산. 모델의 별도 기준일 유지 |

가격 기준일은 오전 실행에서 전일, 오후6시 실행에서 당일이다. 각 종목에는 거래소 현지18시 이후의 일봉만 허용하고, 주말을 제외한다. 휴일은 실제 반환 관측으로 처리한다. 암호자산은 완료된 UTC 일봉만 사용한다. 따라서 한국 저녁에 미국 장중 가격을 넣지 않는다. 과거 실제 발표 시점 빈티지가 없는 거시·컨센서스는 실시간 PIT 자료로 주장하지 않는다.

## 검증과 실패 처리

중복 실행은 Windows 파일 잠금으로 차단한다. 수집 이후 기존 공개 사이트와 분리한 복사본에서 모든 탭을 계산한다. Python 계산 검사, 자료별 날짜·OHLC·그룹·단위 검사, JavaScript 전체 섹션 렌더링·구문 검사를 모두 통과해야 게시한다.

가격 API 실패가20건 이상 시도 중10%를 넘거나, 최신 가격 확보가 직전 대비3% 이상 감소하면 중단한다. 파일 해시 오류·예산 초과·계산/검사 오류도 중단한다. 실패한 계산 결과를 공개 폴더에 덮어쓰지 않는다. 작업 트리가 수정 중이면 코드를 자동 커밋하지 않는다. 깨끗한 작업 트리에서 검증된 파생 JSON·상태·생성 문서만 커밋하고 기존 Git Credential Manager로 푸시한다. 이어서 정적 파일만 Vercel Build Output API v3 패키지로 배포한다. 실제 Vercel의 갱신 JSON이 로컬 파일과 일치해야 정상 게시로 기록한다.

모든 API 실패를 자동으로 해결할 수는 없다. 실패 시 로컬 로그를 확인하고 같은 명령으로 재시도한다. 최신 데이터가 없는 종목/옵션/지표는 개별 날짜와 미확보 범위를 확인한다. QuantiWise 원본 DB가 오래되었으면 수집 실행일이 새로워도 컨센서스 기준일은 그대로 표시한다.
