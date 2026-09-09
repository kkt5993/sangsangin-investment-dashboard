# 상상인 투자 리서치 플랫폼

26개 탭 중 **23개 분석·콘텐츠 탭에 계산 또는 탐색·기록 기능을 연결**했습니다. Overview와 At a Glance는 전체 현황을 표시하며, ROSENBACH는 비공개 데이터·인증 서버가 없어 대기 상태입니다. 연결된 탭에도 부분 구현이 있으며 범위를 구분합니다.

- [팀 페이지](https://kkt5993.github.io/sangsangin-investment-dashboard/)
- [탭별 현황](research/IMPLEMENTATION_STATUS.md)
- [공식 유니버스·단위·날짜](research/DATA_DEFINITIONS.md)
- [차트 구조 대응표](research/CHART_PARITY.md)
- [26개 탭 구현 문서](research/MODULES.md)

## 화면과 데이터

RS·모멘텀, ETF·멀티에셋, 국면·리스크·주말 매크로, 퀀트·패턴·시장 역학, 실적·성장·종목 발굴, ML·MAXIMUS 기준모형, 관계 지도·지구본·연간 수익률 퀼트, 라이브러리·기록 화면을 제공합니다. 원본의 비공개 모델이나 수집되지 않은 관측값을 구현 완료로 표시하지 않습니다.

GitHub Pages는 main의 docs를 게시합니다. 화면을 열 때 원본 사이트나 시세 API를 호출하지 않습니다. 자체 SVG 차트와 로컬 지도 데이터로 표시합니다.

```powershell
python -m http.server 8769 --bind 127.0.0.1 --directory docs
```

## 로컬 수집과 계산

Python 3.13과 [requirements.txt](requirements.txt)의 환경을 사용합니다. 원자료는 형제 폴더 sangsangin-investment-data에 저장합니다. SANGSANGIN_DATA_DIR로 경로를 바꿀 수 있습니다. 같은 빈티지의 수집 성공·실패를 재사용하며 자동 일정은 없습니다.

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
# 아래 계산은 네트워크를 사용하지 않음
python -m pipeline.ml_models --as-of 2026-09-08
python -m pipeline.maximus_model --as-of 2026-09-08
python -m pipeline.build_all --as-of 2026-09-08
```

기본 누적 원자료 한도는 **32 MiB**입니다. 초과 전에 사용자와 협의합니다. 압축 캐시와 해시를 보존하며 공개 저장소에는 코드·문서·작은 계산 결과만 올립니다. 기존 pipeline.collect/build는 초기 RS 검증용이며 전체 갱신에는 위 명령을 사용합니다.

## 검증

```powershell
python -m unittest discover -s tests
python scripts/validate.py
python scripts/validate_extended.py
node scripts/test_charts.cjs
node scripts/test_dashboard.cjs
node scripts/test_extended.cjs
```

날짜, 학습 타깃 만기, OHLC, 행렬·그래프 무결성과 SVG 구조를 검사합니다. 대표 SVG는 브라우저 없이 래스터화해 확인합니다. 전체 브라우저 동작·픽셀 동일성 검사를 완료했다는 의미는 아닙니다.

## 학습 출처

설계 학습의 출발점은 Lee Changwoo 님의 [ARAGORN-INVESTIUM](https://aragorn-investium.pages.dev/#glance)입니다. 원본 HTML/JS/차트/리서치 보존본은 별도 로컬 연구 폴더에 있으며 재게시하지 않습니다. 이번 확장 중 원본 사이트 요청은 하지 않았습니다. [지도 데이터 라이선스](research/MAP_LICENSE.md)를 별도로 표시합니다.
