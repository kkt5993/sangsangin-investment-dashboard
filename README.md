# 상상인 투자 리서치 플랫폼

공개 투자 리서치 플랫폼을 학습하고 팀의 데이터·분석 시스템으로 발전시키는 프로젝트입니다.

**현재 단계: 설계·구현 가이드.** 26개 화면의 목적, 데이터 계약, 구현 순서와 검증 과제를 정리했습니다. 실시간 시세·예측·매매 기능은 아직 연결되어 있지 않습니다.

- [팀 페이지](https://kkt5993.github.io/sangsangin-investment-dashboard/)
- [화면별 구현 문서](research/MODULES.md)
- [전체 구조](research/ARCHITECTURE.md)
- [개발 순서](research/ROADMAP.md)

## 실행

별도 설치와 빌드 없이 정적 파일을 실행할 수 있습니다.

```powershell
python -m http.server 8769 --bind 127.0.0.1 --directory docs
```

GitHub Pages는 `main` 브랜치의 `/docs`를 게시합니다. 메뉴 설명은 `docs/modules.js`, 화면은 `docs/app.js`, 스타일은 `docs/styles.css`에 있습니다.

```powershell
python scripts/validate.py
```

## 데이터 원칙

수집기와 화면을 분리합니다. 원자료의 발표일·수정 이력·단위·기준일을 보존하고, 계산식과 모델 버전을 따라갈 수 있게 만듭니다. 모델을 선택한 구간과 최종 평가 구간을 분리하고 거래비용과 데이터 누출을 확인합니다.

이 저장소에는 팀이 작성한 코드와 구현 노트를 포함합니다. 원 사이트의 HTML/JavaScript/차트/리서치 요약 보존본, 비공개 데이터, 운영 키는 포함하지 않습니다.

## 학습 출처

설계 학습의 출발점은 **Lee Changwoo** 님의 [ARAGORN-INVESTIUM](https://aragorn-investium.pages.dev/#glance)입니다. 본 프로젝트는 팀의 독립적인 학습·구현 작업이며 원 사이트의 공식 미러 또는 제휴 서비스가 아닙니다. 원 사이트와 데이터 제공처의 권리는 각 권리자에게 있습니다.
