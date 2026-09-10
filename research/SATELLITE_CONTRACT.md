# 위성 현장: 위치·영상·계산 계약

원본 보존 `dragonglass.js`의 시설 칩, 평면 지도,400/560/760px 크기, 위치 이동/확대, 촬영일 카드,RGB/NDVI 전환, 시설 Entity 이동을 대조했다. 원본 사이트 요청은 추가하지 않았다. 원본 좌표·영상·수치를 재배포하지 않고 공식 시설 자료와 독립 좌표 근거를 대조하여 새 Sentinel 관측을 수집했다.

현재22시설 슬롯을 모두 유지한다. 14곳에 실제 영상이 있고8곳은 관측 구역을 확인 중이다. 일부 원본 좌표가 실제 시설과 떨어져 있어 임의 좌표로 영상을 채우지 않는다. 원본 Esri 전 지구 위성 배경은 아직 없으며, 현재 지도는 로컬 해안선과 실제 확보한 관측 장면을 사용한다. 이 차이를 완성으로 표시하지 않는다.

## 시설 정의

`config/satellite_sites.json`이 동결된 위치 검토 원장이다. 회사/정부의 공식 시설명·주소/지역, 좌표 출처, 관측 범위, 검토일을 구분한다. 대부분 좌표는 공식 주소와 대조한 OpenStreetMap 시설 객체 대표점으로, 공식 측량점이나 법적 부지 경계가 아니다. Colossus1은 [FCC 공시9쪽](https://docs.fcc.gov/public/attachments/DOC-420685A1.pdf)의 xAI Memphis Gateway 위경도를 십진도로 변환했다. 같은 회사의 Colossus2를 혼합하지 않는다.

| 상태 | 시설 |
|---|---|
| 관측 연결14 | TSMC Arizona, Samsung Taylor, Micron Boise, Stargate Abilene, TSMC Hsinchu 본사/Fab12A, JASM Kumamoto, ASML Veldhoven, Tesla Texas/Fremont, Starbase 발사 시설, Cape Canaveral SLC-40, Vogtle, Meta Hyperion, xAI Colossus1 |
| 위치 대조8 | SK hynix M15X, Samsung Pyeongtaek, Intel Ohio/Magdeburg, Vandenberg SLC-4E, Sabine Pass LNG, Ghawar 유전, Permian 분지 |

국내 M15X와 평택은 주변 다른 공장·도심을 대신 사용하지 않는다. Ghawar/Permian은 넓은 지리적 영역이므로 대표 관측 구역을 먼저 정의해야 한다. Cape/Vandenberg는 상업 발사 시설 주변을 관측하며 기지 전체를 대표하지 않는다. Intel Magdeburg는 [2025-07-24 공식 발표](https://www.intel.de/content/www/de/de/newsroom/news/corporate/lip-bu-tan-steps-in-the-right-direction.html)의 계획 중단을 기록하며 가동 공장으로 표시하지 않는다.

OSM 조회는 설치 시 소수의 이름을 한 PC·한 스레드에서1초 이상 간격으로 대조하고 응답을 로컬 저장했다. [Nominatim 정책](https://operations.osmfoundation.org/policies/nominatim/)에 맞추며, 정기 수집/방문자 검색/자동완성 서비스에 연결하지 않는다. 지도에 OSM 기여자·ODbL 출처를 표시한다. 시설 공식 자료는 각 원장 항목에 직접 링크한다.

## 장면 선택과 다운로드

[Earth Search](https://github.com/Element84/earth-search/blob/main/README.md)의 `sentinel-2-c1-l2a` STAC을 사용한다. 유료·인증·S3 requester-pays 경로를 사용하지 않고 공개 HTTPS COG만 읽는다.

- 검증 위치 주변 최근60일·최대12개 후보를 촬영시각 역순으로 확인한다. 전 세계 모든 후보를 검색한 절대 최신 영상이라고 주장하지 않는다.
- 현장 중심의 UTM10m 격자400×400, 즉4×4km 정사각 창을 읽는다. 경계가 타일 밖으로 나가면 그 후보를 제외한다.
- 장면 전체 cloud-cover만으로 통과시키지 않고 구역의 SCL을 먼저 읽는다. 관측 범위98% 이상, 맑은 분류70% 이상, 최종 유효 NDVI70% 이상을 요구한다. 또한 시설 중심1×1km의 맑은 분류85% 이상과 기준점100×100m의95% 이상을 요구해 공장 위에만 구름이 걸린 장면을 제외한다.
- 적합한 새 후보가 없거나 수집에 실패하면 이전 관측을 `stale`로 유지한다. 촬영시각·원래 확보시각은 변경하지 않는다. 위치 원장이 바뀌면 서명이 다른 이전 영상은 표시하지 않는다.
- 같은 시설·촬영 장면·위치 서명은 이전 로컬 원밴드를 상속한다. 새 배열만NPZ로 저장하고 SHA256으로 검증한다. 검색 결과와 계산에 사용한 밴드 메타데이터도 로컬에 남긴다.

COG의 전체 파일을 읽는 경로를 차단했다. Rasterio의 [사용자 opener](https://rasterio.readthedocs.io/en/stable/topics/vsi.html)가 HTTP Range를 요청하며206응답·정확한 Content-Range·요청 크기를 확인한다. 전체200응답은 본문을 읽지 않고 거부한다. 요청당4MiB, 실행당192MiB전송 한도다. 이는 PC 저장한도와 별개이며 PC 전체 원자료/실행파일512MiB를 계속 검사한다. 14시설의 원자료/조사 기록과 품질 대조 과정에 보존한 장면은 약16.7MiB다.

## RGB와 NDVI

[Copernicus L2A 처리](https://sentiwiki.copernicus.eu/web/s2-processing)의 지표 반사도 제품이다. 밴드별 STAC `raster:bands.scale`과 `offset`을 사용한다. 고정DN/10000만 적용하면 processing baseline별 오프셋 때문에 NDVI가 달라지므로 금지한다.

`reflectance = DN × scale + offset`

`NDVI = (NIR B08 − red B04) / (NIR B08 + red B04)`

[SCL 분류표](https://custom-scripts.sentinel-hub.com/custom-scripts/sentinel-2/scene-classification/)의4(식생),5(비식생),6(물)만 통과시킨다. SCL0/1/2/3/7/8/9/10/11은 결측·결함·그림자·미분류·구름·눈으로 제외한다. SCL은20m에서10m 격자로 최근접 대응한다. 원밴드 nodata, 음의red/NIR, 분모1e−6 이하는 NDVI 결측이다. DN 보정 전 비율, 구름을0으로 채운 평균을 사용하지 않는다.

RGB는 보정된B04/B03/B02를0~0.3 고정 반사도 범위와1/2.2감마로 표시한다. 장면마다 대비를 맞추는 자동 스트레치는 사용하지 않는다. NDVI 색 범위는−1~+1고정이다. 통계는 원래 UTM10m 창의 유효 화소에서 계산한다. 식생비율은 NDVI≥0.3이라는 팀 표시용 임계값이며 식생 면적의 검증된 정답이 아니다.

화면용 PNG는 EPSG:3857로 최근접 재투영한400×400 RGBA다. 지도 위치와 이미지 경계를 같은 투영으로 맞추고 북쪽을 위로 둔다. 제외 화소는 투명하며 화면 바탕색으로 보인다. PNG의 촬영ID·시각·원자료 링크·이미지 해시/크기를 파생 JSON에 포함한다. 공개 파일만 열 때 원본 사이트나 위성 제공처로 요청하지 않는다. 외부 지도/원자료 링크는 사용자가 선택할 때 연다.

**NDVI는 식생 지수다. 건설 진척률, 공장 가동률, 생산량, 실적 선행 신호로 검증하지 않았으므로 그런 수치를 표시하지 않는다.** 계절·농경·수분·그림자/구름 분류오차가 관측에 영향을 준다.

## 동작·갱신·검증

시설 칩/지도 점은 해당 장면으로 이동한다. 드래그/방향키 이동,확대/축소,전체보기,3가지 지도크기를 제공한다. 지도와 개별 카드의 RGB/NDVI 전환은 독립적이다. 영상 카드는 시설 Entity로 이동해 위치·촬영·공식 자료를 표시하며, 관련 기업 자료가 있으면 기업 Entity로 연결한다. 좌표 미확인 시설도 목록과 상세를 보존한다.

기존 평일08/18시 실행 안에서 위성 조회를7일 간격으로 수행한다. 오래된 영상은 오래된 촬영일 그대로다. 구름 때문에 매주 새 영상이 생긴다고 보장하지 않는다.

검사는 보정 전후 NDVI 차이, 구름/결측/음수·분모0,실제 GDAL 부분읽기,전송상한/200응답 거부,22시설 보존,PNG 해시·투영경계·촬영시각,지도변환/이동/크기/키보드,카드전환·Entity 이동·빈 상태·문자열 이스케이프를 포함한다. 오프라인 DOM fixture와 과학 래스터 검사를 수행하며 브라우저 QA로 부르지 않는다.
