# 위성 현장: 위치·영상·계산 계약

원본 보존 `dragonglass.js`의 시설 칩, 평면 지도,400/560/760px 크기, 위치 이동/확대, 촬영일 카드,RGB/NDVI 전환, 시설 Entity 이동을 대조했다. 원본 사이트 요청은 추가하지 않았다. 원본 좌표·영상·수치를 재배포하지 않고 공식 시설 자료와 독립 좌표 근거를 대조하여 새 Sentinel 관측을 수집했다.

현재22시설 슬롯을 모두 유지한다. 22곳의 관측 기준점과 실제 영상을 연결했다. 최신 영상 확보 수와 촬영일은 공개 위성 화면의 결과를 기준으로 한다. 일부 원본 좌표가 실제 시설과 떨어져 있어 임의 좌표로 영상을 채우지 않는다. 전 지구 배경은 NASA GIBS Blue Marble을 연결했고 로컬 해안선으로 전환할 수 있다. 원본 Esri 고해상도 영상·지명 레이어와는 해상도/출처가 다르며 그 동등성을 완료로 표시하지 않는다.

## 시설 정의

`config/satellite_sites.json`이 동결된 위치 검토 원장이다. 회사/정부의 공식 시설명·주소/지역, 좌표 출처, 관측 범위, 검토일을 구분한다. 대부분 좌표는 공식 주소와 대조한 OpenStreetMap 시설 객체 대표점으로, 공식 측량점이나 법적 부지 경계가 아니다. Colossus1은 [FCC 공시9쪽](https://docs.fcc.gov/public/attachments/DOC-420685A1.pdf)의 xAI Memphis Gateway 위경도를 십진도로 변환했다. 같은 회사의 Colossus2를 혼합하지 않는다.

| 관측 기준점 | 위치 근거와 범위 |
|---|---|
| 기존14시설 | 공식 주소·OSM 시설 객체, xAI Colossus1은 FCC 공시 좌표 |
| Samsung Pyeongtaek | 삼성 공식 캠퍼스 내 복지1동 매장 지도 좌표. 개별 P1~P5 팹 중심이 아님 |
| SK hynix M15X | 공식 청주4공장 주소·M15X 배치와 장소 지도상의 기존 M15 공장 대조. 기존 팹 주변4km로 인접 M15X를 포함한 캠퍼스 관측; M15X의 공식 측량점이 아님 |
| Intel Ohio One | Umbra의 공개 Intel Ohio One 메타데이터 `sceneCenterPointLla`. 대용량 SAR 영상은 다운로드하지 않음 |
| Intel Magdeburg | 시의회 DS0471/25 부록1의 Eulenberg 계획 구역과 OSM Eulenberg 지형 기준점 대조 |
| Vandenberg SLC-4E | SpaceX Falcon 사용자 안내서 PDF73쪽(인쇄62쪽)의 발사대 위경도 |
| Sabine Pass LNG | Cheniere 공식 주소 페이지에서 연결한 지도 장소 핀. 지도 화면 중심과 구분 |
| Ghawar 권역 | Aramco 공식 Uthmaniyah 가스 처리 시설과 OSM 산업부지 대표점, USGS 지질 구역 대조 |
| Permian 분지 | NASA ISS013-E-26488의 Yates 유전 사진 중심30.9°N,101.9°W. 위성 직하점·머신러닝 추정점과 구분 |

Ghawar/Permian의4km 관측은 명시한 시설·구역의 표면 영상이며 유전·분지 전체를 대표하는 표본이 아니다. 유정 수, 생산량, 매장량으로 확대 해석하지 않는다. NASA와 Umbra의 과거 촬영 자료는 위치 근거로만 사용하며 실제 표시 영상은 별도로 확보한 Sentinel-2의 촬영일을 따른다. 각 좌표의 직접 출처는 시설 상세와 위치 원장에 보존한다.

Cape/Vandenberg는 상업 발사 시설 주변이며 기지 전체가 아니다. Intel Magdeburg는 [2025-07-24 공식 발표](https://www.intel.de/content/www/de/de/newsroom/news/corporate/lip-bu-tan-steps-in-the-right-direction.html)의 독일 계획 중단을 반영해 계획 부지로 표시한다.

OSM 조회는 설치 시 소수의 이름을 한 PC·한 스레드에서1초 이상 간격으로 대조하고 응답을 로컬 저장했다. [Nominatim 정책](https://operations.osmfoundation.org/policies/nominatim/)에 맞추며, 정기 수집/방문자 검색/자동완성 서비스에 연결하지 않는다. 지도에 OSM 기여자·ODbL 출처를 표시한다. 시설 공식 자료는 각 원장 항목에 직접 링크한다.

## 장면 선택과 다운로드

[Earth Search](https://github.com/Element84/earth-search/blob/main/README.md)의 `sentinel-2-c1-l2a` STAC을 사용한다. 유료·인증·S3 requester-pays 경로를 사용하지 않고 공개 HTTPS COG만 읽는다.

- 검증 위치 주변 최근60일·최대36개 후보를 촬영시각 역순으로 확인한다. 전 세계 모든 후보를 검색한 절대 최신 영상이라고 주장하지 않는다.
- 현장 중심의 UTM10m 격자400×400, 즉4×4km 정사각 창을 읽는다. 경계가 타일 밖으로 나가면 그 후보를 제외한다.
- 장면 전체 cloud-cover만으로 통과시키지 않고 구역의 SCL을 먼저 읽는다. 관측 범위98% 이상, 맑은 분류70% 이상, 최종 유효 NDVI70% 이상을 요구한다. 또한 시설 중심1×1km의 맑은 분류85% 이상과 기준점100×100m의95% 이상을 요구해 공장 위에만 구름이 걸린 장면을 제외한다.
- 적합한 새 후보가 없거나 수집에 실패하면 이전 관측을 `stale`로 유지한다. 촬영시각·원래 확보시각은 변경하지 않는다. 위치 원장이 바뀌면 서명이 다른 이전 영상은 표시하지 않는다.
- 같은 시설·촬영 장면·위치 서명은 이전 로컬 원밴드를 상속한다. 새 배열만NPZ로 저장하고 SHA256으로 검증한다. 검색 캐시 키에 관측 위치·범위 서명과 후보 상한을 포함해 좌표 수정 후 과거 검색 결과가 잘못 재사용되지 않도록 한다. 검색 결과와 계산에 사용한 밴드 메타데이터도 로컬에 남긴다.

COG의 전체 파일을 읽는 경로를 차단했다. Rasterio의 [사용자 opener](https://rasterio.readthedocs.io/en/stable/topics/vsi.html)가 HTTP Range를 요청하며206응답·정확한 Content-Range·요청 크기를 확인한다. 전체200응답은 본문을 읽지 않고 거부한다. 요청별·실행별 전송 용량 상한은 적용하지 않는다. PC의 누적 저장 용량은 검사하거나 제한하지 않는다. 정기 조회는 후보 상한 내에서 맑은 장면을 찾으면 중단한다. 저장·전송량은 로컬 실행 기록으로 확인한다.

## RGB와 NDVI

[Copernicus L2A 처리](https://sentiwiki.copernicus.eu/web/s2-processing)의 지표 반사도 제품이다. 밴드별 STAC `raster:bands.scale`과 `offset`을 사용한다. 고정DN/10000만 적용하면 processing baseline별 오프셋 때문에 NDVI가 달라지므로 금지한다.

`reflectance = DN × scale + offset`

`NDVI = (NIR B08 − red B04) / (NIR B08 + red B04)`

[SCL 분류표](https://custom-scripts.sentinel-hub.com/custom-scripts/sentinel-2/scene-classification/)의4(식생),5(비식생),6(물)만 통과시킨다. SCL0/1/2/3/7/8/9/10/11은 결측·결함·그림자·미분류·구름·눈으로 제외한다. SCL은20m에서10m 격자로 최근접 대응한다. 원밴드 nodata, 음의red/NIR, 분모1e−6 이하는 NDVI 결측이다. DN 보정 전 비율, 구름을0으로 채운 평균을 사용하지 않는다.

RGB는 보정된B04/B03/B02를 기본0~0.3 고정 반사도 범위와1/2.2감마로 표시한다. Ghawar의 밝은 사막은0~0.65 고정 범위를 사용해 지형이 흰색으로 잘리는 현상을 줄였다. 이 시설별 표시 범위는 원장·상세에 명시하고 시점마다 유지하며, NDVI와 원래 반사도 통계는 바꾸지 않는다. 장면마다 대비를 맞추는 자동 스트레치는 사용하지 않는다. NDVI 색 범위는−1~+1고정이다. 통계는 원래 UTM10m 창의 유효 화소에서 계산한다. 식생비율은 NDVI≥0.3이라는 팀 표시용 임계값이며 식생 면적의 검증된 정답이 아니다.

화면용 PNG는 EPSG:3857로 최근접 재투영한400×400 RGBA다. 지도 위치와 이미지 경계를 같은 투영으로 맞추고 북쪽을 위로 둔다. 제외 화소는 투명하며 화면 바탕색으로 보인다. PNG의 촬영ID·시각·원자료 링크·이미지 해시/크기를 파생 JSON에 포함한다. 시설 관측 PNG는 같은 사이트에서 읽는다. NASA 배경은 지도 영역이 보일 때만 외부 GIBS에 요청한다. 외부 지도/원자료 링크는 사용자가 선택할 때 연다.

**NDVI는 식생 지수다. 건설 진척률, 공장 가동률, 생산량, 실적 선행 신호로 검증하지 않았으므로 그런 수치를 표시하지 않는다.** 계절·농경·수분·그림자/구름 분류오차가 관측에 영향을 준다.

## 동작·갱신·검증

시설 칩/지도 점은 해당 장면으로 이동한다. 드래그/방향키 이동,확대/축소,전체보기,3가지 지도크기를 제공한다. 지도와 개별 카드의 RGB/NDVI 전환은 독립적이다. 영상 카드는 시설 Entity로 이동해 위치·촬영·공식 자료를 표시하며, 관련 기업 자료가 있으면 기업 Entity로 연결한다. 좌표 미확인 시설도 목록과 상세를 보존한다.

기존 평일08/18시 실행 안에서 위성 조회를7일 간격으로 수행한다. 오래된 영상은 오래된 촬영일 그대로다. 구름 때문에 매주 새 영상이 생긴다고 보장하지 않는다.

검사는 보정 전후 NDVI 차이, 구름/결측/음수·분모0,실제 GDAL 부분읽기,200응답 거부,22시설 보존,PNG 해시·투영경계·촬영시각,지도변환/이동/크기/키보드,카드전환·Entity 이동·빈 상태·문자열 이스케이프를 포함한다. 오프라인 DOM fixture와 과학 래스터 검사를 수행하며 브라우저 QA로 부르지 않는다.


## 전 지구 배경과 관측의 분리

2026-09-10 [공식 GIBS WMTS 계약](https://nasa-gibs.github.io/gibs-api-docs/access-basics/)과 EPSG3857 GetCapabilities의 `BlueMarble_ShadedRelief_Bathymetry`를 대조했다. 시간 차원이 없는 JPEG,256px 타일,`GoogleMapsCompatible_Level8`,0~8의2진 행렬이다. [NASA Worldview](https://worldview.earthdata.nasa.gov/)의 레이어명은2004년8월이며 [NASA Blue Marble 설명](https://science.nasa.gov/earth/earth-observatory/blue-marble-next-generation/)은500m 원자료를 설명한다. 지도 픽셀 간격과 원자료 해상도를 같은 값으로 표시하지 않는다.

원본은 Esri World Imagery와 World Boundaries and Places를 겹치고 zoom19,시설 이동14,초기 시설 fitBounds,휠 확대 비활성으로 구현했다. [Esri 공식 이용 요약](https://goto.arcgis.com/termsofuse/viewsummary)은 Esri 소프트웨어/구독·출처 표시와 상업 사용 조건을 명시한다. 팀의 해당 권한은 질문한 상태이며, 확인 전 Esri 서비스 요청/타일 복제/재호스팅은 하지 않는다. NASA 공개 배경은 원본의 고해상도·지명 기능을 대체 완료했다는 뜻이 아니다.

- 평면 Web Mercator 좌표·256px 타일 격자를 사용한다. 날짜변경선에서는 타일과 관측/마커를 함께 반복하고 위도는±85.0511288°로 제한한다.400/560/760px 지도 높이와 실제 화면 폭에 맞춰 초기/전체 시설 범위를 계산한다. 확대는19까지지만 배경은8레벨 원래 타일을 확대 표시하고 관측은10m PNG 그대로다.
- 선택 시설의 촬영일·장면 경계/마스크를 보존한다. 불투명 회색 바탕을 관측 아래에 놓아 구름/결측을2004년 배경 화소가 채우지 않게 한다. 배경은 NDVI 계산이나 시설 통계에 사용하지 않는다.
- 화면에 보이는 타일만 동시3요청,동작 종료180ms 후 요청한다. 드래그·화면 밖·브라우저 숨김·다른 탭 이동 때 중단하고 오래된 응답은 버린다. 사전 타일 수집이나 전 지구 다운로드는 없다. 한 요청12초,화면100타일 상한이다.
- Blob 메모리 캐시는 화면 밖 타일을48장까지 재사용하며 오래된 URL을 해제한다. 합산 용량 검사와 상한은 제거했다. 앱은 배경을IndexedDB·원자료 폴더에 저장하지 않는다. 브라우저 기본HTTP캐시는 별개다.401/403/429/503이면 추가 요청을 중단하며 사용자가 다시 읽기를 선택할 수 있다. 배경 실패는 시설 관측을 지우지 않는다.
- Blue Marble은 고정 합성 배경이므로 평일 수집 파이프라인에서 최신 날짜로 바꾸지 않는다. 기존 Sentinel 주간 증분 수집과 평일08/18 검증/게시를 유지한다. 이번 변경은 새 시설 원밴드를 받지 않는다.

오프라인 검사는 타일 원점/날짜변경선/극지/확대,동시 요청 상한,중단/재시도/HTTP429,스트림 형식 검증,캐시 재사용/URL 해제와 관측 마스크 순서를 포함한다. 실제 브라우저에서 NASA 배경의 화면 표시와 시설 이동/NDVI를 별도로 확인한다.
