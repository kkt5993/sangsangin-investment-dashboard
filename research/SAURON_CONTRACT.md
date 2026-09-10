# SAURON 구현·자료 계약

SAURON은 Cesium 3D 지구본에서 시설, 지진 관측과 위성 궤도 계산을 탐색한다. DRAGONGLASS의 Sentinel-2 RGB/NDVI 촬영 영상과는 별도 화면이다. 보존한 원본 `sauron.js`를 로컬에서 대조했으며 원본 사이트에 추가 요청하지 않았다.

## 화면 구조

원본의 초기 카메라(경도30°, 위도18°, 고도26,000km), 시설/지진/위성 토글, 시설 선택과 지명 검색, 6개 화면 효과, 자동 회전·확대/축소·경사·좌우 회전·시설 투어·초기화·HUD·전체화면을 연결했다. 시설 이동은 경사−32°, 방향28°, 거리4,200m이며 투어 간격은4.2초다. 지구 중심 또는 화면 중심 지표를 기준으로 회전한다. 마커를 선택하면 출처·위치·시간·범위를 보여준다. 1~6/H/Esc와 방향키·+/−를 지원한다.

야간투시·열화상·느와르·CRT·스노우는 CSS 색상 효과다. 실제 야간 센서·열 관측이 아니다. 라이선스/지도 출처는 HUD를 숨겨도 표시한다. 작은 화면에서는 HUD 아래 별도 3D 공간을 확보한다. WebGL이나 런타임을 쓸 수 없으면 원장을 계속 읽을 수 있다.

## 실제 관측과 모델

| 항목 | 자료·정의 | 시간·표시 |
|---|---|---|
| 시설 | 검토한22개 시설의 기존 `satellite_sites.json` 대표점·공식 출처 | 공장/분지 전체 중심이나 전체 가동률로 해석하지 않음 |
| 지진 | [USGS 2.5+ 하루 GeoJSON](https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson), type=earthquake, 원값 M≥2.5 | 제공 시점 직전24시간 스냅샷. 진앙을 지표에 표시하고 깊이 km는 원장에 기록 |
| 궤도 | [CelesTrak stations JSON](https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=JSON)의 공개 OMM 요소 | 현재 UTC에서 SGP4/SDP4 계산, 3초마다 좌표 갱신. 수신 텔레메트리와 구분 |

최초 확보는 USGS 응답37개 중 raw M=2.45 한 건을 제외한36개, stations 그룹21개다. 가격 기준일2026-09-08과 관측 시각2026-09-10을 혼동하지 않는다. 이후 건수는 자료 갱신에 따라 변한다. 관측 오류/미확보를0으로 채우지 않는다.

OMM의 EARTH/TEME/UTC/SGP4 정의를 확인한다. 생략된 필드는 [CelesTrak의 문서화된 기본값](https://celestrak.org/NORAD/documentation/gp-data-formats.php)을 적용하고 다른 좌표계·시간계는 거부한다. 6자리 NORAD 번호를 지원하며 원자료 숫자 정밀도는 문자열로 보존한다. 브라우저의 Date/SGP4 입력은 밀리초 정밀도다. 모델 위치를 GMST로 회전하고 WGS84 타원체 위·경도/고도로 변환한다. 고도를200km로 강제 올리지 않는다. 요소가7일보다 오래되거나 미래1일 초과·계산 실패·비정상 고도이면 해당 위치를 숨긴다. ISS/CSS 핵심 본체에만 이름을 붙여 같은 위치의 모듈 이름이 겹치지 않게 한다.

## 배경·검색·트래픽

Cesium1.145.0(Apache-2.0), satellite.js7.1.0(MIT)을 고정하고 npm SHA512와 개별 파일 SHA256을 검증한다. 원본 사이트 코드를 재게시하지 않는다. 공식 라이선스와 Cesium의 제3자 출처를 `docs/vendor/`에 보존한다. 전체 Cesium 배포 파일 약17.1MiB는 필요할 때만 읽고 SAURON 진입 전에는 로드하지 않는다. 일반 화면에 엔진·텍스처·Worker를 일괄 요청하지 않는다.

기본은 패키지에 포함된 Natural Earth II 배경이다. 사용자가 OpenStreetMap 거리 지도를 선택하면 [타일 이용 정책](https://operations.osmfoundation.org/policies/tiles/)에 따라 보이는 화면만 정상 브라우저 캐시로 요청한다. 미리읽기/전 지구 다운로드를 하지 않는다. 자동 브라우저 검사는 OSM 요청을 로컬 fixture로 대체한다. Google 실사3D는 별도 키가 없어 연결하지 않았다. 키가 없는 원본의 지구본 기능과 구분해 기록한다.

검색은 시설명→직접 위도,경도→명시적으로 제출한 지명의 순서다. 외부 검색은 [MediaWiki Search API](https://www.mediawiki.org/wiki/API:Search)의 Wikipedia 문서 대표 좌표를 사용한다. 한글은 ko, 그 외는 en을 조회한다. 한국어 문서에 좌표가 없으면 공식 언어 연결로 최대5개 영문 문서를 한 번 추가 조회하고 원문 링크를 제공한다. 주소 수준의 지오코딩이 아니다. Wikimedia 권장 `Api-User-Agent`에 앱 이름과 공개 저장소를 명시한다. 자동완성·입력 중 조회는 없고 검색 제출2초 간격/50개 메모리 캐시/15초 제한·탭 이탈 취소를 적용한다. Nominatim에 요청하지 않는다.

## PC 갱신과 검증

승인된 평일08/18시 refresh에 수집기를 연결했다. USGS 최소1시간, CelesTrak 최소2시간 캐시를 적용하며 브라우저는 두 관측 공급자를 조회하지 않는다. 성공/확인 시각을 구분하고 실패 시 마지막 성공 자료를 보존한다. [CelesTrak 이용 정책](https://celestrak.org/usage-policy.php)에 따라 어떤 비200 HTTP 응답도 `sauron/stations-halted.json.gz`를 남겨 후속 자동 조회를 중단한다. 원인 확인 후 운영자가 중단 기록을 검토해야 재개할 수 있다. 네트워크 오류와 자료 검증 오류도 수집 원장에 기록한다.

응답당1MiB, 최대200개 OMM/2,000개 지진, 로컬 원자료512MiB 한도를 유지한다. 이번 관측을 넣은 공개 JSON 약8.02MiB를 수용하도록 코드의 정적 JSON 한도만8→10MiB로 늘렸다. 원자료·다운로드 아카이브·실행 로그는 GitHub와 Vercel에 게시하지 않는다.

Python은 규모 원값/빈 관측/범위/시각/중복, OMM 단위·정밀도·6자리 번호·좌표계, 캐시0요청/이전 값 보존/HTTP 중단/크기와 vendor 무결성을 검사한다. JS는 [CelesTrak 검증 구현](https://celestrak.org/software/tutorials/sgp4-verification.php)이 생성한3개 객체×4시점의 TEME 위치·속도와 독립 좌표변환 결과를 대조한다. 허용오차는 TEME 1e−6km, 고도0.01km, 위·경도0.001°다. 이는 수학적 구현 검증이며 실제 궤도 예측 정확도를 보증하지 않는다.

브라우저 검수: Edge 1440/1024/390px의 실제 WebGL, 3레이어·6효과·카메라·투어 중지·마커 상세·3초 갱신·검색/캐시·전체화면·탭 이탈/재진입·가로 넘침과 런타임 실패 시 원장 보존을 검사한다. 실제 실행 증거는 저장소 밖 runtime에 보관한다. SAURON 연결은 밸류체인53업종/151기업의 본사·공급/물류 관계 구현 완료를 뜻하지 않는다.
