# ASK 관측 다이제스트 계약

보존한 ASK 자료의 시장 brief, 기간별 추세,10개 테마,16개 종목,21개 자산, 위험 양음,4개 핵심 지표, 모듈별 요약 구조를 팀 계산과 공개 근거로 채운다. 원본의 저자 논평·구루 보유·뉴스 관심 수치·heat 값을 복제하지 않는다. 질문/해석 메모와 PDF·이미지는 [로컬 리서치 기록](LOCAL_RESEARCH.md)에 보관한다.

## 기간과 가격

1W는7일,1M/3M/6M은 달력 월,1Y/2Y는 달력 연도다. 모든 자산은 자료 기준일에서 해당 기간을 뺀 날짜 이전의 마지막 가격을 기준가격으로 삼는다. 기준가격이 목표일보다7일 초과 오래됐거나 현재 가격이 기준일보다7일 초과 오래되면 미산출이다. 정확히7일 차이는 허용한다. 각 종목의 `starts`에 실제 기준가격 날짜를 저장한다. 주식의 거래일과 암호자산의 매일 관측에 같은252개 값을1년으로 적용하지 않는다.

YTD는 전년 마지막 관측에서 현재까지다. 수정주가를 사용하고 지수는 가격지수다. ETF는 실제 심볼을 함께 표시하며 Nasdaq 이름 아래의 QQQ를 Nasdaq Composite로 바꾸어 부르지 않는다. 선물 근월물 가격 변화는 롤 비용·담보 이자를 반영한 투자 수익률이 아니다. FX는 원/USD·엔/USD 호가 방향으로 계산한다. 자산마다 현지 통화 수익률이며 환율을 합쳐 원화 수익률로 만들지 않는다.

21개 자산의 구성은 `catalog.MULTI`에 있다. 단기 대표 정렬은1M, 중기는6M, 장기는2Y다. 브리프의 상위/하위3개와 기간 선택 표·막대는 같은 원장에서 생성한다. 향후 전망·기대수익을 생성하지 않는다. 가격 추세는 현재가/200관측 평균과3M 변화가 모두 양이면 상승, 모두 음이면 하락, 그 외 혼조다.

## 사업 테마와 공식 산업분류

[digest_themes.json](../config/digest_themes.json)은10개 테마의1~2개 기업, 사업 역할, 공식 출처와 확인일을 기록한다. 출처의 제품/사업 설명을 근거로 편집한 **관찰 목록**이다. KRX·GICS가 정한 공식 업종이나 전체 테마 지수가 아니다. 회사 전체 수익률이 특정 사업의 성과를 분리하지도 않는다.

| 테마 | 현재 관찰 기업 | 사업 근거 |
|---|---|---|
| AI 데이터센터 | NVIDIA·Vertiv | [가속 컴퓨팅](https://www.nvidia.com/en-us/data-center/)·[전력/냉각](https://www.vertiv.com/en-us/solutions/ai-hub/) |
| 첨단 반도체 장비 | Applied Materials·KLA | [제조 장비](https://www.appliedmaterials.com/us/en/semiconductor/products.html)·[공정 제어](https://ir.kla.com/company-information) |
| 로보틱스·피지컬 AI | NVIDIA·Intuitive Surgical | [로봇 플랫폼](https://www.nvidia.com/en-us/industries/robotics/)·[수술 시스템](https://www.intuitive.com/) |
| 파운드리·선단공정 | TSMC ADR | [연차 사업 설명](https://investor.tsmc.com/sites/ir/annual-report/2025/2025%20Annual%20Report_E.pdf) |
| HBM·AI 메모리 | Micron | [HBM 제품](https://www.micron.com/products/memory/hbm) |
| 광통신·AI 네트워킹 | Marvell·NVIDIA | [광 DSP](https://www.marvell.com/solutions/data-center/optical-dsp.html)·[네트워킹](https://www.nvidia.com/en-us/data-center/) |
| 전력·냉각 인프라 | Vertiv·Eaton | [AI 인프라](https://www.vertiv.com/en-us/solutions/ai-hub/)·[전력/냉각 설계](https://www.eaton.com/us/en-us/markets/data-centers/impact-of-ai-data-center-infrastructure/beam-rubin-dsx.html) |
| 온디바이스 AI | Qualcomm | [Snapdragon AI](https://www.qualcomm.com/snapdragon/smartphones/ai) |
| 첨단 패키징 | TSMC ADR·KLA | [3DFabric](https://www.tsmc.com/english/dedicatedFoundry/services/advanced-packaging)·[패키징 공정 검사](https://ir.kla.com/news-events/press-releases/detail/485/kla-unveils-comprehensive-ic-substrate-portfolio-for-a-new) |
| 에너지 안보·LNG | Chevron | [LNG 사업](https://www.chevron.com/what-we-do/energy/oil-and-natural-gas/liquefied-natural-gas-lng) |

기업 중복은 복수 사업 연관을 표시한 것으로 독립 포트폴리오를 뜻하지 않는다. 현재 관찰 목록으로 과거 기간의 개별 수익률을 단순 평균한다. 모든 구성원의 해당 기간이 있어야 평균을 산출한다. 일부 기업을 조용히 제외해 평균하지 않는다. 모멘텀 순위는 가용 목록의3M 평균에 대해 `(평균 순위−1)/(가용 수−1)×100`이고, 동률은 평균 순위다. 사업 투자/주문/공장 가동·뉴스 열기·향후 수익을 측정하는 점수가 아니다. 사업 분류 확인일과 가격 기준일을 별도로 표시한다.

## 종목·뉴스·위험·근거

관찰16종목은 KRX 대형주와 IVV 공식 주식 유니버스에서 기존 RS 상위8개씩이다. RS는 원래의 가중 모멘텀 규칙을 유지하고 ASK에 표시한 기간 수익률은 위 달력 규칙을 사용한다. 공식 업종과 구성 기준일을 표시한다. 기사 제목에서 정확한 이름/심볼 단어가 일치한 현재 RSS 표본만 센다. 예를 들어 `TER`를 `interest`에 매칭하지 않는다. 기준일 종료(KST) 이후 제목은 제외한다. 표본0건은 전 세계 관심0건을 뜻하지 않는다. 구루 보유는 미확보로 남긴다.

9개 위험 관측은 VIX25, HY OAS5%, NFCI0,10Y−3M0, M2 YoY0, Sahm0.5, SPY/KOSPI의MA200괴리0, EPU252관측 z1을 경계로 분리한다. VIX/HY/NFCI/Sahm/EPU는 높은 쪽이 경계, 나머지는 낮은 쪽이 경계다. 정확히 임계값이면 별도 경계값, 결측은 미산출이다. 따라서 IW의 일부 포함형 임계조건과는 경계값 표시가 다르다. NFCI는7일, M2/Sahm은 완료월 기준2개월 시차다. 방향을 합쳐 위기확률이나 매매 비중으로 만들지 않는다.

핵심4개는 구리선물/금선물, SPY/TLT, XLY/XLP, 금융 스트레스(VIX·HY 동일가중 z)다. 앞3개는 비조정 종가의 공통 날짜 비율이며180공통관측 곡선과63공통관측 변화율을 제공한다. 마지막은 지정학의 새3개 복합 중 매크로 스트레스를 참조하며 변화는63공통관측 z 차이다. 2026-09-10 지정학 구조 확장 때 이전 EPU·VIX·HY 3입력에서2입력으로 정렬했고, 기존 보존 차트를 소급 수정하지 않는다. z값의 퍼센트 변화로 혼동하지 않는다. 변환 방식·단위가 다른 수치를 하나의 점수로 합산하지 않는다.

모듈 요약은 현재 계산 묶음의20개 분석 모듈에서 기준일·주요 값·표의첫2행(최대2표)·방법·남은 범위를 참조한다. ML/MAXIMUS의 별도 기준일을 유지하고 이후 날짜 자료가 끼면 중단한다. 원본 내부 요약이18개인 것과 구분한다. 원본에 없는 분석 내용을 만들어 개수를 채우지 않는다.

## 갱신·검증

정기 실행의 `build_all → subview_modules.extend → digest_views`가 가격·뉴스·모델을 모아 다시 생성한다. ASK 화면을 열 때 시세나 원본 사이트를 호출하지 않는다. 테마 사업 설명은 확인한 공개 설정이며 자동 사업분류 모델이라고 표시하지 않는다. 구성 변경 시 출처·확인일을 수정하고 Git 이력을 남긴다.

Python 검사는 달력 시점·매일/거래일 정렬·오래된 가격·부분 결측 평균 금지·동률·뉴스 단어 경계·위험 임계값·정보 시차·z 차이를 확인한다. 공개 스키마와 실제 기간 선택 콜백, 외부 링크/본문 이스케이프, 대표 SVG 래스터를 검사한다. 브라우저 레이아웃 QA는 아니다. 원본 자동 AI 질의 서버·구루/전체 뉴스량·실제 온톨로지 사업 가중치는 남은 범위다.
