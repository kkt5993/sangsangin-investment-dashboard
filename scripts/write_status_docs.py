"""Refresh each tab's implementation handoff from the built public snapshots."""
import json,re
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
load=lambda p:json.loads(p.read_text(encoding='utf8'))
modules=json.loads((ROOT/'docs/modules.js').read_text(encoding='utf8').removeprefix('const MODULES = ').rstrip().removesuffix(';'))
meta=load(ROOT/'docs/data/status.json')
CODE={
 'rs':'market_modules.py · build.py · analytics.py · universe.py','momentum':'build.py · analytics.py · universe.py',
 'etfmon':'market_modules.py','multiasset':'market_modules.py','dynamics':'market_modules.py','watch':'market_modules.py · patterns.py',
 'regime':'macro_modules.py','risk':'macro_modules.py · option_analytics.py','pm_weekend':'macro_modules.py','geoecon':'macro_modules.py',
 'earnings':'financial_modules.py','growth':'financial_modules.py · local_consensus.py','discovery':'discovery.py · financial_modules.py','strategies':'financial_modules.py',
 'quant':'quant_modules.py','ml':'ml_models.py','maximus':'maximus_model.py · ml_models.py',
 'principium':'platform_modules.py','ask_digest':'platform_modules.py','iw':'platform_modules.py','aragorn':'platform_modules.py','dragonglass':'platform_modules.py','globe':'platform_modules.py',
}
for key in ['regime','risk','pm_weekend','geoecon','strategies','earnings','dragonglass','ask_digest','multiasset']:
    CODE[key]+=' · subview_modules.py'
for key in ['strategies','earnings','geoecon']:CODE[key]+=' · events_data.py'
for key in ['risk','pm_weekend']:CODE[key]+=' · cot_data.py'
CODE['regime']+=' · reflexivity.py · industry_details.py'
CODE['regime']+=' · valuation.py · calendar_data.py'
CODE['pm_weekend']+=' · pm_details.py · gpr_data.py'
CODE['risk']+=' · wagdog.py'
CODE['dragonglass']+=' · entities.py'
CODE['multiasset']+=' · allocation_model.py · allocation_views.py · technical_scan.py · oecd_data.py'
CODE['watch']+=' · technical_scan.py'
for key in ['risk','pm_weekend','earnings']:CODE[key]+=' · flows.py · flows_data.py'
# Original structures were read from the saved source and chart captions, offline.
PARITY={
 'overview':('전체 탭 요약·카드·탐색','25탭 상태, 데이터 수, 바로가기','원본의 개인 서술·Tesseract·crowding 보조 엔진은 제외'),
 'glance':('4단계 프로세스·구조·출처','PC 수집→검증→Vercel·평일08/18시 갱신·512MiB 변경분 캐시','원본 Mac 서버 운영 대신 승인된 PC 실행 일정 사용'),
 'maximus':('지수·종목·거시 예측, 전문가 가중치·신호·시계열','3지수·13종목·2거시, 전문가 가중치와 예측·확률·기여 차트','원본 10전문가/로지스틱 게이트/SIS 대신 명시적 3모델 기준모형'),
 'dragonglass':('11개 하위 화면, 관계·시설·관측·원장','3D 관계·Entity 360·로컬 원장 3개 화면','시설·위성·물류·전파모델 8개 화면은 데이터/설정 미연결'),
 'aragorn':('3D 관계 탐색·자산 연간 퀼트','회전·객체 선택·11자산 2016~현재 연간 순위','인과 추정 관계 대신 공식 시장/업종 소속'),
 'globe':('지구본·국가/기업 탐색·교역 관계','로컬 지도 경계·정사영 회전·국가/기업 선택·수치표','본사 좌표·교역 경로/품목/금액은 미연결'),
 'principium':('유형별 리서치 라이브러리·검색·열람','팀 작성 primer/article/report·키워드 검색·기록','기관 리포트 아카이브·관리자 업로드 서버 없음'),
 'regime':('US/KR 성장×물가 4분면·전이 표·RSI 이중축·거시 선','양국 국면·전이 빈도·주간 RSI와 가격·성장/물가 3년 패널','원본 세부 상태 판정·발표 시점 빈티지 동등성 미검증'),
 'rs':('35개 5Y z, 0/±1/±2·중앙 음영, 섹터 막대/히트맵, 강8약6·15위표','공식 상품 35페어·KR/US 종목 1W선별 1M막대·3유니버스 순위','조선 신규 상장으로 5Y 준비 구간 부족, z 비공개 세부 설정 미검증'),
 'momentum':('32자산·24섹터, 기간 히트맵, 상위16×3M/6M=32곡선','동일 그룹 수·5기간·3M/6M 짝·0선·양음 영역','조선 5Y z 없음, 누적 비율/달력 월 계약은 팀 설정'),
 'discovery':('4개 분류·3개 평가축·공식 유니버스 발굴','KR기술100%, US45/30/25%, 시장·분류·검색·더 보기·근거 상세','비공개 정규화/리서치 서술 엔진 대신 공개 팀 규칙'),
 'strategies':('전략별 후보·재무·OHLC·이벤트 결과','흑자전환, 실적 서프라이즈, 일/주봉과 거래량','PEAD 발표일 정렬·내부자·13F·공매도 이벤트 원장 미연결'),
 'earnings':('US/KR 상위 이익 성장·YTD·히트맵·3개년 그룹 막대','연간 NI실적·글로벌 EPS 추정·국내 2025/26/27 NI 막대','해외 FY1/FY2 순이익/영업이익 전체 금액 추정 없음'),
 'growth':('FY1/FY2 3D: x영업이익성장 yYTD z영업이익률, 시총 크기','국내 두 3D 회전·확대·시총, 글로벌 EPS 별도 표','해외 영업이익 컨센서스 부족으로 글로벌 3D 전체 범위 차이'),
 'multiasset':('21자산 막대·열지도·37자산 스캐너·배분/성과','12지표·90봉 스캐너, Boruta/앙상블/Markov/LSTM·33자산8그룹·96월성과/12월비중','74입력/제약/하이퍼파라미터는 팀 설정, 현재 수정 거시 빈티지의 OOS'),
 'risk':('옵션 GEX/스팟곡선·VIX/SKEW·CSD·포트폴리오 위험','3ETF 만기 제한 GEX·OI PCR, CSD·곡선·VaR/CVaR·스트레스','딜러 실제 포지션·전 만기·실제 팀 포트폴리오 없음'),
 'watch':('KR/US 상승6·하락4, 일/주봉·MA·거래량·패턴 근거','5기하 패턴·피벗·120일/52주·MA·ADX/DI/MA4조건·12지표 점수','미공개 판정/ADX 합성 점수 동등성 미검증, 적합도는 성공확률 아님'),
 'ml':('3지수×1M/3M, 실제 막대/예측선·68/90%·적중점·z/확률/가격·OOS','6그룹·만기 정렬 walk-forward·모델 평가·이중축·계수','Boruta/SHAP/LSTM·비공개 모델 선택과 PIT 빈티지 미복제'),
 'quant':('Stat Arb·8팩터·BAB·TSMOM·단기반전 5뷰','페어 z 0/±2·상관/Hurst/공적분/반감기·요인/비중·후보','현재 단면 스크리닝, 역사 구성·모든 전략 비용 후 OOS 필요'),
 'dynamics':('3지수+15주식, 8룩백×시간 변동성표면·β×τ·위험/가격·노출성과','18대상·표면 회전/시간·위상·0~100/65선·가격 우축·전일노출','21D/5D/expanding252는 명시적 팀 파라미터, 거래비용·차입금리 미반영'),
 'iw':('주간 관측·글과 이미지·판단 원장','수치 요약과 개인 메모 저장/수정/삭제/JSON 이동','원본 개인 논평과 과거 기록·팀 공용 저장 없음'),
 'pm_weekend':('주말 매크로 다중 선·이중축·지표표','미국/한국 금리·물가·유동성 등 5년 패널·단위/최신일','원본 주간 서술 대신 자체 관측표'),
 'etfmon':('9분류·73위치, 분배율 막대·기간 수익률·투자금 현금흐름','9그룹·TTM실제분배/현재종가·조정수익률·투자금 변경','분배는 과거12M의 세전 월평균; 미래 지급액·실제 자금유입 추정 아님'),
 'geoecon':('정책·지정학 뉴스와 위험 시계열','EPU/VIX·DXY/WTI·금리/크레딧 이중축','뉴스 원장·NLP/LLM 지정학 종합 점수 미연결'),
 'ask_digest':('유형/키워드별 요약 카드·근거·조회','자체 시장 다이제스트·유형 필터·검색·질문 기록','외부 ASK 토론·저자 요약 아카이브 수집 서버 없음'),
}
labels={'partial':'부분 구현','operational':'계산·화면 연결','blocked':'추가 데이터 필요'}
status_lines=['# 탭별 구현 현황','',f"가격 기준 {meta['as_of']} · 공개 탭 25개 · 분석/콘텐츠 연결 **{meta['implemented']}개** · Overview/At a Glance 2개.",'',
 '연결은 완전 복제와 다르다. 공개된 차트 구조를 맞추면서 실자료 계산과 탐색 기능을 구현했다. 비공개 산식·관측치가 필요한 부분은 아래와 각 화면에 남겨 둔다. 원본 계산 서버와 수치 동등성 인증을 완료한 탭은 없다.','',
 f"로컬 가격 {meta['price_series']}계열, 거시 {meta['macro_series']}계열, 재무·가격 연결 {meta['financial_companies']}기업. 국내 컨센서스 빈티지 {meta['consensus_as_of']}. KRX 대형주100·KOSPI200 공식 응답201·IVV 주식504를 사용한다.",'',
 '| 탭 | 상태 | 연결 범위 | 남은 범위 |','|---|---|---|---|']
parity=['# 차트 구조 대응표','','원본 사이트에 재접속하지 않고 로컬 보존 소스·JSON·차트 주석을 대조했다. 축·단위·그룹·계열·패널을 기준으로 작성하며 색·글꼴은 독립 구현이다. 아래의 차이를 숨기지 않는다.','',
 '| 탭 | 원본 구조 | 현재 구조 | 차이·남은 항목 |','|---|---|---|---|']
for m in modules:
    key=m['id'];st=meta['modules'][key];label=labels[st['status']];original,scope,gap=PARITY[key]
    status_lines.append(f"| [{m['title']}](modules/{key}.md) | {label} | {scope} | {gap} |")
    parity.append(f"| {m['title']} | {original} | {scope} | {gap} |")
    if key in CODE:
        details=load(ROOT/'docs/data'/(key+'.json'));scope=' / '.join(v['name'] for v in details.get('subviews',[]) if v['status']=='connected') or scope;gap=' / '.join(details.get('missing',[])) or gap
        status_lines[-1]=f"| [{m['title']}](modules/{key}.md) | {label} | {scope} | {gap} |"
        parity[-1]=f"| {m['title']} | {original} | {scope} | {gap} |"
    path=ROOT/'research/modules'/(key+'.md');old=path.read_text(encoding='utf8')
    old=re.sub(r'\n<!-- implementation:start -->.*?<!-- implementation:end -->\n','\n',old,flags=re.S)
    first,rest=old.split('\n',1);block=['','<!-- implementation:start -->','## 현재 팀 구현','',f'**{label}** · 가격 기준 {meta["as_of"]}. {scope}.','']
    if key in CODE:
        a=load(ROOT/'docs/data'/(key+'.json'))
        block += [f"- 계산 코드: "+' · '.join(f'[{f}](../../pipeline/{f})' for f in CODE[key].split(' · ')),
          f"- 화면: [{'dashboard.js' if key in ['rs','momentum'] else 'research-dashboard.js'}](../../docs/{'dashboard.js' if key in ['rs','momentum'] else 'research-dashboard.js'}) · [계산 결과](../../docs/data/{key}.json)",
          '- 계산/자료 계약: '+a['method_note'],
          '- 남은 범위: '+' / '.join(a.get('missing') or [gap]),'']
        if a.get('sections'):block += ['연결된 하위 그룹: '+', '.join(dict.fromkeys(s.get('group','공통') for s in a['sections']))+'.','']
    else:block += [f'- 화면: [app.js](../../docs/app.js) · [전체 상태](../../docs/data/status.json)',f'- 남은 범위: {gap}','']
    block += ['[공식 분류·단위·날짜](../DATA_DEFINITIONS.md) · [차트 대응표](../CHART_PARITY.md) · [재계산 및 검사](../../README.md)','',
       '아래는 원본을 학습하며 작성한 설계 가이드다. 초기의 “필요/미확인” 표현은 위 현재 구현 상태를 우선해 읽는다.','<!-- implementation:end -->','']
    path.write_text(first+'\n'+'\n'.join(block)+'\n'+rest.lstrip('\n'),encoding='utf8')
status_lines += ['','## 이번 검증 범위','','Python 날짜·수익률·학습 타깃·미래 변경 불변성·기하 패턴 검증, 실제 스냅샷의 OHLC/행렬/그래프 검증, JS 전체 23개 데이터 탭과 모든 하위 섹션의 오프라인 렌더링을 검사한다. 7종 대표 SVG는 브라우저 없이 래스터화하여 차트 배치와 한글을 확인한다. 브라우저 이벤트 전체나 원본 픽셀 일치 검증을 완료했다는 뜻은 아니다.','',
 '재계산은 [README](../README.md), 공개 정의는 [DATA_DEFINITIONS](DATA_DEFINITIONS.md), 다음 보완은 [ROADMAP](ROADMAP.md)을 따른다.']
parity += ['','## 공통 표시와 검사','','결측값은 0으로 채우지 않는다. 좁은 화면에서는 패널을 한 열로 배치하고 표는 스크롤한다. 신규 SVG는 로컬 코드로 생성하며 외부 차트 CDN을 요구하지 않는다. RS/모멘텀은 키보드 날짜 탐색, 새 3D/지구본은 회전·선택 제어를 제공한다.','',
 '시계열은 날짜 순서와 중복·미래 관측을 검사한다. 예측 타깃만 미래를 허용한다. OHLC 범위, 학습 타깃 만기, 구간 순서, 8개 표면 룩백, 캔들 120일/52주, 25탭 연결, 코드와 데이터 크기를 검사한다. 대표 SVG의 육안 확인을 브라우저 기능 검사 또는 원본 계산 동등성으로 표현하지 않는다.']
(ROOT/'research/IMPLEMENTATION_STATUS.md').write_text('\n'.join(status_lines)+'\n',encoding='utf8')
(ROOT/'research/CHART_PARITY.md').write_text('\n'.join(parity)+'\n',encoding='utf8')
views=['# 세부 화면 연결 현황','',f"가격 기준 {meta['as_of']}. 연결은 해당 화면에 실자료 계산·탐색이 있다는 뜻이며 원본 알고리즘의 완전 복제를 뜻하지 않습니다. 각 탭의 남은 범위도 함께 확인하세요.",'','| 대형 탭 | 세부 화면 | 상태 | 섹션 수 | 필요한 자료 |','|---|---|---|---:|---|']
connected=pending=0
for m in modules:
    for v in meta['modules'][m['id']].get('subviews',[]):
        connected+=v['status']=='connected';pending+=v['status']=='pending'
        views.append(f"| {m['title']} | {v['name']} | {'연결' if v['status']=='connected' else '미연결'} | {v['sections']} | {v['reason'] if v['status']=='pending' else ''} |")
views[2]+=f' 현재 화면 그룹 목록: 연결 {connected}개, 미연결 {pending}개. 이 숫자는 완성된 원본 세부 기능 수가 아닙니다. RS/모멘텀과 원본의 중첩 화면·그룹 내부 기능은 별도 대조가 필요하며 [원본 기능 대조](REFERENCE_PARITY.md)에서 관리합니다.'
(ROOT/'research/SUBVIEWS.md').write_text('\n'.join(views)+'\n',encoding='utf8')
print('Updated 25 module guides, implementation status and chart parity.')
