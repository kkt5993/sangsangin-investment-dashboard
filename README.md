# 상상인 투자 리서치 플랫폼

공개 투자 리서치 플랫폼을 학습하고 팀의 데이터·분석 시스템으로 발전시키는 프로젝트입니다.

**현재 단계: 실제 구현 진행 중.** RS와 모멘텀에 로컬 가격 수집·계산·차트를 연결했습니다. 전체 26개 탭의 가이드는 유지합니다. 원본의 비공개 설정과 미확인 종목이 있어 두 탭 모두 **부분 구현**으로 표시합니다.

- [팀 페이지](https://kkt5993.github.io/sangsangin-investment-dashboard/)
- [화면별 구현 문서](research/MODULES.md)
- [전체 구조](research/ARCHITECTURE.md)
- [개발 순서](research/ROADMAP.md)
- [구현 현황과 다음 작업](research/IMPLEMENTATION_STATUS.md)
- [가격·계산 계약 및 원본 대조](research/PRICE_CONTRACT.md)
- [차트 구조 대응표](research/CHART_PARITY.md)

## 현재 데이터 화면

- [RS](https://kkt5993.github.io/sangsangin-investment-dashboard/#rs): 35개 페어 중 29개 계산, 5년 z-score 시계열, 순위 막대, 히트맵, 상세 표. 미확인 6개와 종목 순위는 사유를 표시합니다.
- [모멘텀](https://kkt5993.github.io/sangsangin-investment-dashboard/#momentum): 국가 13·팩터 10·자산 9개, 섹터 24개 중 21개 계산, 상위 16개 섹터의 3M/6M 차트 32개, 4개 그룹 필터.
- 첫 수집: 2026-09-08까지 요청한 61개 가격 계열. 원자료와 수집 기록 약 1.9 MB는 **PC에만 저장**합니다. 공개 차트용 파생 JSON은 약 0.96 MB입니다.
- 모든 국가·팩터·자산의 비교 기준일은 공통 가격이 있는 2026-09-04입니다. 섹터 기준일은 2026-09-08입니다. 실시간 화면이 아니며 자동 일정은 등록하지 않았습니다.

## 실행

별도 설치와 빌드 없이 정적 파일을 실행할 수 있습니다.

```powershell
python -m http.server 8769 --bind 127.0.0.1 --directory docs
```

GitHub Pages는 `main` 브랜치의 `/docs`를 게시합니다. 메뉴 설명은 `docs/modules.js`, 가이드는 `docs/app.js`, 데이터 화면은 `docs/dashboard.js`, 독립 SVG 차트는 `docs/charts.js`에 있습니다. 외부 차트 CDN이나 브라우저 시세 API는 사용하지 않습니다.

```powershell
python scripts/validate.py
python -m unittest discover -s tests
node scripts/test_charts.cjs
node scripts/test_dashboard.cjs
```

## PC에서 데이터 갱신

Python 3.13.5와 [requirements.txt](requirements.txt)의 설치된 환경으로 검증했습니다. 새 환경이 필요한 팀원은 이 프로젝트에만 `.venv`를 만들고 `pip install -r requirements.txt`로 설치합니다. 계산 과정은 네트워크를 사용하지 않습니다.

```powershell
# 수집은 이 명령을 명시적으로 실행할 때만 발생합니다. 날짜는 완료된 일자로 지정합니다.
python -m pipeline.collect --as-of 2026-09-08
# 이미 받은 같은 날짜의 가격은 다시 요청하지 않습니다.
python -m pipeline.build --vintage 2026-09-08
# 검증 후 docs/data의 계산 결과와 변경 코드를 커밋·푸시하면 Pages에 반영됩니다.
```

기본 로컬 저장 위치는 저장소의 **형제 폴더** `sangsangin-investment-data/`입니다. `SANGSANGIN_DATA_DIR`로 변경할 수 있습니다. 날짜별 압축 CSV와 SHA256·제공처·수집시각·범위가 담긴 manifest를 보존합니다. 수집기는 한 종목씩 2초 이상 간격으로 처리하고, 같은 버전의 성공 파일은 재사용합니다. 초기에는 비교 검증용 종목 3개도 받았으며 현재 자동 대상에서는 제외했습니다.

원자료가 누적 32 MiB에 도달하면 수집을 멈춥니다. 이것은 사용자의 대용량 사전 문의 지시를 위한 보수적 기본 한도입니다. 한도를 자동으로 늘리거나 기존 데이터를 삭제하지 않습니다. 스냅샷은 수집 당시의 수정가격 버전이며, 과거 시점의 가용 데이터를 복원한 백테스트 DB가 아닙니다.

## 데이터 원칙

수집기와 화면을 분리합니다. 원자료의 발표일·수정 이력·단위·기준일을 보존하고, 계산식과 모델 버전을 따라갈 수 있게 만듭니다. 모델을 선택한 구간과 최종 평가 구간을 분리하고 거래비용과 데이터 누출을 확인합니다.

이 저장소에는 팀이 작성한 코드와 구현 노트를 포함합니다. 원 사이트의 HTML/JavaScript/차트/리서치 요약 보존본, 비공개 데이터, 운영 키는 포함하지 않습니다.

## 학습 출처

설계 학습의 출발점은 **Lee Changwoo** 님의 [ARAGORN-INVESTIUM](https://aragorn-investium.pages.dev/#glance)입니다. 본 프로젝트는 팀의 독립적인 학습·구현 작업이며 원 사이트의 공식 미러 또는 제휴 서비스가 아닙니다. 원 사이트와 데이터 제공처의 권리는 각 권리자에게 있습니다.
