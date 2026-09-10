"""Refresh each tab's implementation handoff from the built public snapshots."""
import json,re
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
load=lambda p:json.loads(p.read_text(encoding='utf8'))
modules=json.loads((ROOT/'docs/modules.js').read_text(encoding='utf8').removeprefix('const MODULES = ').rstrip().removesuffix(';'))
meta=load(ROOT/'docs/data/status.json')
CODE={
 'rs':'market_modules.py · build.py · analytics.py · universe.py','momentum':'build.py · analytics.py · universe.py · momentum_highs.py · us100_data.py',
 'etfmon':'etf_details.py','multiasset':'market_modules.py','dynamics':'market_modules.py','watch':'market_modules.py · patterns.py',
 'regime':'macro_modules.py','risk':'macro_modules.py · option_analytics.py','pm_weekend':'macro_modules.py','geoecon':'macro_modules.py',
 'earnings':'financial_modules.py','growth':'financial_modules.py · local_consensus.py','discovery':'discovery.py · financial_modules.py','strategies':'financial_modules.py',
 'quant':'quant_modules.py','ml':'ml_models.py · ml_features.py · ml_ensemble.py · ml_transformer.py · ml_views.py','maximus':'maximus_model.py · maximus_features.py · maximus_moe.py · maximus_views.py',
 'principium':'platform_modules.py','ask_digest':'platform_modules.py','iw':'platform_modules.py','aragorn':'platform_modules.py','dragonglass':'platform_modules.py','globe':'platform_modules.py',
}
for key in ['regime','risk','pm_weekend','geoecon','strategies','earnings','dragonglass','ask_digest','multiasset']:
    CODE[key]+=' · subview_modules.py'
for key in ['strategies','earnings','geoecon']:CODE[key]+=' · events_data.py'
for key in ['risk','pm_weekend']:CODE[key]+=' · cot_data.py'
CODE['regime']+=' · reflexivity.py · industry_details.py'
CODE['regime']+=' · valuation.py · calendar_data.py · kr_calendar.py · calendar_views.py'
CODE['pm_weekend']+=' · pm_details.py · gpr_data.py'
CODE['risk']+=' · wagdog.py · kr_shortgamma.py · kr_shortgamma_data.py'
CODE['geoecon']+=' · geoecon_views.py · gpr_data.py'
CODE['earnings']+=' · earnings_details.py'
CODE['strategies']+=' · sec_ownership.py · ownership_views.py'
CODE['dragonglass']+=' · entities.py · relation_model.py · relation_views.py'
CODE['multiasset']+=' · asset_monitor.py · allocation_model.py · allocation_views.py · technical_scan.py · oecd_data.py'
CODE['watch']+=' · technical_scan.py'
for key in ['risk','pm_weekend','earnings']:CODE[key]+=' · flows.py · flows_data.py'
# Original structures were read from the saved source and chart captions, offline.
PARITY={
 'overview':('TESSERACT6축·CROWDING5축·36월3D·4시점 적층·주도주','6/5축 원단위와 z·36시점 궤적/회전·4층 레이더·시총50표본/주도주10·현황','원본 z 창/극단치 설정·세계 전체 시총50·역사 발표 빈티지 동등성 미확보'),
 'glance':('4단계 프로세스·구조·출처','PC 수집→검증→Vercel·평일08/18시 갱신·512MiB 변경분 캐시','원본 Mac 서버 운영 대신 승인된 PC 실행 일정 사용'),
 'maximus':('지수·종목·거시 예측, 전문가 가중치·신호·시계열','2기본지수+Nasdaq·6매크로·종목 캐시·10전문가/ADF/SIS/게이트·68/95팬·R/I·원장','지수 이익앵커·SEC/KR수급·일부 입력·부분월/임의 티커 서버·PIT 미연결'),
 'dragonglass':('11개 하위 화면, 관계·시설·관측·원장','39객체·근거·3D/전파·8시나리오·701Entity·22시설RGB/NDVI·NASA배경·원장 프리모템/상관','전체255객체/581관계·고해상도 배경/지명·선행/후행·구루/사건·팀DB 미연결'),
 'aragorn':('3D 관계 탐색·자산 연간 퀼트','회전·객체 선택·11자산 2016~현재 연간 순위','인과 추정 관계 대신 공식 시장/업종 소속'),
 'globe':('지구본·국가/기업 탐색·교역 관계','로컬 지도 경계·정사영 회전·국가/기업 선택·수치표','본사 좌표·교역 경로/품목/금액은 미연결'),
 'principium':('3유형·5단 상세·제목 관계지도·키워드 구체·등록/첨부','팀 작성/개인 리서치·5단 상세·공유 키워드 지도·회전 구체·PDF/이미지·휴지통/백업','스캔 OCR/LLM 요약·팀 공용 DB/인증·서버 방문 통계 미연결'),
 'regime':('US/KR 성장×물가 4분면·전이 표·RSI 이중축·거시 선','양국 국면·전이·주간 RSI/가격·성장/물가·한미13출처90일달력·국가/기간/분류검색','원본 세부 상태 판정·발표 시점 빈티지 동등성 미검증'),
 'rs':('35개 5Y z, 0/±1/±2·중앙 음영, 섹터 막대/히트맵, 강8약8표/8+6막대·15위표','공식35페어·고정축·KR/US 1W강약8표·1M막대·KOSPI200 KPI·시장필터·3유니버스 순위','조선 신규 상장으로 5Y 준비 구간 부족, z 비공개 세부 설정 미검증'),
 'momentum':('32자산·24섹터, 강8/약8×3M/6M=32곡선·미국/한국 신고가 카드','5기간·그룹별정렬·짝곡선·OEF101/KOSPI200 공식 신고가·RS/고점점선/44점·검색/시장필터','조선5Y·누적 곡선/원본 사전표본·PIT 동등성 미검증'),
 'discovery':('4개 분류·3개 평가축·공식 유니버스 발굴','KR기술100%, US45/30/25%, 시장·분류·검색·더 보기·근거 상세','비공개 정규화/리서치 서술 엔진 대신 공개 팀 규칙'),
 'strategies':('전략별 후보·재무·OHLC·이벤트 결과','흑자전환·OHLC·PEAD 시각정렬·SEC P 원문/접수 대조·90일 카드/원장','SEC 자동수집 접근 제한·Form4/A·13F·공매도 원장·비용 후 OOS'),
 'earnings':('US/KR 이익성장·글로벌 Top20 겹침막대·한국2/미국10 추정 상세·연간/분기 선택','보고 NI/OP/매출·국내 QuantiWise OP/지배NI·미국 EPS 연결 NI 근사/직접 매출·회계기간/통화 검사','해외 직접 NI/OP 컨센서스·역사 PIT·한국 증권사별 원문 미확보'),
 'growth':('FY1/FY2 3D: x영업이익성장 yYTD z영업이익률, 시총 크기','국내 두 3D 회전·확대·시총, 글로벌 EPS 별도 표','해외 영업이익 컨센서스 부족으로 글로벌 3D 전체 범위 차이'),
 'multiasset':('21자산4KPI·6군신호표·열지도/추세막대·실제지수·37자산 스캐너·배분/성과','12지표·90봉 스캐너, Boruta/앙상블/Markov/LSTM·33자산8그룹·96월성과/12월비중','74입력/제약/하이퍼파라미터는 팀 설정, 현재 수정 거시 빈티지의 OOS'),
 'risk':('옵션 GEX/스팟곡선·VIX/SKEW·CSD·포트폴리오 위험','3ETF 만기 제한 GEX·OI PCR, CSD·곡선·VaR/CVaR·스트레스','딜러 실제 포지션·전 만기·실제 팀 포트폴리오 없음'),
 'watch':('KR/US 상승6·하락4, 일/주봉·MA·거래량·패턴 근거','5기하 패턴·피벗·120일/52주·MA·ADX/DI/MA4조건·12지표 점수','미공개 판정/ADX 합성 점수 동등성 미검증, 적합도는 성공확률 아님'),
 'ml':('3지수×1M/3M, 실제 막대/예측선·68/90%·적중점·z/확률/가격·OOS','6타깃·11모델+2앙상블·Shadow/강제변수·TreeSHAP·3패널 비교·장기/36월·24월표','CAPE/감성 등 일부 입력·원본 하이퍼파라미터·PIT 빈티지 동등성 미검증'),
 'quant':('Stat Arb·8팩터·BAB·TSMOM·단기반전 5뷰','페어 z 0/±2·상관/Hurst/공적분/반감기·요인/비중·후보','현재 단면 스크리닝, 역사 구성·모든 전략 비용 후 OOS 필요'),
 'dynamics':('3지수+15주식, 8룩백×시간 변동성표면·β×τ·위험/가격·노출성과','18대상·표면 회전/시간·위상·0~100/65선·가격 우축·전일노출','21D/5D/expanding252는 명시적 팀 파라미터, 거래비용·차입금리 미반영'),
 'iw':('월말15복기·주간14연대기·국면/ML2그림·판단 원장','원점/실현 방향 집계·지난주 수치/차트 보존·36월3띠/7계열ML·기록별 그림 선택·첨부/백업','현재 자료 OOS 재구성·팀 국면 규칙이며 과거 실제 발행본/PIT/공용 DB 미연결'),
 'pm_weekend':('주말 매크로 다중 선·이중축·지표표','미국/한국 금리·물가·유동성 등 5년 패널·단위/최신일','원본 주간 서술 대신 자체 관측표'),
 'etfmon':('9분류·73위치, 수익률/분배/주기/현금흐름 통합표·배당락일 원장','9그룹·12M현금관측/시장종가·총수익률·금액변경·월간간격 상위·정렬/검색','운용사 NAV 분배율·실제 지급일·원금 반환/별도 자본이득·세금·미래 지급액은 구분'),
 'geoecon':('상황6·지역5·채널6·복합3·키워드·카테고리4·뉴스','제목15주제/4카테고리·30일/7일변화·6채널과보도후가격·3복합z·GPR3지수/8분류/8국가','팀 단어/채널 규칙·제한RSS범위·위성 배경/시설·원본 비공개 감성가중치 미연결'),
 'ask_digest':('시장 brief·3기간·10테마·16종목·21자산·위험/4지표·모듈요약','달력수익·사업공식출처·RS16·9위험관측·4차트·20모듈·로컬 질문/첨부','1~2기업 테마 표본·구루/전체뉴스량·자동 AI 질의 미연결'),
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
    elif key=='overview':block += ['- 계산: [overview_state.py](../../pipeline/overview_state.py) · [화면](../../docs/overview-views.js) · [결과](../../docs/data/overview_state.json)', '- [축·단위·발표 시차·표본 계산 계약](../OVERVIEW_CONTRACT.md)',f'- 남은 범위: {gap}','']
    else:block += [f'- 화면: [app.js](../../docs/app.js) · [전체 상태](../../docs/data/status.json)',f'- 남은 범위: {gap}','']
    block += ['[공식 분류·단위·날짜](../DATA_DEFINITIONS.md) · [차트 대응표](../CHART_PARITY.md) · [재계산 및 검사](../../README.md)','',
       '아래는 원본을 학습하며 작성한 설계 가이드다. 초기의 “필요/미확인” 표현은 위 현재 구현 상태를 우선해 읽는다.','<!-- implementation:end -->','']
    path.write_text(first+'\n'+'\n'.join(block)+'\n'+rest.lstrip('\n'),encoding='utf8')
status_lines += ['','## 이번 검증 범위','','Python 날짜·수익률·학습 타깃·미래 변경 불변성·기하 패턴 검증, 실제 스냅샷의 OHLC/행렬/그래프 검증, JS 전체 23개 데이터 탭과 모든 하위 섹션의 오프라인 렌더링을 검사한다. 대표 SVG는 브라우저 없이 래스터화하여 차트 배치와 한글을 확인한다. 브라우저 이벤트 전체나 원본 픽셀 일치 검증을 완료했다는 뜻은 아니다.','',
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
views[2]+=f' 공통 화면 그룹 목록: 연결 {connected}개, 미연결 {pending}개. 이 숫자는 완성된 원본 세부 기능 수가 아닙니다. RS/모멘텀의 별도 필터는 아래에 기록하며 원본의 중첩 화면·그룹 내부 기능은 [원본 기능 대조](REFERENCE_PARITY.md)에서 관리합니다.'
views += ['', '## RS·모멘텀의 별도 필터', '',
 '이 두 탭은 별도 렌더러를 사용하므로 위 공통 섹션 수에 합산하지 않습니다. 전체 보기는 각 필터를 함께 표시합니다.', '',
 '| 대형 탭 | 필터 | 연결 범위 |', '|---|---|---|',
 '| RS | 한국 / 미국 | 시장별 섹터 z 차트·강약 막대·강약 8종목 표 |',
 '| 모멘텀 | 국가·지역 | 국가 ETF 수익률 막대·기간별 비교표 |',
 '| 모멘텀 | 섹터 로테이션 | 섹터 z 순위·강8/약8의 3M/6M 쌍곡선 |',
 '| 모멘텀 | 팩터(스타일) | 팩터 ETF 수익률 막대·기간별 비교표 |',
 '| 모멘텀 | 자산군 | 자산군 수익률 막대·기간별 비교표 |',
 '| 모멘텀 | 신고가 발굴 | 공식 미국100/KOSPI200 선별·44점 가격선/고점 점선·시장/검색/고점 갱신 필터·전체 유니버스 원장 |', '',
 '[신고가 계산·구성 계약](NEW_HIGHS_CONTRACT.md) · [가격 계산 계약과 남은 차이](PRICE_CONTRACT.md)']
(ROOT/'research/SUBVIEWS.md').write_text('\n'.join(views)+'\n',encoding='utf8')
print('Updated 25 module guides, implementation status and chart parity.')
